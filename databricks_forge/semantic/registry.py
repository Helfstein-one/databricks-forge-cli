"""Semantic Model Registry & YAML Storage for Databricks Forge CLI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from databricks_forge.semantic.models import Entity, Metric, Dimension, Relationship, SemanticSchema


DEFAULT_SEMANTIC_MODEL_PATH = Path("config/semantic_model.yaml")


class SemanticRegistry:
    """Manages the semantic models and generates metadata representations."""

    def __init__(self, schema: Optional[SemanticSchema] = None, file_path: Optional[Path] = None):
        self.schema = schema or SemanticSchema(name="lakehouse_semantic_model")
        self.file_path = file_path or DEFAULT_SEMANTIC_MODEL_PATH

    @classmethod
    def load(cls, file_path: Optional[Path] = None) -> SemanticRegistry:
        """Loads semantic schema from a YAML file, creating a default if missing."""
        path = file_path or DEFAULT_SEMANTIC_MODEL_PATH
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            schema = SemanticSchema.from_dict(data)
            return cls(schema=schema, file_path=path)
        return cls(file_path=path)

    def save(self, file_path: Optional[Path] = None) -> Path:
        """Saves the current semantic schema to YAML."""
        path = file_path or self.file_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self.schema.to_dict(), f, sort_keys=False, indent=2, allow_unicode=True)
        return path

    def add_or_update_entity(self, entity: Entity) -> None:
        """Adds an entity or replaces an existing one by name."""
        for idx, existing in enumerate(self.schema.entities):
            if existing.name == entity.name or existing.full_table_name == entity.full_table_name:
                self.schema.entities[idx] = entity
                return
        self.schema.entities.append(entity)

    def get_entity(self, name: str) -> Optional[Entity]:
        """Gets an entity by name or full table name."""
        for e in self.schema.entities:
            if e.name.lower() == name.lower() or e.full_table_name.lower() == name.lower() or e.table_name.lower() == name.lower():
                return e
        return None

    def list_entities(self) -> List[Entity]:
        return self.schema.entities

    def to_mermaid_erd(self) -> str:
        """Generates a clean Mermaid erDiagram for all registered entities and relationships."""
        lines = ["erDiagram"]
        if not self.schema.entities:
            return "erDiagram\n    NO_ENTITIES {\n        string info\n    }"

        # Relationships
        rendered_rels = set()
        for e in self.schema.entities:
            for r in e.relationships:
                rel_key = f"{r.from_entity}__{r.to_entity}"
                if rel_key not in rendered_rels:
                    lines.append(f"    {r.from_entity} ||--o{{ {r.to_entity} : \"{r.join_condition}\"")
                    rendered_rels.add(rel_key)

        # Entities and fields
        for e in self.schema.entities:
            lines.append(f"    {e.name} {{")
            for dim in e.dimensions:
                dtype = dim.data_type.replace(" ", "_")
                lines.append(f"        {dtype} {dim.column} \"{dim.description or dim.name}\"")
            for metric in e.metrics:
                lines.append(f"        metric {metric.name} \"{metric.aggregation}({metric.formula})\"")
            lines.append("    }")

        return "\n".join(lines)

    def to_mermaid_lineage(self) -> str:
        """Generates a Mermaid graph TD / LR representing the Medallion Lineage."""
        lines = ["graph LR"]
        bronze_nodes = []
        silver_nodes = []
        gold_nodes = []

        for e in self.schema.entities:
            layer = (e.medallion_layer or "silver").lower()
            node_id = f"node_{e.name}"
            node_label = f"\"{e.name}<br/><i>({e.full_table_name})</i>\""
            
            if layer == "bronze":
                bronze_nodes.append((node_id, node_label))
            elif layer == "gold":
                gold_nodes.append((node_id, node_label))
            else:
                silver_nodes.append((node_id, node_label))

        lines.append("    subgraph Bronze[\"🥉 Camada Bronze (Raw Ingestion)\"]")
        for nid, lbl in bronze_nodes:
            lines.append(f"        {nid}[{lbl}]")
        if not bronze_nodes:
            lines.append("        b_none[\"Nenhuma tabela Bronze registrada\"]")
        lines.append("    end")

        lines.append("    subgraph Silver[\"🥈 Camada Silver (Cleaned / Curated)\"]")
        for nid, lbl in silver_nodes:
            lines.append(f"        {nid}[{lbl}]")
        if not silver_nodes:
            lines.append("        s_none[\"Nenhuma tabela Silver registrada\"]")
        lines.append("    end")

        lines.append("    subgraph Gold[\"🥇 Camada Gold (KPIs / Aggregates)\"]")
        for nid, lbl in gold_nodes:
            lines.append(f"        {nid}[{lbl}]")
        if not gold_nodes:
            lines.append("        g_none[\"Nenhuma tabela Gold registrada\"]")
        lines.append("    end")

        # Connect layers
        if bronze_nodes and silver_nodes:
            lines.append(f"    {bronze_nodes[0][0]} --> {silver_nodes[0][0]}")
        if silver_nodes and gold_nodes:
            lines.append(f"    {silver_nodes[0][0]} --> {gold_nodes[0][0]}")

        return "\n".join(lines)
