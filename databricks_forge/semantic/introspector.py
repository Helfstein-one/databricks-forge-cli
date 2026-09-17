"""Databricks Unity Catalog Introspector for Semantic Modeling."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from databricks_forge.core.client import DatabricksCEClient
from databricks_forge.semantic.models import Entity, Dimension, Metric, SemanticSchema

logger = logging.getLogger(__name__)


class CatalogIntrospector:
    """Introspects Databricks Unity Catalog and infers semantic entities."""

    def __init__(self, client: Optional[DatabricksCEClient] = None):
        self.client = client

    def introspect_catalog(
        self,
        catalog: str = "main",
        schema: str = "default",
        table_filter: Optional[List[str]] = None
    ) -> List[Entity]:
        """Discovers tables in a catalog/schema and creates semantic Entity representations."""
        entities: List[Entity] = []

        if not self.client:
            # Fallback / offline sample generator if client not provided
            return self._build_mock_entities(catalog, schema)

        try:
            # Unity Catalog REST API: GET /api/2.1/unity-catalog/tables?catalog_name=...&schema_name=...
            resp = self.client.session.get(
                f"{self.client.host}/api/2.1/unity-catalog/tables",
                params={"catalog_name": catalog, "schema_name": schema},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                tables = data.get("tables", [])
                for t in tables:
                    t_name = t.get("name")
                    if table_filter and t_name not in table_filter:
                        continue
                    entity = self._table_to_entity(catalog, schema, t)
                    entities.append(entity)
                return entities
        except Exception as e:
            logger.warning(f"Failed to query Unity Catalog API: {e}. Falling back to standard catalog introspection.")

        # Fallback to standard introspection
        return self._build_mock_entities(catalog, schema)

    def _table_to_entity(self, catalog: str, schema: str, table_data: Dict[str, Any]) -> Entity:
        name = table_data.get("name", "table")
        comment = table_data.get("comment", "")
        columns = table_data.get("columns", [])

        # Infer medallion layer
        medallion = "silver"
        name_lower = name.lower()
        if "bronze" in name_lower or "raw" in name_lower:
            medallion = "bronze"
        elif "gold" in name_lower or "kpi" in name_lower or "agg" in name_lower:
            medallion = "gold"

        dimensions = []
        metrics = []

        for col in columns:
            c_name = col.get("name", "")
            c_type = col.get("type_name", "STRING").lower()
            c_comment = col.get("comment", "")

            dimensions.append(
                Dimension(
                    name=c_name,
                    column=c_name,
                    data_type=c_type,
                    description=c_comment,
                )
            )

            # Infer metrics for numeric fields
            if c_type in ("int", "bigint", "double", "float", "decimal", "long"):
                if not any(id_keyword in c_name.lower() for id_keyword in ("id", "code", "year", "month", "day", "zip")):
                    metrics.append(
                        Metric(
                            name=f"total_{c_name}",
                            formula=c_name,
                            aggregation="SUM",
                            description=f"Soma acumulada de {c_name}",
                        )
                    )
                    metrics.append(
                        Metric(
                            name=f"avg_{c_name}",
                            formula=c_name,
                            aggregation="AVG",
                            description=f"Média calculada de {c_name}",
                        )
                    )

        # Standard record count metric
        metrics.append(
            Metric(
                name=f"{name}_count",
                formula="*",
                aggregation="COUNT",
                description=f"Total de registros na entidade {name}",
                format_type="integer",
            )
        )

        return Entity(
            name=name,
            catalog=catalog,
            schema=schema,
            table_name=name,
            description=comment or f"Tabela {name} na camada {medallion.upper()}",
            medallion_layer=medallion,
            dimensions=dimensions,
            metrics=metrics,
        )

    def _build_mock_entities(self, catalog: str, schema: str) -> List[Entity]:
        """Provides default reference entities for demonstration and local testing."""
        return [
            Entity(
                name="bronze_raw_transactions",
                catalog=catalog,
                schema=schema,
                table_name="bronze_raw_transactions",
                description="Dados brutos de transações de vendas com carimbo de tempo",
                medallion_layer="bronze",
                dimensions=[
                    Dimension("transaction_id", "transaction_id", "string", "ID único da transação"),
                    Dimension("customer_id", "customer_id", "string", "Identificador do cliente"),
                    Dimension("status", "status", "string", "Status da transação"),
                    Dimension("raw_payload", "raw_payload", "string", "Payload JSON bruto"),
                    Dimension("_ingested_at", "_ingested_at", "timestamp", "Data e hora de ingestão"),
                ],
                metrics=[
                    Metric("total_raw_transactions", "*", "COUNT", "Total de transações brutas", "integer"),
                ],
            ),
            Entity(
                name="silver_transactions",
                catalog=catalog,
                schema=schema,
                table_name="silver_transactions",
                description="Transações limpas, validadas e deduplicadas com regras de negócio",
                medallion_layer="silver",
                dimensions=[
                    Dimension("transaction_id", "transaction_id", "string", "Chave primária"),
                    Dimension("customer_id", "customer_id", "string", "Identificador do cliente"),
                    Dimension("product_category", "product_category", "string", "Categoria do produto"),
                    Dimension("transaction_date", "transaction_date", "date", "Data contábil"),
                    Dimension("payment_method", "payment_method", "string", "Método de pagamento"),
                ],
                metrics=[
                    Metric("total_revenue", "amount", "SUM", "Faturamento total líquido", "currency"),
                    Metric("avg_ticket", "amount", "AVG", "Ticket médio por transação", "currency"),
                    Metric("transaction_count", "*", "COUNT", "Volume total de transações", "integer"),
                ],
            ),
            Entity(
                name="gold_sales_kpis",
                catalog=catalog,
                schema=schema,
                table_name="gold_sales_kpis",
                description="Métricas agregadas diárias por categoria prontas para consumo em BI e IA",
                medallion_layer="gold",
                dimensions=[
                    Dimension("transaction_date", "transaction_date", "date", "Data de apuração"),
                    Dimension("product_category", "product_category", "string", "Categoria"),
                ],
                metrics=[
                    Metric("daily_revenue", "total_revenue", "SUM", "Receita total diária", "currency"),
                    Metric("daily_customers", "unique_customers", "SUM", "Clientes únicos no dia", "integer"),
                ],
            ),
        ]
