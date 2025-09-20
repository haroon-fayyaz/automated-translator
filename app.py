# ==========================================
# translation-service/app.py
# Standalone Flask/FastAPI service for translations
# ==========================================

from flask import Flask, request, jsonify
import logging
import os
import services.translator as ts
import time

app = Flask(__name__)


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

        start_time = time.time()
        result = ts.translate(text)
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


@app.route("/mapping", methods=["GET"])
def get_mapping():
    return jsonify(ts.get_mapping())


@app.route("/mapping", methods=["POST"])
def add_mapping():
    data = request.get_json()
    en_word = data.get("english")
    ur_word = data.get("urdu")

    if not en_word or not ur_word:
        return jsonify({"error": "Both 'english' and 'urdu' are required"}), 400

    ts.add_mapping(en_word, ur_word)
    return jsonify({"message": "Mapping added/updated", "mapping": ts.get_mapping()})


@app.route("/mapping/<word>", methods=["DELETE"])
def delete_mapping(word):
    if ts.delete_mapping(word):
        return jsonify({"message": f"Mapping for '{word}' deleted"})
    else:
        return jsonify({"error": f"No mapping found for '{word}'"}), 404


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Start Flask server
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
