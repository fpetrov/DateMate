from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from datemate.infrastructure.db import FacultyModel, LikeModel, MatchModel, UserModel


class FacultyRepository(Protocol):
    async def list_faculties(self) -> list[FacultyModel]:
        ...

    async def get_by_id(self, faculty_id: str) -> FacultyModel | None:
        ...


class UserRepository(Protocol):
    async def get_by_telegram_id(self, telegram_id: int) -> UserModel | None:
        ...

    async def get_by_id(self, user_id: int) -> UserModel | None:
        ...

    async def upsert_user(
        self,
        telegram_id: int,
        username: str | None,
        name: str,
        sex: str,
        search_sex: str,
        language: str,
        age: int,
        faculty_id: str,
        description: str,
        photo_ids: list[str],
    ) -> UserModel:
        ...


class MatchRepository(Protocol):
    async def get_next_candidate(self, user: UserModel) -> UserModel | None:
        ...

    async def set_reaction(self, liker_id: int, target_id: int, is_like: bool) -> tuple[LikeModel, bool]:
        ...

    async def count_matches(self, user_id: int) -> int:
        ...

    async def list_matches(
        self, user_id: int, offset: int = 0, limit: int = 1
    ) -> tuple[list[tuple[MatchModel, UserModel]], int]:
        ...
