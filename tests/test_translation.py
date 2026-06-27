import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
from fastapi.testclient import TestClient

# Corrected absolute app package imports
from app import config
import app
from app.models import TranslationModel

client = TestClient(app)


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def mock_dependencies(mocker):
    """Mocks heavy ML dependencies to isolate logic and speed up test execution."""
    mock_translator_cls = mocker.patch("ctranslate2.Translator")
    mock_tokenizer_cls = mocker.patch("transformers.AutoTokenizer")
    mock_converter_cls = mocker.patch("ctranslate2.converters.TransformersConverter")
    
    # Setup mock behavior instances
    mock_translator = MagicMock()
    mock_translator.translate_batch.return_value = [
        MagicMock(hypotheses=[["translated", "tokens"]])
    ]
    mock_translator_cls.return_value = mock_translator

    mock_tokenizer = MagicMock()
    mock_tokenizer.encode.return_value = [1, 2, 3]
    mock_tokenizer.convert_ids_to_tokens.return_value = ["mock", "tokens"]
    mock_tokenizer.convert_tokens_to_ids.return_value = [4, 5, 6]
    mock_tokenizer.decode.return_value = "Mfanya kazi wa maji"
    mock_tokenizer_cls.from_pretrained.return_value = mock_tokenizer

    return {
        "translator": mock_translator,
        "tokenizer": mock_tokenizer,
        "converter": mock_converter_cls
    }


# ==============================================================================
# CONTROLLER & ENDPOINT TESTS (API LAYER)
# ==============================================================================

class TestApiEndpoints:

    def test_health_check_gpu_and_healthy(self, mocker):
        """Verifies health check output when system runs on GPU and disk has space."""
        mocker.patch("ctranslate2.get_cuda_device_count", return_value=1)
        mocker.patch("shutil.disk_usage", return_value=(100, 50, 10 * (1024 ** 3))) # 10 GB free
        mocker.patch("os.access", return_value=True)

        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["environment"]["compute_device"] == "gpu"
        assert data["environment"]["free_disk_space_gb"] == 10.0

    def test_health_check_low_disk_space(self, mocker):
        """Verifies health status degrades gracefully to 'low_space' under 2GB free."""
        mocker.patch("ctranslate2.get_cuda_device_count", return_value=0)
        mocker.patch("shutil.disk_usage", return_value=(100, 99, 1.5 * (1024 ** 3))) # 1.5 GB free
        mocker.patch("os.access", return_value=True)

        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "degraded"

    def test_health_check_disk_failure(self, mocker):
        """Verifies overall status flips to 503 Service Unavailable when system calls fail."""
        mocker.patch("shutil.disk_usage", side_effect=OSError("Disk broken"))
        
        response = client.get("/health")
        assert response.status_code == 503
        assert response.json()["status"] == "unhealthy"

    def test_cors_preflight_options(self):
        """Validates that browser CORS OPTIONS preflight headers are allowed and intercepted."""
        headers = {
            "Origin": "http://localhost:5173", # frontend URL path (for local development only)
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        }
        response = client.options("/translate", headers=headers)
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173" # dev model only replace with live URL later

    @patch.object(TranslationModel, "translate", return_value="Maji")
    def test_translate_endpoint_success(self, mock_translate):
        """Validates standard happy-path routing for a translation request."""
        payload = {
            "text": "water",
            "source_lang": "en",
            "target_lang": "sw"
        }
        response = client.post("/translate", json=payload)
        assert response.status_code == 200
        assert response.json() == {"translated_text": "Maji"}
        mock_translate.assert_called_once_with("water", "en", "sw")

    @pytest.mark.parametrize("missing_field", ["text", "source_lang", "target_lang"])
    def test_translate_endpoint_validation_errors(self, missing_field):
        """Ensures FastAPI body validation interceptor catches malformed schemas."""
        payload = {
            "text": "water",
            "source_lang": "en",
            "target_lang": "sw"
        }
        del payload[missing_field]
        
        response = client.post("/translate", json=payload)
        assert response.status_code == 422


# ==============================================================================
# CORE MODEL & CACHE MANAGEMENT LOGIC TESTS (ENGINE LAYER)
# ==============================================================================

class TestTranslationModelCore:

    def test_get_translator_unsupported_pair(self):
        """Verifies engine rejects random language configurations that aren't defined."""
        model_engine = TranslationModel()
        with pytest.raises(ValueError, match="No model available for en-xyz"):
            model_engine.get_translator("en", "xyz")

    def test_cache_is_valid_skips_conversion(self, mock_dependencies, mocker):
        """Ensures system skips full conversion if valid cache file and metadata are found."""
        model_engine = TranslationModel()
        
        mocker.patch.object(Path, "exists", return_value=True)
        mocker.patch("builtins.open", mock_open(read_data='{"hf_model_name": "facebook/nllb-200-distilled-600M"}'))

        model_engine.get_translator("en", "sw")
        mock_dependencies["converter"].assert_not_called()

    def test_stale_cache_triggers_auto_wipe_and_reconvert(self, mock_dependencies, mocker):
        """Verifies production self-healing cache logic clears older layout types."""
        model_engine = TranslationModel()
        
        mocker.patch.object(Path, "exists", return_value=True)
        mocker.patch("builtins.open", mock_open(read_data='{"hf_model_name": "facebook/m2m100_418M"}'))
        mock_rmtree = mocker.patch("shutil.rmtree")
        mocker.patch.object(Path, "mkdir")

        model_engine.get_translator("en", "sw")

        mock_rmtree.assert_called_once()
        mock_dependencies["converter"].assert_called_once()

    def test_conversion_failure_cleanup(self, mock_dependencies, mocker):
        """Validates directory sanitation if CTranslate2 crashes mid-flight."""
        model_engine = TranslationModel()
        
        mocker.patch.object(Path, "exists", return_value=False)
        mocker.patch.object(Path, "mkdir")
        mock_rmtree = mocker.patch("shutil.rmtree")
        
        mock_dependencies["converter"].return_value.convert.side_effect = RuntimeError("Quantization crash")

        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(RuntimeError, match="CTranslate2 conversion failed"):
                model_engine.get_translator("en", "sw")

        mock_rmtree.assert_called_once()

    def test_tokenizer_source_language_fallback_handling(self, mock_dependencies, mocker):
        """Validates fallback string handling works across the nested app hierarchy config."""
        model_engine = TranslationModel()
        
        mocker.patch.object(Path, "exists", return_value=True)
        mocker.patch("builtins.open", mock_open(read_data='{"hf_model_name": "facebook/nllb-200-distilled-600M"}'))

        type(mock_dependencies["tokenizer"]).src_lang = mocker.PropertyMock(
            side_effect=[ValueError("Invalid template"), None]
        )

        with patch.dict(config.SUPPORTED_PAIRS, {"en-sw": {"model": "...", "src_token": "__en__", "tgt_token": "..."}}):
            model_engine.translate("hello", "en", "sw")
            assert mock_dependencies["tokenizer"].src_lang == "en"