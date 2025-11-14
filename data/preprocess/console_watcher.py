# console_watcher.py
from __future__ import annotations

from threading import Lock
from typing import Optional
import logging
from tqdm.auto import tqdm

_progress_bar: Optional[tqdm] = None
_lock = Lock()


class TqdmLoggingHandler(logging.Handler):
    """
    Logging handler that plays nicely with tqdm progress bars.
    """
    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            tqdm.write(msg)
        except Exception:
            self.handleError(record)

_logger = logging.getLogger("preprocess")

def log(msg: str, level: int = logging.INFO) -> None:
    _logger.log(level, msg)

def start_progress(total: int, desc: str = "Processing files") -> None:
    global _progress_bar
    with _lock:
        if _progress_bar is not None:
            _progress_bar.close()
        _progress_bar = tqdm(total=total, desc=desc)

def advance_progress(n: int = 1) -> None:
    with _lock:
        if _progress_bar is not None:
            _progress_bar.update(n)

def end_progress() -> None:
    global _progress_bar
    with _lock:
        if _progress_bar is not None:
            _progress_bar.close()
            _progress_bar = None
