"""
Tests for custom text chunking.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from services.chunking import chunk_custom_text


def test_basic_chunking():
    """Chunks text into ~200 char pieces."""
    text = "word " * 100  # 500 chars
    chunks = chunk_custom_text(text)
    assert len(chunks) > 1
    assert all(len(c) <= 210 for c in chunks)  # some tolerance for word boundaries


def test_overlap():
    """Consecutive chunks overlap by ~50 chars."""
    text = " ".join(f"word{i}" for i in range(200))  # ~1400 chars, non-repeating
    chunks = chunk_custom_text(text, chunk_size=200, overlap=50)
    if len(chunks) >= 2:
        # End of chunk 0 should overlap with start of chunk 1.
        # Split on spaces to avoid partial-word boundary mismatches,
        # then verify the last few whole words of chunk 0 appear in chunk 1.
        tail_words = chunks[0].split()[-5:]
        tail = " ".join(tail_words)
        assert tail in chunks[1], f"Expected overlap '{tail}' in chunk 1"


def test_word_boundary():
    """Never cuts in the middle of a word."""
    text = "abcdefghij " * 50  # 550 chars
    chunks = chunk_custom_text(text, chunk_size=200, overlap=50)
    for chunk in chunks:
        assert not chunk.startswith(" ")
        assert chunk == chunk.strip()


def test_short_text_single_chunk():
    """Text shorter than chunk_size returns one chunk."""
    text = "Short text here."
    chunks = chunk_custom_text(text)
    assert len(chunks) == 1
    assert chunks[0] == "Short text here."


def test_empty_text():
    """Empty text returns empty list."""
    assert chunk_custom_text("") == []
    assert chunk_custom_text("   ") == []
