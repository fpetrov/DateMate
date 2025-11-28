from __future__ import annotations

import json
from typing import Iterable

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class FacultyModel(Base):
    __tablename__ = "faculties"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    users = relationship("UserModel", back_populates="faculty")


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    sex = Column(String(1), nullable=False)
    age = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    faculty_id = Column(String, ForeignKey("faculties.id"), nullable=False)
    faculty = relationship(FacultyModel, back_populates="users")
    photo_ids = Column(Text, nullable=False)

    @property
    def photos(self) -> list[str]:
        try:
            return json.loads(self.photo_ids)
        except json.JSONDecodeError:
            return []

    @photos.setter
    def photos(self, value: Iterable[str]):
        self.photo_ids = json.dumps(list(value))
