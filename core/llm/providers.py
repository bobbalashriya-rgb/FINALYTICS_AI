import json
import logging
import os
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

from core.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class GeminiLLMProvider(BaseLLMProvider):
    """
    Google Gemini LLM provider using the direct official Generative Language REST API.
    Uses structured JSON generation mode.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash",
    ):
        self._api_key = (
            api_key
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
        )
        if not self._api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is not configured.")
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate_analysis(
        self,
        system_instruction: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model_name}:generateContent?key={self._api_key}"
        )
        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}],
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "response_mime_type": "application/json",
            },
        }

        req_data = json.dumps(payload).encode("utf-8")
        max_attempts = 3
        last_err = None

        for attempt in range(1, max_attempts + 1):
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=45) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise RuntimeError("Gemini returned empty candidates list.")
                    text_content = candidates[0]["content"]["parts"][0]["text"]
                    return json.loads(text_content)
            except urllib.error.HTTPError as exc:
                err_msg = exc.read().decode("utf-8")
                last_err = exc
                if exc.code in (429, 500, 502, 503, 504) and attempt < max_attempts:
                    sleep_time = 1.0 * (2 ** (attempt - 1))
                    logger.warning(
                        "Gemini API transient error (%d): %s. Retrying in %.1fs (attempt %d/%d)...",
                        exc.code,
                        err_msg,
                        sleep_time,
                        attempt,
                        max_attempts,
                    )
                    import time
                    time.sleep(sleep_time)
                    continue

                logger.error("Gemini API error (%d): %s", exc.code, err_msg)
                raise RuntimeError(f"Gemini API request failed ({exc.code}): {err_msg}") from exc
            except Exception as exc:
                last_err = exc
                if attempt < max_attempts:
                    import time
                    time.sleep(1.0)
                    continue
                logger.exception("Failed to generate analysis via Gemini: %s", exc)
                raise RuntimeError(f"Gemini LLM generation failed: {exc}") from exc

        raise RuntimeError(f"Gemini LLM generation failed after {max_attempts} attempts: {last_err}")


class OpenAILLMProvider(BaseLLMProvider):
    """
    OpenAI LLM provider using chat completions with JSON mode.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4o-mini",
    ):
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate_analysis(
        self,
        system_instruction: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": self._model_name,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt},
            ],
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choice = data["choices"][0]
                text_content = choice["message"]["content"]
                return json.loads(text_content)
        except urllib.error.HTTPError as exc:
            err_msg = exc.read().decode("utf-8")
            logger.error("OpenAI API error (%d): %s", exc.code, err_msg)
            raise RuntimeError(f"OpenAI API request failed ({exc.code}): {err_msg}") from exc
        except Exception as exc:
            logger.exception("Failed to generate analysis via OpenAI: %s", exc)
            raise RuntimeError(f"OpenAI LLM generation failed: {exc}") from exc


class MockLLMProvider(BaseLLMProvider):
    """
    Offline, deterministic LLM provider for CI and testing without external API keys.
    Synthesizes grounded qualitative analysis using the supplied evidence passages.
    """

    def __init__(self, model_name: str = "mock-analyst-v1"):
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate_analysis(
        self,
        system_instruction: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        # Parse chunk IDs from prompt to construct verifiably grounded citations
        import re

        chunk_matches = re.findall(r"\[Chunk\s+#(\d+)\]", user_prompt)
        cited_ids = [int(cid) for cid in chunk_matches]

        return {
            "executive_summary": (
                "Based strictly on retrieved corporate disclosures, the company maintains steady "
                "operational momentum while navigating documented client budget and macroeconomic headwinds."
            ),
            "key_findings": [
                {
                    "claim": "Company disclosures highlight resilient operational performance and digital growth.",
                    "category": "reported_fact",
                    "chunk_ids": cited_ids[:2] if cited_ids else [],
                    "quote": "Disclosures indicate stable operating metrics.",
                },
                {
                    "claim": "Leadership emphasized deal pipeline health and strategic expansion priorities.",
                    "category": "management_statement",
                    "chunk_ids": cited_ids[1:3] if len(cited_ids) > 1 else cited_ids[:1],
                    "quote": "Management highlighted robust long-term demand drivers.",
                },
                {
                    "claim": "Margin preservation remains dependent on high-value digital contract renewals.",
                    "category": "analytical_interpretation",
                    "chunk_ids": cited_ids[:1] if cited_ids else [],
                    "quote": "Operating margins reflect mix shift toward digital solutions.",
                },
            ],
            "risks_and_uncertainties": [
                "Macroeconomic caution and client budget consolidation in key western markets.",
                "Wage inflation and competitive pricing pressure on legacy service agreements.",
            ],
            "missing_information_and_limitations": [
                "Granular divisional margin breakdowns were not disclosed in the retrieved passages.",
                "Long-term multi-year guidance was absent from the available excerpts.",
            ],
        }
