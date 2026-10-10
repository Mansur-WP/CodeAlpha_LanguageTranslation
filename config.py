import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
# Load environment variables from .env file if present.
# override=True ensures a changed .env is always picked up, even after a hot-reload.
load_dotenv(override=True)

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "codealpha-default-dev-key-change-in-production")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "1").lower() in ("1", "true", "yes")
    PORT = int(os.getenv("PORT", 5000))
    
    # Translation Provider: 'deepl' (official API, default), 'google', or 'mymemory'
    TRANSLATION_PROVIDER = os.getenv("TRANSLATION_PROVIDER", "deepl").strip().lower()
    DEEPL_AUTH_KEY = os.getenv("DEEPL_AUTH_KEY", None)
    MYMEMORY_EMAIL = os.getenv("MYMEMORY_EMAIL", None)
    
    # Character limit for single translation request to prevent abuse and timeout
    MAX_CHAR_LIMIT = int(os.getenv("MAX_CHAR_LIMIT", 5000))
