from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from datemate.infrastructure.db import Base, FacultyModel


def create_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, echo=False, future=True)


async def init_db(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        existing = await session.execute(select(FacultyModel.id))
        existing_ids = {row[0] for row in existing.all()}

        default_faculties = {
            "fkn": "ФКН",
            "fen": "ФЭН",
            "vsb": "ВШБ",
            "fgn": "ФГН",
        }

        for faculty_id, name in default_faculties.items():
            if faculty_id not in existing_ids:
                session.add(FacultyModel(id=faculty_id, name=name))

        await session.commit()

    return session_factory
