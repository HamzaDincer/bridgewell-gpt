from typing import Literal

from injector import inject, singleton
from pydantic import BaseModel, Field

from bridgewell_gpt.components.embedding.embedding_component import EmbeddingComponent


class Embedding(BaseModel):
    index: int
    object: Literal["embedding"]
    embedding: list[float] = Field(examples=[[0.0023064255, -0.009327292]])


@singleton
class EmbeddingsService:
    @inject
    def __init__(self, embedding_component: EmbeddingComponent) -> None:
        self.embedding_component = embedding_component

    def texts_embeddings(self, texts: list[str]) -> list[Embedding]:
        texts_embeddings = self.embedding_component.get_embeddings(texts)
        return [
            Embedding(
                index=texts_embeddings.index(embedding),
                object="embedding",
                embedding=embedding,
            )
            for embedding in texts_embeddings
        ]
