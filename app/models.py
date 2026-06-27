import json
import shutil
from pathlib import Path
import ctranslate2
import transformers
import torch
from app.config import SUPPORTED_PAIRS, MODELS_DIR


class TranslationModel:
    def __init__(self):
        self.translators = {}
        self.tokenizers = {}

    def _get_model_path(self, pair: str) -> Path:
        return MODELS_DIR / pair

    def _convert_model_if_needed(self, hf_model_name: str, pair: str, force: bool = False):
        """
        Converts HF models to CTranslate2 format with automatic self-clearing 
        if the underlying configuration changes in production.
        """
        model_path = self._get_model_path(pair)
        model_file = model_path / "model.bin"
        metadata_file = model_path / "cache_metadata.json"

        cache_is_valid = False

        # Verify if cache exists AND matches the currently active config model
        if model_file.exists() and metadata_file.exists() and not force:
            try:
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                
                # Check if the cached model matches the current config string
                if metadata.get("hf_model_name") == hf_model_name:
                    cache_is_valid = True
            except Exception:
                # If the metadata file is corrupted or unreadable, mark cache as invalid
                cache_is_valid = False

        if cache_is_valid:
            print(f"Model {pair} cache is valid and matches config.")
            return

        # Cache is missing, incomplete, or stale (you changed models in config.py)
        if model_path.exists():
            print(f"Configuration mismatch or stale cache detected for {pair}. Auto-clearing...")
            shutil.rmtree(model_path)

        print(f"Converting {hf_model_name} to CTranslate2 (this may take a minute)...")
        model_path.mkdir(parents=True, exist_ok=True)

        try:
            converter = ctranslate2.converters.TransformersConverter(hf_model_name)
            converter.convert(
                output_dir=str(model_path),
                quantization="int8",      # provides a good balance between speed and size
                force=True
            )
            
            # Write the metadata marker to lock down this conversion version
            with open(metadata_file, "w") as f:
                json.dump({"hf_model_name": hf_model_name}, f)
                
            print(f"Successfully converted {pair} and saved validation metadata.")
            
        except Exception as e:
            # Clean up partial footprints on structural conversion crashes
            if model_path.exists():
                shutil.rmtree(model_path)
            raise RuntimeError(f"CTranslate2 conversion failed for {hf_model_name}: {str(e)}")

    def get_translator(self, src_lang: str, tgt_lang: str):
        pair = f"{src_lang}-{tgt_lang}"

        if pair not in SUPPORTED_PAIRS:
            raise ValueError(f"No model available for {pair}")

        if pair not in self.translators:
            model_info = SUPPORTED_PAIRS[pair]
            hf_model_name = model_info["model"]

            # Automatically checks files and versions; safe to stay False
            self._convert_model_if_needed(hf_model_name, pair, force=False)

            # Load translator
            model_path = self._get_model_path(pair)
            self.translators[pair] = ctranslate2.Translator(
                str(model_path),
                device="cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu",
                compute_type="int8"
            )

            # Load tokenizer for pretrained models masakhane are kind of hard to work with
            self.tokenizers[pair] = transformers.AutoTokenizer.from_pretrained(hf_model_name)

        return self.translators[pair], self.tokenizers[pair]

    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        pair = f"{src_lang}-{tgt_lang}"
        translator, tokenizer = self.get_translator(src_lang, tgt_lang)

        model_info = SUPPORTED_PAIRS.get(pair, {})
        src_token = model_info.get("src_token", src_lang)
        tgt_token = model_info.get("tgt_token", tgt_lang)

        try:
            tokenizer.src_lang = src_token
        except (KeyError, ValueError, AttributeError):
            clean_src = src_token.strip("_")
            tokenizer.src_lang = clean_src

        input_tokens = tokenizer.convert_ids_to_tokens(tokenizer.encode(text))
        results = translator.translate_batch([input_tokens], target_prefix=[[tgt_token]])
        output_tokens = results[0].hypotheses[0]
        
        translated_text = tokenizer.decode(
            tokenizer.convert_tokens_to_ids(output_tokens),
            skip_special_tokens=True
        )

        return translated_text.strip()