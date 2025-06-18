from llama_index.core.llms import ChatMessage, MessageRole
from llama_cloud_services import LlamaExtract
from typing import Dict, List, Optional, Any, Tuple
from injector import inject, singleton
from fastapi import HTTPException
from dotenv import load_dotenv
from pathlib import Path

import shutil
import json
import logging
import difflib
import os
import time

from bridgewell_gpt.server.ingest.ingest_service import IngestService
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

        self.llama_extract = LlamaExtract()
        self.storage_path = local_data_path / "extraction_results"
        self.storage_path.mkdir(parents=True, exist_ok=True)

    @property
    def storage_dir(self) -> Path:
        return self._storage_dir

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

    def _extract_with_gpt(self, text: str, section_type: str, company_config: dict | None = None) -> dict:
        """Extract structured data from section text using GPT."""
        try:
            logger.debug(f"Starting GPT extraction for section type: {section_type}")
            
            # Map the document section type to structure.json section type using company config
            structure_type = self._map_section_type_to_structure(section_type, company_config)
            logger.debug(f"Mapped to structure type: {structure_type}")
            
            # Get only the relevant section structure
            structure = self._load_json_structure(structure_type)
            if not structure:
                logger.warning(f"No structure found for section type: {structure_type}")
                return {}
            
            logger.debug(f"Loaded structure: {json.dumps(structure, indent=2)}")
            
            # Get company-specific field prompts if available
            field_prompts = {}
            if company_config and "benefit_headers" in company_config:
                # Find the matching section in benefit_headers
                for section_name, section_info in company_config["benefit_headers"].items():
                    # Map the section name to structure type for comparison
                    mapped_section = self._map_section_type_to_structure(section_name, company_config)
                    if mapped_section == structure_type and "fields" in section_info:
                        field_prompts = section_info["fields"]
                        logger.debug(f"Found field prompts for section {structure_type}: {list(field_prompts.keys())}")
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

            system_prompt = (
                "You are an AI assistant specialized in extracting specific insurance benefit details from documents. "
                "Your task is to find and extract exact values and their locations from the document text. "
                "Only return information that is explicitly stated in the document. "
                "You must return the information in the exact JSON format specified. "
                "If you cannot find the specific information, respond with 'null'. "
                "Do not include any explanations or additional text in your response. "
                "Be thorough in your search - check all sections of the document as the information might be in unexpected places. "
                "\n\n"
                "Instructions: "
                "1. For each field, find and return the following information: "
                "   - The exact value from the document (see user prompt for details) "
                "   - The page number where the value was found (0-based) "
                "   - The coordinates of the value on the page, as a list of bounding box dictionaries in this format: [{ 'l': left, 't': top, 'r': right, 'b': bottom}] "
                "   - The surrounding text or context where the value was found "
                "2. Return the information in this exact JSON format: "
                '{ "value": "extracted value", "page": page_number, "bbox": [ { "l": left, "t": top, "r": right, "b": bottom } ], "source_snippet": "surrounding text" } '
                "3. If any piece of information is not available, use null for that field. "
                "4. If the information is not found at all, return null. "
                "5. Do not make assumptions or infer values. "
                "6. Look for the information in any relevant section. "
                "Return only the JSON object, no other text. "
                "For bbox, always try to extract a list of bounding boxes with keys 'l', 't', 'r', 'b'. If not available, set bbox to null."
            )
            
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
            
            logger.debug("Sending request to chat service")
            messages = [
                ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
                ChatMessage(role=MessageRole.USER, content=prompt)
            ]
            
            completion = self._chat_service.chat(messages=messages)
            logger.debug("Received response from chat service")
            
            # Clean up the response to extract just the JSON
            response_text = completion.response.strip()
            logger.debug(f"Raw response: {response_text[:200]}...")  # Log first 200 chars
            
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
                logger.debug(f"Successfully parsed JSON: {json.dumps(result, indent=2)}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {response_text}")
                logger.error(f"JSON error: {str(e)}")
                return {}
            
        except Exception as e:
            logger.error(f"GPT extraction failed for section {section_type}: {str(e)}")
            logger.error(f"Text being processed: {text[:200]}...")  # Log first 200 chars of text
            return {}

    def _extract_with_rag(self, doc_id: str, missing_fields: list[str], company_config: dict | None = None) -> dict:
        """Use RAG to find specific missing fields.
        
        Args:
            doc_id: Document ID to analyze
            missing_fields: List of field paths to extract (can include nested paths like 'life_insurance.schedule')
            company_config: Optional company-specific configuration
            
        Returns:
            Dictionary with extracted values for missing fields
        """
        results = {}
        
        try:
            # Get the document IDs from ingested documents
            ingested_docs = self._ingest_service.list_ingested()
            doc_ids = [doc.doc_id for doc in ingested_docs if doc.doc_id == doc_id]
            
            if not doc_ids:
                logger.error(f"No ingested document found for doc_id: {doc_id}")
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
            
            logger.debug(f"Grouped fields for RAG extraction: {json.dumps(field_groups, indent=2)}")
            
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
                    logger.debug(f"Found prompts for section {parent}: {list(section_prompts.keys())}")
                
                for field in fields:
                    # Get field-specific prompt and examples from company config
                    field_prompt = None
                    field_examples = []
                    
                    if company_config and "benefit_headers" in company_config:
                        # Find the matching section in benefit_headers
                        for section_name, section_info in company_config["benefit_headers"].items():
                            if parent in section_name.lower():
                                if "fields" in section_info and field in section_info["fields"]:
                                    field_info = section_info["fields"][field]
                                    field_prompt = field_info.get("prompt")
                                    field_examples = field_info.get("examples", [])
                                    logger.debug(f"\nFound config for {parent}.{field}:")
                                    logger.debug(f"  Prompt: {field_prompt}")
                                    logger.debug(f"  Examples: {field_examples}")
                                break
                    
                    if not field_prompt:
                        field_prompt = f"Find the {field} in the {parent} section"
                        logger.debug(f"\nUsing default prompt for {parent}.{field}: {field_prompt}")
                    
                    examples_text = ""
                    if field_examples:
                        examples_text = "\nExample values:\n" + "\n".join(f"- {ex}" for ex in field_examples)
                    
                    prompt = f"{field_prompt} {examples_text}"
                    
                    logger.debug(f"\nFinal prompt for {parent}.{field}:")
                    logger.debug(prompt)
                    
                    system_prompt = (
                        "You are an advanced AI document analysis assistant with deep expertise in insurance document analysis and benefit extraction. You possess specialized knowledge of insurance terminology, policy structures, and regulatory requirements. Your capabilities include sophisticated document parsing, cross-reference analysis, and precise data extraction from complex insurance documents including benefit summaries, policy documents, and coverage explanations. "
                        "Your task is to find and extract exact values and their locations from the document text. "
                        "Only return information that is explicitly stated in the document. "
                        "You must return the information in the exact JSON format specified. "
                        "If you cannot find the specific information, respond with 'null'. "
                        "Do not include any explanations or additional text in your response. "
                        "Be thorough in your search - check all sections of the document as the information might be in unexpected places. "
                        "\n\n"
                        "Instructions: "
                        "1. For each field, find and return the following information: "
                        "   - The exact value from the document (see user prompt for details) "
                        "   - The page number where the value was found (0-based) "
                        "   - The coordinates of the value extracted on the page, as a bounding box dictionary in this format:  { 'l': left, 't': top, 'r': right, 'b': bottom}"
                        "   - The surrounding text or context where the value was found "
                        "2. Return the information always in this exact JSON format: "
                        '{ "value": "extracted value", "page": page_number, "bbox": { "l": left, "t": top, "r": right, "b": bottom }, "source_snippet": "surrounding text" } '
                        "3. If any piece of information is not available, use null for that field. "
                        "4. If the information is not found at all, return null. "
                        "5. Do not make assumptions or infer values. "
                        "6. Look for the information in any relevant section. "
                        
                    )
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
                        # Safely get source text if available
                        source_text = None
                        try:
                            if hasattr(completion, 'source_nodes') and completion.source_nodes:
                                source_text = completion.source_nodes[0].text
                        except (AttributeError, IndexError) as e:
                            logger.debug(f"Could not get source text: {str(e)}")
                        
                        logger.debug(f"\nRAG response for {parent}.{field}:")
                        logger.debug(f"Response: {response_text}")
                        logger.debug(f"Source text: {source_text}")
                        
                        # Clean up response text - remove markdown code block tags
                        if response_text:
                            # Remove ```json and ``` tags
                            response_text = response_text.replace('```json', '').replace('```', '').strip()
                            logger.debug(f"Cleaned response: {response_text}")
                        
                        # Parse the response as JSON if possible
                        try:
                            if response_text and response_text.lower() not in ['null', 'none', 'not found', 'not specified', 'not stated', 'empty response']:
                                parsed_response = json.loads(response_text)
                                if isinstance(parsed_response, dict):
                                    # Store the result with full structure
                                    if parent:
                                        if parent not in results:
                                            results[parent] = {}
                                        results[parent][field] = parsed_response
                                    else:
                                        results[field] = parsed_response
                                    logger.debug(f"Found structured value for {parent}.{field}: {parsed_response}")
                                else:
                                    logger.warning(f"Response was not a dictionary: {response_text}")
                                    if not isinstance(parsed_response, dict):
                                        parsed_response = {"value": parsed_response, "page": None, "bbox": None, "source_snippet": None}
                            else:
                                logger.debug(f"No value found for {parent}.{field}")
                                if parent:
                                    if parent not in results:
                                        results[parent] = {}
                                    results[parent][field] = None
                                else:
                                    results[field] = None
                        except json.JSONDecodeError:
                            logger.warning(f"Could not parse response as JSON: {response_text}")
                            # Fall back to simple value
                            if response_text and response_text.lower() not in ['null', 'none', 'not found', 'not specified', 'not stated', 'empty response']:
                                simple_result = {
                                    "value": response_text,
                                    "page": None,
                                    "bbox": None,
                                    "source_snippet": source_text
                                }
                                if parent:
                                    if parent not in results:
                                        results[parent] = {}
                                    results[parent][field] = simple_result
                                else:
                                    results[field] = simple_result
                            else:
                                if parent:
                                    if parent not in results:
                                        results[parent] = {}
                                    results[parent][field] = None
                                else:
                                    results[field] = None
                    except Exception as e:
                        logger.error(f"RAG extraction failed for {parent}.{field}: {str(e)}")
                        if parent:
                            if parent not in results:
                                results[parent] = {}
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
        """Get the full path of the original stored document.
        
        Args:
            file_name: Name of the file
            
        Returns:
            Full path to the document if found, None otherwise
        """
        try:
            file_path = self._storage_dir / file_name
            if file_path.exists():
                return str(file_path)
            return None
        
        except Exception as e:
            logger.error(f"Error getting document path: {str(e)}")
            return None

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
            logger.debug(f"Stored PDF at: {target_path}")
            
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
            # Get the path to the original stored PDF file
            original_pdf_path = self._storage_dir / file_name
            if not original_pdf_path.exists():
                logger.error(f"Original file not found: {original_pdf_path}")
                raise FileNotFoundError(f"Original file not found: {file_name}")

            logger.debug(f"Processing full PDF document: {original_pdf_path}")

            try:
                benefit_agent = extractor.get_agent("benefit-summary-parser")
                logger.debug("Successfully retrieved existing benefit-summary-parser agent")
            except Exception as e:
                logger.debug(f"Agent not found, creating new one: {str(e)}")
                benefit_agent = extractor.create_agent(
                    name="benefit-summary-parser",
                    data_schema=InsuranceSummary,
                    config={"extraction_mode": "FAST"}
                )
            
            # Extract data from the entire original PDF
            extraction_result = benefit_agent.extract(str(original_pdf_path))
            logger.debug("Successfully extracted initial data with benefit-summary-parser agent")
            initial_data = extraction_result.data
            
            # Check for missing fields and use RAG to fill them
            missing_fields = self._has_missing_fields(initial_data, InsuranceSummary)
            
            if missing_fields:
                logger.debug(f"Found {len(missing_fields)} missing fields, using RAG to extract them")
                # Load company config if available
                company_config = self._load_company_config(company_name)
                
                # Wait for embeddings to finish before proceeding with RAG
                logger.debug("Waiting for embeddings to complete before RAG extraction")
                ingested_docs = self._ingest_service.list_ingested()
                doc_ids = [doc.doc_id for doc in ingested_docs if doc.doc_metadata.get('file_name') == file_name]
                
                if not doc_ids:
                    logger.warning("No ingested documents found. Waiting for embeddings to complete...")
                    # You might want to add a small delay or retry mechanism here
                    max_retries = 5
                    retry_delay = 2  # seconds
                    
                    for _ in range(max_retries):
                        time.sleep(retry_delay)
                        ingested_docs = self._ingest_service.list_ingested()
                        doc_ids = [doc.doc_id for doc in ingested_docs if doc.doc_metadata.get('file_name') == file_name]
                        if doc_ids:
                            logger.debug("Documents found after waiting for embeddings")
                            break
                    else:
                        logger.error("Embeddings not completed after maximum retries")
                        raise Exception("Embeddings not completed in time")
                
                # Extract missing fields using RAG with ingested document
                rag_results = self._extract_with_rag(
                    doc_id=file_name,
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
                logger.debug("Successfully merged RAG results with initial data")
            else:
                logger.debug("No missing fields found, using initial extraction data")
                final_data = initial_data
            
            # Create the comparison document
            template = BenefitComparisonTemplate()
            output_path = template.fill(final_data)
            
            logger.debug(f"Successfully created benefit comparison at {output_path}")
            return output_path, final_data

        except Exception as e:
            logger.error(f"Error creating benefit comparison: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create benefit comparison: {str(e)}"
            )

    def get_document_info(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document information by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Dictionary containing document information or None if not found
        """
        # Look through all extraction results to find matching document
        for extraction_id in os.listdir(self.storage_path):
            extraction_dir = self.storage_path / extraction_id
            if not extraction_dir.is_dir():
                continue
                
            result_path = extraction_dir / "result.json"
            if result_path.exists():
                with open(result_path, "r") as f:
                    result = json.load(f)
                    if result.get("doc_id") == doc_id:
                        return {
                            "file_name": result.get("file_name"),
                            "document_type": result.get("document_type"),
                            "extraction_id": extraction_id
                        }
        return None

