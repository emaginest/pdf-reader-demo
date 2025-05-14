"""
API endpoints for the PDF RAG system.
"""

import os
import logging
import tempfile
import asyncio
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    BackgroundTasks,
    status,
)

# Import agents-hub components
from agents_hub.vector_stores import PGVector
from agents_hub import Agent
from agents_hub.llm.providers import OpenAIProvider

from app.config import settings
from app.rag import (
    PDFProcessor,
    PDFIngestionService,
    RAGService,
    VersionComparisonService,
    URLIngestionService,
)
from app.api.models import (
    UploadResponse,
    QueryRequest,
    QueryResponse,
    DocumentVersionsResponse,
    ComparisonRequest,
    ComparisonResponse,
    SummaryResponse,
    ChangeQueryRequest,
    ChangeQueryResponse,
    URLIngestionRequest,
    URLsIngestionRequest,
    URLIngestionResponse,
    URLsIngestionResponse,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1")


# Dependencies
async def get_llm():
    """Get LLM instance."""
    # Create OpenAIProvider with just the API key
    llm = OpenAIProvider(
        api_key=settings.llm.api_key,
    )
    return llm


async def get_rag_agent(llm=Depends(get_llm)) -> Agent:
    """Get RAG agent."""
    agent = Agent(
        name="rag_agent",
        llm=llm,
        system_prompt="You are a helpful assistant that answers questions based on document content.",
    )
    return agent


async def get_pgvector(llm=Depends(get_llm)) -> PGVector:
    """Get PGVector instance."""
    # Parse the DSN to get individual connection parameters
    import re

    dsn = str(settings.database.dsn)
    match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", dsn)
    if match:
        user, password, host, port, database = match.groups()
        pgvector = PGVector(
            llm=llm,
            host=host,
            port=int(port),
            database=database,
            user=user,
            password=password,
            schema="vector_store",
        )
        return pgvector
    else:
        raise ValueError(f"Invalid DSN format: {dsn}")


async def get_pdf_processor() -> PDFProcessor:
    """Get PDF processor."""
    return PDFProcessor(
        chunk_size=settings.vector_store.chunk_size,
        chunk_overlap=settings.vector_store.chunk_overlap,
        chunk_method=settings.vector_store.chunk_method,
    )


async def get_ingestion_service(
    pgvector: PGVector = Depends(get_pgvector),
    pdf_processor: PDFProcessor = Depends(get_pdf_processor),
) -> PDFIngestionService:
    """Get PDF ingestion service."""
    return PDFIngestionService(pgvector, pdf_processor)


async def get_rag_service(
    pgvector: PGVector = Depends(get_pgvector),
    rag_agent: Agent = Depends(get_rag_agent),
) -> RAGService:
    """Get RAG service."""
    return RAGService(pgvector, rag_agent)


async def get_comparison_service(
    pgvector: PGVector = Depends(get_pgvector),
    rag_agent: Agent = Depends(get_rag_agent),
    rag_service: RAGService = Depends(get_rag_service),
) -> VersionComparisonService:
    """Get version comparison service."""
    return VersionComparisonService(pgvector, rag_agent, rag_service)


async def get_url_ingestion_service(
    ingestion_service: PDFIngestionService = Depends(get_ingestion_service),
) -> URLIngestionService:
    """Get URL ingestion service."""
    return URLIngestionService(ingestion_service)


# Endpoints
async def process_pdf_in_background(
    temp_file_path: str,
    filename: str,
    document_id: Optional[str],
    version: Optional[str],
    ingestion_service: PDFIngestionService,
):
    """Process a PDF file in the background."""
    try:
        # Reopen the file for reading
        with open(temp_file_path, "rb") as pdf_file:
            # Ingest the PDF
            await ingestion_service.ingest_pdf(pdf_file, filename, document_id, version)
    except Exception as e:
        logger.exception(f"Error processing PDF in background: {e}")
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_file_path)
        except Exception as e:
            logger.error(f"Error removing temporary file: {e}")


