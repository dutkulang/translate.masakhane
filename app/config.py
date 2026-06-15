import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models_cache"
MODELS_DIR.mkdir(exist_ok=True)

# Supported pairs with CTranslate2 converted models
SUPPORTED_PAIRS = {
    "en-lg": {"model": "masakhane/m2m100_418M_en_lg", "type": "hf"},
    "lg-en": {"model": "masakhane/m2m100_418M_lg_en", "type": "hf"},
    "en-sw": {"model": "masakhane/m2m100_418M_en_sw", "type": "hf"},
    "sw-en": {"model": "masakhane/m2m100_418M_sw_en", "type": "hf"},
    "en-yo": {"model": "masakhane/m2m100_418M_en_yo", "type": "hf"},
    "yo-en": {"model": "masakhane/m2m100_418M_yo_en", "type": "hf"},
    # Add more as you convert models
}