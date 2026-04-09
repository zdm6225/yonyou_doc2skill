"""
Performance benchmarking suite for Yonyou Doc2Skill.

Measures and analyzes performance of:
- Documentation scraping
- Embedding generation
- Storage operations
- End-to-end workflows

Features:
- Accurate timing measurements
- Memory usage tracking
- CPU profiling
- Comparison reports
- Optimization recommendations

Usage:
    from yonyou_doc2skill.benchmark import Benchmark

    # Create benchmark
    benchmark = Benchmark("scraping-test")

    # Time operations
    with benchmark.timer("scrape_pages"):
        scrape_docs(config)

    # Generate report
    report = benchmark.report()
"""

from .framework import Benchmark, BenchmarkResult
from .runner import BenchmarkRunner
from .models import BenchmarkReport, Metric

__all__ = [
    "Benchmark",
    "BenchmarkResult",
    "BenchmarkRunner",
    "BenchmarkReport",
    "Metric",
]
