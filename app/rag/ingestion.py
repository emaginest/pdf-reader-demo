"""
PDF ingestion and vectorization module.
"""

import os
import logging
import tempfile
from typing import Dict, Any, List, Optional, Tuple, BinaryIO
from datetime import datetime
import uuid

from agents_hub.vector_stores import PGVector
from pydantic import HttpUrl

from app.config import settings
from app.rag.pdf_processor import PDFProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PDFIngestionService:
    """Service for ingesting PDFs and storing them in the vector database."""

    def __init__(
        self,
        pgvector_tool: PGVector,
        pdf_processor: Optional[PDFProcessor] = None,
    ):
        """Initialize the PDF ingestion service.

        Args:
            pgvector_tool: PGVector tool for storing documents
            pdf_processor: PDFProcessor for processing PDFs (optional, will create one if not provided)
        """
        self.pgvector_tool = pgvector_tool
        self.pdf_processor = (
            pdf_processor
            if pdf_processor
            else PDFProcessor(
                chunk_size=settings.vector_store.chunk_size,
                chunk_overlap=settings.vector_store.chunk_overlap,
                chunk_method=settings.vector_store.chunk_method,
                max_pages=settings.vector_store.max_pages,
                page_batch_size=settings.vector_store.page_batch_size,
                max_chunk_time=settings.vector_store.max_chunk_time,
                batch_size=settings.vector_store.batch_size,
            )
        )
        self.collection_name = settings.vector_store.collection_name

    async def ensure_collection_exists(self) -> None:
        """Ensure that the collection exists in the vector database."""
        try:
            logger.info(f"Checking if collection '{self.collection_name}' exists...")

            # Check if collection exists
            collections_result = await self.pgvector_tool.run(
                {"operation": "list_collections"}
            )
            collections = collections_result.get("collections", [])

            logger.info(f"Found {len(collections)} collections in the database")

            # Check if collection exists by name
            collection_exists = False
            for collection in collections:
                if (
                    isinstance(collection, dict)
                    and collection.get("name") == self.collection_name
                ):
                    collection_exists = True
                    logger.info(f"Found existing collection: {collection}")
                    break

            # Create collection if it doesn't exist
            if not collection_exists:
                logger.info(f"Creating collection: {self.collection_name}")
                create_result = await self.pgvector_tool.run(
                    {
                        "operation": "create_collection",
                        "collection_name": self.collection_name,
                        "metadata": {"description": "PDF document storage"},
                    }
                )
                logger.info(f"Collection creation result: {create_result}")
            else:
                logger.info(f"Collection already exists: {self.collection_name}")

            # Verify collection exists after creation
            collections_result = await self.pgvector_tool.run(
                {"operation": "list_collections"}
            )
            collections = collections_result.get("collections", [])
            logger.info(f"After verification, found {len(collections)} collections")

            # Direct SQL query to check collections table
            try:
                query_result = await self.pgvector_tool.run(
                    {
                        "operation": "execute_sql",
                        "sql": "SELECT * FROM vector_store.collections WHERE name = %s",
                        "params": [self.collection_name],
                    }
                )
                logger.info(f"SQL query result for collections table: {query_result}")
            except Exception as sql_e:
                logger.error(f"Error executing SQL query: {sql_e}")
                logger.exception("SQL query error details:")

        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            logger.exception("Detailed error:")
            raise

    async def ingest_pdf(
        self,
        pdf_file: BinaryIO,
        filename: str,
        document_id: Optional[str] = None,
        version: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None,
        max_chunks_per_batch: Optional[int] = None,  # Process chunks in batches
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Ingest a PDF and store it in the vector database.

        Args:
            pdf_file: PDF file object
            filename: Original filename
            document_id: Optional document ID for versioning (will generate if not provided)
            version: Optional version string (will use timestamp if not provided)
            additional_metadata: Optional additional metadata
            max_chunks_per_batch: Maximum number of chunks to process in a batch

        Returns:
            Tuple of (success, message, metadata)
        """
        try:
            # Extract text and metadata from PDF
            logger.info(f"Processing PDF: {filename}")
            start_time = datetime.now()

            # Extract text with optimized processing
            text = self.pdf_processor.extract_text(pdf_file)
            text_extraction_time = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Text extraction completed in {text_extraction_time:.2f} seconds"
            )

            # Reset file pointer for metadata extraction
            pdf_file.seek(0)
            metadata = self.pdf_processor.extract_metadata(pdf_file)

            # Generate document ID if not provided
            if not document_id:
                document_id = str(uuid.uuid4())

            # Generate version if not provided
            if not version:
                version = datetime.now().isoformat()

            # Prepare metadata
            doc_metadata = {
                "filename": filename,
                "document_id": document_id,
                "version": version,
                "document_type": "pdf",
                "ingestion_date": datetime.now().isoformat(),
                "text_extraction_time_seconds": text_extraction_time,
            }

            # Add PDF metadata
            doc_metadata.update(metadata)

            # Add additional metadata if provided
            if additional_metadata:
                doc_metadata.update(additional_metadata)

            # Chunk the text
            chunking_start = datetime.now()
            logger.info(f"Starting text chunking for {filename}")
            chunks = self.pdf_processor.chunk_text(text)
            chunking_time = (datetime.now() - chunking_start).total_seconds()
            logger.info(
                f"Text chunking completed in {chunking_time:.2f} seconds, generated {len(chunks)} chunks"
            )

            if not chunks:
                logger.warning(f"No text content found in PDF: {filename}")
                return False, f"No text content found in PDF: {filename}", doc_metadata

            # Store chunks in batches
            doc_metadata["chunking_time_seconds"] = chunking_time
            doc_metadata["chunks_count"] = len(chunks)

            # Ensure collection exists before storing chunks
            await self.ensure_collection_exists()

            # Store chunks in batches to avoid overwhelming the database
            storage_start = datetime.now()
            # Use the provided max_chunks_per_batch or fall back to the setting
            batch_size = (
                max_chunks_per_batch or settings.vector_store.max_chunks_per_batch
            )
            logger.info(
                f"Storing {len(chunks)} chunks from PDF: {filename} in batches of {batch_size}"
            )

            for batch_start in range(0, len(chunks), batch_size):
                batch_end = min(batch_start + batch_size, len(chunks))
                logger.info(
                    f"Processing chunk batch {batch_start+1} to {batch_end} of {len(chunks)}"
                )

                for i in range(batch_start, batch_end):
                    chunk = chunks[i]
                    # Add chunk-specific metadata
                    chunk_metadata = doc_metadata.copy()
                    chunk_metadata["chunk_index"] = i
                    chunk_metadata["total_chunks"] = len(chunks)

                    # Store the chunk
                    store_result = await self.pgvector_tool.run(
                        {
                            "operation": "add_document",
                            "document": chunk,
                            "collection_name": self.collection_name,
                            "metadata": chunk_metadata,
                        }
                    )

                    if "error" in store_result:
                        logger.error(
                            f"Error storing chunk {i}: {store_result['error']}"
                        )
                        return (
                            False,
                            f"Error storing chunk {i}: {store_result['error']}",
                            doc_metadata,
                        )

            storage_time = (datetime.now() - storage_start).total_seconds()
            total_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"Successfully ingested PDF: {filename}")
            logger.info(f"Storage completed in {storage_time:.2f} seconds")
            logger.info(f"Total ingestion time: {total_time:.2f} seconds")

            # Add timing information to metadata
            doc_metadata["storage_time_seconds"] = storage_time
            doc_metadata["total_ingestion_time_seconds"] = total_time

            return True, f"Successfully ingested PDF: {filename}", doc_metadata
        except Exception as e:
            logger.exception(f"Error ingesting PDF: {filename}")
            return False, f"Error ingesting PDF: {str(e)}", {}

    async def ingest_pdfs(
        self,
        pdf_files: List[Tuple[BinaryIO, str]],
        document_id: Optional[str] = None,
        version: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Ingest multiple PDFs and store them in the vector database.

        Args:
            pdf_files: List of tuples containing (file_object, filename)
            document_id: Optional document ID for versioning
            version: Optional version string
            additional_metadata: Optional additional metadata

        Returns:
            Dictionary with ingestion results
        """
        # Ensure collection exists
        await self.ensure_collection_exists()

        # Process each PDF
        results = []
        failed_files = []
        metadata_list = []

        for pdf_file, filename in pdf_files:
            success, message, metadata = await self.ingest_pdf(
                pdf_file, filename, document_id, version, additional_metadata
            )

            results.append(
                {"filename": filename, "success": success, "message": message}
            )
            metadata_list.append(metadata)

            if not success:
                failed_files.append(filename)

        # Return summary
        return {
            "status": "completed",
            "message": f"Processed {len(pdf_files)} PDFs, {len(failed_files)} failed",
            "files_processed": len(pdf_files),
            "files_failed": len(failed_files),
            "failed_files": failed_files,
            "results": results,
            "metadata": metadata_list,
        }
