"""
URL ingestion module for downloading and processing PDF documents from URLs.
"""

import os
import logging
import tempfile
from typing import Dict, Any, List, Optional, Tuple, BinaryIO
from datetime import datetime
import uuid
import httpx
from pydantic import AnyHttpUrl

from app.config import settings
from app.rag.pdf_processor import PDFProcessor
from app.rag.ingestion import PDFIngestionService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class URLIngestionService:
    """Service for ingesting PDFs from URLs."""

    def __init__(
        self,
        pdf_ingestion_service: PDFIngestionService,
    ):
        """Initialize the URL ingestion service.

        Args:
            pdf_ingestion_service: PDFIngestionService for processing PDFs
        """
        self.pdf_ingestion_service = pdf_ingestion_service

    async def download_pdf(
        self, url: AnyHttpUrl, timeout: int = 30
    ) -> Tuple[bool, str, Optional[bytes]]:
        """Download a PDF from a URL.

        Args:
            url: URL to download from
            timeout: Timeout in seconds for the HTTP request

        Returns:
            Tuple of (success, message, content)
        """
        try:
            logger.info(f"Downloading PDF from URL: {url}")

            # Download the PDF
            # Disable SSL verification to handle sites with certificate issues
            # Add timeout to prevent hanging on large files
            async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
                logger.info(f"Starting download with timeout of {timeout} seconds")
                response = await client.get(str(url), follow_redirects=True)
                logger.info(
                    f"Download completed, received {len(response.content)} bytes"
                )

                # Check if the request was successful
                if response.status_code != 200:
                    logger.error(f"Error downloading PDF: HTTP {response.status_code}")
                    return (
                        False,
                        f"Error downloading PDF: HTTP {response.status_code}",
                        None,
                    )

                # Check if the content type is PDF
                content_type = response.headers.get("content-type", "")
                if "application/pdf" not in content_type and not str(
                    url
                ).lower().endswith(".pdf"):
                    logger.warning(f"URL may not be a PDF: {content_type}")
                    # Continue anyway, as sometimes content types are not set correctly

                # Get the content
                content = response.content

                # Check if the content is a PDF (starts with %PDF)
                if not content.startswith(b"%PDF"):
                    logger.error("Downloaded content is not a PDF")
                    return False, "Downloaded content is not a PDF", None

                logger.info(f"Successfully downloaded PDF from URL: {url}")
                return True, f"Successfully downloaded PDF from URL: {url}", content
        except Exception as e:
            logger.exception(f"Error downloading PDF from URL: {url}")
            return False, f"Error downloading PDF from URL: {str(e)}", None

    async def ingest_url(
        self,
        url: AnyHttpUrl,
        document_id: Optional[str] = None,
        version: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,  # Timeout for download in seconds
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Ingest a PDF from a URL and store it in the vector database.

        Args:
            url: URL to ingest
            document_id: Optional document ID for versioning
            version: Optional version string
            additional_metadata: Optional additional metadata
            timeout: Timeout in seconds for the HTTP request

        Returns:
            Tuple of (success, message, metadata)
        """
        try:
            # Ensure collection exists before downloading
            await self.pdf_ingestion_service.ensure_collection_exists()

            # Download the PDF with timeout (use provided timeout or fall back to setting)
            from app.config import settings

            actual_timeout = timeout or settings.vector_store.download_timeout
            success, message, content = await self.download_pdf(
                url, timeout=actual_timeout
            )

            if not success or content is None:
                return False, message, {}

            # Create a temporary file to store the downloaded PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                # Write the downloaded content to the temporary file
                temp_file.write(content)
                temp_file.flush()

                # Extract filename from URL
                filename = os.path.basename(str(url))
                if not filename.lower().endswith(".pdf"):
                    filename += ".pdf"

                # Prepare additional metadata
                url_metadata = additional_metadata or {}
                url_metadata["source_url"] = str(url)
                url_metadata["download_date"] = datetime.now().isoformat()

                # Reopen the file for reading
                with open(temp_file.name, "rb") as pdf_file:
                    # Ingest the PDF
                    success, message, metadata = (
                        await self.pdf_ingestion_service.ingest_pdf(
                            pdf_file, filename, document_id, version, url_metadata
                        )
                    )

            # Clean up the temporary file
            os.unlink(temp_file.name)

            return success, message, metadata
        except Exception as e:
            logger.exception(f"Error ingesting URL: {url}")
            return False, f"Error ingesting URL: {str(e)}", {}

    async def ingest_urls(
        self,
        urls: List[AnyHttpUrl],
        document_id: Optional[str] = None,
        version: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,  # Timeout for download in seconds
    ) -> Dict[str, Any]:
        """Ingest multiple PDFs from URLs and store them in the vector database.

        Args:
            urls: List of URLs to ingest
            document_id: Optional document ID for versioning
            version: Optional version string
            additional_metadata: Optional additional metadata
            timeout: Timeout in seconds for the HTTP request

        Returns:
            Dictionary with ingestion results
        """
        # Ensure collection exists before processing URLs
        await self.pdf_ingestion_service.ensure_collection_exists()

        # Process each URL
        results = []
        failed_urls = []
        metadata_list = []

        for url in urls:
            logger.info(f"Processing URL: {url}")
            # Use provided timeout or fall back to setting
            from app.config import settings

            actual_timeout = timeout or settings.vector_store.download_timeout
            success, message, metadata = await self.ingest_url(
                url, document_id, version, additional_metadata, timeout=actual_timeout
            )

            results.append({"url": str(url), "success": success, "message": message})
            metadata_list.append(metadata)

            if not success:
                failed_urls.append(str(url))

        # Return summary
        return {
            "status": "completed",
            "message": f"Processed {len(urls)} URLs, {len(failed_urls)} failed",
            "urls_processed": len(urls),
            "urls_failed": len(failed_urls),
            "failed_urls": failed_urls,
            "results": results,
            "metadata": metadata_list,
        }
