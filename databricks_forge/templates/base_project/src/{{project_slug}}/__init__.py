"""{{project_name}} Lakehouse package."""

from {{project_slug}}.secrets import get_secret
from {{project_slug}}.tuning import apply_spark_tuning_defaults, optimize_delta_table
from {{project_slug}}.logging import setup_pipeline_logging, pipeline_audit_step
from {{project_slug}}.formats import read_dataset, write_dataset, convert_dataset
from {{project_slug}}.iceberg import enable_delta_uniform, read_iceberg_table
from {{project_slug}}.connectors import read_database_table, write_database_table

__version__ = "0.1.0"
__all__ = [
    "get_secret",
    "apply_spark_tuning_defaults",
    "optimize_delta_table",
    "setup_pipeline_logging",
    "pipeline_audit_step",
    "read_dataset",
    "write_dataset",
    "convert_dataset",
    "enable_delta_uniform",
    "read_iceberg_table",
    "read_database_table",
    "write_database_table",
]