@router.post(
    "/documents/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_id: Optional[str] = Form(None),
    version: Optional[str] = Form(None),
    ingestion_service: PDFIngestionService = Depends(get_ingestion_service),
):
    """Upload a PDF document.

    For large PDFs, this endpoint will accept the file and process it in the background.
    The response will be returned immediately with a status of 202 Accepted.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    try:
        # Check file size limit
        if file.size and file.size > settings.api.max_upload_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {settings.api.max_upload_size / (1024 * 1024)} MB",
            )

        # Create a temporary file to store the uploaded PDF
        temp_file_path = os.path.join(
            settings.upload_dir, f"temp_{os.urandom(8).hex()}.pdf"
        )

        # Stream the file to disk in chunks to avoid memory issues
        with open(temp_file_path, "wb") as temp_file:
            # Read and write the file in chunks
            chunk_size = settings.api.chunk_size
            while chunk := await file.read(chunk_size):
                temp_file.write(chunk)

        # Schedule the PDF processing as a background task
        background_tasks.add_task(
            process_pdf_in_background,
            temp_file_path,
            file.filename,
            document_id,
            version,
            ingestion_service,
        )

        # Return an immediate response
        return UploadResponse(
            success=True,
            message=f"File {file.filename} accepted for processing. Processing will continue in the background.",
            document_id=document_id,
            version=version,
            metadata={
                "filename": file.filename,
                "document_id": document_id,
                "version": version,
                "status": "processing",
                "upload_time": datetime.now().isoformat(),
            },
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/query", response_model=QueryResponse)
async def query_rag(
    request: QueryRequest,
    rag_service: RAGService = Depends(get_rag_service),
):
    """Query the RAG system."""
    try:
        result = await rag_service.generate_response(
            request.query,
            request.limit,
            request.filters,
        )

        return QueryResponse(
            response=result.get("response", ""),
            sources=result.get("sources", []),
            error=result.get("error"),
        )
    except Exception as e:
        logger.exception(f"Error querying RAG: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/documents/{document_id}/versions", response_model=DocumentVersionsResponse
)
async def get_document_versions(
    document_id: str,
    rag_service: RAGService = Depends(get_rag_service),
):
    """Get all versions of a document."""
    try:
        result = await rag_service.get_document_versions(document_id)

        if "error" in result:
            return DocumentVersionsResponse(
                document_id=document_id,
                versions=[],
                count=0,
                error=result["error"],
            )

        return DocumentVersionsResponse(
            document_id=result["document_id"],
            versions=result["versions"],
            count=result["count"],
        )
    except Exception as e:
        logger.exception(f"Error getting document versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/compare", response_model=ComparisonResponse)
async def compare_document_versions(
    request: ComparisonRequest,
    comparison_service: VersionComparisonService = Depends(get_comparison_service),
):
    """Compare two versions of a document."""
    try:
        result = await comparison_service.compare_versions(
            request.document_id,
            request.version1,
            request.version2,
        )

        if "error" in result:
            return ComparisonResponse(
                document_id=request.document_id,
                version1=request.version1,
                version2=request.version2,
                error=result["error"],
            )

        return ComparisonResponse(
            document_id=result["document_id"],
            version1=result["version1"],
            version2=result["version2"],
            comparison=result["comparison"],
            metadata_changes=result["metadata_changes"],
        )
    except Exception as e:
        logger.exception(f"Error comparing document versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/summarize-changes", response_model=SummaryResponse)
async def summarize_document_changes(
    request: ComparisonRequest,
    comparison_service: VersionComparisonService = Depends(get_comparison_service),
):
    """Summarize changes between two versions of a document."""
    try:
        result = await comparison_service.summarize_changes(
            request.document_id,
            request.version1,
            request.version2,
        )

        if "error" in result:
            return SummaryResponse(
                document_id=request.document_id,
                version1=request.version1,
                version2=request.version2,
                error=result["error"],
            )

        return SummaryResponse(
            document_id=result["document_id"],
            version1=result["version1"],
            version2=result["version2"],
            summary=result["summary"],
            metadata_changes=result["metadata_changes"],
        )
    except Exception as e:
        logger.exception(f"Error summarizing document changes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/query-changes", response_model=ChangeQueryResponse)
async def query_document_changes(
    request: ChangeQueryRequest,
    comparison_service: VersionComparisonService = Depends(get_comparison_service),
):
    """Answer questions about changes between document versions."""
    try:
        result = await comparison_service.answer_about_changes(
            request.query,
            request.document_id,
            request.version1,
            request.version2,
        )

        if "error" in result:
            return ChangeQueryResponse(
                document_id=request.document_id,
                version1=request.version1,
                version2=request.version2,
                query=request.query,
                response="I'm sorry, I couldn't answer your question.",
                error=result["error"],
            )

        return ChangeQueryResponse(
            document_id=result["document_id"],
            version1=result["version1"],
            version2=result["version2"],
            query=result["query"],
            response=result["response"],
        )
    except Exception as e:
        logger.exception(f"Error querying document changes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/ingest-url", response_model=URLIngestionResponse)
async def ingest_url(
    request: URLIngestionRequest,
    url_ingestion_service: URLIngestionService = Depends(get_url_ingestion_service),
):
    """Ingest a PDF from a URL."""
    try:
        success, message, metadata = await url_ingestion_service.ingest_url(
            request.url,
            request.document_id,
            request.version,
            request.metadata,
        )

        return URLIngestionResponse(
            success=success,
            message=message,
            document_id=metadata.get("document_id"),
            version=metadata.get("version"),
            metadata=metadata,
            url=request.url,
        )
    except Exception as e:
        logger.exception(f"Error ingesting URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/ingest-urls", response_model=URLsIngestionResponse)
async def ingest_urls(
    request: URLsIngestionRequest,
    url_ingestion_service: URLIngestionService = Depends(get_url_ingestion_service),
):
    """Ingest multiple PDFs from URLs."""
    try:
        result = await url_ingestion_service.ingest_urls(
            request.urls,
            request.document_id,
            request.version,
            request.metadata,
        )

        return URLsIngestionResponse(
            status=result["status"],
            message=result["message"],
            urls_processed=result["urls_processed"],
            urls_failed=result["urls_failed"],
            failed_urls=result["failed_urls"],
            results=result["results"],
            metadata=result["metadata"],
        )
    except Exception as e:
        logger.exception(f"Error ingesting URLs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
