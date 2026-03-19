import logging
import os
import uuid
from contextlib import contextmanager
from time import perf_counter
from typing import Iterator


def profiling_enabled() -> bool:
    """
    Toggle profiling logs with env var:
    RAG_PROFILE_LOGGING=1 (default on), set 0/false/off to disable.
    """
    raw = os.getenv("RAG_PROFILE_LOGGING", "1").strip().lower()
    return raw not in {"0", "false", "off", "no"}


def new_request_id() -> str:
    return str(uuid.uuid4())


@contextmanager
def stage_timer(
    logger: logging.Logger,
    stage: str,
    request_id: str,
    **fields: object,
) -> Iterator[None]:
    start = perf_counter()
    try:
        yield
    finally:
        if profiling_enabled():
            elapsed_s = perf_counter() - start
            meta = " ".join(f"{k}={v}" for k, v in fields.items())
            suffix = f" {meta}" if meta else ""
            logger.info("[rag_profile] request_id=%s stage=%s elapsed_s=%.3f%s", request_id, stage, elapsed_s, suffix)
