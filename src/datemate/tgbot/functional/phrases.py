import json
from pathlib import Path
from typing import Any


def __load_phrases__(phrases_path: Path) -> Any:
    with phrases_path.open("r", encoding="utf-8") as path:
        return json.load(path)


class LanguagePhrases:
    def __init__(self, phrases: dict[str, Any]):
        self._phrases = phrases

    def __getitem__(self, item):
        return self._phrases[item]


class Phrases:
    def __init__(self, phrases_dir: str | Path | None = None, default_language: str = "ru"):
        self.base_path = Path(phrases_dir) if phrases_dir else Path(__file__).resolve().parent.parent / "phrases"
        self.default_language = default_language
        self._cache: dict[str, dict[str, Any]] = {}
        self._default_phrases = self._load_language(default_language)

    def _load_language(self, language: str | None) -> dict[str, Any]:
        language_code = (language or self.default_language).lower()
        if language_code in self._cache:
            return self._cache[language_code]

        path = self.base_path / f"phrases_{language_code}.json"
        if not path.exists():
            path = self.base_path / f"phrases_{self.default_language}.json"
            language_code = self.default_language

        phrases = __load_phrases__(path)
        self._cache[language_code] = phrases
        return phrases

    def __getitem__(self, item):
        return self._default_phrases[item]

    def for_language(self, language: str | None) -> LanguagePhrases:
        return LanguagePhrases(self._load_language(language))
