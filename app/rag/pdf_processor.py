"""
PDF processing module for extracting text and metadata from PDF files.
"""

import os
import logging
import tempfile
import time
from typing import Dict, Any, List, Optional, Tuple, BinaryIO
from datetime import datetime
import difflib
import hashlib
from io import BytesIO

import PyPDF2
from app.utils.text_splitter import (
    RecursiveCharacterTextSplitter,
    IncrementalTextSplitter,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PDFProcessor:
    """Class for processing PDF files."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        chunk_method: str = "incremental",  # Changed default to incremental
        max_pages: int = 100,  # Maximum number of pages to process
        page_batch_size: int = 10,  # Process pages in batches
        max_chunk_time: float = 30.0,  # Maximum time in seconds for chunking
        batch_size: int = 10000,  # Process text in batches of this size
    ):
        """Initialize the PDF processor.

        Args:
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            chunk_method: Method for chunking text ('incremental' or 'recursive')
            max_pages: Maximum number of pages to process (0 for unlimited)
            page_batch_size: Number of pages to process in a batch
            max_chunk_time: Maximum time in seconds for chunking
            batch_size: Process text in batches of this size
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunk_method = chunk_method
        self.max_pages = max_pages
        self.page_batch_size = page_batch_size
        self.max_chunk_time = max_chunk_time
        self.batch_size = batch_size

        # Create the appropriate text splitter based on the method
        if chunk_method == "recursive":
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
            )
        else:
            # Default to incremental for better performance with large documents
            self.text_splitter = IncrementalTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                max_chunk_time=max_chunk_time,
                batch_size=batch_size,
            )

    def extract_text(self, pdf_file: BinaryIO) -> str:
        """Extract text from a PDF file.

        Args:
            pdf_file: PDF file object

        Returns:
            Extracted text
        """
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            total_pages = len(pdf_reader.pages)
            logger.info(f"PDF has {total_pages} pages")

            # Limit the number of pages if max_pages is set
            if self.max_pages > 0 and total_pages > self.max_pages:
                logger.warning(
                    f"PDF has {total_pages} pages, limiting to {self.max_pages} pages"
                )
                total_pages = self.max_pages

            text = ""

            # Process pages in batches
            for batch_start in range(0, total_pages, self.page_batch_size):
                batch_end = min(batch_start + self.page_batch_size, total_pages)
                logger.info(
                    f"Processing pages {batch_start+1} to {batch_end} of {total_pages}"
                )

                batch_text = ""
                for page_num in range(batch_start, batch_end):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        batch_text += page_text + "\n\n"

                text += batch_text

            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise

    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        try:
            # Log the size of the text being chunked
            text_size_kb = len(text) / 1024
            logger.info(f"Chunking text of size {text_size_kb:.2f} KB")

            # Set a timeout for the chunking process
            start_time = time.time()

            # Use the text splitter to chunk the text
            chunks = self.text_splitter.split_text(text)

            # Log chunking performance
            chunking_time = time.time() - start_time
            chunks_count = len(chunks)
            logger.info(
                f"Chunked text in {chunking_time:.2f} seconds, generated {chunks_count} chunks"
            )

            # If we didn't get any chunks but have text, create at least one chunk
            if not chunks and text:
                logger.warning(
                    "No chunks generated but text is not empty, creating a single chunk"
                )
                # Truncate if necessary to avoid memory issues
                max_length = min(len(text), self.chunk_size * 2)
                chunks = [text[:max_length]]

            return chunks
        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            logger.exception("Chunking error details:")

            # Return a safe fallback - create simple chunks by splitting the text
            # into fixed-size pieces without any fancy processing
            logger.warning("Using fallback chunking method due to error")
            try:
                # Simple fallback chunking
                fallback_chunks = []
                chunk_size = self.chunk_size

                # Limit text size for safety
                max_text_size = 1000000  # 1MB max
                if len(text) > max_text_size:
                    logger.warning(
                        f"Text too large ({len(text)} bytes), truncating to {max_text_size} bytes"
                    )
                    text = text[:max_text_size]

                # Simple character-based chunking
                for i in range(0, len(text), chunk_size):
                    chunk = text[i : i + chunk_size]
                    if chunk:
                        fallback_chunks.append(chunk)

                logger.info(
                    f"Fallback chunking generated {len(fallback_chunks)} chunks"
                )
                return fallback_chunks
            except Exception as fallback_error:
                logger.error(f"Fallback chunking also failed: {fallback_error}")
                # Last resort: return a single chunk with truncated text
                return [text[: min(len(text), 10000)]] if text else []

    def extract_metadata(self, pdf_file: BinaryIO) -> Dict[str, Any]:
        """Extract metadata from a PDF file.

        Args:
            pdf_file: PDF file object

        Returns:
            Dictionary of metadata
        """
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            metadata = pdf_reader.metadata

            # Calculate document hash for identification
            pdf_file.seek(0)
            doc_hash = hashlib.sha256(pdf_file.read()).hexdigest()

            # Reset file pointer
            pdf_file.seek(0)

            # Extract basic metadata
            result = {
                "title": metadata.get("/Title", ""),
                "author": metadata.get("/Author", ""),
                "subject": metadata.get("/Subject", ""),
                "creator": metadata.get("/Creator", ""),
                "producer": metadata.get("/Producer", ""),
                "creation_date": metadata.get("/CreationDate", ""),
                "modification_date": metadata.get("/ModDate", ""),
                "page_count": len(pdf_reader.pages),
                "document_hash": doc_hash,
                "processed_date": datetime.now().isoformat(),
            }

            return result
        except Exception as e:
            logger.error(f"Error extracting metadata from PDF: {e}")
            raise

    def compare_pdfs(self, pdf1: BinaryIO, pdf2: BinaryIO) -> Dict[str, Any]:
        """Compare two PDF files and identify differences.

        Args:
            pdf1: First PDF file
            pdf2: Second PDF file

        Returns:
            Dictionary with comparison results
        """
        try:
            # Extract text from both PDFs
            text1 = self.extract_text(pdf1)
            text2 = self.extract_text(pdf2)

            # Reset file pointers
            pdf1.seek(0)
            pdf2.seek(0)

            # Extract metadata
            metadata1 = self.extract_metadata(pdf1)
            metadata2 = self.extract_metadata(pdf2)

            # Compare text using difflib
            diff = difflib.unified_diff(
                text1.splitlines(),
                text2.splitlines(),
                lineterm="",
                n=3,  # Context lines
            )

            # Process diff to get additions and deletions
            additions = []
            deletions = []

            for line in diff:
                if line.startswith("+") and not line.startswith("+++"):
                    additions.append(line[1:])
                elif line.startswith("-") and not line.startswith("---"):
                    deletions.append(line[1:])

            # Calculate similarity ratio
            similarity = difflib.SequenceMatcher(None, text1, text2).ratio()

            # Prepare comparison result
            result = {
                "similarity_ratio": similarity,
                "additions_count": len(additions),
                "deletions_count": len(deletions),
                "additions": additions,
                "deletions": deletions,
                "metadata_changes": self._compare_metadata(metadata1, metadata2),
                "page_count_diff": metadata2["page_count"] - metadata1["page_count"],
            }

            return result
        except Exception as e:
            logger.error(f"Error comparing PDFs: {e}")
            raise

    def _compare_metadata(
        self, metadata1: Dict[str, Any], metadata2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare metadata from two PDFs.

        Args:
            metadata1: Metadata from first PDF
            metadata2: Metadata from second PDF

        Returns:
            Dictionary with metadata changes
        """
        changes = {}

        # Compare relevant metadata fields
        for key in ["title", "author", "subject", "creator", "producer"]:
            if metadata1.get(key) != metadata2.get(key):
                changes[key] = {
                    "from": metadata1.get(key),
                    "to": metadata2.get(key),
                }

        return changes
