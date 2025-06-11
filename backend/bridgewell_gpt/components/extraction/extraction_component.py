import logging
from typing import Dict, Any, Optional, List
import json
import os
import uuid
from pathlib import Path
import tempfile
from injector import singleton
from llama_cloud_services import LlamaExtract
from llama_index.core.schema import Document
from dotenv import load_dotenv
from bridgewell_gpt.paths import local_data_path
import datetime

from bridgewell_gpt.server.extraction.insurance_schema import InsuranceSummary

logger = logging.getLogger(__name__)

load_dotenv()

@singleton
class ExtractionComponent:
    def __init__(self) -> None:
        self.llama_extract = LlamaExtract()
        self.storage_path = local_data_path / "extraction_results"
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def extract_document(
        self, 
        documents: List[Document],
        document_type: str,
        file_name: str,
        agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract information from documents using LlamaExtract.
        
        Args:
            documents: List of documents to extract from
            document_type: Type of the document
            file_name: Name of the file
            agent_name: Optional specific agent name to use
            
        Returns:
            Dict containing extraction results
        """
        try:
            # Convert documents to chunks format
            chunks = []
            for doc in documents:
                # Ensure all values are JSON serializable
                metadata = {
                    "page": doc.metadata.get("page"),
                    "bbox": doc.metadata.get("bbox"),
                    "chunk_type": doc.metadata.get("chunk_type")
                }
                chunk = {
                    "text": doc.text,
                    "metadata": {k: v for k, v in metadata.items() if v is not None}  # Remove None values
                }
                chunks.append(chunk)

            logger.info(f"Created {len(chunks)} chunks for extraction")

            # Get agent name from settings if not provided
            if not agent_name:
                agent_name = self._get_agent_name_for_type(document_type)
            
            # Create extraction ID
            extraction_id = str(uuid.uuid4())
            logger.info(f"Generated new extraction_id: {extraction_id}")
            
            # Store chunks for future reference
            self._store_extraction_data(
                extraction_id,
                chunks,
                document_type,
                file_name
            )
            
            # Create content dictionary
            content = {
                "chunks": chunks
            }
                
            # Get the extraction agent
            try:
                benefit_agent = self.llama_extract.get_agent("benefit-summary-parser")
                logger.info("Successfully retrieved existing benefit-summary-parser agent")
            except Exception as e:
                logger.info(f"Agent not found, creating new one: {str(e)}")
                benefit_agent = self.llama_extract.create_agent(
                    name="benefit-summary-parser",
                    data_schema=InsuranceSummary
                )
            
            # Save content to temporary JSON file and extract
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                temp_path = temp_file.name
                logger.info(f"Writing to temp file: {temp_path}")
                # Write the content dictionary to the temp file
                json.dump(content, temp_file)
                temp_file.flush()  # Ensure content is written

                try:
                    # Perform extraction
                    logger.info(f"Starting extraction with agent on file: {temp_path}")
                    extraction_result = benefit_agent.extract(temp_path)
                    result = extraction_result.data
                    
                    logger.info("Extraction completed successfully")
                    logger.debug("Extraction result: %s", json.dumps(result, indent=2))
                    
                    # Store the successful result
                    result_path = self.storage_path / extraction_id / "result.json"
                    logger.info(f"Storing extraction result at: {result_path}")
                    result_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(result_path, "w") as f:
                        json.dump({
                            "extraction_id": extraction_id,
                            "document_type": document_type,
                            "file_name": file_name,
                            "status": "completed",
                            "result": result,
                            "timestamp": datetime.datetime.now().isoformat()
                        }, f, indent=2)
                    
                    logger.info(f"Successfully stored extraction result for ID: {extraction_id}")
                    
                    return {
                        "extraction_id": extraction_id,
                        "document_type": document_type,
                        "file_name": file_name,
                        "status": "completed",
                        "result": result
                    }
                    
                finally:
                    # Clean up temporary file
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Extraction error for {file_name}: {str(e)}")
            return {
                "error": str(e),
                "document_type": document_type,
                "file_name": file_name,
                "status": "error"
            }

    def _get_agent_name_for_type(self, document_type: str) -> str:
        """Get the appropriate agent name for a document type."""
        agent_mapping = {
            "Insurance": "insurance-parser",
            "Contract": "contract-parser",
            "Invoice": "invoice-parser",
            "Benefit": "benefit-summary-parser"  # Added benefit summary parser
        }
        return agent_mapping.get(document_type, "default-parser")

    def _store_extraction_data(
        self,
        extraction_id: str,
        chunks: List[Dict[str, Any]],
        document_type: str,
        file_name: str
    ) -> None:
        """Store extraction data for future reference."""
        extraction_dir = self.storage_path / extraction_id
        extraction_dir.mkdir(parents=True, exist_ok=True)
        
        # Store chunks
        chunks_path = extraction_dir / "chunks.json"
        with open(chunks_path, "w") as f:
            json.dump({
                "chunks": chunks,
                "document_type": document_type,
                "file_name": file_name
            }, f, indent=2)

    def get_extraction_result(self, extraction_id: str) -> Optional[Dict[str, Any]]:
        """Get stored extraction result by ID."""
        extraction_dir = self.storage_path / extraction_id
        if not extraction_dir.exists():
            return None
            
        result_path = extraction_dir / "result.json"
        if result_path.exists():
            with open(result_path, "r") as f:
                return json.load(f)
        return None

    def list_extraction_results(self, document_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all stored extraction results."""
        results = []
        for extraction_id in os.listdir(self.storage_path):
            extraction_dir = self.storage_path / extraction_id
            if not extraction_dir.is_dir():
                continue
                
            result = self.get_extraction_result(extraction_id)
            if result and (not document_type or result["document_type"] == document_type):
                results.append(result)
        return results

    def get_latest_extraction_by_file(self, file_name: str) -> Optional[Dict[str, Any]]:
        """Get the most recent extraction result for a specific file.
        
        Args:
            file_name: Name of the file to get extraction for
            
        Returns:
            The most recent extraction result or None if not found
        """
        results = []
        for extraction_id in os.listdir(self.storage_path):
            extraction_dir = self.storage_path / extraction_id
            if not extraction_dir.is_dir():
                continue
                
            result = self.get_extraction_result(extraction_id)
            if result and result.get("file_name") == file_name:
                results.append(result)
        
        if not results:
            return None
            
        # Return the most recent result based on timestamp
        return max(results, key=lambda x: x.get("timestamp", ""))
