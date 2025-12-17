import pytest
from aiogram.exceptions import TelegramBadRequest

from datemate.tgbot.functional import CoreContext
from tests.stubs import DummyBot, DummyFSM, FakeMessage


@pytest.mark.asyncio
async def test_core_context_reuses_message_on_edit():
    bot = DummyBot()
    state = DummyFSM()
    context = await CoreContext.create(bot, state)
    event = FakeMessage(chat_id=10, message_id=50)

    core = await context.respond_text(event, "hello")
    assert len(bot.sent_messages) == 1

    edited = await context.respond_text(event, "updated")

    assert edited is core
    assert bot.edited_messages[-1][2] == "updated"
    assert len(bot.sent_messages) == 1


@pytest.mark.asyncio
async def test_core_context_creates_new_message_on_edit_error():
    bot = DummyBot()
    bot.edit_error = TelegramBadRequest(message="failure", method="edit_message_text")
    state = DummyFSM()
    context = await CoreContext.create(bot, state, fallback_text="fallback")
    event = FakeMessage(chat_id=11, message_id=60)

    first = await context.respond_text(event, "initial")
    bot.edit_error = TelegramBadRequest(message="Bad Request", method="edit_message_text")
    updated = await context.respond_text(event, "second")

    assert first.message_id != updated.message_id
    assert bot.deleted_messages
    assert len(bot.sent_messages) == 2


@pytest.mark.asyncio
async def test_core_context_photo_fallback_on_media_error():
    bot = DummyBot()
    bot.edit_media_error = TelegramBadRequest(message="media", method="edit_message_media")
    state = DummyFSM()
    context = await CoreContext.create(bot, state, fallback_text="fallback")
    event = FakeMessage(chat_id=12, message_id=70)

    await context.respond_photo(event, "photo1", caption="caption1")
    bot.edit_media_error = TelegramBadRequest(message="media", method="edit_message_media")
    await context.respond_photo(event, "photo2", caption="caption2")

    assert bot.deleted_messages
    assert bot.sent_photos[-1][2] == "fallback"
