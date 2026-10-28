
import asyncio
import logging
from typing import List, Dict

from src.llm.ollama_client import OllamaClient
from src.utils.db import SQLiteSessionManager

logger = logging.getLogger(__name__)


class MemorySummarizer:
    def __init__(self, db: SQLiteSessionManager, llm_client: OllamaClient):
        self.db = db
        self.llm_client = llm_client
        self.trigger_threshold = 15
        self._tasks: set[asyncio.Task] = set()
        self._session_locks: dict[str, asyncio.Lock] = {}

    async def _generate_summary(
        self, old_summary: str, recent_messages: List[Dict]
    ) -> str:
        prompt = """
You are a concise conversation summarizer for a supportive assistant.

Create an updated summary from the existing summary and recent conversation.
Preserve useful user preferences, goals, ongoing concerns, and agreed next steps.
Preserve personal names exactly as written in the conversation, including the original
script, spelling, and capitalization. Do not translate or transliterate names.
Do not invent facts or make clinical diagnoses.
Keep the summary brief and factual.

EXISTING SUMMARY:
{old}

RECENT MESSAGES:
{new}

UPDATED SUMMARY:
"""

        formatted_msgs = "\n".join(
            f"{m.get('role', 'unknown')}: {m.get('content', '')}"
            for m in recent_messages
        )

        final_prompt = prompt.format(
            old=old_summary or "No previous summary.",
            new=formatted_msgs,
        )

        try:
            response = await self.llm_client.chat(
                [{"role": "user", "content": final_prompt}]
            )

            if isinstance(response, dict):
                summary = response.get("content", "")
                if isinstance(summary, str) and summary.strip():
                    return summary.strip()

            logger.warning("Memory summarization returned an empty response.")
            return old_summary or ""

        except Exception:
            logger.exception("Failed to generate memory summary.")
            return old_summary or ""

    async def maybe_summarize(self, session_id: str):
        """Schedule summarization without blocking the chat response."""
        try:
            task = asyncio.create_task(
                self._process_summarization(session_id)
            )
            self._tasks.add(task)
            task.add_done_callback(self._on_task_done)
        except Exception:
            logger.exception("Could not schedule memory summarization.")

    def _on_task_done(self, task: asyncio.Task):
        """Remove completed tasks and log unexpected background failures."""
        self._tasks.discard(task)

        if task.cancelled():
            return

        try:
            error = task.exception()
            if error is not None:
                logger.error(
                    "Background summarization task failed.",
                    exc_info=(type(error), error, error.__traceback__),
                )
        except Exception:
            logger.exception("Could not inspect summarization task.")

    async def close(self):
        """Wait for outstanding summaries during server shutdown."""
        tasks = tuple(self._tasks)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_summarization(self, session_id: str):
        lock = self._session_locks.setdefault(
            session_id, asyncio.Lock()
        )

        async with lock:
            await self._process_summarization_locked(session_id)

    async def _process_summarization_locked(self, session_id: str):
        try:
            message_count = (
                self.db.get_message_count_since_last_summary(session_id)
            )

            if message_count < self.trigger_threshold:
                return

            old_summary = self.db.get_session_summary(session_id) or ""
            messages = self.db.get_unsummarized_messages(session_id)

            if not messages:
                return

            logger.info(
                "Summarizing %d messages for session %s",
                len(messages),
                session_id,
            )

            new_summary = await self._generate_summary(
                old_summary, messages
            )

            if new_summary and new_summary != old_summary:
                self.db.save_session_summary(session_id, new_summary)
                logger.info(
                    "Saved new memory summary for session %s",
                    session_id,
                )

        except Exception:
            logger.exception(
                "Error in background summarization process for session %s",
                session_id,
            )
