# ==========================================
# translation-service/app.py
# Standalone Flask/FastAPI service for translations
# ==========================================

from flask import Flask, request
import logging
import os
from services.translator import AutoTranslator
from threading import Lock
import time

app = Flask(__name__)

# Global translator instance with thread safety
translator_lock = Lock()
translator = None


def get_translator():
    """Get or create translator instance (thread-safe)."""
    global translator
    with translator_lock:
        if translator is None:
            translator = AutoTranslator(
                headless=True,
                wait_time=2
            )
    return translator


@app.route("/health")
def health_check():
    """Health check endpoint."""
    try:
        # Quick health check - don't actually run Selenium
        return {"status": "healthy", "service": "translation"}, 200
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 500


@app.route("/translate", methods=["POST"])
def translate():
    """Translate English address to Urdu."""
    try:
        data = request.get_json()

        if not data or "text" not in data:
            return {"error": "Text is required"}, 400

        text = data["text"]
        source_lang = data.get("source_lang", "en")
        target_lang = data.get("target_lang", "ur")

        # Get translator and perform translation
        translator_instance = get_translator()

        start_time = time.time()
        result = translator_instance.translate(text)
        end_time = time.time()

        # Extract translated text
        if isinstance(result, dict) and text in result:
            translated_text = result[text]
        else:
            translated_text = result

        return {
            "original": text,
            "translated": translated_text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "processing_time": round(end_time - start_time, 2),
        }, 200

    except Exception as e:
        logging.error(f"Translation error: {str(e)}")
        return {"error": f"Translation failed: {str(e)}"}, 500


@app.route("/translate/batch", methods=["POST"])
def translate_batch():
    """Translate multiple texts."""
    try:
        data = request.get_json()

        if not data or "texts" not in data or not isinstance(data["texts"], list):
            return {"error": "texts array is required"}, 400

        texts = data["texts"]
        if len(texts) > 10:  # Limit batch size
            return {"error": "Maximum 10 texts per batch"}, 400

        translator_instance = get_translator()

        start_time = time.time()
        results = translator_instance.translate(texts)
        end_time = time.time()

        return {
            "results": results,
            "count": len(texts),
            "processing_time": round(end_time - start_time, 2),
        }, 200

    except Exception as e:
        logging.error(f"Batch translation error: {str(e)}")
        return {"error": f"Batch translation failed: {str(e)}"}, 500


@app.route("/status")
def status():
    """Get service status and stats."""
    return {
        "service": "translation-service",
        "status": "running",
        "selenium_enabled": True,
        "headless_mode": True,
        "max_batch_size": 10,
    }


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Start Flask server
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
