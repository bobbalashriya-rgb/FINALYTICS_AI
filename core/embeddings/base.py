from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingProvider(ABC):
    """
    Abstract interface for embedding generation providers.
    Allows configuring local, OpenAI, Gemini, or custom embeddings without altering indexing logic.
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """The identifier of the active embedding model."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """The dimensionality of output embedding vectors."""
        pass

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a batch of chunk texts."""
        pass

    def embed_query(self, text: str) -> List[float]:
        """Generates embedding for a single query text."""
        res = self.embed_texts([text])
        return res[0]
