"""
Custom text splitter implementation to avoid using langchain.
"""

import re
import time
import logging
from typing import List, Callable, Optional, Set, Iterator, Generator

# Configure logging
logger = logging.getLogger(__name__)


class TextSplitter:
    """Base text splitter class."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        length_function: Callable[[str], int] = len,
    ):
        """Initialize the text splitter.

        Args:
            chunk_size: Maximum size of chunks
            chunk_overlap: Overlap between chunks
            length_function: Function to measure text length
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.length_function = length_function

    def split_text(self, text: str) -> List[str]:
        """Split text into chunks.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        raise NotImplementedError("Subclasses must implement split_text method")


class IncrementalTextSplitter(TextSplitter):
    """Text splitter that processes text incrementally to avoid memory issues."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        length_function: Callable[[str], int] = len,
        separators: Optional[List[str]] = None,
        max_chunk_time: float = 30.0,  # Maximum time in seconds for chunking
        batch_size: int = 10000,  # Process text in batches of this size
    ):
        """Initialize the incremental text splitter.

        Args:
            chunk_size: Maximum size of chunks
            chunk_overlap: Overlap between chunks
            length_function: Function to measure text length
            separators: List of separators to use for splitting
            max_chunk_time: Maximum time in seconds for chunking
            batch_size: Process text in batches of this size
        """
        super().__init__(chunk_size, chunk_overlap, length_function)
        self.separators = separators or [
            "\n\n",  # Paragraphs
            "\n",  # Lines
            ". ",  # Sentences
            ", ",  # Clauses
            " ",  # Words
        ]
        self.max_chunk_time = max_chunk_time
        self.batch_size = batch_size

    def split_text(self, text: str) -> List[str]:
        """Split text into chunks using incremental processing.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        # Start timing
        start_time = time.time()

        # Return empty list if text is empty
        if not text:
            logger.warning("Empty text provided to text splitter")
            return []

        # Return text as a single chunk if it's small enough
        text_length = self.length_function(text)
        logger.info(
            f"Text length: {text_length} characters, chunk size: {self.chunk_size}"
        )

        if text_length <= self.chunk_size:
            logger.info("Text is smaller than chunk size, returning as single chunk")
            return [text]

        # Process text in batches to avoid memory issues
        chunks = []

        try:
            # Split text into paragraphs first
            logger.info("Splitting text into paragraphs")
            paragraphs = text.split("\n\n")
            logger.info(f"Split text into {len(paragraphs)} paragraphs")

            # Log memory usage
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()
            logger.info(
                f"Memory usage after paragraph splitting: {memory_info.rss / 1024 / 1024:.2f} MB"
            )

            # Process paragraphs in batches
            current_batch = []
            current_batch_size = 0

            logger.info(
                f"Processing paragraphs in batches of approximately {self.batch_size} characters"
            )

            for i, paragraph in enumerate(paragraphs):
                # Log progress periodically
                if i % 100 == 0 and i > 0:
                    elapsed_time = time.time() - start_time
                    logger.info(
                        f"Processed {i}/{len(paragraphs)} paragraphs ({i/len(paragraphs)*100:.1f}%) in {elapsed_time:.2f} seconds"
                    )
                    logger.info(
                        f"Current memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB"
                    )

                # Check if we've exceeded the maximum chunking time
                current_time = time.time()
                elapsed_time = current_time - start_time
                if elapsed_time > self.max_chunk_time:
                    logger.warning(
                        f"Chunking time exceeded {self.max_chunk_time} seconds, stopping at paragraph {i}/{len(paragraphs)} ({i/len(paragraphs)*100:.1f}%)"
                    )
                    logger.warning(
                        f"Memory usage at timeout: {process.memory_info().rss / 1024 / 1024:.2f} MB"
                    )
                    break

                # Add paragraph to current batch
                current_batch.append(paragraph)
                current_batch_size += len(paragraph)

                # Process batch if it's large enough
                if current_batch_size >= self.batch_size or i == len(paragraphs) - 1:
                    # Join batch and split into chunks
                    batch_text = "\n\n".join(current_batch)
                    logger.info(
                        f"Processing batch of size {len(batch_text)} characters"
                    )

                    try:
                        batch_chunks = self._split_batch(batch_text)
                        chunks.extend(batch_chunks)

                        # Reset batch
                        current_batch = []
                        current_batch_size = 0

                        logger.info(
                            f"Processed batch of paragraphs, generated {len(batch_chunks)} chunks, total: {len(chunks)}"
                        )
                    except Exception as e:
                        logger.error(f"Error processing batch: {str(e)}")
                        logger.exception("Batch processing error details:")
                        # Continue with next batch
                        current_batch = []
                        current_batch_size = 0

            # Process any remaining paragraphs
            if current_batch:
                logger.info(
                    f"Processing final batch of {len(current_batch)} paragraphs"
                )
                try:
                    batch_text = "\n\n".join(current_batch)
                    batch_chunks = self._split_batch(batch_text)
                    chunks.extend(batch_chunks)
                except Exception as e:
                    logger.error(f"Error processing final batch: {str(e)}")

            total_time = time.time() - start_time
            logger.info(
                f"Finished chunking, generated {len(chunks)} chunks in {total_time:.2f} seconds ({text_length/total_time:.2f} chars/sec)"
            )

            # Log final memory usage
            logger.info(
                f"Final memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB"
            )

            return chunks

        except Exception as e:
            logger.error(f"Error during text splitting: {str(e)}")
            logger.exception("Text splitting error details:")

            # Return what we have so far, or a simple chunk if nothing
            if not chunks and text:
                logger.warning("No chunks generated, returning text as a single chunk")
                # Truncate if necessary
                max_length = min(len(text), self.chunk_size * 2)
                return [text[:max_length]]

            logger.info(f"Returning {len(chunks)} chunks generated before error")
            return chunks

    def _split_batch(self, text: str) -> List[str]:
        """Split a batch of text into chunks.

        Args:
            text: Text batch to split

        Returns:
            List of text chunks
        """
        # Use simple splitting by separators
        chunks = []

        # Try each separator
        for separator in self.separators:
            if separator in text:
                # Split by this separator
                splits = text.split(separator)

                # Combine splits into chunks
                current_chunk = []
                current_length = 0

                for split in splits:
                    if not split:
                        continue

                    # Calculate length with separator
                    split_length = self.length_function(split)
                    if current_chunk:
                        split_length += self.length_function(separator)

                    # If adding this split would exceed chunk size, finalize current chunk
                    if (
                        current_chunk
                        and current_length + split_length > self.chunk_size
                    ):
                        chunks.append(separator.join(current_chunk))

                        # Start new chunk with overlap
                        overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                        current_chunk = current_chunk[overlap_start:]
                        current_length = self.length_function(
                            separator.join(current_chunk)
                        )

                    # Add split to current chunk
                    if current_chunk:
                        current_chunk.append(split)
                        current_length += self.length_function(separator) + split_length
                    else:
                        current_chunk = [split]
                        current_length = split_length

                # Add final chunk
                if current_chunk:
                    chunks.append(separator.join(current_chunk))

                # If we found chunks, return them
                if chunks:
                    return chunks

        # If no separator worked, split by characters
        return self._split_by_characters(text)

    def _split_by_characters(self, text: str) -> List[str]:
        """Split text by characters when no other separator works.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        chunks = []

        # Calculate the number of characters per chunk
        chars_per_chunk = self.chunk_size

        # Split the text into chunks
        for i in range(0, len(text), chars_per_chunk - self.chunk_overlap):
            # Get the chunk
            chunk = text[i : i + chars_per_chunk]

            # Add the chunk to the list
            if chunk:
                chunks.append(chunk)

        return chunks


