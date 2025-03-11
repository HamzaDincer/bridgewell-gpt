import io
import logging
import json
from typing import BinaryIO, Dict, List, Any, Optional, Callable

from fastapi import HTTPException
from injector import inject, singleton
from llama_index.core.llms import ChatMessage, MessageRole

from private_gpt.server.ingest.ingest_service import IngestService
from private_gpt.server.chat.chat_service import ChatService
from private_gpt.open_ai.extensions.context_filter import ContextFilter

logger = logging.getLogger(__name__)

@singleton
class ExcelService:
    @inject
    def __init__(
        self, 
        ingest_service: IngestService,
        chat_service: ChatService
    ) -> None:
        """Initialize the Excel service.

        Args:
            ingest_service: The ingest service to get documents from.
            chat_service: The chat service to use for AI extraction.
        """
        self._ingest_service = ingest_service
        self._chat_service = chat_service

    def extract_structured_data(
        self,
        file_name: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract insurance data from a document using RAG mode.
        
        This method retrieves content from all pages of a document file and uses RAG to
        extract insurance data according to the predefined insurance schema.
        
        Args:
            file_name: The name of the file to extract data from. All pages
                      of this file will be used for extraction.
            system_prompt: Optional custom system prompt to guide extraction.
            
        Returns:
            A dictionary containing the extracted insurance data structured according to
            the predefined schema.
            
        Raises:
            HTTPException: If document not found or extraction fails.
        """
        logger.info(f"Extracting insurance data from file: {file_name}")
        
        # Get all documents in the system
        all_docs = self._ingest_service.list_ingested()
        
        # Filter documents by filename
        document_ids = [
            doc.doc_id for doc in all_docs 
            if doc.doc_metadata and doc.doc_metadata.get("file_name") == file_name
        ]
        
        if not document_ids:
            raise HTTPException(
                status_code=404,
                detail=f"No documents found with filename: {file_name}"
            )
            
        logger.info(f"Found {len(document_ids)} pages for file: {file_name}")
        
        # Create a context filter for all document IDs
        context_filter = ContextFilter(docs_ids=document_ids)

        logger.info(f"Context filter: {context_filter}")
        
        # Adjust system prompt for multi-page document
        if system_prompt is None:
            system_prompt = (
                "You are an AI assistant specialized in extracting insurance information from documents. "
                "Extract the requested insurance details accurately based on the document content. "
                "Always return your answer as a valid JSON object matching the provided schema. "
                "The document might be split across multiple pages, so consolidate information from all pages. "
                "Search thoroughly through all provided pages of the document to find the information. "
                "Pay special attention to sections labeled 'Benefit Summary', 'Schedule of Benefits', or similar. "
                "If information is not found in the document, use null or appropriate empty values."
            )
            
        # Extraction prompt for multi-page document
        extraction_prompt_prefix = (
            f"""Extract the insurance information from the document, focusing on benefit summary sections, and format it according to this schema.
            The document is split across multiple pages, so search all pages thoroughly. Pay particular attention to:
            
            - Schedule of Benefits sections
            - Benefit Summary sections
            - Life Insurance sections
            - AD&D sections
            - Insurance Summary Tables
            - Dependent Life Coverage sections
            - Long Term Disability sections
            
            Look for information that matches exactly the field names in the schema.
            """
        )
        
        # Use the predefined insurance schema
        extraction_schema = {
            "LIFE INSURANCE & AD&D": {
                "Schedule": "",
                "Reduction": "",
                "Non-Evidence Maximum": "",
                "Termination Age": ""
            },
            "DEPENDENT LIFE": {
                "Spouse": "",
                "Child": "",
                "Termination Age": ""
            },
            "LONG TERM DISABILITY": {
                "Monthly Maximum": "",
                "Tax Status": "",
                "Elimination Period": "",
                "Benefit Period": "",
                "Definition": ""
            }
        }
        
        # Complete the extraction prompt
        extraction_prompt = (
            extraction_prompt_prefix +
            f"{json.dumps(extraction_schema, indent=2)}\n\n"
            f"Return ONLY the JSON result, without any explanations or other text."
        )

        logger.info(f"Extraction prompt: {extraction_prompt}")
        
        # Create the messages for the chat service
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
            ChatMessage(role=MessageRole.USER, content=extraction_prompt)
        ]
        
        try:
            # Use the chat service to extract data using RAG with expanded context retrieval
            completion = self._chat_service.chat(
                messages=messages,
                use_context=True,  # Enable RAG
                context_filter=context_filter
            )
            
            # Parse the response as JSON
            try:
                result = json.loads(completion.response)
                logger.info(f"Successfully extracted insurance data from file: {file_name}")
                return result
            except json.JSONDecodeError:
                logger.error(f"Failed to parse extraction result as JSON: {completion.response}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to parse extraction result as JSON. Please try again."
                )
                
        except Exception as e:
            error_msg = f"Error extracting data: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(
                status_code=500,
                detail=f"Data extraction failed: {str(e)}"
            )

    def extract_insurance_fields_individually(
        self,
        file_name: str,
        system_prompt_template: Optional[str] = None,
        progress_callback: Optional[Callable[[str, str, Any, float], None]] = None
    ) -> Dict[str, Any]:
        """Extract insurance data field-by-field for more precise extraction.
        
        Instead of extracting all data at once, this method loops through each field
        and extracts them individually with targeted prompts.
        
        Args:
            file_name: The name of the file to extract data from.
            system_prompt_template: Optional template for system prompts.
            progress_callback: Optional callback function to report progress.
                If provided, will be called with (section_name, field_name, value, progress_percentage)
            
        Returns:
            A dictionary containing the extracted insurance data.
            
        Raises:
            HTTPException: If document not found or extraction fails.
        """
        logger.info(f"Starting field-by-field extraction from file: {file_name}")
        
        # Get all documents in the system
        all_docs = self._ingest_service.list_ingested()
        
        # Filter documents by filename
        document_ids = [
            doc.doc_id for doc in all_docs 
            if doc.doc_metadata and doc.doc_metadata.get("file_name") == file_name
        ]
        
        if not document_ids:
            raise HTTPException(
                status_code=404,
                detail=f"No documents found with filename: {file_name}"
            )
            
        logger.info(f"Found {len(document_ids)} pages for file: {file_name}")
        
        # Create a context filter for all document IDs
        context_filter = ContextFilter(docs_ids=document_ids)
        
        # Define the full schema structure
        full_schema = {
            "LIFE INSURANCE & AD&D": {
                "Schedule": None,
                "Reduction": None,
                "Non-Evidence Maximum": None,
                "Termination Age": None
            },
            "DEPENDENT LIFE": {
                "Spouse": None,
                "Child": None,
                "Termination Age": None
            },
            "LONG TERM DISABILITY": {
                "Monthly Maximum": None,
                "Tax Status": None,
                "Elimination Period": None,
                "Benefit Period": None,
                "Definition": None
            }
        }
        
        # Default system prompt template if none provided
        if system_prompt_template is None:
            system_prompt_template = (
                "You are an AI assistant specialized in extracting specific insurance information from documents. "
                "Your task is to find the {field_name} in the document. "
                "Extract ONLY this specific piece of information. Be precise and accurate. "
                "If the information is not found in the document, respond with 'null'. "
                "Respond only the value for the field, no other text or explanations."
                "Look for sections labeled 'Benefit Summary', 'Schedule of Benefits', or similar."
            )
        
        # Calculate total number of fields for progress tracking
        total_fields = sum(len(fields) for fields in full_schema.values())
        processed_fields = 0
        
        # Extract each field individually
        for section_name, fields in full_schema.items():
            for field_name in fields.keys():
                # Create a targeted system prompt for this specific field
                system_prompt = system_prompt_template.format(
                    field_name=field_name,
                    section_name=section_name
                )
                
                # Create a targeted extraction prompt for this field
                extraction_prompt = self._create_field_specific_prompt(section_name, field_name)
                
                # Create the messages for the chat service
                messages = [
                    ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
                    ChatMessage(role=MessageRole.USER, content=extraction_prompt)
                ]
                
                try:
                    # Use the chat service to extract this specific field
                    completion = self._chat_service.chat(
                        messages=messages,
                        use_context=True,
                        context_filter=context_filter
                    )
                    
                    # Process the response
                    value = self._process_single_field_response(completion.response)
                    full_schema[section_name][field_name] = value
                    
                    # Update progress tracking
                    processed_fields += 1
                    progress_percentage = (processed_fields / total_fields) * 100
                    
                    logger.info(f"Extracted {section_name}.{field_name}: {value} ({progress_percentage:.1f}%)")
                    
                    # Call progress callback if provided
                    if progress_callback:
                        try:
                            progress_callback(section_name, field_name, value, progress_percentage)
                        except Exception as callback_error:
                            logger.error(f"Error in progress callback: {str(callback_error)}")
                    
                except Exception as e:
                    logger.error(f"Error extracting {section_name}.{field_name}: {str(e)}")
                    # Keep the field as None and continue with other fields
                    
                    # Update progress tracking
                    processed_fields += 1
                    progress_percentage = (processed_fields / total_fields) * 100
                    
                    # Call progress callback if provided
                    if progress_callback:
                        try:
                            progress_callback(section_name, field_name, None, progress_percentage)
                        except Exception as callback_error:
                            logger.error(f"Error in progress callback: {str(callback_error)}")
        
        logger.info(f"Completed field-by-field extraction from file: {file_name}")
        return full_schema
    
    def _create_field_specific_prompt(self, section_name: str, field_name: str) -> str:
        """Create a targeted prompt for a specific field.
        
        Args:
            section_name: Name of the section (e.g., "LIFE INSURANCE & AD&D")
            field_name: Name of the field (e.g., "Schedule")
            
        Returns:
            A string containing the targeted prompt
        """
        base_prompt = f"Find the value for '{field_name}' in the insurance document. Look first in summary section and then in the '{section_name}' section."
        
        # Add field-specific guidance
        if section_name == "LIFE INSURANCE & AD&D":
            if field_name == "Schedule":
                return base_prompt + " This appear as a flat dollar amount. Look in the benefit summary section that is under the the Employee Life Insurance (ie. 20,000$). Respond only the amount value."
            elif field_name == "Reduction":
                return base_prompt + " This typically describes how the benefit amount reduces at certain ages (e.g., 'reduces to 50% at age 65'). Look for age-based reduction clauses."
            elif field_name == "Non-Evidence Maximum":
                return base_prompt + " This is the maximum coverage amount available without providing medical evidence. May also be called 'Non-Medical Maximum' or similar. Respond only the amount value."
            elif field_name == "Termination Age":
                return base_prompt + " This is the age at which coverage terminates, often retirement age or a specific age like 65 or 70. Respond only the age value."
                
        elif section_name == "DEPENDENT LIFE":
            if field_name == "Spouse":
                return base_prompt + " This is the coverage amount for a spouse or partner, typically a flat dollar amount."
            elif field_name == "Child":
                return base_prompt + " This is the coverage amount for dependent children, typically a flat dollar amount."
            elif field_name == "Termination Age":
                return base_prompt + " This is the age at which dependent coverage terminates. Respond only the age value."
                
        elif section_name == "LONG TERM DISABILITY":
            if field_name == "Monthly Maximum":
                return base_prompt + " This is the maximum monthly benefit amount, often expressed as a percentage of salary or a flat dollar amount."
            elif field_name == "Tax Status":
                return base_prompt + " This indicates whether premiums are taxable or non-taxable, or whether benefits are taxable or non-taxable."
            elif field_name == "Elimination Period":
                return base_prompt + " This is the waiting period before benefits begin, typically expressed in days or months (e.g., '120 days')."
            elif field_name == "Benefit Period":
                return base_prompt + " This is how long benefits will be paid, often to age 65 or for a specified period."
            elif field_name == "Definition":
                return base_prompt + " This describes how disability is defined, such as 'own occupation' or 'any occupation' and for what period."
                
        # Default for any other fields
        return base_prompt + " Search the entire document carefully for this information."
    
    def _process_single_field_response(self, response: str) -> Any:
        """Process the response for a single field extraction.
        
        Args:
            response: The response from the LLM
            
        Returns:
            The extracted value, properly formatted
        """
        # Clean the response
        cleaned = response.strip()
        
        # Check for null or empty responses
        if cleaned.lower() in ["null", "none", "not found", "not specified", "not mentioned", "n/a"]:
            return None
            
        if not cleaned:
            return None
            
        # Try to detect and convert numbers
        try:
            if cleaned.replace(".", "", 1).isdigit():
                # It's a number, determine if int or float
                if "." in cleaned:
                    return float(cleaned)
                return int(cleaned)
        except:
            pass
            
        # Return as string if not null or number
        return cleaned

    # All Excel-related methods have been removed
    # We'll rebuild step by step 