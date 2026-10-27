
import json
import logging
import re

import httpx

from .base import BaseLLMClient

logger = logging.getLogger(__name__)

DEFAULT_OPTIONS = {
    "temperature": 0.7,
    "top_p": 0.9,
    "num_predict": 2048,
}

MAX_RETRIES = 1
RETRY_TOKEN_MULTIPLIER = 2
MAX_NUM_PREDICT = 8192


class ContentCleaner:
    @staticmethod
    def strip_think_tags(text: str) -> str:
        if not text:
            return text

        text = re.sub(
            r"<think>.*?</think>",
            "",
            text,
            flags=re.DOTALL,
        )

        return text.strip()


class OllamaClient(BaseLLMClient):
    """Async Ollama client with diagnostics and length-limit retry."""

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    @staticmethod
    def _options(options: dict | None) -> dict:
        result = {**DEFAULT_OPTIONS, **(options or {})}

        try:
            result["num_predict"] = max(
                1, int(result.get("num_predict", 2048))
            )
        except (TypeError, ValueError):
            result["num_predict"] = 2048

        return result

    @staticmethod
    def _clean_message(message: dict) -> dict:
        message = dict(message or {})
        content = message.get("content", "")

        if isinstance(content, str):
            message["content"] = ContentCleaner.strip_think_tags(content)

        return message

    async def chat(
        self,
        messages: list[dict],
        options: dict = None,
        tools: list = None,
    ) -> dict:
        opts = self._options(options)

        timeout = httpx.Timeout(
            connect=10.0,
            read=300.0,
            write=30.0,
            pool=10.0,
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            for attempt in range(MAX_RETRIES + 1):
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "think": False,
                    "options": opts,
                }

                if tools:
                    payload["tools"] = tools

                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                message = self._clean_message(data.get("message", {}))
                done_reason = data.get("done_reason", "unknown")
                content = message.get("content", "")

                # Diagnostic information for investigating short responses.
                logger.warning(
                    "OLLAMA DIAGNOSTIC: model=%s attempt=%d/%d "
                    "done=%s reason=%s num_predict=%s "
                    "prompt_tokens=%s output_tokens=%s response_chars=%d",
                    self.model,
                    attempt + 1,
                    MAX_RETRIES + 1,
                    data.get("done"),
                    done_reason,
                    opts["num_predict"],
                    data.get("prompt_eval_count"),
                    data.get("eval_count"),
                    len(content),
                )

                # Retry once if Ollama explicitly reports a length limit.
                # Do not retry tool calls because they may trigger duplicate actions.
                if (
                    done_reason == "length"
                    and not message.get("tool_calls")
                    and attempt < MAX_RETRIES
                    and opts["num_predict"] < MAX_NUM_PREDICT
                ):
                    opts["num_predict"] = min(
                        opts["num_predict"] * RETRY_TOKEN_MULTIPLIER,
                        MAX_NUM_PREDICT,
                    )

                    logger.warning(
                        "Ollama response hit its token limit; "
                        "retrying with num_predict=%d",
                        opts["num_predict"],
                    )
                    continue

                if done_reason == "length":
                    logger.warning(
                        "Ollama response may be incomplete: model=%s",
                        self.model,
                    )

                # Preserve metadata for callers that need to inspect the result.
                message["_done_reason"] = done_reason
                message["_done"] = data.get("done")

                return message

        raise RuntimeError("Ollama request ended without a response")

    async def chat_stream(
        self,
        messages: list[dict],
        options: dict = None,
        tools: list = None,
    ):
        opts = self._options(options)

        timeout = httpx.Timeout(
            connect=10.0,
            read=300.0,
            write=30.0,
            pool=10.0,
        )

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "think": False,
            "options": opts,
        }

        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        logger.warning(
                            "Skipping invalid JSON from Ollama stream"
                        )
                        continue

                    if data.get("done"):
                        logger.info(
                            "Ollama stream completed: model=%s "
                            "done_reason=%s num_predict=%s "
                            "prompt_tokens=%s output_tokens=%s",
                            self.model,
                            data.get("done_reason"),
                            opts["num_predict"],
                            data.get("prompt_eval_count"),
                            data.get("eval_count"),
                        )

                    yield data
