from fastapi import APIRouter, Depends, Request, HTTPException
from typing import List
from injector import Injector

from .document_type_service import DocumentTypeService
from .document_type_models import DocumentTypeResponse, DocumentTypeCreate
from bridgewell_gpt.server.utils.auth import authenticated

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

# We can add POST endpoint later if needed
# @document_type_router.post("/document-types", ...) ... 