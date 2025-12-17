from datemate.tgbot.functional import Phrases


def test_phrases_default_and_language_loading():
    phrases = Phrases()

    assert "registered" in phrases["menu"]

    english = phrases.for_language("en")
    assert english["menu"]["registered"]

    fallback = phrases.for_language("xx")
    assert fallback["menu"] == phrases["menu"]
