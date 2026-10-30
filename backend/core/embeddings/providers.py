import hashlib
import math
import os
from typing import List
from core.embeddings.base import BaseEmbeddingProvider


class DeterministicLocalEmbeddingProvider(BaseEmbeddingProvider):
    """
    Offline, deterministic embedding provider using L2-normalized token & n-gram feature hashing.
    Enables immediate local testing and RAG development without external API costs or latency.
    """

    def __init__(self, dimension: int = 768, model_name: str = "deterministic-hash-768"):
        self._dim = dimension
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dim

    def _embed_single(self, text: str) -> List[float]:
        if not text.strip():
            return [0.0] * self._dim

        vector = [0.0] * self._dim
        words = text.lower().split()

        # Hash words and character n-grams into vector space
        for word in words:
            # Word feature
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
            vector[idx] += sign

            # 3-gram subword feature
            for i in range(len(word) - 2):
                gram = word[i : i + 3]
                gh = int(hashlib.sha256(gram.encode("utf-8")).hexdigest(), 16)
                g_idx = gh % self._dim
                g_sign = 1.0 if (gh >> 8) % 2 == 0 else -1.0
                vector[g_idx] += 0.5 * g_sign

        # L2 normalization
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [round(x / norm, 6) for x in vector]

        return vector

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_single(t) for t in texts]


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    OpenAI embedding provider using text-embedding-3-small or text-embedding-ada-002.
    """

    def __init__(
        self,
        api_key: str = None,
        model_name: str = "text-embedding-3-small",
        dimension: int = 1536,
    ):
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")
        self._model_name = model_name
        self._dim = dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        import urllib.request
        import json

        req_data = {
            "input": texts,
            "model": self._model_name,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        req = urllib.request.Request(
            "https://api.openai.com/v1/embeddings",
            data=json.dumps(req_data).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            embeddings = [item["embedding"] for item in data["data"]]
            return embeddings


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """
    Google GenAI / Gemini embedding provider (text-embedding-004).
    """

    def __init__(
        self,
        api_key: str = None,
        model_name: str = "text-embedding-004",
        dimension: int = 768,
    ):
        self._api_key = (
            api_key
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
        )
        if not self._api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is not configured.")
        self._model_name = model_name
        self._dim = dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        from google import genai

        client = genai.Client(api_key=self._api_key)
        results = []
        for text in texts:
            resp = client.models.embed_content(
                model=self._model_name,
                contents=text,
            )
            results.append(resp.embedding.values)
        return results
