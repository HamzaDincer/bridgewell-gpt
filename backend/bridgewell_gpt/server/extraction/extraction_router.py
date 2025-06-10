from fastapi import APIRouter, Depends, HTTPException, Request, Form
from llama_cloud_services import LlamaExtract
from typing import Dict, Optional, List, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from pathlib import Path
import logging
import json

from bridgewell_gpt.server.extraction.extraction_service import ExtractionService
from bridgewell_gpt.server.extraction.insurance_schema import InsuranceSummary
from bridgewell_gpt.server.utils.auth import authenticated

extraction_router = APIRouter(prefix="/v1", dependencies=[Depends(authenticated)])

logger = logging.getLogger(__name__)


# Load environment variables
load_dotenv()


# Initialize LlamaExtract client
extractor = LlamaExtract()

class ExtractPagesRequest(BaseModel):
    page_numbers: List[int] = Field(description="List of page numbers to extract (1-based indexing)")
    output_name: Optional[str] = Field(None, description="Optional name for the output file")

class ExtractPagesResponse(BaseModel):
    object: str = "extraction.pages"
    output_path: str
    message: str

class RagExtractionRequest(BaseModel):
    missing_fields: List[str]


@extraction_router.post("/extract/{file_name}", tags=["Extraction"])
async def extract_benefit_summary_direct(
    request: Request,
    file_name: str,
    company_name: Optional[str] = None
) -> dict:
    """Extract benefit summary pages and send directly to extraction API.
    
    Args:
        request: The HTTP request
        file_name: Name of the file to process
        company_name: Optional company name to use specific config
        
    Returns:
        Extraction API response with combined results from both extraction steps
    """
    try:
        service = request.state.injector.get(ExtractionService)
        
        # Create benefit comparison which now handles RAG internally
        output_path, extraction_result = service.create_benefit_comparison(
            file_name=file_name,
            company_name=company_name if company_name else ""
        )
        
        return {
            "status": "success",
            "message": "Benefit summary extracted and processed",
            "extraction_result": extraction_result,
            "comparison_file": str(output_path)
        }
        
    except Exception as e:
        logger.error(f"Error in direct extraction: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in direct extraction: {str(e)}"
        )

@extraction_router.post("/extract/pdf/pages/{file_name}", response_model=ExtractPagesResponse)
async def extract_pdf_pages(
    request: Request,
    file_name: str,
    extract_request: ExtractPagesRequest
) -> ExtractPagesResponse:
    """Extract specific pages from a PDF file.
    
    Args:
        request: The HTTP request
        file_name: Name of the file to extract pages from
        extract_request: Request body containing page numbers and optional output name
        
    Returns:
        ExtractPagesResponse containing the path to the extracted PDF
    """
    try:
        service = request.state.injector.get(ExtractionService)
        
        output_path = service.extract_pdf_pages(
            file_name=file_name,
            page_numbers=extract_request.page_numbers,
            output_name=extract_request.output_name
        )
        
        return ExtractPagesResponse(
            output_path=str(output_path),
            message=f"Successfully extracted pages {extract_request.page_numbers}"
        )
        
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting PDF pages: {str(e)}"
        )

@extraction_router.get("/extract/pdf/benefit-summary/{file_name}", response_model=ExtractPagesResponse)
async def extract_benefit_summary(
    request: Request,
    file_name: str,
    company_name: Optional[str] = None
) -> ExtractPagesResponse:
    """Extract benefit summary pages from a PDF file.
    
    Args:
        request: The HTTP request
        file_name: Name of the file to process
        company_name: Optional company name to use specific config
        
    Returns:
        ExtractPagesResponse containing the path to the extracted benefit summary PDF
    """
    try:
        service = request.state.injector.get(ExtractionService)
        
        output_path = service.extract_benefit_summary(
            file_name=file_name,
            company_name=company_name
        )
        
        return ExtractPagesResponse(
            output_path=str(output_path),
            message="Successfully extracted benefit summary pages"
        )
        
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting benefit summary: {str(e)}"
        )

@extraction_router.post("/create_comparison")
async def create_benefit_comparison(
    request: Request,
    file_name: str = Form(...),
    company_name: str = Form(...)
) -> Dict:
    """Create a benefit comparison Excel file from a PDF document.
    
    Args:
        request: The HTTP request
        file_name: Name of the PDF file to extract from
        company_name: Name of the company for the comparison
        
    Returns:
        Dictionary containing:
        - comparison_file: Path to the generated Excel file
        - extraction_results: The extracted benefit data
    """
    try:
        extraction_service = request.state.injector.get(ExtractionService)
        output_path, extraction_results = extraction_service.create_benefit_comparison(file_name, company_name)
        
        # Get just the filename for Gradio
        comparison_file = output_path.name
        
        return {
            "comparison_file": comparison_file,
            "extraction_results": extraction_results
        }
        
    except Exception as e:
        logger.error(f"Error creating benefit comparison: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create benefit comparison: {str(e)}"
        )
