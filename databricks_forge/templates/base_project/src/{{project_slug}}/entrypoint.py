"""Executable entrypoint for running pipelines locally or on Databricks clusters."""

from __future__ import annotations

import argparse
import logging
import sys
from {{project_slug}}.session import get_spark
from {{project_slug}}.catalog import CatalogManager
from {{project_slug}}.pipelines.example_pipeline import run_lakehouse_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("{{project_slug}}.entrypoint")


def main():
    parser = argparse.ArgumentParser(description="Run {{project_name}} Lakehouse Pipeline")
    parser.add_argument(
        "--mode",
        choices=["local", "remote"],
        default=None,
        help="Execution mode (local or remote via Databricks Connect)",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=500,
        help="Number of synthetic rows to generate if running test pipeline",
    )
    args = parser.parse_args()

    logger.info("Initializing SparkSession (mode=%s)...", args.mode or "default from env")
    spark = get_spark(mode=args.mode)
    catalog = CatalogManager(spark)

    try:
        results = run_lakehouse_pipeline(spark=spark, catalog=catalog, row_count=args.rows)
        logger.info("Pipeline completed successfully! Summary: %s", results)
    except Exception as exc:
        logger.error("Pipeline failed: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
