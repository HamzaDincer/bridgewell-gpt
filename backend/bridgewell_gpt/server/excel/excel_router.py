from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import logging
import json
from pydantic import BaseModel

from bridgewell_gpt.server.excel.excel_service import ExcelService
from bridgewell_gpt.server.ingest.ingest_service import IngestService
from bridgewell_gpt.server.chat.chat_service import ChatService
from bridgewell_gpt.open_ai.extensions.context_filter import ContextFilter
from llama_index.core.llms import ChatMessage, MessageRole
from bridgewell_gpt.server.utils.auth import authenticated

logger = logging.getLogger(__name__)

excel_router = APIRouter(prefix="/v1", dependencies=[Depends(authenticated)])
