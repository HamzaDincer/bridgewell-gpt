"""Test ParallelizedIngestComponent for feature parity with SimpleIngestComponent."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import uuid

from llama_index.core.schema import Document
from llama_index.core.storage import StorageContext

from bridgewell_gpt.components.ingest.ingest_component import (
    ParallelizedIngestComponent,
    SimpleIngestComponent,
)
from bridgewell_gpt.components.extraction.extraction_component import ExtractionComponent
from bridgewell_gpt.settings.settings import Settings


@pytest.fixture
def mock_storage_context():
    """Create a mock storage context."""
    return Mock(spec=StorageContext)


@pytest.fixture
def mock_embed_model():
    """Create a mock embed model."""
    return Mock()


@pytest.fixture
def mock_transformations():
    """Create mock transformations."""
    return [Mock(), Mock()]  # At least 2 transformations required


@pytest.fixture
def mock_extraction_component():
    """Create a mock extraction component."""
    extraction_component = Mock(spec=ExtractionComponent)
    extraction_component.extract_document.return_value = {
        "status": "completed",
        "extraction_id": str(uuid.uuid4()),
        "document_type": "Benefit",
        "result": {
            "basic_info": {
                "company_name": "Test Company",
                "plan_name": "Test Plan"
            }
        }
    }
    return extraction_component


@pytest.fixture
def mock_services():
    """Create mock ingest and chat services."""
    return Mock(), Mock()


class TestParallelizedIngestComponent:
    """Test ParallelizedIngestComponent features."""

    def test_initialization(
        self,
        mock_storage_context,
        mock_embed_model,
        mock_transformations,
        mock_extraction_component,
        mock_services,
    ):
        """Test component initialization with all parameters."""
        ingest_service, chat_service = mock_services
        
        component = ParallelizedIngestComponent(
            storage_context=mock_storage_context,
            embed_model=mock_embed_model,
            transformations=mock_transformations,
            count_workers=2,
            extraction_component=mock_extraction_component,
            ingest_service=ingest_service,
            chat_service=chat_service,
        )
        
        assert component.extraction_component == mock_extraction_component
        assert component._ingest_service == ingest_service
        assert component._chat_service == chat_service
        assert hasattr(component, '_rag_thread_lock')
        assert component.count_workers == 2

    @patch('bridgewell_gpt.components.ingest.ingest_helper.IngestionHelper.store_original_file')
    @patch('bridgewell_gpt.components.ingest.ingest_helper.IngestionHelper.transform_file_into_documents')
    @patch('bridgewell_gpt.server.document_types.document_type_service.DocumentTypeService')
    def test_ingest_with_extraction(
        self,
        mock_doc_type_service,
        mock_transform_docs,
        mock_store_file,
        mock_storage_context,
        mock_embed_model,
        mock_transformations,
        mock_extraction_component,
        mock_services,
    ):
        """Test ingestion with extraction enabled."""
        # Setup mocks
        test_file = Path("test.pdf")
        stored_path = Path("stored/test.pdf")
        mock_store_file.return_value = stored_path
        
        test_documents = [
            Document(text="Test content", metadata={"page": 1})
        ]
        mock_transform_docs.return_value = test_documents
        
        # Create component with extraction
        ingest_service, chat_service = mock_services
        component = ParallelizedIngestComponent(
            storage_context=mock_storage_context,
            embed_model=mock_embed_model,
            transformations=mock_transformations,
            count_workers=2,
            extraction_component=mock_extraction_component,
            ingest_service=ingest_service,
            chat_service=chat_service,
        )
        
        # Mock the index
        component._index = Mock()
        
        # Perform ingestion
        with patch('threading.Thread') as mock_thread:
            result = component.ingest("test.pdf", test_file)
        
        # Verify results
        assert len(result) == 1
        assert result[0].metadata["file_name"] == "test.pdf"
        assert "doc_id" in result[0].metadata
        
        # Verify store_original_file was called
        mock_store_file.assert_called_once_with("test.pdf", test_file)
        
        # Verify document phase was updated
        mock_doc_type_service().update_document_phase.assert_called()
        
        # Verify background thread was started
        mock_thread.assert_called_once()

    def test_ingest_without_extraction(
        self,
        mock_storage_context,
        mock_embed_model,
        mock_transformations,
        mock_services,
    ):
        """Test ingestion without extraction (fallback to original behavior)."""
        ingest_service, chat_service = mock_services
        
        # Create component without extraction
        component = ParallelizedIngestComponent(
            storage_context=mock_storage_context,
            embed_model=mock_embed_model,
            transformations=mock_transformations,
            count_workers=2,
            extraction_component=None,  # No extraction
            ingest_service=ingest_service,
            chat_service=chat_service,
        )
        
        # Mock the pool and index
        component._file_to_documents_work_pool = Mock()
        component._index = Mock()
        
        test_documents = [
            Document(text="Test content", metadata={"page": 1})
        ]
        component._file_to_documents_work_pool.apply.return_value = test_documents
        
        # Mock _save_docs to return documents
        with patch.object(component, '_save_docs', return_value=test_documents):
            result = component.ingest("test.pdf", Path("test.pdf"))
        
        # Verify fallback behavior
        assert result == test_documents
        component._file_to_documents_work_pool.apply.assert_called_once()

    def test_bulk_ingest_with_extraction(
        self,
        mock_storage_context,
        mock_embed_model,
        mock_transformations,
        mock_extraction_component,
        mock_services,
    ):
        """Test bulk ingestion with extraction processes files individually."""
        ingest_service, chat_service = mock_services
        
        component = ParallelizedIngestComponent(
            storage_context=mock_storage_context,
            embed_model=mock_embed_model,
            transformations=mock_transformations,
            count_workers=2,
            extraction_component=mock_extraction_component,
            ingest_service=ingest_service,
            chat_service=chat_service,
        )
        
        # Mock ingest method
        mock_doc = Document(text="", metadata={"file_name": "test.pdf", "doc_id": "123"})
        with patch.object(component, 'ingest', return_value=[mock_doc]):
            files = [
                ("test1.pdf", Path("test1.pdf")),
                ("test2.pdf", Path("test2.pdf")),
            ]
            result = component.bulk_ingest(files)
        
        # Verify individual processing
        assert len(result) == 2
        assert component.ingest.call_count == 2

    def test_bulk_ingest_without_extraction(
        self,
        mock_storage_context,
        mock_embed_model,
        mock_transformations,
        mock_services,
    ):
        """Test bulk ingestion without extraction uses parallel processing."""
        ingest_service, chat_service = mock_services
        
        component = ParallelizedIngestComponent(
            storage_context=mock_storage_context,
            embed_model=mock_embed_model,
            transformations=mock_transformations,
            count_workers=2,
            extraction_component=None,  # No extraction
            ingest_service=ingest_service,
            chat_service=chat_service,
        )
        
        # Mock the pool
        component._ingest_work_pool = Mock()
        mock_docs = [Document(text="Test 1"), Document(text="Test 2")]
        component._ingest_work_pool.starmap.return_value = [[mock_docs[0]], [mock_docs[1]]]
        
        files = [
            ("test1.pdf", Path("test1.pdf")),
            ("test2.pdf", Path("test2.pdf")),
        ]
        result = component.bulk_ingest(files)
        
        # Verify parallel processing
        assert len(result) == 2
        component._ingest_work_pool.starmap.assert_called_once()


class TestFeatureParity:
    """Test feature parity between SimpleIngestComponent and ParallelizedIngestComponent."""

    @pytest.mark.parametrize("component_class", [SimpleIngestComponent, ParallelizedIngestComponent])
    def test_both_components_support_extraction(
        self,
        component_class,
        mock_storage_context,
        mock_embed_model,
        mock_transformations,
        mock_extraction_component,
        mock_services,
    ):
        """Test both components support extraction."""
        ingest_service, chat_service = mock_services
        
        kwargs = {
            "storage_context": mock_storage_context,
            "embed_model": mock_embed_model,
            "transformations": mock_transformations,
            "extraction_component": mock_extraction_component,
            "ingest_service": ingest_service,
            "chat_service": chat_service,
        }
        
        if component_class == ParallelizedIngestComponent:
            kwargs["count_workers"] = 2
        
        component = component_class(**kwargs)
        
        # Verify extraction component is set
        assert component.extraction_component == mock_extraction_component
        assert hasattr(component, '_rag_thread_lock')

    @pytest.mark.parametrize("component_class", [SimpleIngestComponent, ParallelizedIngestComponent])
    def test_both_components_return_stub_documents(
        self,
        component_class,
        mock_storage_context,
        mock_embed_model,
        mock_transformations,
        mock_extraction_component,
        mock_services,
    ):
        """Test both components return stub documents for compatibility."""
        ingest_service, chat_service = mock_services
        
        kwargs = {
            "storage_context": mock_storage_context,
            "embed_model": mock_embed_model,
            "transformations": mock_transformations,
            "extraction_component": mock_extraction_component,
            "ingest_service": ingest_service,
            "chat_service": chat_service,
        }
        
        if component_class == ParallelizedIngestComponent:
            kwargs["count_workers"] = 2
        
        component = component_class(**kwargs)
        component._index = Mock()
        
        with patch('bridgewell_gpt.components.ingest.ingest_helper.IngestionHelper.store_original_file'):
            with patch('bridgewell_gpt.server.document_types.document_type_service.DocumentTypeService'):
                with patch('threading.Thread'):
                    result = component.ingest("test.pdf", Path("test.pdf"))
        
        # Both should return stub documents
        assert len(result) == 1
        assert result[0].metadata.get("file_name") == "test.pdf"
        assert "doc_id" in result[0].metadata