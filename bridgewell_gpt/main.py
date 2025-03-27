"""FastAPI app creation, logger configuration and main API routes."""

from bridgewell_gpt.di import global_injector
from bridgewell_gpt.launcher import create_app

app = create_app(global_injector)
