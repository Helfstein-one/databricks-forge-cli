"""Tests for Databricks compute and machine specifications module."""

import pytest
from databricks_forge.core.compute import (
    COMPUTE_CATALOG,
    ComputeConfig,
    get_available_node_types,
)


def test_get_available_node_types():
    aws_nodes = get_available_node_types("aws")
    assert len(aws_nodes) >= 3
    node_ids = [n.node_type_id for n in aws_nodes]
    assert "i3.xlarge" in node_ids
    assert "m5d.large" in node_ids

    ce_nodes = get_available_node_types("ce")
    assert any(n.node_type_id == "SingleNode" for n in ce_nodes)


def test_compute_config_single_node_ce():
    cfg = ComputeConfig(cloud="ce", num_workers=0)
    assert cfg.single_node is True
    assert cfg.num_workers == 0

    spec = cfg.to_databricks_cluster_spec()
    assert spec["num_workers"] == 0
    assert spec["custom_tags"]["ResourceClass"] == "SingleNode"
    assert spec["spark_conf"]["spark.master"] == "local[*]"


def test_compute_config_multi_node_autoscale():
    cfg = ComputeConfig(
        cloud="aws",
        node_type_id="i3.xlarge",
        num_workers=4,
        autoscale={"min_workers": 2, "max_workers": 8},
        spark_version="14.3.x-scala2.12",
    )
    assert cfg.single_node is False
    spec = cfg.to_databricks_cluster_spec()
    assert spec["node_type_id"] == "i3.xlarge"
    assert spec["autoscale"] == {"min_workers": 2, "max_workers": 8}
    assert spec["spark_version"] == "14.3.x-scala2.12"
