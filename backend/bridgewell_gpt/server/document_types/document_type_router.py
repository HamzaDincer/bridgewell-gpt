import os
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Request, HTTPException
from injector import Injector

from bridgewell_gpt.server.document_types.document_type_models import DocumentTypeResponse, DocumentTypeCreate, DocumentCreate, DocumentResponse
from bridgewell_gpt.server.document_types.document_type_service import DocumentTypeService
from bridgewell_gpt.server.utils.auth import authenticated
from bridgewell_gpt.components.extraction.extraction_component import ExtractionComponent
from bridgewell_gpt.components.ingest.ingest_component import SimpleIngestComponent

# Define router
document_type_router = APIRouter(prefix="/v1", dependencies=[Depends(authenticated)])

# Define endpoint
@document_type_router.get(
    "/document-types", 
    response_model=List[DocumentTypeResponse], # Specify the response model as a list
    tags=["Document Types"]
)
def get_document_types(request: Request) -> List[DocumentTypeResponse]:
    """Retrieve a list of all configured document types."""
    # Inject the service (assuming dependency injection is set up similarly to other routers)
    injector: Injector = request.state.injector
    service = injector.get(DocumentTypeService)
    return service.get_document_types()

# Define POST endpoint (new)
@document_type_router.post(
    "/document-types",
    response_model=DocumentTypeResponse,
    tags=["Document Types"],
    status_code=201 # Indicate resource creation
)
def create_document_type(
    type_create: DocumentTypeCreate, # Use the new model for request body
    request: Request
) -> DocumentTypeResponse:
    """Create a new document type."""
    injector: Injector = request.state.injector
    service = injector.get(DocumentTypeService)
    try:
        return service.create_document_type(type_create)
    except ValueError as e:
        # Handle potential duplicate title error from the service
        raise HTTPException(status_code=400, detail=str(e)) 
    except Exception as e:
        # Catch unexpected errors during creation/saving
        raise HTTPException(status_code=500, detail=f"Failed to create document type: {str(e)}")

@document_type_router.post(
    "/document-types/{type_id}/documents",
    response_model=DocumentTypeResponse,
    tags=["Document Types"]
)
def add_document(
    type_id: int,
    document: DocumentCreate,
    request: Request
) -> DocumentTypeResponse:
    """Add a document to a document type."""
    injector: Injector = request.state.injector
    service = injector.get(DocumentTypeService)
    try:
        return service.add_document(type_id, document)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add document: {str(e)}")

@document_type_router.get(
    "/document-types/{type_id}/documents",
    response_model=List[DocumentResponse],
    tags=["Document Types"]
)
def get_documents(
    type_id: int,
    request: Request
) -> List[DocumentResponse]:
    """Get all documents for a document type."""
    injector: Injector = request.state.injector
    service = injector.get(DocumentTypeService)
    try:
        return service.get_documents(type_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get documents: {str(e)}")

@document_type_router.get(
    "/documents/{doc_id}",
    tags=["Document Types"]
)
def get_document_by_id(doc_id: str, request: Request):
    """Get a document's PDF URL and extraction fields by its ID."""
    injector: Injector = request.state.injector
    service = injector.get(DocumentTypeService)
    extraction_component = injector.get(ExtractionComponent)
    
    # Search all document types for the document
    doc_types = service.get_document_types()
    for doc_type in doc_types:
        for doc in getattr(doc_type, "documents", []):
            if str(doc.id) == str(doc_id):
                # Get file name from doc.name
                file_name = doc.name
                
                # Get extraction results using the file name
                extraction_result = extraction_component.get_latest_extraction_by_file(file_name)
                extraction = {}
                if extraction_result:
                    extraction = extraction_result.get("result", {})
                
                # Construct the PDF URL
                backend_url = os.environ.get("BACKEND_API_URL", "http://localhost:8001")
                url = f"{backend_url}/original_files/{file_name}"
                
                return {"url": url, "extraction": extraction}
    raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

@document_type_router.get(
    "/documents/{doc_id}/extraction",
    response_model=Dict[str, Any],
    tags=["Document Types"]
)
def get_document_extraction(doc_id: str, request: Request) -> Dict[str, Any]:
    """Get the latest extraction results for a document."""
    injector: Injector = request.state.injector
    service = injector.get(DocumentTypeService)
    extraction_component = injector.get(ExtractionComponent)
    
    # First get the document to get its file name
    doc_types = service.get_document_types()
    for doc_type in doc_types:
        for doc in getattr(doc_type, "documents", []):
            if str(doc.id) == str(doc_id):
                # Get extraction results using the file name
                extraction_result = extraction_component.get_latest_extraction_by_file(doc.name)
                if extraction_result:
                    return extraction_result
                else:
                    return {"status": "not_found", "message": "No extraction results found"}
                
    raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

# We can add POST endpoint later if needed
# @document_type_router.post("/document-types", ...) ... 