"""
CodeAlpha - Language Translation Tool
Flask Web Application
"""

import logging
from flask import Flask, render_template, request, jsonify
from config import Config
from translator_service import TranslatorService, TranslationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("CodeAlphaTranslator")

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize translation service
    translator_service = TranslatorService(
        provider=app.config.get("TRANSLATION_PROVIDER", "deepl"),
        auth_key=app.config.get("DEEPL_AUTH_KEY"),
        max_chars=app.config.get("MAX_CHAR_LIMIT", 5000)
    )

    @app.route("/")
    def index():
        """Renders the main translation web UI."""
        languages = translator_service.get_supported_languages()
        return render_template(
            "index.html",
            languages=languages,
            provider=translator_service.provider,
            max_chars=translator_service.max_chars
        )

    @app.route("/api/languages", methods=["GET"])
    def get_languages():
        """Returns JSON mapping of supported language codes to names."""
        return jsonify({
            "success": True,
            "languages": translator_service.get_supported_languages()
        }), 200

    @app.route("/api/translate", methods=["POST"])
    def translate_text():
        """
        API endpoint to translate text.
        Expects JSON payload:
        {
            "text": "Hello world",
            "source_lang": "en" (or "auto"),
            "target_lang": "fr"
        }
        """
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Request body must be valid JSON with 'Content-Type: application/json'."
            }), 400

        data = request.get_json(silent=True)
        if not data:
            return jsonify({
                "success": False,
                "error": "Invalid or empty JSON body."
            }), 400

        text = data.get("text", "")
        source_lang = data.get("source_lang", "auto")
        target_lang = data.get("target_lang", "es")

        try:
            result = translator_service.translate(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang
            )
            return jsonify(result), 200

        except TranslationError as te:
            # 4xx = user input mistake → WARNING (expected, not a bug)
            # 429/5xx = provider/server failure → ERROR (needs attention)
            if te.status_code >= 500 or te.status_code == 429:
                logger.error(
                    f"[{te.status_code}] Provider error: {te.message}"
                )
            else:
                logger.warning(
                    f"[{te.status_code}] Validation error: {te.message}"
                )
            return jsonify({
                "success": False,
                "error": te.message
            }), te.status_code

        except Exception as exc:
            logger.error(f"Unexpected server error during translation: {exc}", exc_info=True)
            return jsonify({
                "success": False,
                "error": "An internal server error occurred while processing your translation."
            }), 500

    @app.route("/api/health", methods=["GET"])
    def health_check():
        """Application health check endpoint."""
        return jsonify({
            "status": "healthy",
            "provider": translator_service.provider,
            "max_chars": translator_service.max_chars
        }), 200

    @app.errorhandler(404)
    def page_not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "error": "API route not found."}), 404
        return render_template("index.html", languages=translator_service.get_supported_languages(), error="Page not found"), 404

    @app.errorhandler(500)
    def server_error(e):
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "error": "Internal server error."}), 500
        return "Internal Server Error", 500

    return app

if __name__ == "__main__":
    app = create_app()
    port = app.config.get("PORT", 5000)
    debug = app.config.get("DEBUG", True)
    print(f"Starting CodeAlpha Language Translation Tool on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
