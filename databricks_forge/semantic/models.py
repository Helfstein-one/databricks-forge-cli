"""Semantic Layer Data Models for Databricks Forge CLI."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class Dimension:
    """A qualitative dimension for filtering, slicing, or grouping."""
    name: str
    column: str
    data_type: str = "string"
    description: str = ""
    expression: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Dimension:
        return cls(
            name=data["name"],
            column=data.get("column", data["name"]),
            data_type=data.get("data_type", "string"),
            description=data.get("description", ""),
            expression=data.get("expression"),
        )


@dataclass
class Metric:
    """A quantitative business metric calculation."""
    name: str
    formula: str
    aggregation: str = "SUM"
    description: str = ""
    format_type: str = "currency"  # currency, percentage, integer, float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Metric:
        return cls(
            name=data["name"],
            formula=data.get("formula", ""),
            aggregation=data.get("aggregation", "SUM"),
            description=data.get("description", ""),
            format_type=data.get("format_type", "currency"),
        )


@dataclass
class Relationship:
    """Relational join between two semantic entities."""
    from_entity: str
    to_entity: str
    join_type: str = "LEFT"
    join_condition: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Relationship:
        return cls(
            from_entity=data["from_entity"],
            to_entity=data["to_entity"],
            join_type=data.get("join_type", "LEFT"),
            join_condition=data.get("join_condition", ""),
        )


@dataclass
class Entity:
    """A business entity mapped to a physical table or view in Databricks."""
    name: str
    catalog: str
    schema: str
    table_name: str
    description: str = ""
    medallion_layer: str = "silver"  # bronze, silver, gold
    dimensions: List[Dimension] = field(default_factory=list)
    metrics: List[Metric] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)

    @property
    def full_table_name(self) -> str:
        return f"{self.catalog}.{self.schema}.{self.table_name}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "catalog": self.catalog,
            "schema": self.schema,
            "table_name": self.table_name,
            "description": self.description,
            "medallion_layer": self.medallion_layer,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "metrics": [m.to_dict() for m in self.metrics],
            "relationships": [r.to_dict() for r in self.relationships],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Entity:
        return cls(
            name=data["name"],
            catalog=data.get("catalog", "main"),
            schema=data.get("schema", "default"),
            table_name=data.get("table_name", data["name"]),
            description=data.get("description", ""),
            medallion_layer=data.get("medallion_layer", "silver"),
            dimensions=[Dimension.from_dict(d) for d in data.get("dimensions", [])],
            metrics=[Metric.from_dict(m) for m in data.get("metrics", [])],
            relationships=[Relationship.from_dict(r) for r in data.get("relationships", [])],
        )


@dataclass
class SemanticSchema:
    """Root contract for the Lakehouse semantic ontology."""
    name: str = "databricks_lakehouse_semantic_model"
    version: str = "1.0.0"
    description: str = ""
    entities: List[Entity] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "entities": [e.to_dict() for e in self.entities],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SemanticSchema:
        return cls(
            name=data.get("name", "databricks_lakehouse_semantic_model"),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            entities=[Entity.from_dict(e) for e in data.get("entities", [])],
        )
