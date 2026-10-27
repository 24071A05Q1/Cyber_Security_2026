from __future__ import annotations

from functools import lru_cache

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.config import settings
from src.retrieval.base import RetrievedDocument


class LocalRunbookRetriever:
    def __init__(self) -> None:
        self.df = pd.read_csv(settings.runbook_path)
        corpus = (self.df["title"] + " " + self.df["content"] + " " + self.df["category"]).tolist()
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self.matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(self, query: str, category: str | None = None, top_k: int = 3) -> list[RetrievedDocument]:
        query_vector = self.vectorizer.transform([f"{query} {category or ''}"])
        scores = cosine_similarity(query_vector, self.matrix)[0]
        candidate_indices = list(range(len(self.df)))
        if category:
            matching = [idx for idx in candidate_indices if self.df.iloc[idx]["category"] == category]
            if matching:
                candidate_indices = matching
        ranked = sorted(candidate_indices, key=lambda idx: scores[idx], reverse=True)
        results: list[RetrievedDocument] = []
        for idx in ranked[:top_k]:
            row = self.df.iloc[int(idx)]
            results.append(RetrievedDocument(
                source_id=str(row["source_id"]),
                title=str(row["title"]),
                content=str(row["content"]),
                score=float(scores[int(idx)]),
            ))
        return results


@lru_cache(maxsize=1)
def get_local_retriever() -> LocalRunbookRetriever:
    return LocalRunbookRetriever()
