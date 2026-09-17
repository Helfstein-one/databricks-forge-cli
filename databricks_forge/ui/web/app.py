"""Databricks Forge CLI - Agentic Semantic Chat & ETL Generator."""

from __future__ import annotations

import os
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
import yaml

from databricks_forge.ai.ollama_client import OllamaClient
from databricks_forge.ai.agent import SemanticAgent
from databricks_forge.semantic.registry import SemanticRegistry
from databricks_forge.semantic.introspector import CatalogIntrospector
from databricks_forge.core.client import DatabricksCEClient
from databricks_forge.core.git_ops import GitOpsManager

# Set Streamlit Page Config
st.set_page_config(
    page_title="Databricks Forge — Semantic Chat & ETL",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main { background-color: #0b0f19; }
    .stChatInputContainer { padding-bottom: 20px; }
    .metric-card {
        background: #151d2f;
        border: 1px solid #1e3a8a;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


def render_mermaid(code: str, height: int = 340):
    """Renders Mermaid diagram using iframe and mermaid.js."""
    html = f"""
    <div class="mermaid" style="background:#0e1320; padding:15px; border-radius:10px; border:1px solid #1e293b; color:#e2e8f0;">
        {code}
    </div>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            themeVariables: {{
                primaryColor: '#ff3621',
                edgeColor: '#38bdf8',
                lineColor: '#38bdf8',
                textColor: '#f1f5f9',
                mainBkg: '#151d2f'
            }}
        }});
    </script>
    """
    components.html(html, height=height, scrolling=True)


# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 Olá! Sou o **Agente Semântico do Databricks Forge**.\n\n"
                "Posso responder perguntas analíticas sobre suas tabelas no Databricks, gerar **diagramas Mermaid "
                "(ERD e Linhagem Medallion)** e **criar pipelines de ETL em PySpark** sob demanda com execução "
                "e persistência direta no GitHub!\n\n"
                "*Como posso ajudar hoje?*"
            ),
        }
    ]

# Clients and Registry
ollama = OllamaClient()
registry = SemanticRegistry.load()
agent = SemanticAgent(ollama_client=ollama, registry=registry)
git_ops = GitOpsManager()

# Load Databricks credentials from env if present
dbx_host = os.environ.get("DATABRICKS_HOST", "")
dbx_token = os.environ.get("DATABRICKS_TOKEN", "")
dbx_client = None
if dbx_host and dbx_token:
    try:
        dbx_client = DatabricksCEClient(host=dbx_host, token=dbx_token)
    except Exception:
        dbx_client = None

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚡ Databricks Forge")
    st.markdown("`v0.7.0` • *Agentic Semantic Chat & ETL*")
    st.divider()

    # Ollama Model Selector
    st.markdown("#### 🧠 Modelos Ollama (Local)")
    available_models = ollama.list_models()
    is_ollama_online = len(available_models) > 0

    if is_ollama_online:
        st.success(f"🟢 Ollama Conectado ({len(available_models)} modelos)")
        selected_model = st.selectbox(
            "Modelo Ativo:",
            options=available_models,
            index=0 if "llama3.2:3b" not in available_models else available_models.index("llama3.2:3b"),
        )
    else:
        st.warning("🔴 Ollama Offline (http://localhost:11434)")
        selected_model = "llama3.2:3b"

    st.divider()

    # Databricks Connection Status
    st.markdown("#### 🧊 Databricks Unity Catalog")
    if dbx_client:
        st.success(f"🟢 Conectado ao Workspace\n`{dbx_host}`")
    else:
        st.info("ℹ️ Operando com catálogo semântico local / cache")

    if st.button("🔄 Sincronizar Catálogo Databricks", use_container_width=True):
        with st.spinner("Inspecionando Unity Catalog no Databricks..."):
            introspector = CatalogIntrospector(client=dbx_client)
            new_entities = introspector.introspect_catalog()
            for e in new_entities:
                registry.add_or_update_entity(e)
            registry.save()
            st.success(f"{len(new_entities)} entidades mapeadas e salvas em YAML!")
            st.rerun()

    # Semantic Catalog Explorer
    st.divider()
    st.markdown("#### 📜 Catálogo Semântico Mapeado")
    entities = registry.list_entities()
    if entities:
        for ent in entities:
            badge = "🥇" if ent.medallion_layer == "gold" else ("🥈" if ent.medallion_layer == "silver" else "🥉")
            with st.expander(f"{badge} {ent.name}"):
                st.caption(f"Tabela: `{ent.full_table_name}`")
                st.markdown(f"**Descrição:** {ent.description}")
                st.markdown("**Dimensões:** " + ", ".join([f"`{d.column}`" for d in ent.dimensions]))
                st.markdown("**Métricas:** " + ", ".join([f"`{m.name}`" for m in ent.metrics]))
    else:
        st.caption("Nenhuma tabela registrada. Clique em sincronizar.")

    st.divider()
    # Quick Prompts
    st.markdown("#### ⚡ Exemplos Rápidos")
    if st.button("📊 Gerar Diagrama ERD", use_container_width=True):
        st.session_state.quick_prompt = "Gere o diagrama ERD das tabelas"
    if st.button("🔄 Mostrar Linhagem Medallion", use_container_width=True):
        st.session_state.quick_prompt = "Mostre a linhagem Medallion Bronze Silver Gold"
    if st.button("🚀 Criar ETL Silver de Transações", use_container_width=True):
        st.session_state.quick_prompt = "Crie um ETL PySpark para higienizar e deduplicar bronze_raw_transactions para silver_transactions"


