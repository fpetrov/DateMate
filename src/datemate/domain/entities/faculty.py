from __future__ import annotations

from pydantic import BaseModel


class Faculty(BaseModel):
    id: str
    name: str

    class Config:
        frozen = True
