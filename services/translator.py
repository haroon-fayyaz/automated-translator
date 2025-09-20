import json
import os
import re
from deep_translator import GoogleTranslator

MAPPING_FILE = "mapping.json"

# 🔑 Load or initialize mapping
if os.path.exists(MAPPING_FILE):
    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        WORD_MAPPING = {k.lower(): v for k, v in json.load(f).items()}
else:
    WORD_MAPPING = {}


def save_mapping():
    """Persist mapping to JSON file (with lowercase keys)."""
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(WORD_MAPPING, f, ensure_ascii=False, indent=2)


def translate(text: str) -> str:
    """Translate text, preferring custom mappings before Google Translate."""
    tokens = re.findall(r"\w+|\s+|[^\w\s]", text, re.UNICODE)
    result_tokens = []

    for token in tokens:
        if token.strip() == "":
            result_tokens.append(token)
            continue

        mapped_value = WORD_MAPPING.get(token.lower())
        if mapped_value:
            result_tokens.append(mapped_value)
        else:
            translated = GoogleTranslator(source="en", target="ur").translate(token)
            result_tokens.append(translated)

    return "".join(result_tokens)


def get_mapping():
    return WORD_MAPPING


def add_mapping(en_word: str, ur_word: str):
    WORD_MAPPING[en_word.lower()] = ur_word
    save_mapping()


def delete_mapping(word: str) -> bool:
    if word.lower() in WORD_MAPPING:
        del WORD_MAPPING[word.lower()]
        save_mapping()
        return True
    return False
