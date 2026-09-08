"""Compute and machine specification catalog and configurations for Databricks clusters."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NodeTypeInfo:
    node_type_id: str
    category: str
    vcpus: int
    memory_gb: float
    description: str


# Catalog of standard Databricks supported machine types per cloud provider
COMPUTE_CATALOG: Dict[str, List[NodeTypeInfo]] = {
    "ce": [
        NodeTypeInfo("SingleNode", "Community Edition", 2, 15.3, "Community Edition Free Tier Single-Node (1 driver, 0 workers)"),
    ],
    "aws": [
        NodeTypeInfo("i3.xlarge", "Storage Optimized", 4, 30.5, "Fast local NVMe SSD, great for Delta Lake cache"),
        NodeTypeInfo("m5d.large", "General Purpose", 2, 8.0, "Cost-effective small pipeline node"),
        NodeTypeInfo("m5d.xlarge", "General Purpose", 4, 16.0, "Balanced general purpose data engineering node"),
        NodeTypeInfo("c5.xlarge", "Compute Optimized", 4, 8.0, "High CPU compute-bound workloads"),
        NodeTypeInfo("r5.xlarge", "Memory Optimized", 4, 32.0, "High memory for wide transformations and joins"),
    ],
    "azure": [
        NodeTypeInfo("Standard_DS3_v2", "General Purpose", 4, 14.0, "Standard general purpose compute node"),
        NodeTypeInfo("Standard_D4s_v5", "General Purpose", 4, 16.0, "Modern balanced engineering VM"),
        NodeTypeInfo("Standard_E4ds_v4", "Memory Optimized", 4, 32.0, "High memory for large cache & aggregations"),
        NodeTypeInfo("Standard_F4s_v2", "Compute Optimized", 4, 8.0, "High clock speed compute node"),
    ],
    "gcp": [
        NodeTypeInfo("n1-standard-4", "General Purpose", 4, 15.0, "Standard Google Cloud compute node"),
        NodeTypeInfo("n2-highmem-4", "Memory Optimized", 4, 32.0, "Memory optimized GCP compute node"),
        NodeTypeInfo("c2-standard-4", "Compute Optimized", 4, 16.0, "Compute optimized high performance node"),
    ],
}


DEFAULT_SPARK_VERSION = "14.3.x-scala2.12"


@dataclass
class ComputeConfig:
    """Represents the Databricks cluster / machine compute specification."""

    cloud: str = "ce"
    node_type_id: str = "SingleNode"
    driver_node_type_id: Optional[str] = None
    spark_version: str = DEFAULT_SPARK_VERSION
    single_node: bool = True
    num_workers: int = 0
    autoscale: Optional[Dict[str, int]] = None
    custom_tags: Dict[str, str] = field(default_factory=dict)
    spark_conf: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        self.cloud = self.cloud.lower().strip()
        if self.cloud not in COMPUTE_CATALOG:
            # Fallback to aws if unknown
            self.cloud = "ce" if self.single_node else "aws"

        # If CE or 0 workers, enforce single_node configuration
        if self.cloud == "ce" or self.num_workers == 0:
            self.single_node = True
            self.num_workers = 0
        else:
            self.single_node = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ComputeConfig:
        """Constructs ComputeConfig from a dictionary (e.g. from workflow.yaml)."""
        cloud = data.get("cloud", "ce").lower()
        node_type = data.get("node_type_id", "SingleNode" if cloud == "ce" else "m5d.large")
        driver_node = data.get("driver_node_type_id")
        spark_ver = data.get("spark_version", DEFAULT_SPARK_VERSION)
        num_workers = int(data.get("num_workers", 0))
        single_node = bool(data.get("single_node", num_workers == 0))
        autoscale = data.get("autoscale")
        tags = data.get("custom_tags", {})
        conf = data.get("spark_conf", {})

        return cls(
            cloud=cloud,
            node_type_id=node_type,
            driver_node_type_id=driver_node,
            spark_version=spark_ver,
            single_node=single_node,
            num_workers=num_workers,
            autoscale=autoscale,
            custom_tags=tags,
            spark_conf=conf,
        )

    def to_databricks_cluster_spec(self) -> Dict[str, Any]:
        """Generates the native Databricks new_cluster JSON spec for Jobs API v2.1."""
        tags = dict(self.custom_tags)
        spark_conf = dict(self.spark_conf)

        spec: Dict[str, Any] = {
            "spark_version": self.spark_version,
            "node_type_id": self.node_type_id,
            "custom_tags": tags,
            "spark_conf": spark_conf,
        }

        if self.driver_node_type_id:
            spec["driver_node_type_id"] = self.driver_node_type_id

        if self.single_node:
            tags["ResourceClass"] = "SingleNode"
            spark_conf["spark.master"] = "local[*]"
            spark_conf["spark.databricks.cluster.profile"] = "singleNode"
            spec["num_workers"] = 0
        elif self.autoscale and "min_workers" in self.autoscale and "max_workers" in self.autoscale:
            spec["autoscale"] = {
                "min_workers": self.autoscale["min_workers"],
                "max_workers": self.autoscale["max_workers"],
            }
        else:
            spec["num_workers"] = max(1, self.num_workers)

        return spec

    def to_yaml_dict(self) -> Dict[str, Any]:
        """Returns clean dict representation for YAML configs."""
        res: Dict[str, Any] = {
            "cloud": self.cloud,
            "node_type_id": self.node_type_id,
            "spark_version": self.spark_version,
            "single_node": self.single_node,
            "num_workers": self.num_workers,
        }
        if self.driver_node_type_id:
            res["driver_node_type_id"] = self.driver_node_type_id
        if self.autoscale:
            res["autoscale"] = self.autoscale
        return res


def get_available_node_types(cloud: str = "aws") -> List[NodeTypeInfo]:
    """Returns available node types for a given cloud provider."""
    return COMPUTE_CATALOG.get(cloud.lower(), COMPUTE_CATALOG["aws"])
