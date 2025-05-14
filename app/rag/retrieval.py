"""
Vector search and retrieval module.
"""

import logging
from typing import Dict, Any, List, Optional

from agents_hub.vector_stores import PGVector
from agents_hub import Agent

from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RAGService:
    """Service for retrieving information using RAG."""

    def __init__(self, pgvector_tool: PGVector, rag_agent: Agent):
        """Initialize the RAG service.

        Args:
            pgvector_tool: PGVector tool for searching documents
            rag_agent: Agent for generating responses
        """
        self.pgvector_tool = pgvector_tool
        self.rag_agent = rag_agent
        self.collection_name = settings.vector_store.collection_name
        self.search_limit = settings.vector_store.search_limit

    async def search(
        self,
        query: str,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Search for documents related to the query.

        Args:
            query: Query to search for
            limit: Maximum number of results to return
            filters: Optional metadata filters

        Returns:
            Dictionary with search results
        """
        try:
            # Prepare search parameters
            search_params = {
                "operation": "search",
                "query": query,
                "collection_name": self.collection_name,
                "limit": limit or self.search_limit,
            }

            # Add filters if provided
            if filters:
                search_params["filter"] = filters

            # Search for relevant documents
            logger.info(f"Searching for: {query}")
            search_result = await self.pgvector_tool.run(search_params)

            if "error" in search_result:
                logger.error(f"Error searching: {search_result['error']}")
                return {"error": search_result["error"], "results": []}

            # Extract search results
            results = search_result.get("results", [])
            logger.info(f"Found {len(results)} results for query: {query}")

            return {"query": query, "results": results, "count": len(results)}
        except Exception as e:
            logger.exception(f"Error searching: {query}")
            return {"error": str(e), "results": []}

    async def generate_response(
        self,
        query: str,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a response to the query using RAG.

        Args:
            query: Query to answer
            limit: Maximum number of results to use
            filters: Optional metadata filters

        Returns:
            Dictionary with the response and sources
        """
        try:
            # Search for relevant documents
            search_result = await self.search(query, limit, filters)

            # Detect language of the query (simple heuristic)
            is_spanish = any(
                word in query.lower()
                for word in [
                    "qué",
                    "cómo",
                    "cuál",
                    "quién",
                    "dónde",
                    "cuándo",
                    "por qué",
                    "cuánto",
                ]
            )

            if "error" in search_result:
                logger.error(f"Error searching: {search_result['error']}")
                if is_spanish:
                    error_message = "Lo siento, no pude encontrar información relevante para responder a tu pregunta."
                else:
                    error_message = "I'm sorry, I couldn't find any relevant information to answer your question."
                return {
                    "response": error_message,
                    "sources": [],
                }

            results = search_result.get("results", [])
            if not results:
                logger.warning(f"No relevant documents found for query: {query}")
                if is_spanish:
                    error_message = "No tengo suficiente información para responder a esta pregunta."
                else:
                    error_message = (
                        "I don't have enough information to answer this question."
                    )
                return {
                    "response": error_message,
                    "sources": [],
                }

            # Prepare context from search results
            context = "\n\n".join(
                [
                    f"Document {i+1}:\n{result['document']}"
                    for i, result in enumerate(results)
                ]
            )

            # Detect language of the query (simple heuristic)
            is_spanish = any(
                word in query.lower()
                for word in [
                    "qué",
                    "cómo",
                    "cuál",
                    "quién",
                    "dónde",
                    "cuándo",
                    "por qué",
                    "cuánto",
                ]
            )

            # Generate answer using the agent with language-aware prompt
            prompt = f"""
            Question: {query}

            Please answer the question based on the following information:

            {context}

            Important instructions:
            1. Answer the question using ONLY the information provided above.
            2. If the question is in Spanish, respond in Spanish. If the question is in English, respond in English.
            3. Match the language of your response to the language of the question.
            4. Be concise and direct in your answer.
            5. If the information to answer the question is not in the provided context, say so.

            Answer:
            """

            logger.info(
                f"Generating response for query: {query} (Detected language: {'Spanish' if is_spanish else 'English'})"
            )
            response = await self.rag_agent.run(prompt)

            # Extract sources for citation
            sources = []
            for result in results:
                metadata = result.get("metadata", {})
                source = {
                    "title": metadata.get("title", "Unknown"),
                    "document_id": metadata.get("document_id", "Unknown"),
                    "version": metadata.get("version", "Unknown"),
                    "filename": metadata.get("filename", "Unknown"),
                    "chunk_index": metadata.get("chunk_index", 0),
                    "similarity_score": result.get("similarity", 0),
                }
                sources.append(source)

            return {"response": response, "sources": sources}
        except Exception as e:
            logger.exception(f"Error generating response: {query}")
            # Detect language of the query (simple heuristic)
            is_spanish = any(
                word in query.lower()
                for word in [
                    "qué",
                    "cómo",
                    "cuál",
                    "quién",
                    "dónde",
                    "cuándo",
                    "por qué",
                    "cuánto",
                ]
            )

            if is_spanish:
                error_message = (
                    "Lo siento, encontré un error al intentar responder a tu pregunta."
                )
            else:
                error_message = "I'm sorry, I encountered an error while trying to answer your question."

            return {
                "response": error_message,
                "sources": [],
                "error": str(e),
            }

    async def get_document_versions(self, document_id: str) -> Dict[str, Any]:
        """Get all versions of a document.

        Args:
            document_id: Document ID

        Returns:
            Dictionary with document versions
        """
        try:
            # Search for documents with the given document_id
            # The agents-hub PGVector requires a query parameter for search
            search_params = {
                "operation": "search",
                "query": "document",  # Adding a dummy query
                "collection_name": self.collection_name,
                "filter": {"document_id": document_id},
                "limit": 100,  # Set a high limit to get all versions
            }

            logger.info(f"Fetching versions for document: {document_id}")
            search_result = await self.pgvector_tool.run(search_params)

            if "error" in search_result:
                logger.error(f"Error fetching versions: {search_result['error']}")
                return {"error": search_result["error"], "versions": []}

            # Extract results
            results = search_result.get("results", [])

            if not results:
                logger.warning(f"No documents found with ID: {document_id}")
                return {"document_id": document_id, "versions": []}

            # Extract unique versions
            versions = {}
            for result in results:
                metadata = result.get("metadata", {})
                version = metadata.get("version")

                if version and version not in versions:
                    versions[version] = {
                        "version": version,
                        "filename": metadata.get("filename", "Unknown"),
                        "title": metadata.get("title", "Unknown"),
                        "ingestion_date": metadata.get("ingestion_date", "Unknown"),
                        "page_count": metadata.get("page_count", 0),
                    }

            # Convert to list and sort by version
            version_list = list(versions.values())
            version_list.sort(key=lambda x: x["version"])

            return {
                "document_id": document_id,
                "versions": version_list,
                "count": len(version_list),
            }
        except Exception as e:
            logger.exception(f"Error getting document versions: {document_id}")
            return {"error": str(e), "versions": []}
