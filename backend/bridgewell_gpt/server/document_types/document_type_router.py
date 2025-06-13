import os
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Request, HTTPException, Body
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
    response_model=None,  # We'll return a dict with alreadyExists and type fields
    tags=["Document Types"],
    status_code=201 # Indicate resource creation
)
def create_document_type(
    type_create: DocumentTypeCreate, # Use the new model for request body
    request: Request
) -> dict:
    """Create a new document type."""
    injector: Injector = request.state.injector
    service = injector.get(DocumentTypeService)
    try:
        result = service.create_document_type(type_create)
        # Flatten the response for the frontend: merge type fields at top level
        type_data = result["type"].dict() if hasattr(result["type"], "dict") else dict(result["type"])
        response = {"alreadyExists": result["alreadyExists"], **type_data}
        return response
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
                file_name = doc.name
                extraction_result = extraction_component.get_latest_extraction_by_doc_id(doc_id)
                extraction = {}
                if extraction_result:
                    extraction = extraction_result.get("result", {})
                scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
                host = request.headers.get("host", request.url.hostname)
                url = f"{scheme}://{host}/original_files/{file_name}"
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
    doc_types = service.get_document_types()
    for doc_type in doc_types:
        for doc in getattr(doc_type, "documents", []):
            if str(doc.id) == str(doc_id):
                extraction_result = extraction_component.get_latest_extraction_by_doc_id(doc_id)
                if extraction_result:
                    return extraction_result
                else:
                    return {"status": "not_found", "message": "No extraction results found"}
    raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

@document_type_router.post(
    "/documents/{doc_id}/extraction",
    tags=["Document Types"]
)
def update_document_extraction(doc_id: str, request: Request, extraction: dict = Body(...)):
    """
    Update the extraction result for a document.
    """
    injector: Injector = request.state.injector
    extraction_component = injector.get(ExtractionComponent)
    extraction_component.save_extraction_result(doc_id, extraction)
    return extraction_component.get_latest_extraction_by_doc_id(doc_id)

# We can add POST endpoint later if needed
# @document_type_router.post("/document-types", ...) ... 