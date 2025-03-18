import logging
from typing import Dict, Any, Optional, Callable, List
import json

from injector import inject, singleton
from fastapi import HTTPException

from llama_index.core.llms import ChatMessage, MessageRole
from private_gpt.open_ai.extensions.context_filter import ContextFilter

from private_gpt.server.chat.chat_service import ChatService
from private_gpt.server.ingest.ingest_service import IngestService
from private_gpt.server.excel.prompts.base import (
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_FIELD_SYSTEM_PROMPT_TEMPLATE,
    EXTRACTION_PROMPT_PREFIX,
    INSURANCE_SCHEMA,
    create_field_specific_prompt,
    get_generic_examples,
    get_extraction_prompt
)
from private_gpt.server.excel.prompts.utils import (
    process_single_field_response,
    detect_insurance_company
)
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
            system_prompt = DEFAULT_SYSTEM_PROMPT
        
        # Get the extraction schema and create prompt
        extraction_schema = INSURANCE_SCHEMA.copy()
        extraction_prompt = get_extraction_prompt(extraction_schema)

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
        progress_callback: Optional[Callable[[str, str, Any, float], None]] = None,
        company_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract insurance data field-by-field for more precise extraction.
        
        Instead of extracting all data at once, this method loops through each field
        and extracts them individually with targeted prompts.
        
        Args:
            file_name: The name of the file to extract data from.
            system_prompt_template: Optional template for system prompts.
            progress_callback: Optional callback function to report progress.
                If provided, will be called with (section_name, field_name, value, progress_percentage)
            company_name: Optional insurance company name to use company-specific prompts.
                If None, will attempt to detect from filename.
            
        Returns:
            A dictionary containing the extracted insurance data.
            
        Raises:
            HTTPException: If document not found or extraction fails.
        """
        logger.info(f"Starting field-by-field extraction from file: {file_name}")
        
        # Auto-detect insurance company if not provided
        if company_name is None:
            company_name = detect_insurance_company(file_name)
            logger.info(f"Detected insurance company: {company_name}")
        
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
        full_schema = INSURANCE_SCHEMA.copy()
        for section in full_schema.values():
            for field in section:
                section[field] = None
        
        # Default system prompt template if none provided
        if system_prompt_template is None:
            system_prompt_template = DEFAULT_FIELD_SYSTEM_PROMPT_TEMPLATE
        
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
                extraction_prompt = create_field_specific_prompt(section_name, field_name, company_name)
                
                # Get examples for this field
                examples = get_generic_examples(section_name, field_name)
                if examples:
                    extraction_prompt = f"{examples}\n\n{extraction_prompt}"
                
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
                    value = process_single_field_response(completion.response)
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

    def extract_insurance_fields_selectively(
        self,
        file_name: str,
        sections_to_extract: Optional[List[str]] = None,
        fields_to_extract: Optional[Dict[str, List[str]]] = None,
        system_prompt_template: Optional[str] = None,
        progress_callback: Optional[Callable[[str, str, Any, float], None]] = None,
        company_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract only specific insurance data fields for testing purposes.
        
        This allows extracting only specific sections or fields instead of the entire schema,
        which is useful for testing and development.
        
        Args:
            file_name: The name of the file to extract data from.
            sections_to_extract: Optional list of section names to extract.
                If None, will use fields_to_extract to determine sections.
            fields_to_extract: Optional dictionary mapping section names to lists of field names.
                If None, will extract all fields from sections_to_extract.
            system_prompt_template: Optional template for system prompts.
            progress_callback: Optional callback function to report progress.
                If provided, will be called with (section_name, field_name, value, progress_percentage)
            company_name: Optional insurance company name to use company-specific prompts.
                If None, will attempt to detect from filename.
            
        Returns:
            A dictionary containing the extracted insurance data for the specified sections/fields.
            
        Raises:
            HTTPException: If document not found or extraction fails.
        """
        logger.info(f"Starting selective field extraction from file: {file_name}")
        
        # Auto-detect insurance company if not provided
        if company_name is None:
            company_name = detect_insurance_company(file_name)
            logger.info(f"Detected insurance company: {company_name}")
        
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
        
        # Define the schema structure based on sections_to_extract and fields_to_extract
        full_schema = INSURANCE_SCHEMA.copy()
        extraction_schema = {}
        
        # If sections_to_extract is provided, use only those sections
        if sections_to_extract:
            for section in sections_to_extract:
                if section in full_schema:
                    extraction_schema[section] = {}
                    # If fields_to_extract is provided for this section, use only those fields
                    if fields_to_extract and section in fields_to_extract:
                        for field in fields_to_extract[section]:
                            if field in full_schema[section]:
                                extraction_schema[section][field] = None
                    else:
                        # Otherwise, use all fields in this section
                        for field in full_schema[section]:
                            extraction_schema[section][field] = None
        # If only fields_to_extract is provided, extract only those specific fields
        elif fields_to_extract:
            for section, fields in fields_to_extract.items():
                if section in full_schema:
                    extraction_schema[section] = {}
                    for field in fields:
                        if field in full_schema[section]:
                            extraction_schema[section][field] = None
        else:
            # If neither is provided, use the entire schema
            extraction_schema = full_schema.copy()
            for section in extraction_schema.values():
                for field in section:
                    section[field] = None
        
        # Default system prompt template if none provided
        if system_prompt_template is None:
            system_prompt_template = DEFAULT_FIELD_SYSTEM_PROMPT_TEMPLATE
        
        # Calculate total number of fields for progress tracking
        total_fields = sum(len(fields) for fields in extraction_schema.values())
        processed_fields = 0
        
        if total_fields == 0:
            logger.warning("No fields to extract. Check that your section/field names match the schema.")
            return {}
        
        # Extract each field individually
        for section_name, fields in extraction_schema.items():
            for field_name in fields.keys():
                # Create a targeted system prompt for this specific field
                system_prompt = system_prompt_template.format(
                    field_name=field_name,
                    section_name=section_name
                )
                
                # Create a targeted extraction prompt for this field
                extraction_prompt = create_field_specific_prompt(section_name, field_name, company_name)
                
                # Get examples for this field
                examples = get_generic_examples(section_name, field_name)
                if examples:
                    extraction_prompt = f"{examples}\n\n{extraction_prompt}"
                
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
                    value = process_single_field_response(completion.response)
                    extraction_schema[section_name][field_name] = value
                    
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
        
        logger.info(f"Completed selective field extraction from file: {file_name}")
        return extraction_schema