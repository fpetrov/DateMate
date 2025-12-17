import pytest

from datemate.domain.repositories import UserRepository
from datemate.tgbot.functional import CoreContext, Phrases
from datemate.tgbot.handlers.registration import (
    RegistrationState,
    finish_photos,
    set_age,
    set_description,
    set_faculty,
    set_language,
    set_name,
    set_photos,
    set_search_sex,
    set_sex,
    start_registration,
)
from tests.stubs import DummyBot, DummyFSM, FakeCallback, FakeMessage


@pytest.mark.asyncio
async def test_registration_full_happy_path(session):
    bot = DummyBot()
    state = DummyFSM()
    context = await CoreContext.create(bot, state)
    phrases = Phrases()
    user_id = 999

    initial_message = FakeMessage(chat_id=1, message_id=10, from_user_id=user_id)
    callback = FakeCallback("action:register", message=initial_message, from_user_id=user_id)

    await start_registration(callback, state, context, phrases, session)
    assert state.state == RegistrationState.language

    lang_callback = FakeCallback("language:en", message=initial_message, from_user_id=user_id)
    await set_language(lang_callback, state, context, phrases.for_language("en"), phrases)
    assert state.state == RegistrationState.name
    assert state.data["language"] == "en"

    name_message = FakeMessage(chat_id=1, message_id=11, text="John Doe", from_user_id=user_id)
    await set_name(name_message, state, context, phrases.for_language("en"))
    assert state.state == RegistrationState.sex

    sex_callback = FakeCallback("sex:M", message=initial_message, from_user_id=user_id)
    await set_sex(sex_callback, state, context, phrases.for_language("en"))
    assert state.state == RegistrationState.search_sex

    search_callback = FakeCallback("search_sex:F", message=initial_message, from_user_id=user_id)
    await set_search_sex(search_callback, state, context, phrases.for_language("en"))
    assert state.state == RegistrationState.age

    age_message = FakeMessage(chat_id=1, message_id=12, text="25", from_user_id=user_id)
    await set_age(age_message, state, context, phrases.for_language("en"), session)
    assert state.state == RegistrationState.faculty

    faculty_callback = FakeCallback("faculty:fkn", message=initial_message, from_user_id=user_id)
    await set_faculty(faculty_callback, state, context, phrases.for_language("en"), session)
    assert state.state == RegistrationState.description

    description_message = FakeMessage(chat_id=1, message_id=13, text="About me", from_user_id=user_id)
    await set_description(description_message, state, context, phrases.for_language("en"))
    assert state.state == RegistrationState.photos

    photo_message = FakeMessage(
        chat_id=1,
        message_id=14,
        from_user_id=user_id,
        photo=[type("Photo", (), {"file_id": "file_1"})()],
    )
    await set_photos(photo_message, state, context, phrases.for_language("en"), session)

    finish_callback = FakeCallback("photos:done", message=initial_message, from_user_id=user_id)
    await finish_photos(finish_callback, state, context, phrases.for_language("en"), session)

    user_repo = UserRepository(session)
    saved_user = await user_repo.get_by_telegram_id(user_id)
    assert saved_user is not None
    assert saved_user.name == "John Doe"
    assert saved_user.photos == ["file_1"]
