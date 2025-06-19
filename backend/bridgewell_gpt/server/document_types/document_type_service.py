import json
import logging
import os
import fcntl
from typing import List
from injector import singleton
from datetime import datetime
import tempfile
import pytz

from bridgewell_gpt.paths import local_data_path
from .document_type_models import DocumentTypeResponse, DocumentTypeCreate, DocumentCreate, DocumentResponse

logger = logging.getLogger(__name__)

@singleton
class DocumentTypeService:
    def __init__(self):
        self._data_path = local_data_path / "document_types.json"
        self._ensure_data_file()
        logger.debug(f"DocumentTypeService initialized, using data file: {self._data_path}")

    def _ensure_data_file(self):
        """Creates the data file with an empty list if it doesn't exist or is empty (0 bytes), using atomic write and file locking."""
        try:
            if not self._data_path.exists():
                self._data_path.parent.mkdir(parents=True, exist_ok=True)
                tmp_path = str(self._data_path) + ".tmp"
                with open(tmp_path, 'w') as tmp_file:
                    fcntl.flock(tmp_file, fcntl.LOCK_EX)
                    json.dump([], tmp_file)
                    tmp_file.flush()
                    os.fsync(tmp_file.fileno())
                    fcntl.flock(tmp_file, fcntl.LOCK_UN)
                os.replace(tmp_path, self._data_path)
                logger.debug(f"Created empty document types data file: {self._data_path}")
            else:
                # If file exists but is empty (0 bytes), repair it atomically
                if self._data_path.stat().st_size == 0:
                    tmp_path = str(self._data_path) + ".tmp"
                    with open(tmp_path, 'w') as tmp_file:
                        fcntl.flock(tmp_file, fcntl.LOCK_EX)
                        json.dump([], tmp_file)
                        tmp_file.flush()
                        os.fsync(tmp_file.fileno())
                        fcntl.flock(tmp_file, fcntl.LOCK_UN)
                    os.replace(tmp_path, self._data_path)
                    logger.debug(f"Repaired empty document types data file: {self._data_path}")
        except Exception as e:
            logger.error(f"Error ensuring data file {self._data_path}: {e}", exc_info=True)
            raise

    def _load_data(self) -> List[dict]:
        """Loads the document type data from the JSON file."""
        try:
            with open(self._data_path, 'r') as f:
                data = json.load(f)
                # Basic validation
                if not isinstance(data, list):
                    logger.error(f"Data file {self._data_path} does not contain a list. Resetting.")
                    return []
                return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading data from {self._data_path}: {e}. Returning empty list.")
            return [] # Return empty list if file is missing or corrupt
        except Exception as e:
            logger.error(f"Unexpected error loading data from {self._data_path}: {e}", exc_info=True)
            return []

    def _save_data(self, data: List[dict]):
        """Saves the document type data to the JSON file atomically and safely, using a unique temp file per write."""
        try:
            self._data_path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile('w', dir=self._data_path.parent, delete=False) as tmp_file:
                fcntl.flock(tmp_file, fcntl.LOCK_EX)
                json.dump(data, tmp_file, indent=2)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
                fcntl.flock(tmp_file, fcntl.LOCK_UN)
                tmp_path = tmp_file.name
            os.replace(tmp_path, self._data_path)
        except Exception as e:
            logger.error(f"Error saving data to {self._data_path}: {e}", exc_info=True)
            raise

    def get_document_types(self) -> List[DocumentTypeResponse]:
        """Retrieve document types from the JSON file."""
        logger.debug("DocumentTypeService: Fetching document types from file")
        data = self._load_data()
        # Convert dicts to the Pydantic response model
        return [DocumentTypeResponse(**item) for item in data]

    def create_document_type(self, type_create: DocumentTypeCreate) -> dict:
        """Creates a new document type and saves it to the JSON file. Returns a dict with alreadyExists flag."""
        logger.debug(f"DocumentTypeService: Creating document type '{type_create.title}'")
        data = self._load_data()
        # Check for existing title
        if any(item['title'].lower() == type_create.title.lower() for item in data):
            logger.warning(f"Document type with title '{type_create.title}' already exists.")
            existing = next((item for item in data if item['title'].lower() == type_create.title.lower()), None)
            if existing:
                return {"alreadyExists": True, "type": DocumentTypeResponse(**existing)}
            raise ValueError(f"Duplicate title error for '{type_create.title}'") 
        # Determine the next ID
        new_id = max((item['id'] for item in data), default=100) + 1
        new_type_data = {
            "id": new_id,
            "title": type_create.title,
            "uploaded": 0,
            "review_pending": 0,
            "approved": 0,
            "setup_required": True,
            "documents": []
        }
        data.append(new_type_data)
        self._save_data(data)
        logger.debug(f"Successfully created document type ID {new_id} with title '{type_create.title}'")
        return {"alreadyExists": False, "type": DocumentTypeResponse(**new_type_data)}

    def add_document(self, type_id: int, document: DocumentCreate) -> DocumentTypeResponse:
        """Add a document to a document type."""
        logger.debug(f"DocumentTypeService: Adding document '{document.doc_name}' to type {type_id}")
        data = self._load_data()
        # Find the document type
        type_data = next((item for item in data if item['id'] == type_id), None)
        if not type_data:
            raise ValueError(f"Document type with ID {type_id} not found")
        # Prevent duplicate documents by id only
        if any(doc['id'] == document.doc_id for doc in type_data['documents']):
            logger.warning(f"Document with id={document.doc_id} already exists in type {type_id}, skipping append.")
            return DocumentTypeResponse(**type_data)
        # Create new document entry with initial phase
        toronto_tz = pytz.timezone('America/Toronto')
        new_doc = {
            "id": document.doc_id,
            "name": document.doc_name,
            "date_added": datetime.now(toronto_tz).isoformat(),
            "phase": "uploading"
        }
        # Add document to type
        type_data['documents'].append(new_doc)
        type_data['uploaded'] = len(type_data['documents'])
        self._save_data(data)
        logger.debug(f"Successfully added document to type {type_id}")
        return DocumentTypeResponse(**type_data)

    def get_documents(self, type_id: int) -> List[DocumentResponse]:
        """Get all documents for a document type, using the stored phase."""
        logger.debug(f"DocumentTypeService: Getting documents for type {type_id}")
        data = self._load_data()
        # Find the document type
        type_data = next((item for item in data if item['id'] == type_id), None)
        if not type_data:
            raise ValueError(f"Document type with ID {type_id} not found")
        documents = []
        for doc in type_data.get('documents', []):
            documents.append(doc)
        return [DocumentResponse(**doc) for doc in documents]

    def update_document_type_counts(self, type_id: int, uploaded: int = None, pending: int = None, approved: int = None) -> DocumentTypeResponse:
        """Update the counts for a document type."""
        data = self._load_data()
        for item in data:
            if item['id'] == type_id:
                if uploaded is not None:
                    item['uploaded'] = uploaded
                if pending is not None:
                    item['review_pending'] = pending
                if approved is not None:
                    item['approved'] = approved
                self._save_data(data)
                return DocumentTypeResponse(**item)
        raise ValueError(f"Document type with ID {type_id} not found")

    def update_document_phase(self, doc_id: str, phase: str) -> None:
        """Update the phase of a document in document_types.json."""
        data = self._load_data()
        for type_data in data:
            for doc in type_data.get('documents', []):
                if doc['id'] == doc_id:
                    doc['phase'] = phase
                    self._save_data(data)
                    logger.debug(f"Updated phase for doc_id={doc_id} to {phase}")
                    return
        logger.warning(f"Document with id={doc_id} not found for phase update.")

    def delete_document_completely(self, doc_id: str) -> dict:
        """
        Completely delete a document and all its associated data.
        
        This will delete:
        - Document from vector store and node store (embeddings and chunks)
        - Original file from storage
        - Extraction results directory 
        - Document entry from document_types.json
        
        Args:
            doc_id: The document ID to delete
            
        Returns:
            Dictionary containing deletion results and any errors
        """
        import shutil
        from pathlib import Path
        
        logger.info(f"Starting comprehensive deletion for document: {doc_id}")
        
        deletion_results = {
            "doc_id": doc_id,
            "deleted_components": [],
            "errors": [],
            "warnings": []
        }
        
        # 1. Get document information before deletion
        doc_info = self._get_document_info(doc_id)
        if not doc_info:
            deletion_results["warnings"].append(f"Document {doc_id} not found in document types")
        
        # 2. Delete from vector store and node store (using existing ingest service)
        try:
            from bridgewell_gpt.di import global_injector
            from bridgewell_gpt.server.ingest.ingest_service import IngestService
            ingest_service = global_injector.get(IngestService)
            ingest_service.delete(doc_id)
            deletion_results["deleted_components"].append("vector_store_and_nodes")
            logger.info(f"Successfully deleted {doc_id} from vector store and node store")
        except Exception as e:
            error_msg = f"Failed to delete from vector/node stores: {str(e)}"
            deletion_results["errors"].append(error_msg)
            logger.error(error_msg)
        
        # 3. Delete original file (only if no other documents reference it)
        if doc_info and doc_info.get("file_name"):
            try:
                file_name = doc_info["file_name"]
                # Check if any other documents reference this file
                if self._is_file_referenced_by_other_documents(doc_id, file_name):
                    deletion_results["warnings"].append(f"Original file '{file_name}' is referenced by other documents, skipping deletion")
                    logger.info(f"Skipping deletion of original file '{file_name}' - referenced by other documents")
                else:
                    original_files_dir = local_data_path / "original_files"
                    file_path = original_files_dir / file_name
                    if file_path.exists():
                        file_path.unlink()
                        logger.debug(f"Deleted original file: {file_path}")
                        deletion_results["deleted_components"].append("original_file")
                        logger.info(f"Successfully deleted original file: {file_name}")
                    else:
                        deletion_results["warnings"].append(f"Original file '{file_name}' not found on disk")
            except Exception as e:
                error_msg = f"Failed to delete original file: {str(e)}"
                deletion_results["errors"].append(error_msg)
                logger.error(error_msg)
        else:
            deletion_results["warnings"].append("No file name found, skipping original file deletion")
        
        # 4. Delete extraction results directory
        try:
            extraction_results_dir = local_data_path / "extraction_results" / doc_id
            if extraction_results_dir.exists():
                shutil.rmtree(extraction_results_dir)
                logger.debug(f"Deleted extraction results directory: {extraction_results_dir}")
            deletion_results["deleted_components"].append("extraction_results")
            logger.info(f"Successfully deleted extraction results for: {doc_id}")
        except Exception as e:
            error_msg = f"Failed to delete extraction results: {str(e)}"
            deletion_results["errors"].append(error_msg)
            logger.error(error_msg)
        
        # 5. Remove document from document_types.json
        try:
            if self._delete_document_from_types(doc_id):
                deletion_results["deleted_components"].append("document_type_entry")
                logger.info(f"Successfully removed document entry from document types: {doc_id}")
            else:
                deletion_results["warnings"].append("Document entry not found in document types")
        except Exception as e:
            error_msg = f"Failed to remove from document types: {str(e)}"
            deletion_results["errors"].append(error_msg)
            logger.error(error_msg)
        
        # Summary
        total_components = len(deletion_results["deleted_components"])
        total_errors = len(deletion_results["errors"])
        
        if total_errors == 0:
            logger.info(f"Successfully completed comprehensive deletion of {doc_id}. Deleted {total_components} components.")
            deletion_results["status"] = "success"
        else:
            logger.warning(f"Partial deletion of {doc_id}. Deleted {total_components} components with {total_errors} errors.")
            deletion_results["status"] = "partial_success"
        
        return deletion_results

    def _get_document_info(self, doc_id: str) -> dict | None:
        """Get document information from document types."""
        try:
            data = self._load_data()
            for type_data in data:
                for doc in type_data.get('documents', []):
                    if doc['id'] == doc_id:
                        return {
                            "file_name": doc.get("name"),  # Using 'name' field as file_name
                            "document_type": type_data.get("title", "Unknown"),
                            "document_entry": doc
                        }
        except Exception as e:
            logger.warning(f"Error getting document info for {doc_id}: {str(e)}")
        return None

    def _is_file_referenced_by_other_documents(self, current_doc_id: str, file_name: str) -> bool:
        """Check if the file is referenced by any documents other than the current one."""
        try:
            data = self._load_data()
            for type_data in data:
                for doc in type_data.get('documents', []):
                    # Skip the current document we're deleting
                    if doc['id'] == current_doc_id:
                        continue
                    # Check if another document has the same file name
                    if doc.get("name") == file_name:
                        logger.debug(f"File '{file_name}' is referenced by document {doc['id']}")
                        return True
            return False
        except Exception as e:
            logger.warning(f"Error checking file references for {file_name}: {str(e)}")
            # If we can't check, err on the side of caution and don't delete
            return True

    def _delete_document_from_types(self, doc_id: str) -> bool:
        """Delete a document from document_types.json and update counts."""
        logger.debug(f"DocumentTypeService: Deleting document {doc_id}")
        data = self._load_data()
        
        for type_data in data:
            documents = type_data.get('documents', [])
            original_count = len(documents)
            
            # Filter out the document with matching doc_id
            type_data['documents'] = [doc for doc in documents if doc['id'] != doc_id]
            
            # If a document was removed, update counts and save
            if len(type_data['documents']) < original_count:
                type_data['uploaded'] = len(type_data['documents'])
                # Update other counts based on remaining documents
                type_data['review_pending'] = len([doc for doc in type_data['documents'] if doc.get('phase') == 'review_pending'])
                type_data['approved'] = len([doc for doc in type_data['documents'] if doc.get('phase') == 'approved'])
                
                self._save_data(data)
                logger.info(f"Successfully deleted document {doc_id} from document type '{type_data['title']}'")
                return True
        
        logger.warning(f"Document {doc_id} not found in any document type")
        return False

 