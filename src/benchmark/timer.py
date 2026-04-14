"""Timing utility using time.perf_counter() as specified in the measurement contract."""

import time


class PerfTimer:
    """Context manager that records elapsed wall-clock time in milliseconds."""

    def __init__(self):
        self.start: float = 0.0
        self.end: float = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end = time.perf_counter()
        self.elapsed_ms = (self.end - self.start) * 1000


def perf_counter_ms() -> float:
    """Return current perf_counter reading in milliseconds."""
    return time.perf_counter() * 1000
