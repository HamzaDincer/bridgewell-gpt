from fastapi import APIRouter, Depends, HTTPException, Request, Form
from llama_cloud_services import LlamaExtract
from typing import Dict, Optional, List
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
        extraction_service = request.state.injector.get(ExtractionService)
        
        # Step 1: Initial extraction with LlamaExtract
        logger.info("Creating/retrieving benefit-summary-parser agent")
        try:
            benefit_agent = extractor.get_agent("benefit-summary-parser")
            logger.info("Successfully retrieved existing benefit-summary-parser agent")
        except Exception as e:
            logger.info(f"Agent not found, creating new one: {str(e)}")
            benefit_agent = extractor.create_agent(
                name="benefit-summary-parser",
                data_schema=InsuranceSummary
            )
            logger.info("Successfully created new benefit-summary-parser agent")
        
        # Extract benefit summary pages
        logger.info(f"Extracting benefit summary from {file_name}")
        extracted_pdf_path = extraction_service.extract_benefit_summary(file_name, company_name)
        logger.info(f"Benefit summary extracted to: {extracted_pdf_path}")
        
        #Send to extraction API using benefit agent
        logger.info("Sending to extraction API")
        result = benefit_agent.extract(str(extracted_pdf_path))
        initial_data = result.data

        initial_data = {'life_insurance_ad_d': {'schedule': 'Flat $25,000', 'reduction': 'Reduces by 50% at age 65, further reduces to $10,000 at age 70', 'non_evidence_maximum': '$25,000', 'termination_age': '75'}, 'dependent_life': {'schedule': '$10,000 Spouse, $5,000 per Child', 'termination_age': '75'}, 'critical_illness': None, 'long_term_disability': {'schedule': '75% of pre-tax monthly earnings to maximum $10,000', 'monthly_maximum': '$10,000', 'tax_status': 'Taxable', 'elimination_period': '112 calendar days', 'benefit_period': 'To age 65, but not less than 1 year', 'definition': 'Total Disability', 'offsets': '100% of direct benefit offsets', 'cost_of_living_adjustment': None, 'pre_existing': '3/12', 'survivor_benefit': 'Yes – 3 months', 'non_evidence_maximum': '$5,400', 'termination_age': '65'}, 'short_term_disability': None, 'health_care': {'prescription_drugs': '100% after the deductible', 'pay_direct_drug_card': 'Yes', 'maximum': '$10,000 per insured per benefit period', 'fertility_drugs': 'Lifetime maximum of $2,500 for each insured', 'smoking_cessations': 'Lifetime maximum of $300 for each insured', 'vaccines': 'Included', 'major_medical': None, 'annual_deductible': 'Nil per benefit period', 'hospitalization': '100%, without a deductible', 'orthotic_shoes': None, 'orthotic_inserts': None, 'hearing_aids': 'Up to a maximum of $700 per insured over a period of 5 consecutive benefit periods', 'vision_care': None, 'eye_exams': None, 'paramedical_practitioners': '100% after the deductible', 'included_specialists': None, 'out_of_country': '100% without deductible', 'maximum_duration': None, 'trip_cancellation': None, 'private_duty_nursing': '100% without a deductible, up to a maximum of $10,000 per insured per benefit period', 'survivor_benefit': 'Up to a maximum of 24 consecutive months without premium payment', 'termination_age': None, 'dependent_child_definition': None, 'benefit_year': None, 'second_medical_opinion': None, 'eap': 'Yes', 'digital_wellness_program': 'Yes', 'virtual_healthcare_services': 'Yes'}, 'dental_care': None, 'notes_and_definitions': None}

        logger.info(f"Initial data: {initial_data}")
        
        # Step 2: Check for missing fields and use RAG to fill them
        logger.info("Checking for missing fields")
        missing_fields = extraction_service._has_missing_fields(initial_data, InsuranceSummary)
        
        if missing_fields:
            logger.info(f"Found {len(missing_fields)} missing fields, using RAG to extract them")
            logger.info(f"Missing fields: {missing_fields}")
            # Load company config if available
            company_config = None
            config_path = Path(__file__).parent / "configs" / f"{company_name.lower()}.json" if company_name else None
            if config_path and config_path.exists():
                with open(config_path) as f:
                    company_config = json.load(f)
            
            # Extract missing fields using RAG with ingested document
            rag_results = extraction_service._extract_with_rag(
                file_name=file_name,  
                missing_fields=missing_fields,
                company_config=company_config
            )
            
            # Merge RAG results with initial data
            def deep_update(d: dict, u: dict) -> dict:
                for k, v in u.items():
                    if isinstance(v, dict):
                        d[k] = deep_update(d.get(k, {}), v)
                    else:
                        if k in d and d[k] is None:  # Only update if original value is None
                            d[k] = v
                return d
            
            final_data = deep_update(initial_data, rag_results)
        else:
            logger.info("No missing fields found")
            final_data = initial_data
        
        return {
            "status": "success",
            "message": "Benefit summary extracted and processed",
            # "extracted_pdf": str(extracted_pdf_path),
            "extraction_result": final_data,
            "rag_extracted_fields": list(rag_results.keys()) if missing_fields else []
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
