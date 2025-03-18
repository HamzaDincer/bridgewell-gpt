from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse
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
    company_name: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "file_name": "Canada Life Booklet - Northern Labs.pdf",
                "company_name": "CanadaLife"
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
        extract_request: The extraction request with file_name, optional system_prompt_template, and optional company_name
        
    Returns:
        The extracted insurance data in JSON format, with the same schema as the standard endpoint
    """
    excel_service = request.state.injector.get(ExcelService)
    
    try:
        result = excel_service.extract_insurance_fields_individually(
            file_name=extract_request.file_name,
            system_prompt_template=extract_request.system_prompt_template,
            company_name=extract_request.company_name
        )
        return result
    except Exception as e:
        logger.error(f"Error extracting insurance data precisely: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Precise insurance data extraction failed: {str(e)}")

class ExtractInsuranceDataSelectiveRequest(BaseModel):
    file_name: str
    sections_to_extract: Optional[List[str]] = None
    fields_to_extract: Optional[Dict[str, List[str]]] = None
    system_prompt_template: Optional[str] = None
    company_name: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "file_name": "Canada Life Booklet - Northern Labs.pdf",
                "sections_to_extract": ["LIFE INSURANCE & AD&D"],
                "fields_to_extract": {"LIFE INSURANCE & AD&D": ["Schedule", "Reduction"]},
                "company_name": "CanadaLife"
            }
        }

@excel_router.post("/extract-insurance-data-selective", tags=["Data Extraction"])
async def extract_insurance_data_selective(request: Request, extract_request: ExtractInsuranceDataSelectiveRequest) -> Dict[str, Any]:
    """
    Extract only specific sections or fields from insurance data for testing purposes.
    
    This endpoint allows you to extract only the sections or fields you want to test,
    which is much faster than extracting everything when you only need to test specific parts.
    
    Args:
        request: The HTTP request
        extract_request: The extraction request with file_name, sections_to_extract, fields_to_extract,
                         optional system_prompt_template, and optional company_name
        
    Returns:
        The extracted insurance data only for the requested sections/fields
    """
    excel_service = request.state.injector.get(ExcelService)
    
    try:
        result = excel_service.extract_insurance_fields_selectively(
            file_name=extract_request.file_name,
            sections_to_extract=extract_request.sections_to_extract,
            fields_to_extract=extract_request.fields_to_extract,
            system_prompt_template=extract_request.system_prompt_template,
            company_name=extract_request.company_name
        )
        return result
    except Exception as e:
        logger.error(f"Error extracting selective insurance data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Selective insurance data extraction failed: {str(e)}")
