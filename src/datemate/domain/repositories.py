from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from datemate.infrastructure.db import FacultyModel, LikeModel, MatchModel, UserModel


class FacultyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_faculties(self) -> list[FacultyModel]:
        result = await self.session.execute(select(FacultyModel))
        return list(result.scalars().all())

    async def get_by_id(self, faculty_id: str) -> FacultyModel | None:
        result = await self.session.execute(select(FacultyModel).where(FacultyModel.id == faculty_id))
        return result.scalars().first()


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> UserModel | None:
        result = await self.session.execute(select(UserModel).where(UserModel.telegram_id == telegram_id))
        return result.scalars().first()

    async def get_by_id(self, user_id: int) -> UserModel | None:
        result = await self.session.execute(
            select(UserModel).options(selectinload(UserModel.faculty)).where(UserModel.id == user_id)
        )
        return result.scalars().first()

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
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = UserModel(
                telegram_id=telegram_id,
                username=username,
                name=name,
                sex=sex,
                search_sex=search_sex,
                language=language,
                age=age,
                description=description,
                faculty_id=faculty_id,
                photo_ids="[]",
            )
            self.session.add(user)

        user.name = name
        user.sex = sex
        user.search_sex = search_sex
        user.language = language
        user.age = age
        user.description = description
        user.faculty_id = faculty_id
        user.username = username or user.username
        user.photos = photo_ids

        await self.session.commit()
        await self.session.refresh(user)
        return user


class MatchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_next_candidate(self, user: UserModel) -> UserModel | None:
        rated_subquery = select(LikeModel.target_id).where(LikeModel.liker_id == user.id)

        base_conditions = [
            UserModel.id != user.id,
            ~UserModel.id.in_(rated_subquery),
            UserModel.search_sex == user.sex,
        ]

        if user.search_sex:
            base_conditions.append(UserModel.sex == user.search_sex)

        prioritized_stmt = (
            select(UserModel)
            .join(LikeModel, LikeModel.liker_id == UserModel.id)
            .options(selectinload(UserModel.faculty))
            .where(
                LikeModel.target_id == user.id,
                LikeModel.is_like.is_(True),
                *base_conditions,
            )
            .order_by(func.random())
            .limit(1)
        )

        prioritized_candidate = (await self.session.execute(prioritized_stmt)).scalars().first()
        if prioritized_candidate:
            return prioritized_candidate

        stmt = (
            select(UserModel)
            .options(selectinload(UserModel.faculty))
            .where(*base_conditions)
            .order_by(func.random())
            .limit(1)
        )

        return (await self.session.execute(stmt)).scalars().first()

    async def set_reaction(self, liker_id: int, target_id: int, is_like: bool) -> tuple[LikeModel, bool]:
        existing = (
            await self.session.execute(
                select(LikeModel).where(
                    LikeModel.liker_id == liker_id,
                    LikeModel.target_id == target_id,
                )
            )
        ).scalars().first()

        if existing:
            existing.is_like = is_like
            like = existing
        else:
            like = LikeModel(liker_id=liker_id, target_id=target_id, is_like=is_like)
            self.session.add(like)

        await self.session.commit()
        await self.session.refresh(like)

        matched = False
        if is_like and await self._has_positive_reaction(target_id, liker_id):
            matched = await self._ensure_match(liker_id, target_id)

        return like, matched

    async def _has_positive_reaction(self, liker_id: int, target_id: int) -> bool:
        stmt = select(LikeModel).where(
            LikeModel.liker_id == liker_id,
            LikeModel.target_id == target_id,
            LikeModel.is_like.is_(True),
        )
        return (await self.session.execute(stmt)).scalars().first() is not None

    async def _ensure_match(self, user_a_id: int, user_b_id: int) -> bool:
        left_id, right_id = sorted((user_a_id, user_b_id))
        stmt = select(MatchModel).where(
            MatchModel.user_left_id == left_id,
            MatchModel.user_right_id == right_id,
        )
        existing = (await self.session.execute(stmt)).scalars().first()
        if existing:
            return False

        match = MatchModel(user_left_id=left_id, user_right_id=right_id)
        self.session.add(match)
        await self.session.commit()
        return True

    async def count_matches(self, user_id: int) -> int:
        stmt = select(func.count()).select_from(MatchModel).where(
            or_(MatchModel.user_left_id == user_id, MatchModel.user_right_id == user_id)
        )
        return (await self.session.execute(stmt)).scalar_one()

    async def list_matches(
        self, user_id: int, offset: int = 0, limit: int = 1
    ) -> tuple[list[tuple[MatchModel, UserModel]], int]:
        total = await self.count_matches(user_id)
        if total == 0:
            return [], 0

        stmt = (
            select(MatchModel)
            .where(or_(MatchModel.user_left_id == user_id, MatchModel.user_right_id == user_id))
            .order_by(MatchModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        matches = list((await self.session.execute(stmt)).scalars().all())
        if not matches:
            return [], total

        other_user_ids = [
            match.user_right_id if match.user_left_id == user_id else match.user_left_id
            for match in matches
        ]

        users = (
            await self.session.execute(
                select(UserModel)
                .options(selectinload(UserModel.faculty))
                .where(UserModel.id.in_(other_user_ids))
            )
        ).scalars().all()
        users_map = {user.id: user for user in users}

        pairs: list[tuple[MatchModel, UserModel]] = []
        for match, other_id in zip(matches, other_user_ids):
            other_user = users_map.get(other_id)
            if other_user:
                pairs.append((match, other_user))

        return pairs, total
