"""
Translator Service Module
Provides an abstraction layer for text translation, input validation,
language management, and robust error handling.
"""

import time
import logging
from typing import Dict, Any, Tuple
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

# How many times to retry a rate-limited translation request before giving up.
# Between retries the service waits: 1s, 2s, 4s (exponential backoff).
MAX_RETRIES = 3

# Standard list of popular supported languages for easy selection
SUPPORTED_LANGUAGES = {
    "auto": "Detect Language",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh-CN": "Chinese (Simplified)",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi",
    "tr": "Turkish",
    "nl": "Dutch",
    "pl": "Polish",
    "sv": "Swedish",
    "el": "Greek",
    "uk": "Ukrainian",
    "vi": "Vietnamese",
    "id": "Indonesian",
    "th": "Thai",
    "sw": "Swahili",
    "yo": "Yoruba",
    "ha": "Hausa",
    "ig": "Igbo",
}

class TranslationError(Exception):
    """Custom exception raised when translation fails."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class TranslatorService:
    def __init__(self, provider: str = "google", max_chars: int = 5000):
        self.provider = provider.lower()
        self.max_chars = max_chars

    @staticmethod
    def get_supported_languages() -> Dict[str, str]:
        """Returns the dictionary of supported languages and codes."""
        return SUPPORTED_LANGUAGES

    def validate_request(self, text: str, source_lang: str, target_lang: str) -> Tuple[str, str, str]:
        """
        Validates input parameters.
        Raises TranslationError if input is invalid.
        """
        if not text or not isinstance(text, str) or not text.strip():
            raise TranslationError("Text to translate cannot be empty.", status_code=400)

        cleaned_text = text.strip()
        if len(cleaned_text) > self.max_chars:
            raise TranslationError(
                f"Text exceeds the maximum length of {self.max_chars} characters (received {len(cleaned_text)}).",
                status_code=400
            )

        if not target_lang or not isinstance(target_lang, str):
            raise TranslationError("A target language must be specified.", status_code=400)

        source_lang = source_lang.strip() if source_lang else "auto"
        target_lang = target_lang.strip()

        if target_lang == "auto":
            raise TranslationError("Target language cannot be set to 'auto'. Please select a specific language.", status_code=400)

        # Validate against known languages
        if source_lang != "auto" and source_lang not in SUPPORTED_LANGUAGES:
            raise TranslationError(f"Unsupported source language code: '{source_lang}'.", status_code=400)

        if target_lang not in SUPPORTED_LANGUAGES:
            raise TranslationError(f"Unsupported target language code: '{target_lang}'.", status_code=400)

        return cleaned_text, source_lang, target_lang

    def translate(self, text: str, source_lang: str = "auto", target_lang: str = "en") -> Dict[str, Any]:
        """
        Translates text from source_lang to target_lang using deep-translator.

        Automatically retries up to MAX_RETRIES times (with exponential backoff)
        when Google's rate-limit is hit, so brief burst limits self-resolve
        without any action from the user.

        Returns a dictionary with translated text and metadata.
        """
        cleaned_text, src, tgt = self.validate_request(text, source_lang, target_lang)

        # Optimisation: identical source and target — skip the network call entirely
        if src == tgt:
            return {
                "success": True,
                "translated_text": cleaned_text,
                "source_lang": src,
                "target_lang": tgt,
                "character_count": len(cleaned_text),
                "provider": self.provider,
                "note": "Source and target languages are identical."
            }

        # Build the provider translator once
        try:
            if self.provider == "mymemory":
                from deep_translator import MyMemoryTranslator
                translator = MyMemoryTranslator(source=src, target=tgt)
            else:
                from deep_translator import GoogleTranslator
                translator = GoogleTranslator(source=src, target=tgt)
        except Exception as e:
            logger.error(f"Failed to initialise translation provider: {e}")
            raise TranslationError(f"Could not initialise the translation provider: {e}", status_code=502)

        # --- Retry loop with exponential backoff ---
        last_error: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = translator.translate(cleaned_text)

                if result is None:
                    raise TranslationError(
                        "The translation provider returned an empty response.",
                        status_code=502
                    )

                logger.info(
                    f"Translation successful on attempt {attempt}: "
                    f"{src} -> {tgt} ({len(cleaned_text)} chars)"
                )
                return {
                    "success": True,
                    "translated_text": result,
                    "source_lang": src,
                    "target_lang": tgt,
                    "character_count": len(cleaned_text),
                    "provider": self.provider
                }

            except TranslationError:
                # Our own validation errors — don't retry, re-raise immediately
                raise

            except RequestException as e:
                logger.error(f"Network error during translation (attempt {attempt}): {e}")
                raise TranslationError(
                    "Network error: Unable to connect to the translation service. "
                    "Check your internet connection.",
                    status_code=503
                )

            except Exception as e:
                error_msg = str(e)
                last_error = e

                is_rate_limit = (
                    "too many requests" in error_msg.lower()
                    or "server error" in error_msg.lower()
                    or "rate" in error_msg.lower()
                    or "429" in error_msg
                )
                is_unsupported = "not supported" in error_msg.lower()

                if is_unsupported:
                    raise TranslationError(f"Translation error: {error_msg}", status_code=400)

                if is_rate_limit and attempt < MAX_RETRIES:
                    wait_seconds = 2 ** (attempt - 1)   # 1s, 2s on retries 1 and 2
                    logger.warning(
                        f"Rate limit hit (attempt {attempt}/{MAX_RETRIES}). "
                        f"Retrying in {wait_seconds}s…"
                    )
                    time.sleep(wait_seconds)
                    continue   # next attempt

                # All retries exhausted or non-retryable error
                logger.error(f"Translation provider error after {attempt} attempt(s): {error_msg}")
                if is_rate_limit:
                    raise TranslationError(
                        "Google Translate is still rate-limiting after several retries. "
                        "Please wait a moment and try again.",
                        status_code=429
                    )
                raise TranslationError(
                    f"Translation service failed: {error_msg}",
                    status_code=502
                )

        # Should never be reached, but satisfies type checkers
        raise TranslationError("Translation failed after all retry attempts.", status_code=502)

