"""
Tests for the custom text splitter.
"""

import pytest
from app.utils.text_splitter import TextSplitter, RecursiveCharacterTextSplitter


def test_recursive_character_text_splitter_small_text():
    """Test that small text is not split."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=0)
    text = "This is a small text."
    chunks = splitter.split_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_recursive_character_text_splitter_paragraph_split():
    """Test splitting by paragraphs."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=0)
    text = "This is paragraph one.\n\nThis is paragraph two.\n\nThis is paragraph three."
    chunks = splitter.split_text(text)
    assert len(chunks) == 3
    assert chunks[0] == "This is paragraph one."
    assert chunks[1] == "This is paragraph two."
    assert chunks[2] == "This is paragraph three."


def test_recursive_character_text_splitter_line_split():
    """Test splitting by lines."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=20, chunk_overlap=0)
    text = "Line one.\nLine two.\nLine three."
    chunks = splitter.split_text(text)
    assert len(chunks) == 3
    assert chunks[0] == "Line one."
    assert chunks[1] == "Line two."
    assert chunks[2] == "Line three."


def test_recursive_character_text_splitter_sentence_split():
    """Test splitting by sentences."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=15, chunk_overlap=0)
    text = "Short sentence. Another one. And a third."
    chunks = splitter.split_text(text)
    assert len(chunks) == 3
    assert chunks[0] == "Short sentence"
    assert chunks[1] == "Another one"
    assert chunks[2] == "And a third."


def test_recursive_character_text_splitter_word_split():
    """Test splitting by words."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=10, chunk_overlap=0)
    text = "These are some words to split."
    chunks = splitter.split_text(text)
    assert len(chunks) > 1
    assert "These are" in chunks[0]


def test_recursive_character_text_splitter_character_split():
    """Test splitting by characters."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=5, chunk_overlap=0)
    text = "abcdefghijklmnopqrstuvwxyz"
    chunks = splitter.split_text(text)
    assert len(chunks) == 6
    assert chunks[0] == "abcde"
    assert chunks[1] == "fghij"
    assert chunks[2] == "klmno"
    assert chunks[3] == "pqrst"
    assert chunks[4] == "uvwxy"
    assert chunks[5] == "z"


def test_recursive_character_text_splitter_with_overlap():
    """Test splitting with overlap."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=10, chunk_overlap=3)
    text = "abcdefghijklmnopqrstuvwxyz"
    chunks = splitter.split_text(text)
    assert len(chunks) > 1
    assert chunks[0] == "abcdefghij"
    assert chunks[1][0:3] == "hij"  # Overlap from previous chunk
