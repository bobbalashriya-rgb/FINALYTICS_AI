from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseLLMProvider(ABC):
    """
    Abstract interface for LLM providers used for evidence-grounded fundamental analysis.
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the underlying LLM model."""
        pass

    @abstractmethod
    def generate_analysis(
        self,
        system_instruction: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Generates a structured JSON response conforming to the research analysis schema.
        """
        pass
