"""
Tests for the chat service (LangChain LLM integration).

Uses a mock LLM to avoid real API calls in tests.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import MagicMock, patch
from services.chat import ChatService


@pytest.fixture()
def mock_chat_service():
    """Chat service with a mocked LLM."""
    svc = ChatService.__new__(ChatService)
    svc._llm = MagicMock()
    svc._llm.invoke = MagicMock(return_value=MagicMock(content="Mocked LLM response"))
    return svc


def test_generate_response(mock_chat_service):
    """Generate a response given context, history, and a message."""
    sources = [
        {"id": "doc1", "title": "Python Guide", "content": "Python is great.", "score": 0.9, "metadata": {}},
    ]
    history = [
        {"role": "user", "content": "What is Python?"},
        {"role": "assistant", "content": "A programming language."},
    ]

    response = mock_chat_service.generate_response(
        message="Tell me more",
        history=history,
        sources=sources,
    )

    assert response == "Mocked LLM response"
    svc_llm = mock_chat_service._llm
    assert svc_llm.invoke.called


def test_generate_response_empty_context(mock_chat_service):
    """Handles empty sources gracefully."""
    response = mock_chat_service.generate_response(
        message="Hello",
        history=[],
        sources=[],
    )

    assert response == "Mocked LLM response"
