"""Utility functions for logging and progress tracking"""

import os
import time
import logging
from datetime import datetime, timedelta


class ProgressTracker:
    """Track scraping progress with ETA calculation"""

    def __init__(self, total, log_dir="."):
        self.total = total
        self.processed = 0
        self.start_time = time.time()
        self.last_log_time = time.time()
        self.current_item = ""
        self.current_page = 0
        self.log_dir = log_dir

    def update(self, processed, current_item="", current_page=0):
        self.processed = processed
        if current_item:
            self.current_item = current_item
        if current_page:
            self.current_page = current_page

    def get_eta(self):
        if self.processed == 0:
            return "calculating..."
        elapsed = time.time() - self.start_time
        rate = self.processed / elapsed
        remaining = (self.total - self.processed) / rate if rate > 0 else 0
        eta = datetime.now() + timedelta(seconds=remaining)
        return eta.strftime("%H:%M:%S")

    def get_progress_line(self):
        pct = (self.processed / self.total * 100) if self.total > 0 else 0
        eta = self.get_eta()
        return (
            f"[{self.processed}/{self.total}] {pct:.1f}% | "
            f"Page: {self.current_page} | "
            f"Current: {self.current_item[:40]:40s} | "
            f"ETA: {eta}"
        )


def setup_logging(log_dir="."):
    os.makedirs(log_dir, exist_ok=True)

    success_logger = logging.getLogger("success")
    success_logger.setLevel(logging.INFO)
    fh = logging.FileHandler(os.path.join(log_dir, "success.log"), encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    success_logger.addHandler(fh)

    failed_logger = logging.getLogger("failed")
    failed_logger.setLevel(logging.WARNING)
    fh2 = logging.FileHandler(os.path.join(log_dir, "failed.log"), encoding="utf-8")
    fh2.setFormatter(logging.Formatter("%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    failed_logger.addHandler(fh2)

    progress_logger = logging.getLogger("progress")
    progress_logger.setLevel(logging.INFO)
    fh3 = logging.FileHandler(os.path.join(log_dir, "progress.log"), encoding="utf-8")
    fh3.setFormatter(logging.Formatter("%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    progress_logger.addHandler(fh3)

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(message)s"))
    progress_logger.addHandler(console)

    return success_logger, failed_logger, progress_logger
