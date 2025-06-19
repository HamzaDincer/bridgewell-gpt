import logging
from pathlib import Path
import os
import shutil
from typing import List
import json
import tempfile

from llama_index.core.readers import StringIterableReader
from llama_index.core.readers.base import BaseReader
from llama_index.core.readers.json import JSONReader
from llama_index.core.schema import Document
from agentic_doc.parse import parse_documents
from bridgewell_gpt.components.extraction.extraction_component import ExtractionComponent
from bridgewell_gpt.paths import local_data_path
from bridgewell_gpt.server.document_types.document_type_service import DocumentTypeService

logger = logging.getLogger(__name__)

# Inspired by the `llama_index.core.readers.file.base` module
def _try_loading_included_file_formats() -> dict[str, type[BaseReader]]:
    try:
        from llama_index.readers.file.docs import (  # type: ignore
            DocxReader,
            HWPReader,
            PDFReader,
        )
        from llama_index.readers.file.epub import EpubReader  # type: ignore
        from llama_index.readers.file.image import ImageReader  # type: ignore
        from llama_index.readers.file.ipynb import IPYNBReader  # type: ignore
        from llama_index.readers.file.markdown import MarkdownReader  # type: ignore
        from llama_index.readers.file.mbox import MboxReader  # type: ignore
        from llama_index.readers.file.slides import PptxReader  # type: ignore
        from llama_index.readers.file.tabular import PandasCSVReader  # type: ignore
        from llama_index.readers.file.video_audio import (  # type: ignore
            VideoAudioReader,
        )
    except ImportError as e:
        raise ImportError("`llama-index-readers-file` package not found") from e

    default_file_reader_cls: dict[str, type[BaseReader]] = {
        ".hwp": HWPReader,
        ".jpg": ImageReader,
        ".png": ImageReader,
        ".jpeg": ImageReader,
        ".mp3": VideoAudioReader,
        ".mp4": VideoAudioReader,
        ".csv": PandasCSVReader,
        ".epub": EpubReader,
        ".md": MarkdownReader,
        ".mbox": MboxReader,
        ".ipynb": IPYNBReader,
    }
    return default_file_reader_cls

# Patching the default file reader to support other file types
FILE_READER_CLS = _try_loading_included_file_formats()
FILE_READER_CLS.update(
    {
        ".json": JSONReader,
    }
)

status_dir = local_data_path / "status"
status_dir.mkdir(parents=True, exist_ok=True)

