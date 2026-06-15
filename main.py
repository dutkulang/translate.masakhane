from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.languages import LanguageManager
from app.models import TranslationModel

app = FastAPI(title="Masakhane Translation API")

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


@app.get("/health")
async def health_check():
    return {"status": "healthy"}