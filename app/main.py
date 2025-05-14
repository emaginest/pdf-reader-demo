"""
Main application module.
"""

import os
import logging
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.config import settings
from app.api import router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.api.title,
    description=settings.api.description,
    version=settings.api.version,
    docs_url=settings.api.docs_url,
    redoc_url=settings.api.redoc_url,
    openapi_url=settings.api.openapi_url,
    root_path=settings.api.root_path,
)


# Create a custom JSONResponse class to handle Unicode characters properly
class UnicodeJSONResponse(JSONResponse):
    """Custom JSON response that handles Unicode characters properly."""

    def render(self, content):
        """Render the content with proper encoding."""
        # First convert to JSON-compatible Python objects
        json_compatible_content = jsonable_encoder(content)

        # Then serialize to JSON with proper encoding
        return json.dumps(
            json_compatible_content,
            ensure_ascii=False,  # This is key for proper Unicode handling
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set default response class
app.default_response_class = UnicodeJSONResponse

# Include API router
app.include_router(router)

# Create upload directory if it doesn't exist
os.makedirs(settings.upload_dir, exist_ok=True)


# Add exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.exception(f"Unhandled exception: {exc}")
    return UnicodeJSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


# Add health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


# Add root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.api.title,
        "version": settings.api.version,
        "docs_url": settings.api.docs_url,
    }


# Run the application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        timeout_keep_alive=settings.api.request_timeout,
        timeout_graceful_shutdown=30,
        limit_concurrency=20,  # Limit concurrent connections
        limit_max_requests=1000,  # Limit max requests per worker
    )
