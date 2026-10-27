from __future__ import annotations

import boto3

from src.config import settings
from src.retrieval.base import RetrievedDocument


class BedrockKnowledgeBaseRetriever:
    def __init__(self) -> None:
        if not settings.bedrock_knowledge_base_id:
            raise ValueError("BEDROCK_KNOWLEDGE_BASE_ID is required for Bedrock mode.")
        self.client = boto3.client("bedrock-agent-runtime", region_name=settings.aws_region)

    def retrieve(self, query: str, category: str | None = None, top_k: int = 3) -> list[RetrievedDocument]:
        enriched_query = f"Incident category: {category}. {query}" if category else query
        response = self.client.retrieve(
            knowledgeBaseId=settings.bedrock_knowledge_base_id,
            retrievalQuery={"text": enriched_query},
            retrievalConfiguration={
                "vectorSearchConfiguration": {"numberOfResults": top_k}
            },
        )
        documents: list[RetrievedDocument] = []
        for index, item in enumerate(response.get("retrievalResults", []), start=1):
            location = item.get("location", {})
            uri = (
                location.get("s3Location", {}).get("uri")
                or location.get("webLocation", {}).get("url")
                or f"bedrock-source-{index}"
            )
            content = item.get("content", {}).get("text", "")
            documents.append(RetrievedDocument(
                source_id=uri,
                title=uri.rsplit("/", 1)[-1],
                content=content,
                score=float(item.get("score", 0.0)),
            ))
        return documents
