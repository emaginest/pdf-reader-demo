"""
Version comparison module for comparing different versions of PDF documents.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from agents_hub.vector_stores import PGVector
from agents_hub import Agent

from app.config import settings
from app.rag.retrieval import RAGService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VersionComparisonService:
    """Service for comparing different versions of documents."""

    def __init__(
        self, 
        pgvector_tool: PGVector, 
        rag_agent: Agent,
        rag_service: Optional[RAGService] = None
    ):
        """Initialize the version comparison service.

        Args:
            pgvector_tool: PGVector tool for searching documents
            rag_agent: Agent for generating responses
            rag_service: RAGService for retrieving documents (optional)
        """
        self.pgvector_tool = pgvector_tool
        self.rag_agent = rag_agent
        self.rag_service = rag_service or RAGService(pgvector_tool, rag_agent)
        self.collection_name = settings.vector_store.collection_name

    async def _get_version_content(
        self, document_id: str, version: str
    ) -> Dict[str, Any]:
        """Get the content of a specific document version.

        Args:
            document_id: Document ID
            version: Version string

        Returns:
            Dictionary with document content
        """
        try:
            # Search for documents with the given document_id and version
            search_params = {
                "operation": "search",
                "collection_name": self.collection_name,
                "filter": {
                    "document_id": document_id,
                    "version": version
                },
                "limit": 100,  # Set a high limit to get all chunks
            }
            
            logger.info(f"Fetching content for document: {document_id}, version: {version}")
            search_result = await self.pgvector_tool.run(search_params)

            if "error" in search_result:
                logger.error(f"Error fetching content: {search_result['error']}")
                return {"error": search_result["error"], "content": ""}

            # Extract results
            results = search_result.get("results", [])
            
            if not results:
                logger.warning(f"No content found for document: {document_id}, version: {version}")
                return {"document_id": document_id, "version": version, "content": ""}

            # Sort chunks by index
            results.sort(key=lambda x: x.get("metadata", {}).get("chunk_index", 0))
            
            # Combine chunks into full content
            content = "\n\n".join([result["document"] for result in results])
            
            # Get metadata from first chunk
            metadata = results[0].get("metadata", {})
            
            return {
                "document_id": document_id,
                "version": version,
                "content": content,
                "metadata": metadata,
                "chunks": len(results)
            }
        except Exception as e:
            logger.exception(f"Error getting version content: {document_id}, {version}")
            return {"error": str(e), "content": ""}

    async def compare_versions(
        self, document_id: str, version1: str, version2: str
    ) -> Dict[str, Any]:
        """Compare two versions of a document.

        Args:
            document_id: Document ID
            version1: First version
            version2: Second version

        Returns:
            Dictionary with comparison results
        """
        try:
            # Get content of both versions
            v1_result = await self._get_version_content(document_id, version1)
            v2_result = await self._get_version_content(document_id, version2)
            
            if "error" in v1_result or "error" in v2_result:
                error = v1_result.get("error") or v2_result.get("error")
                logger.error(f"Error retrieving content: {error}")
                return {"error": error}
            
            # Generate comparison using the agent
            prompt = f"""
            I need you to compare two versions of a document and identify the key differences.
            
            Document ID: {document_id}
            
            Version 1 ({version1}):
            {v1_result["content"][:5000]}  # Limit content to avoid token limits
            
            Version 2 ({version2}):
            {v2_result["content"][:5000]}  # Limit content to avoid token limits
            
            Please analyze these two versions and provide:
            1. A summary of the main differences
            2. What content was added in version 2
            3. What content was removed in version 2
            4. Any changes in structure or organization
            
            Format your response as a structured analysis.
            """
            
            logger.info(f"Generating comparison for document: {document_id}, versions: {version1} vs {version2}")
            comparison = await self.rag_agent.run(prompt)
            
            # Get metadata for both versions
            v1_metadata = v1_result.get("metadata", {})
            v2_metadata = v2_result.get("metadata", {})
            
            # Compare metadata
            metadata_changes = {}
            for key in ["title", "author", "subject", "creator", "producer", "page_count"]:
                if v1_metadata.get(key) != v2_metadata.get(key):
                    metadata_changes[key] = {
                        "from": v1_metadata.get(key),
                        "to": v2_metadata.get(key),
                    }
            
            return {
                "document_id": document_id,
                "version1": version1,
                "version2": version2,
                "comparison": comparison,
                "metadata_changes": metadata_changes,
            }
        except Exception as e:
            logger.exception(f"Error comparing versions: {document_id}, {version1} vs {version2}")
            return {"error": str(e)}

    async def summarize_changes(
        self, document_id: str, version1: str, version2: str
    ) -> Dict[str, Any]:
        """Summarize changes between two versions of a document.

        Args:
            document_id: Document ID
            version1: First version
            version2: Second version

        Returns:
            Dictionary with summary of changes
        """
        try:
            # Get comparison
            comparison_result = await self.compare_versions(document_id, version1, version2)
            
            if "error" in comparison_result:
                return comparison_result
            
            # Generate concise summary using the agent
            prompt = f"""
            Based on the following comparison between two document versions, provide a concise summary of the changes.
            
            {comparison_result["comparison"]}
            
            Please provide a brief, executive summary of the key changes (no more than 3-5 bullet points).
            """
            
            logger.info(f"Generating summary for document: {document_id}, versions: {version1} vs {version2}")
            summary = await self.rag_agent.run(prompt)
            
            return {
                "document_id": document_id,
                "version1": version1,
                "version2": version2,
                "summary": summary,
                "metadata_changes": comparison_result.get("metadata_changes", {}),
            }
        except Exception as e:
            logger.exception(f"Error summarizing changes: {document_id}, {version1} vs {version2}")
            return {"error": str(e)}

    async def answer_about_changes(
        self, query: str, document_id: str, version1: str, version2: str
    ) -> Dict[str, Any]:
        """Answer questions about changes between document versions.

        Args:
            query: Question about the changes
            document_id: Document ID
            version1: First version
            version2: Second version

        Returns:
            Dictionary with answer
        """
        try:
            # Get comparison
            comparison_result = await self.compare_versions(document_id, version1, version2)
            
            if "error" in comparison_result:
                return {
                    "response": "I'm sorry, I couldn't retrieve the document versions to answer your question.",
                    "error": comparison_result["error"]
                }
            
            # Generate answer using the agent
            prompt = f"""
            Question: {query}
            
            Please answer the question based on the following comparison between two document versions:
            
            {comparison_result["comparison"]}
            
            Metadata changes: {comparison_result.get("metadata_changes", {})}
            
            Answer:
            """
            
            logger.info(f"Answering question about changes: {query}")
            answer = await self.rag_agent.run(prompt)
            
            return {
                "document_id": document_id,
                "version1": version1,
                "version2": version2,
                "query": query,
                "response": answer,
            }
        except Exception as e:
            logger.exception(f"Error answering about changes: {query}")
            return {
                "response": "I'm sorry, I encountered an error while trying to answer your question.",
                "error": str(e)
            }
