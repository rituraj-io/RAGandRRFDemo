"""
Shared test fixtures.
"""

import os
import shutil
import tempfile

import pytest
from fastapi.testclient import TestClient

from config import Settings


@pytest.fixture()
def tmp_data_dir():
    """Create a temporary data directory for tests."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


@pytest.fixture()
def test_settings(tmp_data_dir):
    """Settings pointing to temporary data directory."""
    return Settings(
        chroma_path=os.path.join(tmp_data_dir, "chroma"),
        sqlite_bm25_path=os.path.join(tmp_data_dir, "bm25.db"),
        sqlite_chat_path=os.path.join(tmp_data_dir, "chat.db"),
        llm_api_key="",
        llm_model="gpt-4o-mini",
    )


@pytest.fixture()
def client():
    """FastAPI test client."""
    from main import app
    return TestClient(app)
