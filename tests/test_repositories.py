import pytest

from datemate.domain.repositories import FacultyRepository, MatchRepository, UserRepository
from datemate.infrastructure.db import LikeModel


@pytest.mark.asyncio
async def test_default_faculties(session):
    repo = FacultyRepository(session)
    faculties = await repo.list_faculties()

    assert {f.id for f in faculties} >= {"fkn", "fen", "vsb", "fgn"}


@pytest.mark.asyncio
async def test_user_upsert_creates_and_updates(session):
    repo = UserRepository(session)

    created = await repo.upsert_user(
        telegram_id=1,
        username="first",
        name="Alice",
        sex="F",
        search_sex="M",
        language="ru",
        age=21,
        faculty_id="fkn",
        description="hello",
        photo_ids=["p1"],
    )

    assert created.id is not None
    assert created.photos == ["p1"]

    updated = await repo.upsert_user(
        telegram_id=1,
        username=None,
        name="Alice Updated",
        sex="F",
        search_sex="M",
        language="en",
        age=22,
        faculty_id="fen",
        description="updated",
        photo_ids=["p2", "p3"],
    )

    assert updated.id == created.id
    assert updated.name == "Alice Updated"
    assert updated.language == "en"
    assert updated.photos == ["p2", "p3"]


@pytest.mark.asyncio
async def test_prioritized_candidate_is_returned_first(session):
    user_repo = UserRepository(session)
    base_user = await user_repo.upsert_user(
        telegram_id=100,
        username="user100",
        name="User",
        sex="M",
        search_sex="F",
        language="ru",
        age=25,
        faculty_id="fkn",
        description="base",
        photo_ids=[],
    )

    prioritized = await user_repo.upsert_user(
        telegram_id=200,
        username="prio",
        name="Prioritized",
        sex="F",
        search_sex="M",
        language="ru",
        age=24,
        faculty_id="fen",
        description="likes base",
        photo_ids=[],
    )

    _ = await user_repo.upsert_user(
        telegram_id=300,
        username="regular",
        name="Regular",
        sex="F",
        search_sex="M",
        language="ru",
        age=24,
        faculty_id="fen",
        description="another",
        photo_ids=[],
    )

    session.add(LikeModel(liker_id=prioritized.id, target_id=base_user.id, is_like=True))
    await session.commit()

    match_repo = MatchRepository(session)
    candidate = await match_repo.get_next_candidate(base_user)

    assert candidate.id == prioritized.id


@pytest.mark.asyncio
async def test_set_reaction_creates_match_once(session):
    user_repo = UserRepository(session)
    alice = await user_repo.upsert_user(
        telegram_id=400,
        username="alice",
        name="Alice",
        sex="F",
        search_sex="M",
        language="ru",
        age=23,
        faculty_id="fgn",
        description="",
        photo_ids=[],
    )

    bob = await user_repo.upsert_user(
        telegram_id=500,
        username="bob",
        name="Bob",
        sex="M",
        search_sex="F",
        language="ru",
        age=24,
        faculty_id="vsb",
        description="",
        photo_ids=[],
    )

    match_repo = MatchRepository(session)

    _, first_match = await match_repo.set_reaction(alice.id, bob.id, is_like=True)
    assert first_match is False

    _, second_match = await match_repo.set_reaction(bob.id, alice.id, is_like=True)
    assert second_match is True

    _, repeat_match = await match_repo.set_reaction(alice.id, bob.id, is_like=True)
    assert repeat_match is False

    pairs, total = await match_repo.list_matches(alice.id, offset=0, limit=10)
    assert total == 1
    assert pairs[0][1].id == bob.id
