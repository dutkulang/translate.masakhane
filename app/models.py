import ctranslate2
import transformers
from pathlib import Path
from app.config import SUPPORTED_PAIRS, MODELS_DIR

class TranslationModel:
    def __init__(self):
        self.translators = {}      # Cache for CTranslate2 translators
        self.tokenizers = {}       # Cache for tokenizers

    def _get_model_path(self, pair: str) -> Path:
        """Return local path for converted CTranslate2 model"""
        return MODELS_DIR / pair

    def _convert_model_if_needed(self, hf_model_name: str, pair: str):
        """Convert Hugging Face model to CTranslate2 format (one-time)"""
        model_path = self._get_model_path(pair)
        if model_path.exists():
            return

        print(f"Converting model {hf_model_name} to CTranslate2...")
        model_path.mkdir(parents=True, exist_ok=True)

        # Convert using CTranslate2 tool
        converter = ctranslate2.converters.TransformersConverter(hf_model_name)
        converter.convert(str(model_path), quantization="int8")   # int8 = fast + small

    def get_translator(self, src_lang: str, tgt_lang: str):
        pair = f"{src_lang}-{tgt_lang}"

        if pair not in SUPPORTED_PAIRS:
            raise ValueError(f"No model available for {pair}")

        if pair not in self.translators:
            model_info = SUPPORTED_PAIRS[pair]
            hf_model_name = model_info["model"]

            # Convert model if not already converted
            self._convert_model_if_needed(hf_model_name, pair)

            # Load CTranslate2 translator
            model_path = self._get_model_path(pair)
            self.translators[pair] = ctranslate2.Translator(
                str(model_path),
                device="cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu",
                compute_type="int8"   # Change to "float16" if you have good GPU
            )

            # Load tokenizer
            self.tokenizers[pair] = transformers.AutoTokenizer.from_pretrained(hf_model_name)

        return self.translators[pair], self.tokenizers[pair]

    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        translator, tokenizer = self.get_translator(src_lang, tgt_lang)

        # Prepare input
        tokenizer.src_lang = src_lang
        input_tokens = tokenizer.convert_ids_to_tokens(tokenizer.encode(text))

        # Translate
        results = translator.translate_batch([input_tokens], target_prefix=[[tgt_lang]])

        # Decode output
        output_tokens = results[0].hypotheses[0]
        translated_text = tokenizer.decode(tokenizer.convert_tokens_to_ids(output_tokens))

        return translated_text.strip()