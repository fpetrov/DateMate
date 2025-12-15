from __future__ import annotations

import json
from typing import Iterable

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
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
    telegram_id = Column(BigInteger, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    sex = Column(String(1), nullable=False)
    search_sex = Column(String(1), nullable=False)
    language = Column(String(2), nullable=False, default="ru")
    age = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    username = Column(String, nullable=True)
    faculty_id = Column(String, ForeignKey("faculties.id"), nullable=False)
    faculty = relationship(FacultyModel, back_populates="users")
    photo_ids = Column(Text, nullable=False)
    likes_sent = relationship(
        "LikeModel", foreign_keys="LikeModel.liker_id", back_populates="liker"
    )
    likes_received = relationship(
        "LikeModel", foreign_keys="LikeModel.target_id", back_populates="target"
    )
    matches_as_left = relationship(
        "MatchModel",
        foreign_keys="MatchModel.user_left_id",
        back_populates="user_left",
    )
    matches_as_right = relationship(
        "MatchModel",
        foreign_keys="MatchModel.user_right_id",
        back_populates="user_right",
    )

    @property
    def photos(self) -> list[str]:
        try:
            return json.loads(self.photo_ids)
        except json.JSONDecodeError:
            return []

    @photos.setter
    def photos(self, value: Iterable[str]):
        self.photo_ids = json.dumps(list(value))


class LikeModel(Base):
    __tablename__ = "likes"
    __table_args__ = (
        UniqueConstraint("liker_id", "target_id", name="uq_likes_pair"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    liker_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_like = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    liker = relationship("UserModel", foreign_keys=[liker_id], back_populates="likes_sent")
    target = relationship(
        "UserModel", foreign_keys=[target_id], back_populates="likes_received"
    )


class MatchModel(Base):
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("user_left_id", "user_right_id", name="uq_matches_pair"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_left_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_right_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user_left = relationship(
        "UserModel", foreign_keys=[user_left_id], back_populates="matches_as_left"
    )
    user_right = relationship(
        "UserModel", foreign_keys=[user_right_id], back_populates="matches_as_right"
    )
