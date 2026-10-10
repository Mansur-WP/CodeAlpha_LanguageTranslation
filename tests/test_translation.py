import pytest
from unittest.mock import MagicMock, patch
from requests.exceptions import ConnectionError

def test_home_page_renders(client):
    """Test that the index route returns 200 and serves the UI with key elements."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Polyglot" in html
    assert "CodeAlpha" in html
    assert "source-text" in html
    assert "target-text" in html
    assert "Translate" in html

def test_api_languages_endpoint(client):
    """Test that the API languages route returns supported languages."""
    response = client.get("/api/languages")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "languages" in data
    assert "en" in data["languages"]
    assert "es" in data["languages"]
    assert "fr" in data["languages"]
    assert "yo" in data["languages"]

def test_health_check_endpoint(client):
    """Test application health check."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert "provider" in data

def test_translate_valid_request_with_mock(client, monkeypatch):
    """Test successful translation using a mocked translation provider."""
    mock_translator_instance = MagicMock()
    mock_translator_instance.translate.return_value = "Hola Mundo"

    # Patch GoogleTranslator in deep_translator module
    monkeypatch.setattr(
        "deep_translator.GoogleTranslator",
        lambda source, target: mock_translator_instance
    )

    payload = {
        "text": "Hello World",
        "source_lang": "en",
        "target_lang": "es"
    }

    response = client.post("/api/translate", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["translated_text"] == "Hola Mundo"
    assert data["source_lang"] == "en"
    assert data["target_lang"] == "es"
    assert data["character_count"] == len("Hello World")

def test_translate_identical_languages_shortcut(client):
    """When source and target languages are identical, return text without provider call."""
    payload = {
        "text": "Hello World",
        "source_lang": "en",
        "target_lang": "en"
    }
    response = client.post("/api/translate", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["translated_text"] == "Hello World"

def test_translate_missing_json_payload(client):
    """Test request with non-JSON payload returns 400."""
    response = client.post("/api/translate", data="raw string")
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert "valid JSON" in data["error"]

def test_translate_empty_text(client):
    """Test validation fails when text is empty or just whitespace."""
    payload = {
        "text": "   ",
        "source_lang": "en",
        "target_lang": "es"
    }
    response = client.post("/api/translate", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert "cannot be empty" in data["error"]

def test_translate_target_cannot_be_auto(client):
    """Test validation fails when target language is 'auto'."""
    payload = {
        "text": "Bonjour",
        "source_lang": "fr",
        "target_lang": "auto"
    }
    response = client.post("/api/translate", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert "Target language cannot be set to 'auto'" in data["error"]

def test_translate_unsupported_language(client):
    """Test validation fails when language code is invalid/unsupported."""
    payload = {
        "text": "Hello",
        "source_lang": "en",
        "target_lang": "xyz_invalid"
    }
    response = client.post("/api/translate", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert "Unsupported" in data["error"]

def test_translate_char_limit_exceeded(client):
    """Test validation fails when text length exceeds maximum configured limit."""
    long_text = "A" * 600  # Configured limit in TestConfig is 500
    payload = {
        "text": long_text,
        "source_lang": "en",
        "target_lang": "es"
    }
    response = client.post("/api/translate", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert "exceeds the maximum length" in data["error"]

def test_translate_provider_network_failure(client, monkeypatch):
    """Test network error handling returns 503 with friendly message."""
    mock_translator_instance = MagicMock()
    mock_translator_instance.translate.side_effect = ConnectionError("Connection refused by remote host")

    monkeypatch.setattr(
        "deep_translator.GoogleTranslator",
        lambda source, target: mock_translator_instance
    )

    payload = {
        "text": "Hello World",
        "source_lang": "en",
        "target_lang": "es"
    }
    response = client.post("/api/translate", json=payload)
    assert response.status_code == 503
    data = response.get_json()
    assert data["success"] is False
    assert "Network error" in data["error"]

def test_translate_provider_generic_error(client, monkeypatch):
    """Test unexpected provider exception returns 502."""
    mock_translator_instance = MagicMock()
    mock_translator_instance.translate.side_effect = RuntimeError("Internal provider failure")

    monkeypatch.setattr(
        "deep_translator.GoogleTranslator",
        lambda source, target: mock_translator_instance
    )

    payload = {
        "text": "Hello World",
        "source_lang": "en",
        "target_lang": "es"
    }
    response = client.post("/api/translate", json=payload)
    assert response.status_code == 502
    data = response.get_json()
    assert data["success"] is False
    assert "Translation service failed" in data["error"]

def test_translate_provider_empty_response(client, monkeypatch):
    """Test provider returning None returns 502."""
    mock_translator_instance = MagicMock()
    mock_translator_instance.translate.return_value = None

    monkeypatch.setattr(
        "deep_translator.GoogleTranslator",
        lambda source, target: mock_translator_instance
    )

    payload = {
        "text": "Hello World",
        "source_lang": "en",
        "target_lang": "es"
    }
    response = client.post("/api/translate", json=payload)
    assert response.status_code == 502
    data = response.get_json()
    assert data["success"] is False
    assert "empty response" in data["error"]
