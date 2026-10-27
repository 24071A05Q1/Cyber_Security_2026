from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RetrievedDocument:
    source_id: str
    title: str
    content: str
    score: float


class Retriever(Protocol):
    def retrieve(self, query: str, category: str | None = None, top_k: int = 3) -> list[RetrievedDocument]: ...
