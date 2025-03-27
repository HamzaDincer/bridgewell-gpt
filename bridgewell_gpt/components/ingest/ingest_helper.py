import logging
from pathlib import Path
import os
import shutil

from llama_index.core.readers import StringIterableReader
from llama_index.core.readers.base import BaseReader
from llama_index.core.readers.json import JSONReader
from llama_index.core.schema import Document
from llama_cloud_services import LlamaParse
from llama_index.core import SimpleDirectoryReader
from dotenv import load_dotenv
from bridgewell_gpt.paths import local_data_path

load_dotenv()

logger = logging.getLogger(__name__)
# Get API key from environment variable
LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")

if not LLAMA_CLOUD_API_KEY:
    logger.warning("LLAMA_CLOUD_API_KEY not found in environment variables")
else:
    logger.debug("LLAMA_CLOUD_API_KEY configured")

llama_parser = LlamaParse(api_key=LLAMA_CLOUD_API_KEY, result_type="markdown")

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
        ".pdf": PDFReader if not llama_parser else None,  # Use LlamaParse for PDFs if available
        ".docx": DocxReader if not llama_parser else None,  # Use LlamaParse for DOCX if available
        ".pptx": PptxReader if not llama_parser else None,  # Use LlamaParse for PPTX if available
        ".ppt": PptxReader if not llama_parser else None,  # Use LlamaParse for PPT if available
        ".pptm": PptxReader if not llama_parser else None,  # Use LlamaParse for PPTM if available
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
    # Remove None values (where LlamaParse will be used instead)
    return {k: v for k, v in default_file_reader_cls.items() if v is not None}

# Patching the default file reader to support other file types
FILE_READER_CLS = _try_loading_included_file_formats()
FILE_READER_CLS.update(
    {
        ".json": JSONReader,
    }
)

# File extensions that LlamaParse can handle
LLAMAPARSE_EXTENSIONS = {".pdf", ".docx", ".pptx", ".ppt", ".pptm"}

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
            # Copy the file preserving metadata
            shutil.copy2(file_data, file_path)
            logger.info(f"Successfully stored file at: {file_path}")
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
        logger.debug("Transforming file_name=%s into documents", file_name)
        extension = Path(file_name).suffix.lower()

        # Try LlamaParse first for supported file types
        if llama_parser and extension in LLAMAPARSE_EXTENSIONS:
            try:
                logger.info("Using LlamaParse for file_name=%s", file_name)
                # Use SimpleDirectoryReader with LlamaParse as the file extractor
                file_extractor = {extension: llama_parser}
                raw_documents = SimpleDirectoryReader(
                    input_files=[str(file_data)],
                    file_extractor=file_extractor,
                    filename_as_id=True,  # Use filename as document ID
                ).load_data()
                
                # Create new clean documents without unwanted metadata
                documents = []
                for raw_doc in raw_documents:
                    # Create a new document with only the essential metadata
                    clean_doc = Document(
                        text=raw_doc.text,
                        metadata={
                            "file_name": file_name,
                            "doc_id": raw_doc.doc_id
                        },
                        excluded_embed_metadata_keys=["file_name", "doc_id"],
                        excluded_llm_metadata_keys=["file_name", "doc_id", "page_label"],
                        relationships={},  # Reset relationships
                    )
                    documents.append(clean_doc)
                
                return documents
            except Exception as e:
                logger.warning(f"LlamaParse failed for {file_name}, falling back to default reader: {e}")

        # Fall back to default readers
        reader_cls = FILE_READER_CLS.get(extension)
        if reader_cls is None:
            logger.debug(
                "No reader found for extension=%s, using default string reader",
                extension,
            )
            try:
                # Try reading as text first
                text = file_data.read_text(errors='ignore')
            except Exception as e:
                logger.warning(f"Failed to read file as text: {e}")
                # If text reading fails, try binary and decode with errors ignored
                with open(file_data, 'rb') as f:
                    text = f.read().decode('utf-8', errors='ignore')
            
            string_reader = StringIterableReader()
            return string_reader.load_data([text])

        logger.debug("Specific reader found for extension=%s", extension)
        documents = reader_cls().load_data(file_data)

        # Sanitize NUL bytes in text which can't be stored in Postgres
        for i in range(len(documents)):
            documents[i].text = documents[i].text.replace("\u0000", "")

        return documents

    @staticmethod
    def _exclude_metadata(documents: list[Document]) -> None:
        logger.debug("Excluding metadata from count=%s documents", len(documents))
        for document in documents:
            document.metadata["doc_id"] = document.doc_id
            # We don't want the Embeddings search to receive this metadata
            document.excluded_embed_metadata_keys = [
                "doc_id", "file_path", "file_type", "file_size",
                "creation_date", "last_modified_date"
            ]
            # We don't want the LLM to receive these metadata in the context
            document.excluded_llm_metadata_keys = [
                "file_name", "doc_id", "page_label",
                "file_path", "file_type", "file_size",
                "creation_date", "last_modified_date"
            ]
