import json
from pathlib import Path
from typing import Dict, List, Optional
class LanguageManager:
    def __init__(self):
        self.file_path = Path("app/languages.json")
        self.languages: List[dict] = json.loads(self.file_path.read_text(encoding="utf-8"))
        self.lang_dict: Dict[str, dict] = {lang["language_short"]: lang for lang in self.languages}

    def get_language(self, code: str) -> Optional[dict]:
        return self.lang_dict.get(code)

    def validate_pair(self, source: str, target: str) -> tuple[bool, str]:
        if source not in self.lang_dict:
            return False, f"Source language code '{source}' not supported"
        if target not in self.lang_dict:
            return False, f"Target language code '{target}' not supported"
        if source == target:
            return False, "Source and target languages cannot be the same"
        return True, ""

    def get_all_languages(self) -> List[dict]:
        return self.languages