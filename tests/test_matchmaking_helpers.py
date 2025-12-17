import pytest

from datemate.domain.repositories import MatchRepository, UserRepository
from datemate.tgbot.functional import CoreContext, Phrases
from datemate.tgbot.handlers.matchmaking import _resolve_username, _show_match_by_index
from tests.stubs import DummyBot, DummyFSM, FakeMessage


@pytest.mark.asyncio
async def test_resolve_username_prefers_profile_username(session):
    bot = DummyBot()
    state = DummyFSM()
    context = await CoreContext.create(bot, state)

    user = type("User", (), {"username": "known", "telegram_id": 42})()
    resolved = await _resolve_username(user, context)
    assert resolved == "@known"

    user_no_username = type("User", (), {"username": None, "telegram_id": 100})()
    bot.chat_usernames[user_no_username.telegram_id] = "from_chat"
    resolved_chat = await _resolve_username(user_no_username, context)
    assert resolved_chat == "@from_chat"


@pytest.mark.asyncio
async def test_show_match_by_index_renders_match(session):
    user_repo = UserRepository(session)
    phrases = Phrases()
    bot = DummyBot()
    state = DummyFSM()
    context = await CoreContext.create(bot, state)
    viewer = await user_repo.upsert_user(
        telegram_id=1,
        username="viewer",
        name="Viewer",
        sex="M",
        search_sex="F",
        language="ru",
        age=20,
        faculty_id="fkn",
        description="",
        photo_ids=["photo_viewer"],
    )

    partner = await user_repo.upsert_user(
        telegram_id=2,
        username="partner",
        name="Partner",
        sex="F",
        search_sex="M",
        language="ru",
        age=21,
        faculty_id="fen",
        description="",
        photo_ids=["photo_partner"],
    )

    match_repo = MatchRepository(session)
    await match_repo.set_reaction(viewer.id, partner.id, is_like=True)
    await match_repo.set_reaction(partner.id, viewer.id, is_like=True)

    event = FakeMessage(chat_id=5, message_id=1, from_user_id=viewer.telegram_id)
    await _show_match_by_index(event, context, phrases, match_repo, viewer, 0)

    assert bot.sent_photos or bot.sent_messages
