import pytest
from unittest.mock import MagicMock, patch
import deepl
from app import create_app
from config import Config

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
    assert "de" in data["languages"]
    assert "ja" in data["languages"]

def test_health_check_endpoint(client):
    """Test application health check."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert "provider" in data
    assert data["provider"] == "deepl"

def test_translate_valid_request_with_mock(client, monkeypatch):
    """Test successful translation using a mocked DeepL translation provider."""
    mock_result = MagicMock()
    mock_result.text = "Hola Mundo"
    mock_result.detected_source_lang = "EN"

    mock_client = MagicMock()
    mock_client.translate_text.return_value = mock_result

    monkeypatch.setattr("deepl.DeepLClient", lambda auth_key: mock_client)

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
    assert data["provider"] == "deepl"

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
    mock_client = MagicMock()
    mock_client.translate_text.side_effect = deepl.ConnectionException("Connection timed out")

    monkeypatch.setattr("deepl.DeepLClient", lambda auth_key: mock_client)

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
    mock_client = MagicMock()
    mock_client.translate_text.side_effect = deepl.DeepLException("Internal provider failure")

    monkeypatch.setattr("deepl.DeepLClient", lambda auth_key: mock_client)

    payload = {
        "text": "Hello World",
        "source_lang": "en",
        "target_lang": "es"
    }
    response = client.post("/api/translate", json=payload)
    assert response.status_code == 502
    data = response.get_json()
    assert data["success"] is False
    assert "DeepL translation service error" in data["error"]

def test_translate_provider_empty_response(client, monkeypatch):
    """Test provider returning None returns 502."""
    mock_client = MagicMock()
    mock_client.translate_text.return_value = None

    monkeypatch.setattr("deepl.DeepLClient", lambda auth_key: mock_client)

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

# --- DeepL Specific Test Suite (Phase 3 Expanded Coverage) ---

def test_translate_missing_credentials(monkeypatch):
    """Verify application returns 503 and clear error when DEEPL_AUTH_KEY is missing."""
    monkeypatch.delenv("DEEPL_AUTH_KEY", raising=False)

    class NoKeyConfig(Config):
        TESTING = True
        TRANSLATION_PROVIDER = "deepl"
        DEEPL_AUTH_KEY = None
        MAX_CHAR_LIMIT = 500

    no_key_app = create_app(NoKeyConfig)
    test_client = no_key_app.test_client()

    payload = {
        "text": "Hello World",
        "source_lang": "en",
        "target_lang": "es"
    }
    response = test_client.post("/api/translate", json=payload)
    assert response.status_code == 503
    data = response.get_json()
    assert data["success"] is False
    assert "DEEPL_AUTH_KEY" in data["error"]

def test_translate_authentication_failure(client, monkeypatch):
    """Test invalid or rejected DeepL API key returns 401."""
    mock_client = MagicMock()
    mock_client.translate_text.side_effect = deepl.AuthorizationException("Forbidden 401: Invalid auth key")

    monkeypatch.setattr("deepl.DeepLClient", lambda auth_key: mock_client)

    payload = {
        "text": "Hello World",
        "source_lang": "en",
        "target_lang": "es"
    }
    response = client.post("/api/translate", json=payload)
    assert response.status_code == 401
    data = response.get_json()
    assert data["success"] is False
    assert "authentication failed" in data["error"]

def test_translate_quota_exhausted(client, monkeypatch):
    """Test quota exhaustion returns 429."""
    mock_client = MagicMock()
    mock_client.translate_text.side_effect = deepl.QuotaExceededException("Quota exceeded for this month")

    monkeypatch.setattr("deepl.DeepLClient", lambda auth_key: mock_client)

    payload = {
        "text": "Hello World",
        "source_lang": "en",
        "target_lang": "es"
    }
    response = client.post("/api/translate", json=payload)
    assert response.status_code == 429
    data = response.get_json()
    assert data["success"] is False
    assert "quota exceeded" in data["error"]

def test_translate_rate_limit_too_many_requests(client, monkeypatch):
    """Test rate limiting returns 429 after retries."""
    mock_client = MagicMock()
    mock_client.translate_text.side_effect = deepl.TooManyRequestsException("Rate limit 429")

    monkeypatch.setattr("deepl.DeepLClient", lambda auth_key: mock_client)

    payload = {
        "text": "Hello World",
        "source_lang": "en",
        "target_lang": "es"
    }
    response = client.post("/api/translate", json=payload)
    assert response.status_code == 429
    data = response.get_json()
    assert data["success"] is False
    assert "rate limit" in data["error"]

def test_translate_auto_detect_source_language(client, monkeypatch):
    """Verify source_lang='auto' maps to source_lang=None in DeepL and resolves detected lang."""
    mock_result = MagicMock()
    mock_result.text = "Hello world"
    mock_result.detected_source_lang = "FR"

    mock_client = MagicMock()
    mock_client.translate_text.return_value = mock_result

    monkeypatch.setattr("deepl.DeepLClient", lambda auth_key: mock_client)

    payload = {
        "text": "Bonjour le monde",
        "source_lang": "auto",
        "target_lang": "en"
    }
    response = client.post("/api/translate", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["source_lang"] == "fr"

    # Verify DeepLClient was called with source_lang=None
    call_kwargs = mock_client.translate_text.call_args[1]
    assert call_kwargs["source_lang"] is None

def test_translate_language_code_mapping(client, monkeypatch):
    """Verify code mapping for DeepL targets ('en' -> 'EN-US', 'pt' -> 'PT-PT', 'zh-CN' -> 'ZH')."""
    mock_result = MagicMock()
    mock_result.text = "Translated"
    mock_result.detected_source_lang = "ES"

    mock_client = MagicMock()
    mock_client.translate_text.return_value = mock_result

    monkeypatch.setattr("deepl.DeepLClient", lambda auth_key: mock_client)

    # Test target 'en' maps to 'EN-US'
    client.post("/api/translate", json={"text": "Hola", "source_lang": "es", "target_lang": "en"})
    assert mock_client.translate_text.call_args[1]["target_lang"] == "EN-US"

    # Test target 'pt' maps to 'PT-PT'
    client.post("/api/translate", json={"text": "Hola", "source_lang": "es", "target_lang": "pt"})
    assert mock_client.translate_text.call_args[1]["target_lang"] == "PT-PT"

    # Test target 'zh-CN' maps to 'ZH'
    client.post("/api/translate", json={"text": "Hola", "source_lang": "es", "target_lang": "zh-CN"})
    assert mock_client.translate_text.call_args[1]["target_lang"] == "ZH"

def test_unsupported_languages_not_advertised(client):
    """Verify languages unsupported by DeepL (such as Yoruba 'yo') are not in DeepL catalog."""
    response = client.get("/api/languages")
    data = response.get_json()
    assert "yo" not in data["languages"]
