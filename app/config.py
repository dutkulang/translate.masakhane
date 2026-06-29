import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models_cache"
MODELS_DIR.mkdir(exist_ok=True)

# Added explicit token mappings for both M2M100 and NLLB model families
from pathlib import Path

BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parent
# load environment variables
load_dotenv(dotenv_path=ROOT_DIR / ".env")

# Read the origins string and provide a safe local fallback if it's missing
raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
# Clean and parse the string into a list of strings
CORS_ORIGINS = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

MODELS_DIR = BASE_DIR / "models_cache"
MODELS_DIR.mkdir(exist_ok=True)

# masakhane models use joet that is not supported here using CTranslate2 useable models
# for now am using the faceboook nllb model
# the dictionary supports switching of models hence the no need for one main base model
# I understand that masakhane community has no ready to use models
SUPPORTED_PAIRS = {
    "en-yo": {"model": "facebook/nllb-200-distilled-600M", "src_token": "eng_Latn", "tgt_token": "yor_Latn"},
    "en-lg": {"model": "facebook/nllb-200-distilled-600M", "src_token": "eng_Latn", "tgt_token": "lug_Latn"},
    "yo-en": {"model": "facebook/nllb-200-distilled-600M", "src_token": "yor_Latn", "tgt_token": "eng_Latn"},
    "en-sw": {"model": "facebook/nllb-200-distilled-600M", "src_token": "eng_Latn", "tgt_token": "swh_Latn"},
    "sw-en": {"model": "facebook/nllb-200-distilled-600M", "src_token": "swh_Latn", "tgt_token": "eng_Latn"},
    "en-ig": {"model": "facebook/nllb-200-distilled-600M", "src_token": "eng_Latn", "tgt_token": "ibo_Latn"},
    "en-ha": {"model": "facebook/nllb-200-distilled-600M", "src_token": "eng_Latn", "tgt_token": "hau_Latn"},
}