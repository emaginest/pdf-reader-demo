"""
Tests for the PDF processor module.
"""

import os
import pytest
from io import BytesIO

from app.rag.pdf_processor import PDFProcessor


@pytest.fixture
def sample_pdf():
    """Create a sample PDF for testing."""
    # This is a minimal PDF file
    pdf_content = b"%PDF-1.4\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>>>>>/Parent 2 0 R>>\nendobj\n4 0 obj\n<</Length 44>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test PDF document) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\n0000000254 00000 n\ntrailer\n<</Size 5/Root 1 0 R>>\nstartxref\n345\n%%EOF"
    return BytesIO(pdf_content)


def test_extract_text(sample_pdf):
    """Test extracting text from a PDF."""
    processor = PDFProcessor()
    text = processor.extract_text(sample_pdf)
    assert "Test PDF document" in text


def test_chunk_text():
    """Test chunking text."""
    processor = PDFProcessor(chunk_size=10, chunk_overlap=2)
    text = "This is a test document for chunking text into smaller pieces."
    chunks = processor.chunk_text(text)
    assert len(chunks) > 1
    assert "This is a" in chunks[0]


def test_extract_metadata(sample_pdf):
    """Test extracting metadata from a PDF."""
    processor = PDFProcessor()
    metadata = processor.extract_metadata(sample_pdf)
    assert "document_hash" in metadata
    assert metadata["page_count"] == 1


def test_compare_pdfs(sample_pdf):
    """Test comparing two PDFs."""
    # Create a second PDF with slight differences
    pdf_content2 = b"%PDF-1.4\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>>>>>/Parent 2 0 R>>\nendobj\n4 0 obj\n<</Length 51>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test PDF document updated) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\n0000000254 00000 n\ntrailer\n<</Size 5/Root 1 0 R>>\nstartxref\n352\n%%EOF"
    sample_pdf2 = BytesIO(pdf_content2)
    
    processor = PDFProcessor()
    comparison = processor.compare_pdfs(sample_pdf, sample_pdf2)
    
    assert comparison["similarity_ratio"] < 1.0
    assert comparison["additions_count"] > 0
