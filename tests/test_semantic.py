"""Unit tests for the Semantic Layer module."""

import pytest
from pathlib import Path
from databricks_forge.semantic.models import Dimension, Metric, Relationship, Entity, SemanticSchema
from databricks_forge.semantic.registry import SemanticRegistry
from databricks_forge.semantic.introspector import CatalogIntrospector
from databricks_forge.semantic.compiler import SemanticCompiler


def test_semantic_models_serialization():
    dim = Dimension(name="customer_id", column="customer_id", data_type="string", description="Customer PK")
    metric = Metric(name="total_revenue", formula="amount", aggregation="SUM", description="Total Revenue")
    rel = Relationship(from_entity="orders", to_entity="customers", join_type="LEFT", join_condition="orders.c_id = customers.id")

    entity = Entity(
        name="orders",
        catalog="main",
        schema="retail",
        table_name="orders",
        medallion_layer="silver",
        dimensions=[dim],
        metrics=[metric],
        relationships=[rel],
    )

    schema = SemanticSchema(name="retail_model", entities=[entity])
    data = schema.to_dict()

    reloaded = SemanticSchema.from_dict(data)
    assert reloaded.name == "retail_model"
    assert len(reloaded.entities) == 1
    assert reloaded.entities[0].name == "orders"
    assert reloaded.entities[0].dimensions[0].column == "customer_id"
    assert reloaded.entities[0].metrics[0].formula == "amount"
    assert reloaded.entities[0].full_table_name == "main.retail.orders"


def test_semantic_registry_save_load_and_mermaid(tmp_path: Path):
    yaml_path = tmp_path / "semantic_model.yaml"
    introspector = CatalogIntrospector()
    entities = introspector.introspect_catalog(catalog="main", schema="default")

    schema = SemanticSchema(name="test_schema", entities=entities)
    registry = SemanticRegistry(schema=schema, file_path=yaml_path)
    registry.save()

    assert yaml_path.exists()

    loaded = SemanticRegistry.load(yaml_path)
    assert len(loaded.list_entities()) == 3
    assert loaded.get_entity("silver_transactions") is not None

    erd = loaded.to_mermaid_erd()
    assert "erDiagram" in erd
    assert "silver_transactions" in erd

    lineage = loaded.to_mermaid_lineage()
    assert "graph LR" in lineage
    assert "Camada Bronze" in lineage
    assert "Camada Gold" in lineage


def test_semantic_compiler():
    introspector = CatalogIntrospector()
    entities = introspector.introspect_catalog()
    schema = SemanticSchema(entities=entities)
    compiler = SemanticCompiler(schema)

    query = compiler.compile_query(
        entity_name="silver_transactions",
        dimensions=["product_category", "payment_method"],
        metrics=["total_revenue", "avg_ticket"],
        filters=["status = 'COMPLETED'"],
        order_by="total_revenue DESC",
        limit=50
    )

    assert "SELECT" in query["sql"]
    assert "FROM main.default.silver_transactions" in query["sql"]
    assert "SUM(amount) AS total_revenue" in query["sql"]
    assert "WHERE status = 'COMPLETED'" in query["sql"]
    assert "GROUP BY product_category, payment_method" in query["sql"]
    assert "ORDER BY total_revenue DESC" in query["sql"]
    assert "LIMIT 50;" in query["sql"]


def test_semantic_compiler_unknown_entity_raises():
    schema = SemanticSchema()
    compiler = SemanticCompiler(schema)
    with pytest.raises(ValueError, match="não encontrada no catálogo semântico"):
        compiler.compile_query(entity_name="non_existent")