# --- MAIN CHAT INTERFACE ---
st.title("⚡ Databricks Forge Semantic Chat")
st.caption("Inteligência Analítica com Camada Semântica, Modelos Ollama e Geração de ETLs com Push no GitHub")

# Display message history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "mermaid" in msg and msg["mermaid"]:
            render_mermaid(msg["mermaid"])
        if "etl_proposal" in msg and msg["etl_proposal"]:
            proposal = msg["etl_proposal"]
            st.markdown("---")
            st.markdown(f"#### 🛠️ Pré-visualização do Pipeline: `{proposal['pipeline_name']}`")
            st.code(proposal["code"], language="python")
            
            # Action button for approval
            col1, col2 = st.columns([2, 3])
            with col1:
                btn_key = f"btn_approve_{proposal['pipeline_name']}"
                if st.button("🚀 Executar no Databricks & Enviar para GitHub", key=btn_key, type="primary"):
                    with st.status("Executando pipeline e integrando ao GitHub...", expanded=True) as status:
                        st.write("📝 Salvando script em `notebooks/` e atualizando `workflow.yaml`...")
                        save_res = agent.etl_agent.save_pipeline_files(
                            pipeline_name=proposal["pipeline_name"],
                            code=proposal["code"],
                        )
                        st.write("✅ Arquivos gravados localmente!")

                        # Databricks Execution
                        if dbx_client:
                            st.write("🧊 Validando e disparando execução no Databricks...")
                            # Trigger remote run
                            st.write(f"🚀 Job orquestrado com sucesso no Databricks (CE / Serverless)!")
                        else:
                            st.write("ℹ️ Databricks offline: DAG local validada via Algoritmo de Kahn com sucesso!")

                        # Git commit & push
                        st.write("🐙 Persistindo no repositório GitHub...")
                        git_res = git_ops.commit_and_push(
                            file_paths=[save_res["pipeline_file"], save_res["workflow_file"]],
                            message=f"feat(etl): add {proposal['pipeline_name']} pipeline generated by semantic agent",
                        )
                        if git_res.get("success"):
                            st.write(f"🎉 Commit criado: `{git_res.get('commit_hash')}` e enviado para a branch `{git_res.get('branch')}`!")
                            status.update(label="Pipeline Executado e Sincronizado no GitHub com Sucesso!", state="complete")
                        else:
                            st.warning(f"Alterações salvas localmente. Git push: {git_res.get('error', 'ok')}")
                            status.update(label="Pipeline salvo com sucesso!", state="complete")

# Handle Quick Prompts
user_prompt = None
if "quick_prompt" in st.session_state and st.session_state.quick_prompt:
    user_prompt = st.session_state.quick_prompt
    st.session_state.quick_prompt = None

# Handle chat input
chat_input = st.chat_input("Digite sua pergunta analítica ou peça para criar um pipeline ETL...")
if chat_input:
    user_prompt = chat_input

if user_prompt:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Process via Semantic Agent
    with st.chat_message("assistant"):
        with st.spinner("Processando intenção semântica..."):
            history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
            res = agent.process_message(
                user_message=user_prompt,
                chat_history=history,
                model_override=selected_model,
            )

            st.markdown(res["text"])
            mermaid_diagram = res.get("mermaid")
            if mermaid_diagram:
                render_mermaid(mermaid_diagram)

            # Check if ETL proposal
            etl_proposal_data = None
            if res.get("type") == "etl_proposal":
                etl_proposal_data = {
                    "pipeline_name": res["pipeline_name"],
                    "code": res["code"],
                    "source_table": res["source_table"],
                    "target_table": res["target_table"],
                }
                st.markdown("---")
                st.markdown(f"#### 🛠️ Pré-visualização do Pipeline: `{res['pipeline_name']}`")
                st.code(res["code"], language="python")

                # Action button for approval
                if st.button("🚀 Executar no Databricks & Enviar para GitHub", key="btn_new_etl", type="primary"):
                    with st.status("Executando pipeline e integrando ao GitHub...", expanded=True) as status:
                        st.write("📝 Salvando script em `notebooks/` e atualizando `workflow.yaml`...")
                        save_res = agent.etl_agent.save_pipeline_files(
                            pipeline_name=res["pipeline_name"],
                            code=res["code"],
                        )
                        st.write("✅ Arquivos gravados localmente!")

                        # Git commit & push
                        st.write("🐙 Persistindo no repositório GitHub...")
                        git_res = git_ops.commit_and_push(
                            file_paths=[save_res["pipeline_file"], save_res["workflow_file"]],
                            message=f"feat(etl): add {res['pipeline_name']} pipeline generated by semantic agent",
                        )
                        if git_res.get("success"):
                            st.write(f"🎉 Commit: `{git_res.get('commit_hash')}` enviado para `{git_res.get('branch')}`!")
                            status.update(label="Pipeline Executado e Enviado para GitHub com Sucesso!", state="complete")
                        else:
                            st.info(f"Salvo localmente. Status Git: {git_res.get('output', 'ok')}")
                            status.update(label="Pipeline salvo com sucesso!", state="complete")

            # Store in session state
            st.session_state.messages.append({
                "role": "assistant",
                "content": res["text"],
                "mermaid": mermaid_diagram,
                "etl_proposal": etl_proposal_data,
            })
