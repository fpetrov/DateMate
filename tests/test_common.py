from datetime import datetime
from types import SimpleNamespace

from datemate.tgbot.handlers.common import format_profile_caption
from datemate.tgbot.functional import Phrases


class DummyUser:
    def __init__(self, name, age, sex, search_sex, faculty_name, description, photos=None, username=None):
        self.name = name
        self.age = age
        self.sex = sex
        self.search_sex = search_sex
        self.faculty = SimpleNamespace(name=faculty_name)
        self.description = description
        self.photos = photos or []
        self.username = username


def test_format_profile_caption_includes_core_fields():
    phrases = Phrases()
    user = DummyUser("Alex", 20, "M", "F", "ФКН", "about me")

    caption = format_profile_caption(user, phrases=phrases)

    assert "Alex, 20" in caption
    assert "ФКН" in caption
    assert "about me" in caption


def test_format_profile_caption_adds_username_and_match_time():
    phrases = Phrases()
    user = DummyUser("Jane", 22, "F", "M", "ФЭН", "hello", username="janedoe")
    match_time = datetime(2024, 1, 1)

    caption = format_profile_caption(user, match_time=match_time, phrases=phrases, username="@jane")

    assert "@jane" in caption
    assert match_time.strftime(phrases["profile"]["match_time_format"]) in caption
