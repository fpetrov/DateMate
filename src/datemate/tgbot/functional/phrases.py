import json
from pathlib import Path
from typing import Any


def __load_phrases__(phrases_path: str) -> Any:
    with open(phrases_path, 'r', encoding='utf-8') as path:
        return json.load(path)


class Phrases:
    def __init__(self, phrases_path: str | Path = None):
        default_path = Path(__file__).resolve().parent.parent / 'phrases' / 'phrases_ru.json'
        phrases_location = Path(phrases_path) if phrases_path else default_path
        self.phrases = __load_phrases__(phrases_location)

    def __getitem__(self, item):
        return self.phrases[item]
