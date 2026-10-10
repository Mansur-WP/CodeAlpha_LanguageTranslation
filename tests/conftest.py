import pytest
import os
import sys

# Ensure parent directory is in sys.path so app and modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from config import Config

class TestConfig(Config):
    TESTING = True
    FLASK_ENV = "testing"
    DEBUG = False
    TRANSLATION_PROVIDER = "google"
    MAX_CHAR_LIMIT = 500

@pytest.fixture
def app():
    """Create and configure a Flask application instance for testing."""
    app_instance = create_app(TestConfig)
    return app_instance

@pytest.fixture
def client(app):
    """A test client for making simulated HTTP requests to the app."""
    return app.test_client()