class IngestionHelper:
    """Helper class to transform a file into a list of documents.

    This class should be used to transform a file into a list of documents.
    These methods are thread-safe (and multiprocessing-safe).
    """
    
    # Directory for storing original files
    
    original_files_dir = local_data_path / "original_files"
    original_files_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def store_original_file(file_name: str, file_data: Path) -> Path:
        """Store the original file in the original_files directory.
        
        Args:
            file_name: Name of the file
            file_data: Path to the file
            
        Returns:
            Path where the file was stored
        """
        logger.info(f"Storing original file: {file_name}")
        file_path = IngestionHelper.original_files_dir / file_name
        
        try:
            # Only copy if source and destination are different
            if Path(file_data).resolve() != file_path.resolve():
                # Use copyfile instead of copy for GCS FUSE compatibility (avoids all metadata operations)
                shutil.copyfile(file_data, file_path)
                logger.info(f"Successfully stored file at: {file_path}")
            else:
                logger.info(f"Source and destination are the same file, skipping copy: {file_path}")
                file_path = file_data
            return file_path
        except Exception as e:
            logger.error(f"Error storing file: {str(e)}")
            raise

    @staticmethod
    def transform_file_into_documents(
        file_name: str, file_data: Path
    ) -> list[Document]:
        """Transform a file into a list of documents.
        
        This method will:
        1. Store the original file
        2. Transform it into documents
        3. Add metadata
        4. Return the documents
        
        Args:
            file_name: Name of the file
            file_data: Path to the file
            
        Returns:
            List of documents created from the file
        """
        # Store the original file first
        try:
            IngestionHelper.store_original_file(file_name, file_data)
        except Exception as e:
            logger.error(f"Failed to store original file {file_name}: {str(e)}")
            # Continue with document creation even if storage fails
        
        # Transform file into documents
        documents = IngestionHelper._load_file_to_documents(file_name, file_data)
        for document in documents:
            document.metadata["file_name"] = file_name
        IngestionHelper._exclude_metadata(documents)
        return documents

    @staticmethod
    def _load_file_to_documents(file_name: str, file_data: Path) -> list[Document]:
        """Load a file into a list of documents.
        
        Args:
            file_name: Name of the file
            file_data: Path to the file
            
        Returns:
            List of documents with metadata including grounding info for extraction
        """
        logger.info(f"Loading file {file_name}")

        # Try agentic-doc first for all files
        try:
            logger.info(f"Using agentic-doc parser for {file_name}")
            file_path = file_data.resolve()  # Get absolute path
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
                
            parsed_docs = parse_documents([str(file_path)])
            
            if parsed_docs:
                parsed_doc = parsed_docs[0]
                documents = []
                for chunk in parsed_doc.chunks:
                    bbox = [g.box.dict() for g in chunk.grounding] if chunk.grounding else None
                    doc = Document(
                        text=chunk.text,
                        metadata={
                            "file_name": file_name,
                            "chunk_type": chunk.chunk_type.value if hasattr(chunk, 'chunk_type') else None,
                            "chunk_id": chunk.chunk_id if hasattr(chunk, 'chunk_id') else None,
                            "page": chunk.grounding[0].page if chunk.grounding else None,
                            "bbox": bbox
                        }
                    )
                    documents.append(doc)
                
                logger.info(f"Successfully parsed {len(documents)} chunks with agentic-doc")
                return documents
            else:
                logger.warning("No documents parsed by agentic-doc, falling back to default reader")
        except Exception as e:
            logger.warning(f"agentic-doc failed for {file_name}, falling back to default reader: {e}")
        
        # Try default reader if available
        file_extension = file_data.suffix.lower()
        reader_cls = FILE_READER_CLS.get(file_extension)
        if reader_cls:
            try:
                logger.info(f"Using default reader {reader_cls.__name__} for {file_name}")
                reader = reader_cls()
                documents = reader.load_data(file_data)
                
                # Add file name to metadata
                for doc in documents:
                    doc.metadata["file_name"] = file_name
                
                logger.info(f"Successfully loaded {len(documents)} documents with default reader")
                return documents
            except Exception as e:
                logger.warning(f"Default reader failed for {file_name}, falling back to string reader: {e}")

        # Fall back to string reader as last resort
        try:
            logger.info(f"Attempting to read {file_name} as text")
            try:
                # Try reading as text first
                text = file_data.read_text(errors='ignore')
            except Exception as text_e:
                logger.warning(f"Failed to read as text, trying binary: {text_e}")
                # If text reading fails, try binary and decode
                with open(file_data, 'rb') as f:
                    text = f.read().decode('utf-8', errors='ignore')
            
            string_reader = StringIterableReader()
            documents = string_reader.load_data([text])

            # Add file name to metadata
            for doc in documents:
                doc.metadata["file_name"] = file_name

            logger.info(f"Successfully loaded file as text, created {len(documents)} documents")
            return documents
        except Exception as e:
            error_msg = f"Failed to load file {file_name} with any available reader: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    @staticmethod
    def _exclude_metadata(documents: list[Document]) -> None:
        logger.debug("Excluding metadata from count=%s documents", len(documents))
        for document in documents:
            document.metadata["doc_id"] = document.doc_id
            # We don't want the Embeddings search to receive this metadata
            document.excluded_embed_metadata_keys = [
                "doc_id", "file_path", "file_type", "file_size",
                "raw_chunk","chunk_type","chunk_id", 
                "extraction", "extraction_id", "document_type",
                "page_label", "page", "bbox",
                "creation_date", "last_modified_date"
            ]
            # We don't want the LLM to receive these metadata in the context
            document.excluded_llm_metadata_keys = [
                "file_name", "doc_id",  "page_label", "chunk_type", "chunk_id", 
                "raw_chunk", "extraction", "extraction_id", "document_type",
                "file_path", "file_type", "file_size",
                "creation_date", "last_modified_date"
            ]

    @staticmethod
    def write_status(doc_id: str, phase: str) -> None:
        # No-op: phase update is now handled in the background ingestion component to avoid circular import
        pass

    @staticmethod
    def read_status(doc_id: str) -> str | None:
        # No longer used; phase is now stored in document_types.json
        return None
