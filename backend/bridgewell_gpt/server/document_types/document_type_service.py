import json
import logging
from pathlib import Path
from typing import List
from injector import singleton
from datetime import datetime

from bridgewell_gpt.paths import local_data_path
from .document_type_models import DocumentTypeResponse, DocumentTypeCreate, DocumentCreate, DocumentResponse

logger = logging.getLogger(__name__)

@singleton
class DocumentTypeService:
    def __init__(self):
        self._data_path = local_data_path / "document_types.json"
        self._ensure_data_file()
        logger.info(f"DocumentTypeService initialized, using data file: {self._data_path}")

    def _ensure_data_file(self):
        """Creates the data file with an empty list if it doesn't exist."""
        try:
            if not self._data_path.exists():
                self._data_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self._data_path, 'w') as f:
                    json.dump([], f)
                logger.info(f"Created empty document types data file: {self._data_path}")
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
        """Saves the document type data to the JSON file."""
        try:
            with open(self._data_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving data to {self._data_path}: {e}", exc_info=True)
            raise

    def get_document_types(self) -> List[DocumentTypeResponse]:
        """Retrieve document types from the JSON file."""
        logger.info("DocumentTypeService: Fetching document types from file")
        data = self._load_data()
        # Convert dicts to the Pydantic response model
        return [DocumentTypeResponse(**item) for item in data]

    def create_document_type(self, type_create: DocumentTypeCreate) -> DocumentTypeResponse:
        """Creates a new document type and saves it to the JSON file."""
        logger.info(f"DocumentTypeService: Creating document type '{type_create.title}'")
        data = self._load_data()
        
        # Check for existing title
        if any(item['title'].lower() == type_create.title.lower() for item in data):
            logger.warning(f"Document type with title '{type_create.title}' already exists.")
            existing = next((item for item in data if item['title'].lower() == type_create.title.lower()), None)
            if existing:
                 return DocumentTypeResponse(**existing)
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
        logger.info(f"Successfully created document type ID {new_id} with title '{type_create.title}'")
        return DocumentTypeResponse(**new_type_data)

    def add_document(self, type_id: int, document: DocumentCreate) -> DocumentTypeResponse:
        """Add a document to a document type."""
        logger.info(f"DocumentTypeService: Adding document '{document.doc_name}' to type {type_id}")
        data = self._load_data()
        
        # Find the document type
        type_data = next((item for item in data if item['id'] == type_id), None)
        if not type_data:
            raise ValueError(f"Document type with ID {type_id} not found")

        # Create new document entry
        new_doc = {
            "id": document.doc_id,
            "name": document.doc_name,
            "status": "pending",
            "date_added": datetime.now().isoformat()
        }

        # Add document to type
        type_data['documents'].append(new_doc)
        type_data['uploaded'] = len(type_data['documents'])
        
        self._save_data(data)
        logger.info(f"Successfully added document to type {type_id}")
        return DocumentTypeResponse(**type_data)

    def get_documents(self, type_id: int) -> List[DocumentResponse]:
        """Get all documents for a document type."""
        logger.info(f"DocumentTypeService: Getting documents for type {type_id}")
        data = self._load_data()
        
        # Find the document type
        type_data = next((item for item in data if item['id'] == type_id), None)
        if not type_data:
            raise ValueError(f"Document type with ID {type_id} not found")

        # Convert document dicts to DocumentResponse objects
        return [DocumentResponse(**doc) for doc in type_data.get('documents', [])]

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

    # Potential future methods:
    # def update_counts(self, type_id: int, uploaded: int, pending: int, approved: int):
    #     data = self._load_data()
    #     for item in data:
    #         if item['id'] == type_id:
    #             item['uploaded'] = uploaded
    #             item['reviewPending'] = pending
    #             item['approved'] = approved
    #             self._save_data(data)
    #             return DocumentTypeResponse(**item)
    #     raise ValueError("Document type not found") # Or HTTPException

    # def set_setup_required(self, type_id: int, required: bool):
    #     # ... load, find, update, save ...
    #     pass 