class RecursiveCharacterTextSplitter(TextSplitter):
    """Text splitter that recursively splits by different separators."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        length_function: Callable[[str], int] = len,
        separators: Optional[List[str]] = None,
    ):
        """Initialize the recursive character text splitter.

        Args:
            chunk_size: Maximum size of chunks
            chunk_overlap: Overlap between chunks
            length_function: Function to measure text length
            separators: List of separators to use for splitting
        """
        super().__init__(chunk_size, chunk_overlap, length_function)
        self.separators = separators or [
            "\n\n",  # Paragraphs
            "\n",  # Lines
            ". ",  # Sentences
            ", ",  # Clauses
            " ",  # Words
            "",  # Characters
        ]

    def split_text(self, text: str) -> List[str]:
        """Split text into chunks using recursive character splitting.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        # Return empty list if text is empty
        if not text:
            return []

        # Return text as a single chunk if it's small enough
        if self.length_function(text) <= self.chunk_size:
            return [text]

        # Find the first separator that splits the text
        for separator in self.separators:
            # Skip empty separator - we'll handle character-level splitting separately
            if separator == "":
                continue

            if separator in text:
                # Split by this separator
                return self._split_by_separator(text, separator)

        # If no separator works, split by characters
        return self._split_by_characters(text)

    def _split_by_separator(self, text: str, separator: str) -> List[str]:
        """Split text by the given separator and then combine into chunks.

        Args:
            text: Text to split
            separator: Separator to use

        Returns:
            List of text chunks
        """
        # Split the text by the separator
        splits = text.split(separator)

        # Initialize the list of chunks
        chunks = []

        # Initialize the current chunk and its length
        current_chunk = []
        current_length = 0

        # Process each split
        for split in splits:
            # If the split is empty, skip it
            if not split:
                continue

            # Calculate the length of this split (plus separator if needed)
            split_length = self.length_function(split)
            if current_chunk:  # Add separator length if not the first split
                split_length += self.length_function(separator)

            # If adding this split would exceed the chunk size, finalize the current chunk
            if current_chunk and current_length + split_length > self.chunk_size:
                # Join the current chunk and add it to the list of chunks
                chunks.append(separator.join(current_chunk))

                # Start a new chunk with overlap
                overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                current_chunk = current_chunk[overlap_start:]
                current_length = self.length_function(separator.join(current_chunk))

            # Add the split to the current chunk
            if current_chunk:
                current_chunk.append(split)
                current_length += self.length_function(separator) + split_length
            else:
                current_chunk = [split]
                current_length = split_length

        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(separator.join(current_chunk))

        # If we still have chunks that are too large, recursively split them
        final_chunks = []
        for chunk in chunks:
            if self.length_function(chunk) > self.chunk_size:
                # Find the next separator in the list
                next_separator_index = self.separators.index(separator) + 1

                # Skip to the next non-empty separator
                while next_separator_index < len(self.separators):
                    next_separator = self.separators[next_separator_index]
                    if next_separator == "":
                        # Skip empty separator
                        next_separator_index += 1
                        continue
                    # Recursively split with the next separator
                    final_chunks.extend(self._split_by_separator(chunk, next_separator))
                    break
                else:
                    # If there's no next separator, split by characters
                    final_chunks.extend(self._split_by_characters(chunk))
            else:
                final_chunks.append(chunk)

        return final_chunks

    def _split_by_characters(self, text: str) -> List[str]:
        """Split text by characters when no other separator works.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        chunks = []

        # Calculate the number of characters per chunk
        chars_per_chunk = self.chunk_size

        # Split the text into chunks
        for i in range(0, len(text), chars_per_chunk - self.chunk_overlap):
            # Get the chunk
            chunk = text[i : i + chars_per_chunk]

            # Add the chunk to the list
            if chunk:
                chunks.append(chunk)

        return chunks
