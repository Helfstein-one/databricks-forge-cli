"""Conversational Semantic & Lakehouse Agent."""

from __future__ import annotations

import re
from typing import Any, Dict, Generator, List, Optional
from databricks_forge.ai.ollama_client import OllamaClient
from databricks_forge.ai.prompts import SYSTEM_SEMANTIC_AGENT_PROMPT
from databricks_forge.ai.etl_agent import ETLAgent
from databricks_forge.semantic.registry import SemanticRegistry
from databricks_forge.semantic.compiler import SemanticCompiler


class SemanticAgent:
    """Conversational Agent for Semantic Queries, Mermaid Diagrams & ETL Creation."""

    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        registry: Optional[SemanticRegistry] = None,
        model: str = "llama3.2:3b",
    ):
        self.ollama = ollama_client or OllamaClient()
        self.registry = registry or SemanticRegistry.load()
        self.compiler = SemanticCompiler(self.registry.schema)
        self.etl_agent = ETLAgent(self.ollama)
        self.model = model

    def get_available_models(self) -> List[str]:
        """Returns the list of locally installed Ollama models."""
        return self.ollama.list_models()

    def build_system_context(self) -> str:
        """Injects current semantic entities, dimensions, and metrics into the system prompt."""
        entities_summary = []
        for e in self.registry.list_entities():
            dims = [d.name for d in e.dimensions]
            mets = [m.name for m in e.metrics]
            entities_summary.append(
                f"- Tabela: {e.name} (Camada: {e.medallion_layer.upper()}, Full: {e.full_table_name})\n"
                f"  Dimensões: {', '.join(dims)}\n"
                f"  Métricas: {', '.join(mets)}"
            )
        catalog_text = "\n".join(entities_summary) if entities_summary else "Nenhuma tabela registrada ainda."

        return (
            f"{SYSTEM_SEMANTIC_AGENT_PROMPT}\n\n"
            f"CATÁLOGO SEMÂNTICO ATUAL DISPONÍVEL NO DATABRICKS:\n"
            f"{catalog_text}\n"
        )

    def is_etl_request(self, message: str) -> bool:
        """Heuristic check if the user intent is creating an ETL or pipeline."""
        m_lower = message.lower()
        triggers = [
            "crie um etl", "criar etl", "gerar etl", "monte um etl",
            "crie um pipeline", "criar pipeline", "fazer pipeline",
            "transforme", "transformar", "limpe a tabela", "limpar tabela",
            "pyspark", "spark.sql", "escreva um etl"
        ]
        return any(t in m_lower for t in triggers)

    def is_diagram_request(self, message: str) -> bool:
        """Heuristic check if user wants a Mermaid diagram (ERD or lineage)."""
        m_lower = message.lower()
        return any(t in m_lower for t in ["mermaid", "diagrama", "erd", "linhagem", "fluxo", "arquitetura"])

    def process_message(
        self,
        user_message: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        model_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Processes user message and returns structured result with text, diagrams, and optional ETL action."""
        active_model = model_override or self.model

        # 1. Check if user explicitly asked for diagrams
        if self.is_diagram_request(user_message):
            if "linhagem" in user_message.lower() or "medallion" in user_message.lower() or "fluxo" in user_message.lower():
                mermaid_code = self.registry.to_mermaid_lineage()
                explanation = "Aqui está o diagrama de **Linhagem Medallion** mapeando as camadas Bronze, Silver e Gold do seu Lakehouse:"
            else:
                mermaid_code = self.registry.to_mermaid_erd()
                explanation = "Aqui está o **Diagrama de Entidade-Relacionamento (ERD)** das tabelas e dimensões registradas no catálogo semântico:"

            return {
                "type": "diagram",
                "text": f"{explanation}\n\n```mermaid\n{mermaid_code}\n```",
                "mermaid": mermaid_code,
            }

        # 2. Check if user wants to create an ETL pipeline
        if self.is_etl_request(user_message):
            # Parse entities
            source_table = "bronze_raw_transactions"
            target_table = "silver_transactions"
            pipeline_name = "clean_silver_pipeline"

            for e in self.registry.list_entities():
                if e.name.lower() in user_message.lower():
                    if e.medallion_layer == "bronze":
                        source_table = e.name
                    elif e.medallion_layer == "silver":
                        target_table = e.name

            code = self.etl_agent.generate_pipeline_code(
                prompt=user_message,
                model=active_model,
                source_table=source_table,
                target_table=target_table,
                pipeline_name=pipeline_name,
            )
            mermaid_flow = self.etl_agent.to_mermaid_pipeline(pipeline_name, source_table, target_table)

            return {
                "type": "etl_proposal",
                "text": (
                    f"Compreendi a sua solicitação para criar o pipeline **`{pipeline_name}`**!\n\n"
                    f"• **Origem**: `{source_table}`\n"
                    f"• **Destino**: `{target_table}`\n\n"
                    "O script PySpark de produção foi estruturado com auditoria (`@pipeline_audit_step`) "
                    "e gravação Delta Lake ACID. Você pode revisar o código e o diagrama abaixo e aprovar "
                    "para executar no Databricks e sincronizar no GitHub."
                ),
                "code": code,
                "mermaid": mermaid_flow,
                "pipeline_name": pipeline_name,
                "source_table": source_table,
                "target_table": target_table,
            }

        # 3. Standard Semantic conversational query
        system_context = self.build_system_context()
        messages = [{"role": "system", "content": system_context}]
        if chat_history:
            messages.extend(chat_history[-6:])
        messages.append({"role": "user", "content": user_message})

        if self.ollama.is_available():
            try:
                reply = self.ollama.chat(
                    model=active_model,
                    messages=messages,
                    temperature=0.2,
                )
                # Check if reply contains a mermaid diagram
                mermaid_match = re.search(r"```mermaid\s*(.*?)\s*```", reply, re.DOTALL)
                mermaid_code = mermaid_match.group(1).strip() if mermaid_match else None
                return {
                    "type": "chat",
                    "text": reply,
                    "mermaid": mermaid_code,
                }
            except Exception as e:
                pass

        # Offline fallback reply
        return {
            "type": "chat",
            "text": (
                f"Olá! O agente semântico está operando em modo local. Encontrei {len(self.registry.list_entities())} "
                "tabelas mapeadas no seu catálogo Databricks. Você pode pedir diagramas ERD, consultas de métricas ou pedir para "
                "criar novos pipelines ETL em PySpark!"
            ),
            "mermaid": self.registry.to_mermaid_erd(),
        }
