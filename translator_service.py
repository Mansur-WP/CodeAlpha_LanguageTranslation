"""
Translator Service Module
Provides an abstraction layer for text translation, input validation,
language management, and robust error handling using the official DeepL API.
"""

import time
import logging
from typing import Dict, Any, Tuple, Optional
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

# How many times to retry a rate-limited translation request before giving up.
MAX_RETRIES = 3

# Official DeepL Supported Languages catalog
# Source: DeepL API documentation (validated against DeepL v2 API)
DEEPL_SUPPORTED_LANGUAGES = {
    "auto": "Detect Language",
    "ar": "Arabic",
    "bg": "Bulgarian",
    "cs": "Czech",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "et": "Estonian",
    "fi": "Finnish",
    "fr": "French",
    "hu": "Hungarian",
    "id": "Indonesian",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "nb": "Norwegian (Bokmål)",
    "nl": "Dutch",
    "pl": "Polish",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "sv": "Swedish",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "zh-CN": "Chinese (Simplified)",
}

# Legacy fallback catalog for google / mymemory providers
GOOGLE_SUPPORTED_LANGUAGES = {
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
    def __init__(
        self,
        provider: str = "deepl",
        auth_key: Optional[str] = None,
        max_chars: int = 5000,
        validate_plan_languages: bool = False
    ):
        self.provider = provider.lower()
        self.auth_key = auth_key.strip() if (auth_key and isinstance(auth_key, str)) else None
        self.max_chars = max_chars
        self._deepl_client = None
        self._cached_supported_languages = None

        if self.provider == "deepl" and self.auth_key and validate_plan_languages:
            try:
                self._fetch_plan_languages()
            except Exception as e:
                logger.info(f"DeepL client initialisation note: {e}")

    def get_auth_key(self) -> Optional[str]:
        """Returns configured auth key, re-checking environment if initially unset."""
        if self.auth_key:
            return self.auth_key
        import os
        env_key = os.getenv("DEEPL_AUTH_KEY")
        if env_key and isinstance(env_key, str) and env_key.strip():
            return env_key.strip()
        return None

    def _get_client(self):
        """Returns a DeepLClient instance dynamically to allow monkeypatching in unit tests."""
        if self._deepl_client is not None:
            return self._deepl_client
        import deepl
        key = self.get_auth_key()
        return deepl.DeepLClient(key)

    def _fetch_plan_languages(self) -> None:
        """
        Validates languages supported by the actual DeepL API plan.
        Filters out any unsupported languages from being advertised.
        """
        if not self.auth_key:
            return
        try:
            client = self._get_client()
            target_langs = client.get_target_languages()
            if target_langs:
                dynamic_catalog: Dict[str, str] = {"auto": "Detect Language"}
                for lang in target_langs:
                    code_raw = lang.code.upper()
                    if code_raw in ("EN-US", "EN-GB"):
                        dynamic_catalog["en"] = "English"
                    elif code_raw in ("PT-PT", "PT-BR"):
                        dynamic_catalog["pt"] = "Portuguese"
                    elif code_raw == "ZH":
                        dynamic_catalog["zh-CN"] = "Chinese (Simplified)"
                    else:
                        dynamic_catalog[lang.code.lower()] = lang.name

                if len(dynamic_catalog) > 1:
                    self._cached_supported_languages = dynamic_catalog
                    logger.info(f"Validated {len(dynamic_catalog)} languages from DeepL API plan.")
        except Exception as e:
            logger.debug(f"DeepL API plan validation deferred: {e}")

    def get_supported_languages(self_or_cls=None) -> Dict[str, str]:
        """
        Returns supported language dictionary. Can be invoked as an instance
        or static method. Does not advertise unsupported languages.
        """
        if self_or_cls is not None and isinstance(self_or_cls, TranslatorService):
            if self_or_cls._cached_supported_languages:
                return self_or_cls._cached_supported_languages
            if self_or_cls.provider in ("google", "mymemory"):
                return GOOGLE_SUPPORTED_LANGUAGES
            return DEEPL_SUPPORTED_LANGUAGES
        return DEEPL_SUPPORTED_LANGUAGES

    @staticmethod
    def map_source_lang(lang_code: str) -> Optional[str]:
        """
        Maps internal source language code to DeepL API format.
        'auto' -> None (triggers DeepL automatic language detection)
        'zh-CN' -> 'ZH'
        Other codes -> uppercase ISO code
        """
        if not lang_code:
            return None
        code = lang_code.strip()
        if code.lower() in ("auto", "detect", ""):
            return None
        if code.lower() == "zh-cn":
            return "ZH"
        return code.upper()

    @staticmethod
    def map_target_lang(lang_code: str) -> str:
        """
        Maps internal target language code to DeepL API format.
        DeepL requires regional variants for specific target languages:
        'en' -> 'EN-US'
        'pt' -> 'PT-PT'
        'zh-CN' -> 'ZH'
        Other codes -> uppercase ISO code
        """
        code = lang_code.strip()
        c_lower = code.lower()
        if c_lower == "en":
            return "EN-US"
        elif c_lower == "pt":
            return "PT-PT"
        elif c_lower == "zh-cn":
            return "ZH"
        return code.upper()

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

        supported = self.get_supported_languages()

        # Validate against supported languages
        if source_lang != "auto" and source_lang not in supported:
            raise TranslationError(f"Unsupported source language code: '{source_lang}'.", status_code=400)

        if target_lang not in supported:
            raise TranslationError(f"Unsupported target language code: '{target_lang}'.", status_code=400)

        return cleaned_text, source_lang, target_lang

    def translate(self, text: str, source_lang: str = "auto", target_lang: str = "en") -> Dict[str, Any]:
        """
        Translates text from source_lang to target_lang.
        Uses DeepLClient when provider is 'deepl'.
        Preserves response contract and metadata.
        """
        cleaned_text, src, tgt = self.validate_request(text, source_lang, target_lang)

        # Optimisation: identical source and target — skip network call
        if src.lower() == tgt.lower():
            return {
                "success": True,
                "translated_text": cleaned_text,
                "source_lang": src,
                "target_lang": tgt,
                "character_count": len(cleaned_text),
                "provider": self.provider,
                "note": "Source and target languages are identical."
            }

        # --- DeepL Provider Execution ---
        if self.provider == "deepl":
            auth_key = self.get_auth_key()
            if not auth_key:
                logger.error("DEEPL_AUTH_KEY is not configured.")
                raise TranslationError(
                    "DeepL API authentication key is missing. Please set DEEPL_AUTH_KEY in your .env file.",
                    status_code=503
                )

            import deepl

            try:
                client = self._get_client()
            except Exception as exc:
                logger.error(f"Failed to instantiate DeepLClient: {exc}")
                raise TranslationError(f"Could not initialise DeepL client: {exc}", status_code=502)

            src_param = self.map_source_lang(src)
            tgt_param = self.map_target_lang(tgt)

            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    result = client.translate_text(
                        cleaned_text,
                        source_lang=src_param,
                        target_lang=tgt_param
                    )

                    if result is None:
                        raise TranslationError(
                            "The translation provider returned an empty response.",
                            status_code=502
                        )

                    translated_str = result.text if hasattr(result, "text") else str(result)
                    detected_lang = getattr(result, "detected_source_lang", None)
                    resolved_src = src
                    if src == "auto" and detected_lang:
                        resolved_src = str(detected_lang).lower()

                    logger.info(
                        f"DeepL translation successful (attempt {attempt}): "
                        f"{src} ({resolved_src}) -> {tgt} ({len(cleaned_text)} chars)"
                    )
                    return {
                        "success": True,
                        "translated_text": translated_str,
                        "source_lang": resolved_src,
                        "target_lang": tgt,
                        "character_count": len(cleaned_text),
                        "provider": "deepl"
                    }

                except TranslationError:
                    raise

                except deepl.AuthorizationException as ae:
                    logger.error(f"DeepL Authorisation failed: {ae}")
                    raise TranslationError(
                        "DeepL authentication failed. The provided API key is invalid or unauthorized.",
                        status_code=401
                    )

                except deepl.QuotaExceededException as qe:
                    logger.error(f"DeepL quota exceeded: {qe}")
                    raise TranslationError(
                        "DeepL translation quota exceeded. Please upgrade your plan or wait for quota reset.",
                        status_code=429
                    )

                except deepl.TooManyRequestsException as tmre:
                    logger.warning(f"DeepL rate limit hit (attempt {attempt}/{MAX_RETRIES}): {tmre}")
                    if attempt < MAX_RETRIES:
                        wait_seconds = 2 ** (attempt - 1)
                        time.sleep(wait_seconds)
                        continue
                    raise TranslationError(
                        "DeepL rate limit reached. Too many requests. Please wait a moment and try again.",
                        status_code=429
                    )

                except (deepl.ConnectionException, RequestException) as net_err:
                    logger.error(f"DeepL network error (attempt {attempt}): {net_err}")
                    raise TranslationError(
                        "Network error: Unable to connect to DeepL translation service. Check your internet connection.",
                        status_code=503
                    )

                except deepl.DeepLException as de:
                    logger.error(f"DeepL provider error: {de}")
                    raise TranslationError(
                        f"DeepL translation service error: {de}",
                        status_code=502
                    )

                except Exception as exc:
                    logger.error(f"Unexpected provider error: {exc}")
                    raise TranslationError(
                        f"Translation service failed: {exc}",
                        status_code=502
                    )

        # --- Fallback: deep-translator (google / mymemory) ---
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

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = translator.translate(cleaned_text)
                if result is None:
                    raise TranslationError(
                        "The translation provider returned an empty response.",
                        status_code=502
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
                raise
            except RequestException as e:
                logger.error(f"Network error during translation: {e}")
                raise TranslationError(
                    "Network error: Unable to connect to the translation service.",
                    status_code=503
                )
            except Exception as e:
                err_str = str(e)
                if "too many requests" in err_str.lower() or "429" in err_str:
                    if attempt < MAX_RETRIES:
                        time.sleep(2 ** (attempt - 1))
                        continue
                    raise TranslationError(
                        "Translation provider is rate-limiting. Please wait a moment and try again.",
                        status_code=429
                    )
                raise TranslationError(f"Translation service failed: {err_str}", status_code=502)

        raise TranslationError("Translation failed after all retry attempts.", status_code=502)
