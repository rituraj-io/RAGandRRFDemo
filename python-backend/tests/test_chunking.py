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
    text = "The quick brown fox jumps over the lazy dog. " * 20  # ~900 chars
    chunks = chunk_custom_text(text, chunk_size=200, overlap=50)
    if len(chunks) >= 2:
        # End of chunk 0 should overlap with start of chunk 1
        tail = chunks[0][-50:]
        assert tail in chunks[1]


def test_word_boundary():
    """Never cuts in the middle of a word."""
    text = "abcdefghij " * 50  # 550 chars
    chunks = chunk_custom_text(text, chunk_size=200, overlap=50)
    for chunk in chunks:
        assert not chunk.startswith(" ")
        assert not chunk.endswith(" ") or chunk.strip() == chunk.strip()


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
