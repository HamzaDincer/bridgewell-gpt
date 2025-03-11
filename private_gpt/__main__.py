# start a fastapi server with uvicorn

import os
import sys
import uvicorn

from private_gpt.settings.settings import settings

# Check if running in development mode (set by environment variable)
dev_mode = os.environ.get("PGPT_DEV_MODE", "").lower() in ("true", "1", "yes")

if dev_mode:
    # In development mode, use an import string for the app to enable hot reload
    uvicorn.run(
        "private_gpt.main:app",  # Import string instead of direct reference
        host="0.0.0.0", 
        port=settings().server.port, 
        log_config=None,
        reload=True,
        reload_dirs=["private_gpt"]  # Watch the private_gpt directory for changes
    )
else:
    # In production mode, import the app directly (no hot reload)
    from private_gpt.main import app
    
    # Set log_config=None to do not use the uvicorn logging configuration, and
    # use ours instead. For reference, see below:
    # https://github.com/tiangolo/fastapi/discussions/7457#discussioncomment-5141108
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=settings().server.port, 
        log_config=None
    )
