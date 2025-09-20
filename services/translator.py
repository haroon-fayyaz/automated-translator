import json
import os
import re
from deep_translator import GoogleTranslator

MAPPING_FILE = "mapping.json"

# Load or initialize mapping
if os.path.exists(MAPPING_FILE):
    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        WORD_MAPPING = {k.lower(): v for k, v in json.load(f).items()}
else:
    WORD_MAPPING = {}

def save_mapping():
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(WORD_MAPPING, f, ensure_ascii=False, indent=2)


def translate(text: str) -> str:
    """
    Translate text using mapping first, then Google Translate for remaining words.
    Mapping replacement is case-insensitive.
    """

    # Regex to match words only (ignore punctuation and spaces)
    def replace_match(match):
        word = match.group(0)
        mapped = WORD_MAPPING.get(word.lower())
        return mapped if mapped else word

    # Apply mapping replacements
    mapped_text = re.sub(r"\b\w+\b", replace_match, text)

    # Translate only if any unmapped words remain
    # We send the whole sentence to Google Translate
    final_translation = GoogleTranslator(source="en", target="ur").translate(mapped_text)
    
    return final_translation


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
