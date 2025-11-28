from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from datemate.infrastructure.db import FacultyModel, UserModel


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

    async def upsert_user(self,
                          telegram_id: int,
                          name: str,
                          sex: str,
                          age: int,
                          faculty_id: str,
                          description: str,
                          photo_ids: list[str]) -> UserModel:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = UserModel(
                telegram_id=telegram_id,
                name=name,
                sex=sex,
                age=age,
                description=description,
                faculty_id=faculty_id,
                photo_ids="[]",
            )
            self.session.add(user)

        user.name = name
        user.sex = sex
        user.age = age
        user.description = description
        user.faculty_id = faculty_id
        user.photos = photo_ids

        await self.session.commit()
        await self.session.refresh(user)
        return user
