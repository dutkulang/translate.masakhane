from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from app.languages import LanguageManager
from app.models import TranslationModel
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import ctranslate2
from app.config import MODELS_DIR, CORS_ORIGINS
app = FastAPI(title="Masakhane Translation API")


# Add the CORS middleware to your FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,           # loads COR origins from dotenv file or environment variables
    allow_credentials=True,
    allow_methods=["*"],             # Allows POST, GET, OPTIONS, etc.
    allow_headers=["*"],             # Allows headers like Content-Type
)

lang_manager = LanguageManager()
translator = TranslationModel()

class TranslateRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str


@app.post("/translate")
async def translate(request: TranslateRequest):
    valid, message = lang_manager.validate_pair(request.source_lang, request.target_lang)
    if not valid:
        raise HTTPException(status_code=400, detail=message)

    try:
        translated_text = translator.translate(
            text=request.text.strip(),
            src_lang=request.source_lang,
            tgt_lang=request.target_lang
        )

        return {
            "success": True,
            "input": request.text,
            "translated_text": translated_text,
            "source_lang": request.source_lang,
            "target_lang": request.target_lang,
            "source_name": lang_manager.get_language(request.source_lang)["language_en"],
            "target_name": lang_manager.get_language(request.target_lang)["language_en"]
        }

    except ValueError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")


@app.get("/languages")
async def get_languages():
    return lang_manager.get_all_languages()


@app.get("/health", status_code=200)
async def health_check(response: Response):
    # Check for Hardware Acceleration State
    cuda_devices = ctranslate2.get_cuda_device_count()
    device_type = "gpu" if cuda_devices > 0 else "cpu"
    
    # Check for Storage Space for Model Cache
    # This prevents the app from choking during an in-flight model download/conversion
    try:
        total, used, free = shutil.disk_usage(MODELS_DIR)
        free_gb = free / (1024 ** 3)  # Convert bytes to GB
        disk_status = "ok" if free_gb > 2.0 else "low_space"  # Warning threshold at 2GB
    except Exception:
        disk_status = "error"
        free_gb = 0

    # 3. Determine Overall Status
    # If disk status is broken, mark the service as unhealthy or degraded
    if disk_status == "error":
        status = "unhealthy"
        response.status_code = 503  # Service Unavailable (Signals load balancers to pull this instance)
    elif disk_status == "low_space":
        status = "degraded"
        # Keep 200 OK but flag it in logs/metrics
    else:
        status = "healthy"

    return {
        "status": status,
        "environment": {
            "compute_device": device_type,
            "cuda_device_count": cuda_devices,
            "cache_dir_writable": os.access(MODELS_DIR, os.W_OK),
            "free_disk_space_gb": f"{round(free_gb, 2)} GB"
        }
    }

from mangum import Mangum
handler = Mangum(app)
