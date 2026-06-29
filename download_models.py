# download_models.py
import os
import sys

# Ensure app directory is discoverable by the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.config import SUPPORTED_PAIRS
from app.models import TranslationModel

print("🚀 Starting container build-time model pre-conversion...")
engine = TranslationModel()

# Run an initial check for all pairs to compile local CTranslate2 artifacts
for pair in SUPPORTED_PAIRS.keys():
    src, tgt = pair.split("-")
    print(f"📦 Pre-converting and caching layouts for: {pair}")
    engine.get_translator(src, tgt)

print("✅ Model compilation step complete. All artifacts baked into container layer.")