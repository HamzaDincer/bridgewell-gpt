from typing import Dict, List, Optional, Any, Tuple
from injector import inject, singleton
from fastapi import HTTPException
import json
from pathlib import Path
import logging
import difflib
from llama_index.core.llms import ChatMessage, MessageRole
from llama_cloud_services import LlamaExtract
import os
import shutil
from PyPDF2 import PdfReader, PdfWriter
from dotenv import load_dotenv

from bridgewell_gpt.server.ingest.ingest_service import IngestService
from bridgewell_gpt.server.ingest.model import IngestedDoc
from bridgewell_gpt.settings.settings import settings
from bridgewell_gpt.server.chat.chat_service import ChatService
from bridgewell_gpt.open_ai.extensions.context_filter import ContextFilter
from bridgewell_gpt.paths import local_data_path
from bridgewell_gpt.server.extraction.template_service import BenefitComparisonTemplate
from bridgewell_gpt.server.extraction.insurance_schema import InsuranceSummary

# Load environment variables
load_dotenv()

extractor = LlamaExtract()

logger = logging.getLogger(__name__)

@singleton
class ExtractionService:
    
    @inject
    def __init__(
        self,
        ingest_service: IngestService,
        chat_service: ChatService,
    ) -> None:
        """Initialize the extraction service.

        Args:
            ingest_service: The ingest service for document processing.
            chat_service: The chat service for text extraction.
        """
        self._ingest_service = ingest_service
        self._chat_service = chat_service
        
        # Initialize storage directories
        self._config_dir = Path(__file__).parent / "configs"
        
        # Set up storage directories
        self._storage_dir = local_data_path / "original_files"
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        
        self._extracted_pages_dir = local_data_path / "extracted_pages"
        self._extracted_pages_dir.mkdir(parents=True, exist_ok=True)

    @property
    def storage_dir(self) -> Path:
        return self._storage_dir

    @property
    def extracted_pages_dir(self) -> Path:
        return self._extracted_pages_dir

    def _load_company_config(self, company_name: str) -> dict | None:
        """Load configuration for a specific company.
        
        Args:
            company_name: Name of the company to load config for
            
        Returns:
            Company configuration dict if found, None otherwise
        """
        config_file = self._config_dir / f"{company_name.lower()}.json"
        logger.debug(f"Looking for config file: {config_file}")
        if not config_file.exists():
            logger.warning(f"Config file not found: {config_file}")
            return None
            
        with open(config_file) as f:
            config = json.load(f)
            logger.debug(f"Loaded config with headers: {config['benefit_headers'].keys()}")
            return config

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity ratio between two strings."""
        return difflib.SequenceMatcher(None, str1, str2).ratio()

    def _find_matching_section(self, text: str, patterns: list[str], similarity_threshold: float = 0.8) -> bool:
        """Find if text matches any pattern using fuzzy matching.
        
        Args:
            text: Text to search in
            patterns: List of patterns to match
            similarity_threshold: Minimum similarity ratio to consider a match
            
        Returns:
            True if a match is found, False otherwise
        """
        # Convert text to uppercase for case-insensitive matching
        text = text.upper()
        
        # Try exact matches first
        if any(pattern.upper() in text for pattern in patterns):
            return True
        
        # Try fuzzy matching
        text_lines = text.split('\n')
        for line in text_lines:
            line = line.strip()
            if not line:
                continue
                
            for pattern in patterns:
                similarity = self._calculate_similarity(line, pattern.upper())
                if similarity >= similarity_threshold:
                    logger.debug(f"Fuzzy match found: '{line}' matches '{pattern}' with similarity {similarity:.2f}")
                    return True
                
        return False

    def _extract_with_gpt(self, text: str, section_type: str, company_config: dict | None = None) -> dict:
        """Extract structured data from section text using GPT."""
        try:
            logger.info(f"Starting GPT extraction for section type: {section_type}")
            
            # Map the document section type to structure.json section type using company config
            structure_type = self._map_section_type_to_structure(section_type, company_config)
            logger.info(f"Mapped to structure type: {structure_type}")
            
            # Get only the relevant section structure
            structure = self._load_json_structure(structure_type)
            if not structure:
                logger.warning(f"No structure found for section type: {structure_type}")
                return {}
            
            logger.info(f"Loaded structure: {json.dumps(structure, indent=2)}")
            
            # Get company-specific field prompts if available
            field_prompts = {}
            if company_config and "benefit_headers" in company_config:
                # Find the matching section in benefit_headers
                for section_name, section_info in company_config["benefit_headers"].items():
                    # Map the section name to structure type for comparison
                    mapped_section = self._map_section_type_to_structure(section_name, company_config)
                    if mapped_section == structure_type and "fields" in section_info:
                        field_prompts = section_info["fields"]
                        logger.info(f"Found field prompts for section {structure_type}: {list(field_prompts.keys())}")
                        break
            
            # Build a detailed prompt with field-specific instructions and examples
            field_instructions = []
            for field in structure.keys():
                field_info = field_prompts.get(field, {})
                field_prompt = field_info.get("prompt", f"Find the {field} value")
                field_format = field_info.get("format", "string")
                field_examples = field_info.get("examples", [])  # Get examples if available
                
                instruction = f"- {field}: {field_prompt} (format: {field_format})"
                if field_examples:
                    instruction += f"\n  Examples: {json.dumps(field_examples, indent=2)}"
                field_instructions.append(instruction)

            system_prompt = f"""
            You are an AI assistant specialized in extracting insurance details from documents. 
            Your task is to find the information in the document. 
            You can only answer questions about the provided text. If you know the answer but it is not based in the provided text, respond with 'null'.
            If the requested data is not found in the document, respond with 'null'. 
            Respond concisely only with the formatted value given examples in the prompt, no other text or explanations."""
            
            prompt = f"""
            Extract information from this insurance benefit section into the following JSON structure.
            Only include fields that are present in the text. Use null for missing values.
            
            Section Type: {structure_type}
            Expected Structure: {json.dumps(structure, indent=2)}
            
            Field-specific instructions and examples:
            {chr(10).join(field_instructions)}
            
            Text to analyze:
            {text}
            
            Return only the JSON object, no other text.
            """
            
            logger.info("Sending request to chat service")
            messages = [
                ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
                ChatMessage(role=MessageRole.USER, content=prompt)
            ]
            
            completion = self._chat_service.chat(messages=messages)
            logger.info("Received response from chat service")
            
            # Clean up the response to extract just the JSON
            response_text = completion.response.strip()
            logger.info(f"Raw response: {response_text[:200]}...")  # Log first 200 chars
            
            # Remove markdown code block markers if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            # Remove "assistant:" prefix if present
            if response_text.startswith("assistant:"):
                response_text = response_text[9:]
            
            # Clean up any remaining whitespace
            response_text = response_text.strip()
            
            # Try to parse the cleaned JSON
            try:
                result = json.loads(response_text)
                logger.info(f"Successfully parsed JSON: {json.dumps(result, indent=2)}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {response_text}")
                logger.error(f"JSON error: {str(e)}")
                return {}
            
        except Exception as e:
            logger.error(f"GPT extraction failed for section {section_type}: {str(e)}")
            logger.error(f"Text being processed: {text[:200]}...")  # Log first 200 chars of text
            return {}

    def _extract_with_rag(self, file_name: str, missing_fields: list[str], company_config: dict | None = None) -> dict:
        """Use RAG to find specific missing fields.
        
        Args:
            file_name: Name of the file to analyze
            missing_fields: List of field paths to extract (can include nested paths like 'life_insurance.schedule')
            company_config: Optional company-specific configuration
            
        Returns:
            Dictionary with extracted values for missing fields
        """
        results = {}
        
        try:
            # Get the document IDs from ingested documents
            ingested_docs = self._ingest_service.list_ingested()
            doc_ids = [doc.doc_id for doc in ingested_docs if doc.doc_metadata.get('file_name') == file_name]
            
            if not doc_ids:
                logger.error(f"No ingested document found for file: {file_name}")
                return results
                
            # Group fields by their parent path for more efficient extraction
            field_groups = {}
            for field_path in missing_fields:
                parts = field_path.split('.')
                if len(parts) > 1:
                    # For nested fields, group by parent
                    parent = parts[0]
                    child = parts[1]  # Get just the field name
                    if parent not in field_groups:
                        field_groups[parent] = []
                    field_groups[parent].append(child)
                else:
                    # For top-level fields, use empty string as parent
                    if '' not in field_groups:
                        field_groups[''] = []
                    field_groups[''].append(field_path)
            
            logger.info(f"Grouped fields for RAG extraction: {json.dumps(field_groups, indent=2)}")
            
            # Process each group of fields
            for parent, fields in field_groups.items():
                # Initialize section in results if it's a parent section
                if parent and parent not in results:
                    results[parent] = {}
                
                # Get section-specific prompts from company config
                section_prompts = {}
                if company_config and "benefit_headers" in company_config:
                    # Get prompts for this section
                    section_prompts = company_config["benefit_headers"].get(parent, {}).get("fields", {})
                    logger.info(f"Found prompts for section {parent}: {list(section_prompts.keys())}")
                
                for field in fields:
                    # Get field-specific prompt from config
                    field_info = section_prompts.get(field, {})
                    field_prompt = field_info.get("prompt")
                    field_examples = field_info.get("examples", [])
            
                    logger.info(f"Looking up field {field} in section {parent}")
                    logger.info(f"Found prompt: {field_prompt}")
                    logger.info(f"Found examples: {field_examples}")
                    
                    # Build the prompt
                    if not field_prompt:
                        # Generate a default prompt based on the field name
                        field_display = field.replace('_', ' ')
                        field_prompt = f"""Find the {field_display} in the document. Extract the exact value if found."""
                    
                    # Add examples to the prompt if available
                    examples_text = ""
                    if field_examples:
                        examples_text = "\nExample values:\n" + "\n".join(f"- {ex}" for ex in field_examples)
                    
                    prompt = f"""
                        {field_prompt}
                        
                        Important:
                        1. Only extract the specific value for this field.
                        2. If the information is not explicitly stated in the text, respond with 'null'.
                        3. Do not make assumptions or infer values.
                        4. Return the value exactly as it appears in the document.
                        5. Look for the information in any relevant section, including headers, bullet points, and tables.
                        6. Consider variations in terminology (e.g., "second medical opinion" might be listed as "second opinion service" or "medical second opinion").
                        {examples_text}
                    """
            
                    system_prompt = """
                        You are an AI assistant specialized in extracting specific insurance benefit details from documents.
                        Your task is to find and extract exact values from the document text.
                        Only return information that is explicitly stated in the document.
                        If you cannot find the specific information, respond with 'null'.
                        Do not include any explanations or additional text in your response.
                        Be thorough in your search - check all sections of the document as the information might be in unexpected places.
                    """
            
                    try:
                        messages = [
                            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
                            ChatMessage(role=MessageRole.USER, content=prompt)
                        ]
                
                        # Create context filter with all document IDs
                        context_filter = ContextFilter(
                            docs_ids=doc_ids,
                            text=None
                        )
                
                        completion = self._chat_service.chat(
                            messages=messages,
                            use_context=True,
                            context_filter=context_filter
                        )
                
                        response_text = completion.response.strip() if completion.response else None
                        
                        # Clean up the response
                        if not response_text or response_text.lower() in ['null', 'none', 'not found', 'not specified', 'not stated', 'empty response']:
                            response_text = None
                            logger.info(f"No value found for {parent}.{field}")
                        else:
                            # Remove quotes and normalize whitespace
                            response_text = response_text.strip('"\'')
                            response_text = ' '.join(response_text.split())
                            logger.info(f"Found value for {parent}.{field}: {response_text}")
                        
                        # Store the result
                        if parent:
                            results[parent][field] = response_text
                        else:
                            results[field] = response_text
                        
                    except Exception as e:
                        logger.error(f"RAG extraction failed for {parent}.{field}: {str(e)}")
                        if parent:
                            results[parent][field] = None
                        else:
                            results[field] = None
            
            return results

        except Exception as e:
            logger.error(f"Error in RAG extraction: {str(e)}")
            return results

    def _has_missing_fields(self, data: dict, schema_class: type) -> list[str]:
        """Find fields that are None in sections that exist in the data.
        Note: We ignore sections that are None themselves.
        
        Args:
            data: The extracted data dictionary
            schema_class: Unused, kept for compatibility
            
        Returns:
            List of field paths that are None in existing sections
        """
        missing = []
        
        def check_section(section_data: dict, prefix: str = "") -> None:
            """Recursively check a section for None fields."""
            if not isinstance(section_data, dict):
                return
                
            for field_name, value in section_data.items():
                field_path = f"{prefix}{field_name}" if prefix else field_name
                
                if isinstance(value, dict):
                    # Recursively check nested dictionaries
                    check_section(value, f"{field_path}.")
                elif value is None:
                    # Add field to missing list if it's None
                    missing.append(field_path)
        
        # Process each top-level section
        for section_name, section_data in data.items():
            # Skip sections that are None entirely
            if section_data is not None:
                check_section(section_data, f"{section_name}.")
        
        return missing

    def get_document_path(self, file_name: str) -> str | None:
        """Get the full path of an ingested document.
        
        Args:
            file_name: Name of the file
            
        Returns:
            Full path to the document if found, None otherwise
        """
        try:
            # Check in the storage directory
            file_path = self._storage_dir / file_name
            if file_path.exists():
                return str(file_path)
            
            # Check in the extracted pages directory
            file_path = self._extracted_pages_dir / file_name
            if file_path.exists():
                return str(file_path)
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting document path: {str(e)}")
            return None

    def extract_pdf_pages(self, file_name: str, page_numbers: List[int], output_name: Optional[str] = None) -> Path:
        """Extract specific pages from a PDF file.
        
        Args:
            file_name: Name of the file to extract pages from
            page_numbers: List of page numbers to extract (1-based indexing)
            output_name: Optional name for the output file
            
        Returns:
            Path to the new PDF containing only the specified pages
        """
        # Get the original file path from the original_files directory
        original_file_path = self._storage_dir / file_name
        if not original_file_path.exists():
            raise FileNotFoundError(f"Original file not found: {file_name}")
            
        if not output_name:
            output_name = f"{Path(file_name).stem}_benefit_summary.pdf"
            
        output_path = self._extracted_pages_dir / output_name
        
        try:
            # Read the PDF
            reader = PdfReader(original_file_path)
            writer = PdfWriter()
            
            # Convert to 0-based indexing and validate page numbers
            page_indices = [i - 1 for i in page_numbers]  # Convert to 0-based indexing
            max_page = len(reader.pages)
            valid_indices = [i for i in page_indices if 0 <= i < max_page]
            
            if not valid_indices:
                raise ValueError(f"No valid page numbers provided. PDF has {max_page} pages.")
            
            # Add selected pages to the writer
            for page_idx in valid_indices:
                writer.add_page(reader.pages[page_idx])
            
            # Save the new PDF
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
                
            logger.info(f"Successfully extracted pages {page_numbers} to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error extracting PDF pages: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error extracting PDF pages: {str(e)}"
            )

    def get_benefit_summary_pages(self, file_name: str, company_name: str | None = None) -> list[int]:
        """Identify pages containing benefit summary information.
        
        Args:
            file_name: Name of the file to analyze
            company_name: Optional company name to use specific config
            
        Returns:
            List of page numbers containing benefit information
        """
        try:
            # Get the original file path
            file_path = self._storage_dir / file_name
            if not file_path.exists():
                raise FileNotFoundError(f"Original file not found: {file_name}")

            # Load company config for markers
            company_config = self._load_company_config(company_name) if company_name else None
            if not company_config or "document_structure" not in company_config:
                logger.warning(f"No valid config found for company {company_name}, using default markers")
                start_markers = [
                    "BENEFIT SUMMARIES",
                    "GROUP INSURANCE BENEFIT SUMMARY",
                    "BENEFIT SUMMARY",
                    "INSURANCE BENEFITS",
                    "SUMMARY OF BENEFITS",
                    "SCHEDULE OF BENEFITS"
                ]
                end_markers = [
                    "GENERAL DEFINITIONS",
                    "GENERAL PROVISIONS",
                ]
                toc_markers = ["TABLE OF CONTENTS", "CONTENTS"]
            else:
                doc_structure = company_config["document_structure"]
                start_markers = doc_structure["start_markers"]
                end_markers = doc_structure["end_markers"]
                toc_markers = doc_structure["toc_markers"]
            
            logger.info(f"Using markers - Start: {start_markers}, End: {end_markers}, TOC: {toc_markers}")
            
            # Read the PDF
            reader = PdfReader(file_path)
            benefit_pages = []
            in_toc = False
            in_benefit_section = False
            total_pages = len(reader.pages)
            start_page = None
            
            logger.info(f"Processing PDF with {total_pages} pages")
            
            # Process each page
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text().upper()  # Convert to uppercase for case-insensitive matching
                logger.debug(f"Processing page {page_num}")
                
                # Check if we're in TOC
                if any(marker.upper() in text for marker in toc_markers):
                    logger.info(f"Found TOC on page {page_num}")
                    in_toc = True
                    continue
                
                # Check for start of benefit section using fuzzy matching
                if not in_benefit_section:
                    for marker in start_markers:
                        if self._calculate_similarity(marker.upper(), text) > 0.8 or marker.upper() in text:
                            logger.info(f"Found benefit section start on page {page_num} (matched with '{marker}')")
                            in_toc = False
                            in_benefit_section = True
                            start_page = page_num
                            break
                
                # Check for end of benefit section
                if in_benefit_section:
                    # Check for exact matches first
                    if any(marker.upper() in text for marker in end_markers):
                        logger.info(f"Found benefit section end on page {page_num}")
                        # Add all pages from start to end (inclusive of start, exclusive of end)
                        benefit_pages = list(range(start_page, page_num))
                        break
                    
                    # Then check for fuzzy matches
                    for marker in end_markers:
                        if self._calculate_similarity(marker.upper(), text) > 0.8:
                            logger.info(f"Found fuzzy match for end marker on page {page_num} (matched with '{marker}')")
                            # Add all pages from start to end (inclusive of start, exclusive of end)
                            benefit_pages = list(range(start_page, page_num))
                            break
            
            if not benefit_pages and start_page:
                # If we found a start but no end, include pages up to page 20
                logger.warning("No end marker found, including pages up to page 20")
                benefit_pages = list(range(start_page, min(21, total_pages + 1)))

            if not benefit_pages:
                logger.warning("No benefit summary pages found with markers, using first section of document")
                # Default to first few pages if no markers found
                benefit_pages = list(range(5, min(21, total_pages + 1)))  # First 10 pages or all pages if less

            logger.info(f"Found benefit summary pages: {benefit_pages}")
            return benefit_pages
            
        except Exception as e:
            logger.error(f"Error identifying benefit summary pages: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error identifying benefit summary pages: {str(e)}"
            )

    def extract_benefit_summary(self, file_name: str, company_name: Optional[str] = None) -> Path:
        """Extract benefit summary pages from a PDF file.
        
        Args:
            file_name: Name of the file to process
            company_name: Optional company name to use specific config
            
        Returns:
            Path to the new PDF containing only benefit summary pages
        """
        # First identify which pages contain benefit information
        benefit_pages = self.get_benefit_summary_pages(file_name, company_name)
        
        # Extract those pages into a new PDF
        return self.extract_pdf_pages(
            file_name=file_name,
            page_numbers=benefit_pages,
            output_name=f"{Path(file_name).stem}_benefit_summary.pdf"
        )

    def store_pdf(self, source_path: str | Path, file_name: str) -> Path:
        """Store a PDF file in the storage directory.
        
        Args:
            source_path: Path to the source PDF file
            file_name: Name to save the file as
            
        Returns:
            Path to the stored file
        """
        try:
            # Create storage directory if it doesn't exist
            self._storage_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine target path
            target_path = self._storage_dir / file_name
            
            # Copy the file
            shutil.copy2(source_path, target_path)
            logger.info(f"Stored PDF at: {target_path}")
            
            return target_path
        
        except Exception as e:
            logger.error(f"Error storing PDF: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error storing PDF: {str(e)}"
            )

    def create_benefit_comparison(self, file_name: str, company_name: str) -> Tuple[Path, dict]:
        """Create a benefit comparison Excel file from extraction results.
        
        Args:
            file_name: Name of the PDF file to extract from
            company_name: Name of the company for the comparison
            
        Returns:
            Tuple of (Path to generated Excel file, Extraction results dictionary)
        """
        try:
            # Extract the benefit summary pages
            extracted_pdf_path = self.extract_benefit_summary(file_name, company_name)

            try:
                benefit_agent = extractor.get_agent("benefit-summary-parser")
                logger.info("Successfully retrieved existing benefit-summary-parser agent")
            except Exception as e:
                logger.info(f"Agent not found, creating new one: {str(e)}")
                benefit_agent = extractor.create_agent(
                    name="benefit-summary-parser",
                    data_schema=InsuranceSummary
                )
            
            extraction_result = benefit_agent.extract(str(extracted_pdf_path))
            logger.info("Successfully created new benefit-summary-parser agent")
            initial_data = extraction_result.data
            
            # Check for missing fields and use RAG to fill them
            missing_fields = self._has_missing_fields(initial_data, InsuranceSummary)
            
            if missing_fields:
                logger.info(f"Found {len(missing_fields)} missing fields, using RAG to extract them")
                # Load company config if available
                company_config = self._load_company_config(company_name)
                
                # Extract missing fields using RAG
                rag_results = self._extract_with_rag(
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
                final_data = initial_data
            # Create the comparison document
            template = BenefitComparisonTemplate()
            output_path = template.fill(final_data)  # Changed from fill_template to fill
            
            logger.info(f"Successfully created benefit comparison at {output_path}")
            return output_path, final_data

        except Exception as e:
            logger.error(f"Error creating benefit comparison: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create benefit comparison: {str(e)}"
            )

