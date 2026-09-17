"""Semantic Query Compiler for Databricks Forge CLI."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from databricks_forge.semantic.models import Entity, SemanticSchema


class SemanticCompiler:
    """Compiles high-level semantic queries into strict, validated Spark SQL."""

    def __init__(self, schema: SemanticSchema):
        self.schema = schema

    def compile_query(
        self,
        entity_name: str,
        metrics: Optional[List[str]] = None,
        dimensions: Optional[List[str]] = None,
        filters: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Compiles a semantic query specification into verified Spark SQL."""
        entity: Optional[Entity] = None
        for e in self.schema.entities:
            if e.name.lower() == entity_name.lower() or e.table_name.lower() == entity_name.lower():
                entity = e
                break

        if not entity:
            available = [e.name for e in self.schema.entities]
            raise ValueError(f"Entidade '{entity_name}' não encontrada no catálogo semântico. Disponíveis: {available}")

        # Resolve dimensions
        selected_dims = []
        if dimensions:
            for d_name in dimensions:
                matched = next((d for d in entity.dimensions if d.name.lower() == d_name.lower() or d.column.lower() == d_name.lower()), None)
                if matched:
                    selected_dims.append(matched.column)
                else:
                    selected_dims.append(d_name)

        # Resolve metrics
        selected_metrics = []
        if metrics:
            for m_name in metrics:
                matched = next((m for m in entity.metrics if m.name.lower() == m_name.lower()), None)
                if matched:
                    if matched.formula == "*":
                        expr = f"{matched.aggregation}(*) AS {matched.name}"
                    else:
                        expr = f"{matched.aggregation}({matched.formula}) AS {matched.name}"
                    selected_metrics.append(expr)
                else:
                    selected_metrics.append(m_name)
        else:
            # Default to count
            selected_metrics.append(f"COUNT(*) AS {entity.name}_count")

        # Construct SELECT items
        select_clause = []
        if selected_dims:
            select_clause.extend(selected_dims)
        select_clause.extend(selected_metrics)
        select_str = ",\n  ".join(select_clause)

        # Construct FROM clause
        from_str = entity.full_table_name

        # Construct WHERE clause
        where_str = ""
        if filters:
            where_str = "WHERE " + " AND ".join(filters)

        # Construct GROUP BY clause
        group_by_str = ""
        if selected_dims and selected_metrics:
            group_by_str = "GROUP BY " + ", ".join(selected_dims)

        # Construct ORDER BY clause
        order_str = ""
        if order_by:
            order_str = f"ORDER BY {order_by}"
        elif selected_dims:
            order_str = f"ORDER BY {selected_dims[0]} ASC"

        # Limit
        limit_str = f"LIMIT {limit}" if limit else ""

        # Assemble SQL
        sql_parts = [
            f"SELECT\n  {select_str}",
            f"FROM {from_str}",
        ]
        if where_str:
            sql_parts.append(where_str)
        if group_by_str:
            sql_parts.append(group_by_str)
        if order_str:
            sql_parts.append(order_str)
        if limit_str:
            sql_parts.append(limit_str)

        compiled_sql = "\n".join(sql_parts) + ";"

        return {
            "entity": entity.name,
            "table": entity.full_table_name,
            "dimensions": selected_dims,
            "metrics": metrics or [f"{entity.name}_count"],
            "sql": compiled_sql,
        }
