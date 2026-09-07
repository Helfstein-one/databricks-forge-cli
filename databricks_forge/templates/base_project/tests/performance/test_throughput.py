"""Performance and profiling tests to measure pipeline throughput before deployment."""

import time
import pytest
from {{project_slug}}.pipelines.example_pipeline import (
    generate_synthetic_bronze_data,
    clean_transactions,
    aggregate_daily_metrics,
)


def test_transformation_throughput(spark_session, benchmark=None):
    """Benchmarks the end-to-end transformation time on synthetic dataset."""
    raw_df = generate_synthetic_bronze_data(spark_session, row_count=2000).cache()
    raw_df.count()  # materialize

    def run_transformations():
        cleaned = clean_transactions(raw_df)
        gold = aggregate_daily_metrics(cleaned)
        return gold.count()

    if benchmark is not None:
        result_count = benchmark(run_transformations)
        assert result_count > 0
    else:
        start = time.perf_counter()
        count = run_transformations()
        elapsed = time.perf_counter() - start
        assert count > 0
        # Pipeline benchmark threshold: 2,000 rows should process in under 10 seconds locally
        assert elapsed < 10.0, f"Transformation took too long: {elapsed:.2f}s"
