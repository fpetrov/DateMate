import asyncio
import os

import pytest
from aiogram.types import InlineKeyboardMarkup

from datemate.config import load_settings
from datemate.tgbot.functional import Phrases, keyboards
from datemate.tgbot.middlewares.db import DbSessionMiddleware
from datemate.tgbot.middlewares.interface import InterfaceMiddleware
from datemate.tgbot.middlewares.throttling import ThrottlingMiddleware
from tests.stubs import DummyBot, DummyFSM, FakeMessage


def test_load_settings(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "token")
    monkeypatch.setenv("REDIS_URL", "redis://localhost")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///test.db")

    settings = load_settings()

    assert settings.bot_token == "token"
    assert settings.redis_url.startswith("redis")
    assert settings.database_url.startswith("sqlite")


def test_keyboards_build_inline_markup():
    phrases = Phrases()
    faculties = [type("Faculty", (), {"id": "f1", "name": "F1"})(), type("Faculty", (), {"id": "f2", "name": "F2"})()]

    kb = keyboards.main_menu(phrases)
    assert isinstance(kb, InlineKeyboardMarkup)

    faculty_kb = keyboards.faculty_keyboard(faculties)
    assert any(button.callback_data.startswith("faculty:") for row in faculty_kb.inline_keyboard for button in row)

    candidate_kb = keyboards.candidate_actions(phrases, "1")
    assert any("rate:like" in button.callback_data for row in candidate_kb.inline_keyboard for button in row)


@pytest.mark.asyncio
async def test_db_session_middleware_adds_session(session_factory):
    middleware = DbSessionMiddleware(session_factory)
    event = FakeMessage(chat_id=1, message_id=1)
    data = {}

    async def handler(evt, data_dict):
        assert "session" in data_dict
        return "ok"

    result = await middleware(handler, event, data)
    assert result == "ok"


@pytest.mark.asyncio
async def test_throttling_middleware_blocks_repeated_messages():
    middleware = ThrottlingMiddleware(time_limit=1)
    event = FakeMessage(chat_id=2, message_id=1)
    data = {}
    calls = []

    async def handler(evt, data_dict):
        calls.append(evt)
        return "handled"

    first = await middleware(handler, event, data)
    second = await middleware(handler, event, data)

    assert first == "handled"
    assert second is None
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_interface_middleware_injects_context(session_factory):
    async with session_factory() as session:
        middleware = InterfaceMiddleware(Phrases())
        bot = DummyBot()
        state = DummyFSM()
        event = FakeMessage(chat_id=3, message_id=1)

        async def handler(evt, data_dict):
            assert "context" in data_dict
            assert "phrases" in data_dict
            return "ok"

        data = {"bot": bot, "state": state, "session": session}
        result = await middleware(handler, event, data)

    assert result == "ok"
    assert bot.deleted_messages == [(event.chat.id, event.message_id)]
