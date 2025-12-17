from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from datemate.infrastructure.db.models import FacultyModel


class Faculty(BaseModel):
    id: str
    name: str

    model_config = ConfigDict(frozen=True)

    @classmethod
    def from_model(cls, model: "FacultyModel") -> "Faculty":
        return cls(id=model.id, name=model.name)
