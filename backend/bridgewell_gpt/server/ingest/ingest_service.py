import logging
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, AnyStr, BinaryIO, Any, List

from injector import inject, singleton
from llama_index.core.node_parser import SentenceWindowNodeParser
from llama_index.core.storage import StorageContext

from bridgewell_gpt.components.embedding.embedding_component import EmbeddingComponent
from bridgewell_gpt.components.ingest.ingest_component import get_ingestion_component
from bridgewell_gpt.components.llm.llm_component import LLMComponent
from bridgewell_gpt.components.node_store.node_store_component import NodeStoreComponent
from bridgewell_gpt.components.vector_store.vector_store_component import (
    VectorStoreComponent,
)
from bridgewell_gpt.server.ingest.model import IngestedDoc
from bridgewell_gpt.settings.settings import settings
from bridgewell_gpt.server.chat.chat_service import ChatService

if TYPE_CHECKING:
    from llama_index.core.storage.docstore.types import RefDocInfo

logger = logging.getLogger(__name__)


@singleton
class IngestService:
    @inject
    def __init__(
        self,
        llm_component: LLMComponent,
        vector_store_component: VectorStoreComponent,
        embedding_component: EmbeddingComponent,
        node_store_component: NodeStoreComponent,
        chat_service: ChatService,
    ) -> None:
        self.llm_service = llm_component
        self.storage_context = StorageContext.from_defaults(
            vector_store=vector_store_component.vector_store,
            docstore=node_store_component.doc_store,
            index_store=node_store_component.index_store,
        )
        node_parser = SentenceWindowNodeParser.from_defaults()
        self.chat_service = chat_service

        self.ingest_component = get_ingestion_component(
            self.storage_context,
            embed_model=embedding_component.embedding_model,
            transformations=[node_parser],
            settings=settings(),
            ingest_service=self,
            chat_service=self.chat_service,
        )

    def _ingest_data(self, file_name: str, file_data: AnyStr) -> list[IngestedDoc]:
        logger.debug("Got file data of size=%s to ingest", len(file_data))
        # llama-index mainly supports reading from files, so
        # we have to create a tmp file to read for it to work
        # delete=False to avoid a Windows 11 permission error.
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            try:
                path_to_tmp = Path(tmp.name)
                if isinstance(file_data, bytes):
                    path_to_tmp.write_bytes(file_data)
                else:
                    path_to_tmp.write_text(str(file_data))
                return self.ingest_file(file_name, path_to_tmp)
            finally:
                tmp.close()
                path_to_tmp.unlink()

    def ingest_file(self, file_name: str, file_data: Path) -> list[IngestedDoc]:
        logger.info("Ingesting file_name=%s", file_name)
        documents = self.ingest_component.ingest(file_name, file_data)
        logger.info("Finished ingestion file_name=%s", file_name)
        return [IngestedDoc.from_document(document) for document in documents]

    def ingest_text(self, file_name: str, text: str) -> list[IngestedDoc]:
        logger.debug("Ingesting text data with file_name=%s", file_name)
        return self._ingest_data(file_name, text)

    def ingest_bin_data(
        self, file_name: str, raw_file_data: BinaryIO
    ) -> list[IngestedDoc]:
        logger.debug("Ingesting binary data with file_name=%s", file_name)
        file_data = raw_file_data.read()
        return self._ingest_data(file_name, file_data)

    def bulk_ingest(self, files: list[tuple[str, Path]]) -> list[IngestedDoc]:
        logger.info("Ingesting file_names=%s", [f[0] for f in files])
        documents = self.ingest_component.bulk_ingest(files)
        logger.info("Finished ingestion file_name=%s", [f[0] for f in files])
        return [IngestedDoc.from_document(document) for document in documents]

    def list_ingested(self) -> list[IngestedDoc]:
        ingested_docs: list[IngestedDoc] = []
        try:
            docstore = self.storage_context.docstore
            ref_docs: dict[str, RefDocInfo] | None = docstore.get_all_ref_doc_info()

            if not ref_docs:
                return ingested_docs

            for doc_id, ref_doc_info in ref_docs.items():
                doc_metadata = None
                if ref_doc_info is not None and ref_doc_info.metadata is not None:
                    doc_metadata = IngestedDoc.curate_metadata(ref_doc_info.metadata)
                ingested_docs.append(
                    IngestedDoc(
                        object="ingest.document",
                        doc_id=doc_id,
                        doc_metadata=doc_metadata,
                    )
                )
        except ValueError:
            logger.warning("Got an exception when getting list of docs", exc_info=True)
            pass
        logger.debug("Found count=%s ingested documents", len(ingested_docs))
        return ingested_docs

    def delete(self, doc_id: str) -> None:
        """Delete an ingested document.

        :raises ValueError: if the document does not exist
        """
        logger.info(
            "Deleting the ingested document=%s in the doc and index store", doc_id
        )
        self.ingest_component.delete(doc_id)

    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        """Get a document's content and metadata by its ID.

        Args:
            doc_id: The ID of the document to retrieve.

        Returns:
            A dictionary containing the document's content and metadata, or None if not found.
        """
        try:
            docstore = self.storage_context.docstore
            ref_doc_info = docstore.get_ref_doc_info(doc_id)
            if not ref_doc_info:
                return None

            # Get all nodes for this document
            nodes = docstore.get_nodes(ref_doc_info.node_ids)
            # Combine the text from all nodes
            text = "\n".join(node.get_content() for node in nodes)
            return {
                "text": text,
                "metadata": IngestedDoc.curate_metadata(ref_doc_info.metadata) if ref_doc_info.metadata else None
            }
        except Exception:
            logger.warning(f"Document {doc_id} not found or error occurred", exc_info=True)
            return None

    def extract_benefit_pages(self, file_name: str, page_numbers: List[int]) -> Path:
        """Extract benefit summary pages from a PDF file.
        
        Args:
            file_name: Name of the file to extract pages from
            page_numbers: List of page numbers to extract (1-based indexing)
            
        Returns:
            Path to the new PDF containing only the specified pages
        """
        # Get the original file path
        original_file_path = self.ingest_component.storage_context.docstore.get_ref_doc_info(file_name)
        if not original_file_path:
            # Try looking in the original_files directory
            original_file_path = Path(self.ingest_component.storage_context.persist_dir) / "original_files" / file_name
            if not original_file_path.exists():
                raise FileNotFoundError(f"Original file not found: {file_name}")
        
        # Extract the specified pages
        from bridgewell_gpt.components.ingest.ingest_helper import IngestionHelper
        output_name = f"{Path(file_name).stem}_benefit_summary.pdf"
        extracted_path = IngestionHelper.extract_pdf_pages(
            file_path=original_file_path,
            page_numbers=page_numbers,
            output_name=output_name
        )
        
        logger.info(f"Successfully extracted benefit summary pages to: {extracted_path}")
        return extracted_path
