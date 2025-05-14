"""
API models for request and response validation.
"""

from typing import Dict, Any, List, Optional, Annotated
from datetime import datetime
from pydantic import BaseModel, Field, AnyHttpUrl


class UploadResponse(BaseModel):
    """Response model for document upload."""

    success: bool
    message: str
    document_id: Optional[str] = None
    version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class QueryRequest(BaseModel):
    """Request model for querying the RAG system."""

    query: str = Field(..., description="The query to answer")
    filters: Optional[Dict[str, Any]] = Field(
        None, description="Optional metadata filters"
    )
    limit: Optional[int] = Field(None, description="Maximum number of results to use")


class QueryResponse(BaseModel):
    """Response model for RAG queries."""

    response: str
    sources: List[Dict[str, Any]] = []
    error: Optional[str] = None


class DocumentVersion(BaseModel):
    """Model for document version information."""

    version: str
    filename: str
    title: Optional[str] = None
    ingestion_date: Optional[str] = None
    page_count: Optional[int] = None


class DocumentVersionsResponse(BaseModel):
    """Response model for document versions."""

    document_id: str
    versions: List[DocumentVersion] = []
    count: int
    error: Optional[str] = None


class ComparisonRequest(BaseModel):
    """Request model for document version comparison."""

    document_id: str = Field(..., description="Document ID")
    version1: str = Field(..., description="First version")
    version2: str = Field(..., description="Second version")


class ComparisonResponse(BaseModel):
    """Response model for document version comparison."""

    document_id: str
    version1: str
    version2: str
    comparison: Optional[str] = None
    metadata_changes: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SummaryResponse(BaseModel):
    """Response model for document version summary."""

    document_id: str
    version1: str
    version2: str
    summary: Optional[str] = None
    metadata_changes: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ChangeQueryRequest(BaseModel):
    """Request model for querying about changes."""

    document_id: str = Field(..., description="Document ID")
    version1: str = Field(..., description="First version")
    version2: str = Field(..., description="Second version")
    query: str = Field(..., description="Question about the changes")


class ChangeQueryResponse(BaseModel):
    """Response model for change queries."""

    document_id: str
    version1: str
    version2: str
    query: str
    response: str
    error: Optional[str] = None


class URLIngestionRequest(BaseModel):
    """Request model for URL ingestion."""

    url: AnyHttpUrl = Field(..., description="URL of the PDF to ingest")
    document_id: Optional[str] = Field(
        None, description="Optional document ID for versioning"
    )
    version: Optional[str] = Field(None, description="Optional version string")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Optional additional metadata"
    )


class URLsIngestionRequest(BaseModel):
    """Request model for multiple URL ingestion."""

    urls: List[AnyHttpUrl] = Field(..., description="List of URLs to ingest")
    document_id: Optional[str] = Field(
        None, description="Optional document ID for versioning"
    )
    version: Optional[str] = Field(None, description="Optional version string")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Optional additional metadata"
    )


class URLIngestionResponse(BaseModel):
    """Response model for URL ingestion."""

    success: bool
    message: str
    document_id: Optional[str] = None
    version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    url: AnyHttpUrl


class URLsIngestionResponse(BaseModel):
    """Response model for multiple URL ingestion."""

    status: str
    message: str
    urls_processed: int
    urls_failed: int
    failed_urls: List[str] = []
    results: List[Dict[str, Any]] = []
    metadata: List[Dict[str, Any]] = []
