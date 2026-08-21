"""Measure how wall time scales with the number of pool workers.

Each fake "book" just sleeps, standing in for download latency, so this
only tells you the pool itself scales and where returns start to
diminish. It says nothing about real scrapes - tune against an actual
mirror for that.

Usage: .venv/bin/python scripts/benchmark_concurrency.py [--books 64] [--latency-ms 30]
"""

import argparse
import time
from collections.abc import Callable

from gutenberg2zim.core.concurrency import parallel_map

CONCURRENCY_LEVELS = (1, 2, 4, 8, 16, 24, 32)


def make_workload(latency_s: float) -> Callable[[int], None]:
    def work(_book_index: int) -> None:
        time.sleep(latency_s)  # stands in for download latency per book

    return work


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--books", type=int, default=64)
    parser.add_argument("--latency-ms", type=float, default=30.0)
    args = parser.parse_args()

    latency_s = args.latency_ms / 1000.0
    work = make_workload(latency_s)
    serial_estimate = args.books * latency_s

    print(
        f"{args.books} books x {args.latency_ms:.0f}ms simulated latency "
        f"(serial estimate: {serial_estimate:.2f}s)"
    )
    header = f"{'workers':>7} | {'wall (s)':>8} | {'speedup':>7} | {'efficiency':>10}"
    print(header)
    print("-" * len(header))

    baseline = None
    for concurrency in CONCURRENCY_LEVELS:
        start = time.monotonic()
        parallel_map(work, range(args.books), concurrency)
        elapsed = time.monotonic() - start
        if baseline is None:
            baseline = elapsed
        speedup = baseline / elapsed
        efficiency = speedup / concurrency
        row = f"{concurrency:>7} | {elapsed:>8.2f} | {speedup:>6.1f}x"
        print(f"{row} | {efficiency:>9.0%}")


if __name__ == "__main__":
    main()
