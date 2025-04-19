import logging
from typing import Dict, Any, Optional, Callable, List
import json

from injector import inject, singleton
from fastapi import HTTPException

from llama_index.core.llms import ChatMessage, MessageRole
from bridgewell_gpt.open_ai.extensions.context_filter import ContextFilter

from bridgewell_gpt.server.chat.chat_service import ChatService
from bridgewell_gpt.server.ingest.ingest_service import IngestService

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


   