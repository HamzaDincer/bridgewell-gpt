import json
from pathlib import Path
from typing import Any

from llama_index.core.schema import Document

from bridgewell_gpt.server.ingest.ingest_service import IngestService
from bridgewell_gpt.settings.settings import settings
from bridgewell_gpt.components.embedding.embedding_component import EmbeddingComponent
from bridgewell_gpt.components.llm.llm_component import LLMComponent
from bridgewell_gpt.components.node_store.node_store_component import NodeStoreComponent
from bridgewell_gpt.components.vector_store.vector_store_component import VectorStoreComponent

def create_documents_from_chunks(json_data: dict[str, Any]) -> list[Document]:
    documents = []
    for chunk in json_data.get("chunks", []):
        # Create a document for each chunk
        doc = Document(
            text=chunk["text"],
            metadata={
                "chunk_id": chunk["chunk_id"],
                "chunk_type": chunk["chunk_type"],
                "page": chunk["grounding"][0]["page"] if chunk["grounding"] else None,
                "coordinates": chunk["grounding"][0]["box"] if chunk["grounding"] else None,
            }
        )
        documents.append(doc)
    return documents

def main():
    # Initialize components
    settings_instance = settings()
    llm_component = LLMComponent(settings_instance)
    vector_store_component = VectorStoreComponent(settings_instance)
    embedding_component = EmbeddingComponent(settings_instance)
    node_store_component = NodeStoreComponent(settings_instance)
    
    # Create ingest service
    ingest_service = IngestService(
        llm_component=llm_component,
        vector_store_component=vector_store_component,
        embedding_component=embedding_component,
        node_store_component=node_store_component,
    )
    
    # Load JSON file
    json_file = Path("/Users/hamzadincer/Downloads/sample.extraction.json")
    with open(json_file) as f:
        json_data = json.load(f)
    
    # Create documents from chunks
    documents = create_documents_from_chunks(json_data)
    
    # Ingest documents
    ingested_docs = ingest_service.ingest_component.ingest("sample.extraction.json", json_file)
    print(f"Ingested {len(ingested_docs)} documents")

if __name__ == "__main__":
    main() 