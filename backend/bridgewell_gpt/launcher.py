"""FastAPI app creation, logger configuration and main API routes."""

import logging
import os

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from injector import Injector
from llama_index.core.callbacks import CallbackManager
from llama_index.core.callbacks.global_handlers import create_global_handler
from llama_index.core.settings import Settings as LlamaIndexSettings

from bridgewell_gpt.server.chat.chat_router import chat_router
from bridgewell_gpt.server.chunks.chunks_router import chunks_router
from bridgewell_gpt.server.completions.completions_router import completions_router
from bridgewell_gpt.server.embeddings.embeddings_router import embeddings_router

from bridgewell_gpt.server.health.health_router import health_router
from bridgewell_gpt.server.ingest.ingest_router import ingest_router
from bridgewell_gpt.server.recipes.summarize.summarize_router import summarize_router
from bridgewell_gpt.server.extraction.extraction_router import extraction_router
from bridgewell_gpt.server.document_types.document_type_router import document_type_router
from bridgewell_gpt.settings.settings import Settings
from bridgewell_gpt.server.utils.cors_staticfiles import CORSAwareStaticFiles

logger = logging.getLogger(__name__)


def create_app(root_injector: Injector) -> FastAPI:

    # Start the API
    async def bind_injector_to_request(request: Request) -> None:
        request.state.injector = root_injector

    app = FastAPI(dependencies=[Depends(bind_injector_to_request)])

    app.include_router(completions_router)
    app.include_router(chat_router)
    app.include_router(chunks_router)
    app.include_router(ingest_router)
    app.include_router(summarize_router)
    app.include_router(embeddings_router)
    app.include_router(health_router)
    app.include_router(extraction_router)
    app.include_router(document_type_router)

    # Expose original_files as static files
    original_files_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../local_data/bridgewell_gpt/original_files"
        )
    )
    os.makedirs(original_files_path, exist_ok=True)
    app.mount(
        "/original_files",
        CORSAwareStaticFiles(directory=original_files_path),
        name="original_files"
    )

    # Add LlamaIndex simple observability
    global_handler = create_global_handler("simple")
    if global_handler:
        LlamaIndexSettings.callback_manager = CallbackManager([global_handler])

    settings = root_injector.get(Settings)
    if settings.server.cors.enabled:
        logger.debug("Setting up CORS middleware")
        app.add_middleware(
            CORSMiddleware,
            allow_credentials=settings.server.cors.allow_credentials,
            allow_origins=settings.server.cors.allow_origins,
            allow_origin_regex=settings.server.cors.allow_origin_regex,
            allow_methods=settings.server.cors.allow_methods,
            allow_headers=settings.server.cors.allow_headers,
        )

    if settings.ui.enabled:
        logger.debug("Importing the UI module")
        try:
            from bridgewell_gpt.ui.production_ui import ProductionUI
        except ImportError as e:
            raise ImportError(
                "UI dependencies not found, install with `poetry install --extras ui`"
            ) from e

        ui = root_injector.get(ProductionUI)
        ui.mount_in_app(app, settings.ui.path)

    return app
