"""{{project_name}} Lakehouse package."""

from {{project_slug}}.secrets import get_secret
from {{project_slug}}.tuning import apply_spark_tuning_defaults, optimize_delta_table
from {{project_slug}}.logging import setup_pipeline_logging, pipeline_audit_step

__version__ = "0.1.0"
__all__ = [
    "get_secret",
    "apply_spark_tuning_defaults",
    "optimize_delta_table",
    "setup_pipeline_logging",
    "pipeline_audit_step",
]
