from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, List, Dict, Any
import logging
import json
from pydantic import BaseModel

from private_gpt.server.excel.excel_service import ExcelService
from private_gpt.server.ingest.ingest_service import IngestService
from private_gpt.server.chat.chat_service import ChatService
from private_gpt.open_ai.extensions.context_filter import ContextFilter
from llama_index.core.llms import ChatMessage, MessageRole
from private_gpt.server.utils.auth import authenticated

logger = logging.getLogger(__name__)

excel_router = APIRouter(prefix="/v1", dependencies=[Depends(authenticated)])

# All Excel-related endpoints have been removed
# We'll rebuild step by step

class ExtractInsuranceDataRequest(BaseModel):
    file_name: str
    system_prompt: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "file_name": "Canada Life Booklet - Northern Labs.pdf"
            }
        }

@excel_router.post("/extract-insurance-data", tags=["Data Extraction"])
async def extract_insurance_data(request: Request, extract_request: ExtractInsuranceDataRequest) -> Dict[str, Any]:
    """
    Extract insurance data from a document using RAG and a predefined insurance schema.
    
    This endpoint extracts structured insurance information including life insurance,
    dependent life, and long term disability details from all pages of the specified file.
    
    Args:
        request: The HTTP request
        extract_request: The extraction request with file_name and optional system_prompt
        
    Returns:
        The extracted insurance data in JSON format
    """
    excel_service = request.state.injector.get(ExcelService)
    
    try:
        result = excel_service.extract_structured_data(
            file_name=extract_request.file_name,
            system_prompt=extract_request.system_prompt
        )
        return result
    except Exception as e:
        logger.error(f"Error extracting insurance data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Insurance data extraction failed: {str(e)}")

class ExtractInsuranceDataPreciseRequest(BaseModel):
    file_name: str
    system_prompt_template: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "file_name": "Canada Life Booklet - Northern Labs.pdf"
            }
        }

@excel_router.post("/extract-insurance-data-precise", tags=["Data Extraction"])
async def extract_insurance_data_precise(request: Request, extract_request: ExtractInsuranceDataPreciseRequest) -> Dict[str, Any]:
    """
    Extract insurance data field-by-field for more precise extraction.
    
    This endpoint extracts each field individually with targeted prompts,
    which generally provides more accurate results at the cost of more API calls.
    
    Args:
        request: The HTTP request
        extract_request: The extraction request with file_name and optional system_prompt_template
        
    Returns:
        The extracted insurance data in JSON format, with the same schema as the standard endpoint
    """
    excel_service = request.state.injector.get(ExcelService)
    
    try:
        result = excel_service.extract_insurance_fields_individually(
            file_name=extract_request.file_name,
            system_prompt_template=extract_request.system_prompt_template
        )
        return result
    except Exception as e:
        logger.error(f"Error extracting insurance data precisely: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Precise insurance data extraction failed: {str(e)}")

