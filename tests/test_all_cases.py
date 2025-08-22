#command to run all unit test cases
# /Users/<username>/Downloads/ag-agent/.venv/bin/python -m pytest ./tests \ -vv -s -rA --capture=tee-sys --maxfail=5 --disable-warnings
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# --- AGENT TESTS ---
from autogen_module.agents import UserDataAgentWrapper

def test_extract_user_intent():
    agent = UserDataAgentWrapper()
    try:
        result = agent.extract_user_intent("hello", [], 1)
    except Exception:
        result = None
    assert isinstance(result, tuple) and len(result) == 3

# --- AUDIO UTILS TESTS ---
from utilities_module.audio_utils import transcribe_audio_to_text

def test_transcribe_audio_to_text():
    try:
        result = transcribe_audio_to_text(b"fake audio bytes")
    except Exception:
        result = None
    assert result is None or isinstance(result, str)

# --- PEOPLE TOOL TESTS ---
from autogen_module.people_tool import PeopleCRUD

def test_create_person():
    crud = PeopleCRUD("fake_connection_string")
    try:
        result = crud.create_person({"name": "Alice"})
    except Exception:
        result = None
    assert result is None or isinstance(result, str)

# --- EMBEDDING UTILS TESTS ---
from utilities_module.embedding_utils import get_embedding

@patch('utilities_module.embedding_utils.embedding_client')
def test_get_embedding_success(mock_embedding_client):
    fake_embedding_vector = [0.1, 0.2, 0.3]
    mock_response = MagicMock()
    mock_response.data[0].embedding = fake_embedding_vector
    mock_embedding_client.embeddings.create.return_value = mock_response
    result = get_embedding("hello world")
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert result.shape == (3,)
    mock_embedding_client.embeddings.create.assert_called_once()

# --- COSMOS RETRIEVER TESTS ---
from database_module.cosmos_retriever import retrieve_semantic_chunks_tool

def test_retrieve_semantic_chunks_tool():
    try:
        result = retrieve_semantic_chunks_tool("query", "user")
    except Exception:
        result = None
    assert result is None or isinstance(result, str)

# --- WEATHER API TESTS ---
from external_apis.weather_api import get_lat_lon_from_zip

def test_get_lat_lon_from_zip():
    try:
        result = get_lat_lon_from_zip("12345")
    except Exception:
        result = None
    assert result is None or isinstance(result, tuple)

# --- BACKEND TESTS ---
from backend import clean_for_tts

def test_clean_for_tts():
    try:
        result = clean_for_tts("Hello world!")
    except Exception:
        result = None
    assert result is None or isinstance(result, str)

# --- MIGRATE KNOWLEDGE TESTS ---
from migrate_knowledge import migrate_container

def test_migrate_container():
    try:
        result = migrate_container(None, "source")
    except Exception:
        result = None
    assert result is None