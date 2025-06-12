from typing import Literal, Any

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from bridgewell_gpt.server.ingest.ingest_service import IngestService
from bridgewell_gpt.server.ingest.model import IngestedDoc
from bridgewell_gpt.server.utils.auth import authenticated
from bridgewell_gpt.components.extraction.extraction_component import ExtractionComponent
from bridgewell_gpt.components.ingest.ingest_helper import IngestionHelper
from bridgewell_gpt.server.document_types.document_type_service import DocumentTypeService

ingest_router = APIRouter(prefix="/v1", dependencies=[Depends(authenticated)])


class IngestTextBody(BaseModel):
    file_name: str = Field(examples=["Avatar: The Last Airbender"])
    text: str = Field(
        examples=[
            "Avatar is set in an Asian and Arctic-inspired world in which some "
            "people can telekinetically manipulate one of the four elements—water, "
            "earth, fire or air—through practices known as 'bending', inspired by "
            "Chinese martial arts."
        ]
    )


class IngestResponse(BaseModel):
    object: Literal["list"]
    model: Literal["private-gpt"]
    data: list[IngestedDoc]


@ingest_router.post("/ingest", tags=["Ingestion"], deprecated=True)
def ingest(request: Request, file: UploadFile) -> IngestResponse:
    """Ingests and processes a file.

    Deprecated. Use ingest/file instead.
    """
    return ingest_file(request, file)


@ingest_router.post("/ingest/file", tags=["Ingestion"])
def ingest_file(request: Request, file: UploadFile) -> dict:
    """Ingests and processes a file, storing its chunks to be used as context.

    Returns immediately after starting background processing.
    """
    service = request.state.injector.get(IngestService)
    if file.filename is None:
        raise HTTPException(400, "No file name provided")
    # Save the file and start background processing
    ingested_documents = service.ingest_bin_data(file.filename, file.file)
    # Debug logging
    print("DEBUG: ingested_documents =", ingested_documents)
    doc_ids = [getattr(doc, 'doc_id', None) for doc in ingested_documents]
    print("DEBUG: doc_ids =", doc_ids)
    # Return document IDs and status immediately
    return {
        "status": "processing",
        "doc_ids": doc_ids,
        "message": "File received. Processing in background."
    }


@ingest_router.post("/ingest/text", tags=["Ingestion"])
def ingest_text(request: Request, body: IngestTextBody) -> IngestResponse:
    """Ingests and processes a text, storing its chunks to be used as context.

    The context obtained from files is later used in
    `/chat/completions`, `/completions`, and `/chunks` APIs.

    A Document will be generated with the given text. The Document
    ID is returned in the response, together with the
    extracted Metadata (which is later used to improve context retrieval). That ID
    can be used to filter the context used to create responses in
    `/chat/completions`, `/completions`, and `/chunks` APIs.
    """
    service = request.state.injector.get(IngestService)
    if len(body.file_name) == 0:
        raise HTTPException(400, "No file name provided")
    ingested_documents = service.ingest_text(body.file_name, body.text)
    return IngestResponse(object="list", model="private-gpt", data=ingested_documents)


@ingest_router.get("/ingest/list", tags=["Ingestion"])
def list_ingested(request: Request) -> IngestResponse:
    """Lists already ingested Documents including their Document ID and metadata.

    Those IDs can be used to filter the context used to create responses
    in `/chat/completions`, `/completions`, and `/chunks` APIs.
    """
    service = request.state.injector.get(IngestService)
    ingested_documents = service.list_ingested()
    return IngestResponse(object="list", model="private-gpt", data=ingested_documents)


@ingest_router.delete("/ingest/{doc_id}", tags=["Ingestion"])
def delete_ingested(request: Request, doc_id: str) -> None:
    """Delete the specified ingested Document.

    The `doc_id` can be obtained from the `GET /ingest/list` endpoint.
    The document will be effectively deleted from your storage context.
    """
    service = request.state.injector.get(IngestService)
    service.delete(doc_id)


@ingest_router.get("/ingest/{doc_id}", tags=["Ingestion"])
def get_document(request: Request, doc_id: str) -> dict[str, Any]:
    """Get a document's content and metadata by its ID.

    The `doc_id` can be obtained from the `GET /ingest/list` endpoint.
    
    Returns:
        A dictionary containing the document's content and metadata.
        
    Raises:
        HTTPException: If the document is not found.
    """
    service = request.state.injector.get(IngestService)
    doc = service.get_document(doc_id)
    if not doc:
        raise HTTPException(404, f"Document {doc_id} not found")
    return doc


@ingest_router.get("/ingest/status/{doc_id}", tags=["Ingestion"])
def get_ingest_status(request: Request, doc_id: str) -> dict:
    """Get the processing status of a document by its ID.

    Returns a detailed status: 'uploading', 'parsing', 'extraction', 'embedding', 'rag', 'completed'.
    """
    # Use DocumentTypeService to get the phase
    service = request.state.injector.get(DocumentTypeService)
    # Search all document types for the document
    for doc_type in service.get_document_types():
        for doc in getattr(doc_type, "documents", []):
            if str(doc.id) == str(doc_id):
                phase = getattr(doc, "phase", None)
                if phase == "completed":
                    return {"status": "completed", "phase": phase, "doc_id": doc_id}
                elif phase:
                    return {"status": "processing", "phase": phase, "doc_id": doc_id}
                else:
                    return {"status": "processing", "phase": "uploading", "doc_id": doc_id}
    return {"status": "processing", "phase": "uploading", "doc_id": doc_id}