@excel_router.post("/extract-insurance-data-precise-stream", tags=["Data Extraction"])
async def extract_insurance_data_precise_stream(request: Request, extract_request: ExtractInsuranceDataPreciseRequest):
    """
    Extract insurance data field-by-field with streaming progress updates.
    
    This endpoint extracts each field individually and streams progress updates
    to the client as Server-Sent Events (SSE) before returning the final result.
    
    Args:
        request: The HTTP request
        extract_request: The extraction request with file_name and optional system_prompt_template
        
    Returns:
        Server-Sent Events with progress updates, and final JSON result
    """
    excel_service = request.state.injector.get(ExcelService)
    
    async def event_generator():
        # Create a queue for communication between the callback and generator
        from asyncio import Queue, sleep
        queue = Queue()
        
        # Define the progress callback
        def progress_callback(section_name, field_name, value, progress_percentage):
            # Create a progress update event
            progress_event = {
                "event": "progress",
                "data": {
                    "section": section_name,
                    "field": field_name, 
                    "value": value,
                    "percentage": progress_percentage
                }
            }
            # Add to queue
            queue.put_nowait(f"event: progress\ndata: {json.dumps(progress_event)}\n\n")
            
        # Run the extraction in a separate task
        import asyncio
        
        async def run_extraction():
            try:
                # Run the extraction
                result = excel_service.extract_insurance_fields_individually(
                    file_name=extract_request.file_name,
                    system_prompt_template=extract_request.system_prompt_template,
                    progress_callback=progress_callback
                )
                
                # Return the final result as a completion event
                completion_event = {
                    "event": "completion",
                    "data": result
                }
                queue.put_nowait(f"event: completion\ndata: {json.dumps(completion_event)}\n\n")
                queue.put_nowait(None)  # Signal end of stream
                
            except Exception as e:
                error_msg = f"Precise insurance data extraction failed: {str(e)}"
                logger.error(error_msg)
                
                # Return an error event
                error_event = {
                    "event": "error",
                    "data": {"error": error_msg}
                }
                queue.put_nowait(f"event: error\ndata: {json.dumps(error_event)}\n\n")
                queue.put_nowait(None)  # Signal end of stream
        
        # Start the extraction task
        asyncio.create_task(run_extraction())
        
        # Yield events from the queue
        while True:
            try:
                event = await queue.get()
                if event is None:
                    break
                yield event
                await sleep(0.01)  # Small delay to avoid overwhelming the client
            except Exception as e:
                logger.error(f"Error in stream processing: {str(e)}")
                break
        
    # Return a streaming response with CORS headers
    response = StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@excel_router.get("/extract-insurance-data-precise-stream", tags=["Data Extraction"])
async def extract_insurance_data_precise_stream_get(
    request: Request, 
    file_name: str = Query(..., description="The name of the file to extract data from"),
    system_prompt_template: Optional[str] = Query(None, description="Optional template for system prompts")
):
    """
    Extract insurance data field-by-field with streaming progress updates (GET method).
    
    This endpoint is identical to the POST version but accepts query parameters instead of JSON.
    It's designed to work with EventSource clients which can only use GET requests.
    
    Args:
        request: The HTTP request
        file_name: The name of the file to extract data from
        system_prompt_template: Optional template for system prompts
        
    Returns:
        Server-Sent Events with progress updates, and final JSON result
    """
    excel_service = request.state.injector.get(ExcelService)
    
    async def event_generator():
        # Create a queue for communication between the callback and generator
        from asyncio import Queue, sleep
        queue = Queue()
        
        # Define the progress callback
        def progress_callback(section_name, field_name, value, progress_percentage):
            # Create a progress update event
            progress_event = {
                "event": "progress",
                "data": {
                    "section": section_name,
                    "field": field_name, 
                    "value": value,
                    "percentage": progress_percentage
                }
            }
            # Add to queue
            queue.put_nowait(f"event: progress\ndata: {json.dumps(progress_event)}\n\n")
            
        # Run the extraction in a separate task
        import asyncio
        
        async def run_extraction():
            try:
                # Run the extraction
                result = excel_service.extract_insurance_fields_individually(
                    file_name=file_name,
                    system_prompt_template=system_prompt_template,
                    progress_callback=progress_callback
                )
                
                # Return the final result as a completion event
                completion_event = {
                    "event": "completion",
                    "data": result
                }
                queue.put_nowait(f"event: completion\ndata: {json.dumps(completion_event)}\n\n")
                queue.put_nowait(None)  # Signal end of stream
                
            except Exception as e:
                error_msg = f"Precise insurance data extraction failed: {str(e)}"
                logger.error(error_msg)
                
                # Return an error event
                error_event = {
                    "event": "error",
                    "data": {"error": error_msg}
                }
                queue.put_nowait(f"event: error\ndata: {json.dumps(error_event)}\n\n")
                queue.put_nowait(None)  # Signal end of stream
        
        # Start the extraction task
        asyncio.create_task(run_extraction())
        
        # Yield events from the queue
        while True:
            try:
                event = await queue.get()
                if event is None:
                    break
                yield event
                await sleep(0.01)  # Small delay to avoid overwhelming the client
            except Exception as e:
                logger.error(f"Error in stream processing: {str(e)}")
                break
        
    # Return a streaming response with CORS headers
    response = StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response
