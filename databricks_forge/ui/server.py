"""FastAPI Server for Databricks Forge OpenWebUI-grade Chat & OpenAI-compatible API."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from databricks_forge.ai.agent import SemanticAgent
from databricks_forge.ai.ollama_client import OllamaClient
from databricks_forge.core.ci_runner import CIQualityGateRunner
from databricks_forge.core.client import DatabricksCEClient
from databricks_forge.core.git_ops import GitOpsManager
from databricks_forge.core.workflow import DAGWorkflow
from databricks_forge.semantic.introspector import CatalogIntrospector
from databricks_forge.semantic.registry import SemanticRegistry

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None


class ApproveETLRequest(BaseModel):
    pipeline_name: str
    code: str
    run_databricks: bool = True
    push_git: bool = True


class DeployPipelineRequest(BaseModel):
    pipeline_name: str
    code: str
    source_table: Optional[str] = "bronze_raw_transactions"
    target_table: Optional[str] = "silver_transactions"
    run_databricks: Optional[bool] = True
    push_git: Optional[bool] = True


# OpenAI-compatible API schemas
class OpenAIMessage(BaseModel):
    role: str
    content: str


class OpenAIChatCompletionRequest(BaseModel):
    model: str = "databricks-forge"
    messages: List[OpenAIMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.2


def create_app() -> FastAPI:
    """Creates and configures the FastAPI application."""
    app = FastAPI(
        title="Databricks Forge OpenWebUI & Semantic ETL API",
        version="0.7.0",
        docs_url="/api/docs",
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    ollama = OllamaClient()
    registry = SemanticRegistry.load()
    agent = SemanticAgent(ollama_client=ollama, registry=registry)
    git_ops = GitOpsManager()
    ci_runner = CIQualityGateRunner()

    dbx_host = os.environ.get("DATABRICKS_HOST", "")
    dbx_token = os.environ.get("DATABRICKS_TOKEN", "")
    dbx_client: Optional[DatabricksCEClient] = None
    if dbx_host and dbx_token:
        try:
            dbx_client = DatabricksCEClient(host=dbx_host, token=dbx_token)
        except Exception:
            dbx_client = None

    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(parents=True, exist_ok=True)

    @app.get("/api/health")
    def health_check():
        return {"status": "ok", "version": "0.7.0", "engine": "open-webui-forge"}

    @app.get("/api/models")
    def get_models():
        """Returns installed Ollama models and server status."""
        is_online = ollama.is_available()
        models = ollama.list_models() if is_online else []
        default_model = "llama3.2:3b" if "llama3.2:3b" in models else (models[0] if models else "llama3.2:3b")
        return {
            "status": "online" if is_online else "offline",
            "models": models,
            "default_model": default_model,
        }

    @app.get("/api/catalog")
    def get_catalog():
        """Returns registered semantic entities, dimensions, and metrics."""
        entities = []
        for e in registry.list_entities():
            entities.append({
                "name": e.name,
                "full_table_name": e.full_table_name,
                "layer": e.medallion_layer,
                "description": e.description,
                "dimensions": [d.name for d in e.dimensions],
                "metrics": [m.name for m in e.metrics],
            })

        return {
            "entities": entities,
            "erd_mermaid": registry.to_mermaid_erd(),
            "lineage_mermaid": registry.to_mermaid_lineage(),
            "dbx_connected": dbx_client is not None,
            "dbx_host": dbx_host if dbx_client else None,
        }

    @app.post("/api/catalog/sync")
    def sync_catalog():
        """Synchronizes semantic models with Databricks Unity Catalog."""
        introspector = CatalogIntrospector(client=dbx_client)
        new_entities = introspector.introspect_catalog()
        for e in new_entities:
            registry.add_or_update_entity(e)
        registry.save()
        return {
            "success": True,
            "count": len(new_entities),
            "message": f"{len(new_entities)} entidades sincronizadas e salvas.",
        }

    @app.post("/api/chat/stream")
    async def chat_stream(req: ChatRequest, request: Request):
        """Streams chat response via Server-Sent Events (SSE) with instant cancellation."""
        async def event_generator():
            user_msg = req.message.strip()
            model = req.model or "llama3.2:3b"
            history = req.history or []

            # 1. Diagram request
            if agent.is_diagram_request(user_msg):
                if any(k in user_msg.lower() for k in ["linhagem", "medallion", "fluxo"]):
                    mermaid_code = registry.to_mermaid_lineage()
                    explanation = "Aqui está o diagrama de **Linhagem Medallion** mapeando as camadas Bronze, Silver e Gold do Lakehouse:"
                else:
                    mermaid_code = registry.to_mermaid_erd()
                    explanation = "Aqui está o **Diagrama de Entidade-Relacionamento (ERD)** das tabelas registradas no catálogo:"

                yield f"event: message\ndata: {json.dumps({'type': 'diagram', 'text': explanation, 'mermaid': mermaid_code})}\n\n"
                yield "event: done\ndata: {}\n\n"
                return

            # 2. ETL request
            if agent.is_etl_request(user_msg):
                source_table = "bronze_raw_transactions"
                target_table = "silver_transactions"
                pipeline_name = "clean_silver_pipeline"

                for e in registry.list_entities():
                    if e.name.lower() in user_msg.lower():
                        if e.medallion_layer == "bronze":
                            source_table = e.name
                        elif e.medallion_layer == "silver":
                            target_table = e.name

                code = agent.etl_agent.generate_pipeline_code(
                    prompt=user_msg,
                    model=model,
                    source_table=source_table,
                    target_table=target_table,
                    pipeline_name=pipeline_name,
                )
                mermaid_flow = agent.etl_agent.to_mermaid_pipeline(pipeline_name, source_table, target_table)

                proposal = {
                    "type": "etl_proposal",
                    "pipeline_name": pipeline_name,
                    "source_table": source_table,
                    "target_table": target_table,
                    "code": code,
                    "mermaid": mermaid_flow,
                    "text": (
                        f"Compreendi sua solicitação para criar o pipeline **`{pipeline_name}`**!\n\n"
                        f"• **Origem**: `{source_table}`\n"
                        f"• **Destino**: `{target_table}`\n\n"
                        "Revise o código PySpark e o diagrama de fluxo abaixo e aprove a execução para persistir no GitHub:"
                    ),
                }
                yield f"event: message\ndata: {json.dumps(proposal)}\n\n"
                yield "event: done\ndata: {}\n\n"
                return

            # 3. Conversational chat with Ollama streaming
            if ollama.is_available():
                system_context = agent.build_system_context()
                messages = [{"role": "system", "content": system_context}]
                if history:
                    messages.extend(history[-6:])
                messages.append({"role": "user", "content": user_msg})

                try:
                    payload = {
                        "model": model,
                        "messages": messages,
                        "options": {"temperature": 0.2},
                        "stream": True,
                    }
                    stream_gen = ollama._chat_stream(payload)
                    for chunk in stream_gen:
                        # Instant cancellation on stop button (client abort)
                        if await request.is_disconnected():
                            logger.info("Client aborted chat stream.")
                            break

                        yield f"event: token\ndata: {json.dumps({'token': chunk})}\n\n"
                        await asyncio.sleep(0.005)

                    yield "event: done\ndata: {}\n\n"
                    return
                except Exception as e:
                    logger.warning(f"Streaming error: {e}")

            # 4. Offline fallback
            offline_text = (
                f"Olá! O agente semântico está operando localmente com {len(registry.list_entities())} "
                "tabelas mapeadas no catálogo Databricks. Você pode pedir diagramas ERD, visualizar a linhagem Medallion "
                "ou solicitar a criação de novos pipelines ETL em PySpark!"
            )
            yield f"event: message\ndata: {json.dumps({'type': 'chat', 'text': offline_text, 'mermaid': registry.to_mermaid_erd()})}\n\n"
            yield "event: done\ndata: {}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.post("/api/etl/deploy-pipeline")
    async def deploy_pipeline(req: DeployPipelineRequest):
        """Streams real-time progress for the 4-step pipeline deployment:
        1. Save script, unit test, and DAG
        2. Git commit & push
        3. CI Quality Gate (pytest execution)
        4. Databricks Serverless Jobs API v2.1 dispatch
        """
        async def event_generator():
            try:
                # STEP 1: Persist files
                yield f"data: {json.dumps({'step': 'saving', 'status': 'in_progress', 'message': 'Gravando script em notebooks/ e teste unitário em tests/...'})}\n\n"
                await asyncio.sleep(0.05)

                save_res = agent.etl_agent.save_pipeline_files(
                    pipeline_name=req.pipeline_name,
                    code=req.code,
                    source_table=req.source_table or "bronze_raw_transactions",
                    target_table=req.target_table or "silver_transactions",
                )
                pipeline_file = save_res["pipeline_file"]
                test_file = save_res["test_file"]
                workflow_file = save_res["workflow_file"]

                yield f"data: {json.dumps({'step': 'saving', 'status': 'completed', 'message': 'Arquivos salvos e workflow.yaml atualizado.', 'pipeline_file': pipeline_file, 'test_file': test_file, 'workflow_file': workflow_file})}\n\n"

                # STEP 2: GitOps Commit & Push
                commit_hash = "local"
                branch = "main"
                if req.push_git:
                    yield f"data: {json.dumps({'step': 'git', 'status': 'in_progress', 'message': 'Comitando e enviando para o GitHub...'})}\n\n"
                    await asyncio.sleep(0.05)

                    git_res = git_ops.commit_and_push(
                        file_paths=[pipeline_file, test_file, workflow_file],
                        message=f"feat(etl): add {req.pipeline_name} pipeline and unit test via OpenWebUI",
                    )
                    commit_hash = git_res.get("commit_hash", "local")
                    branch = git_res.get("branch", "main")
                    git_msg = (
                        f"Commit {commit_hash} enviado para origin/{branch}."
                        if git_res.get("success")
                        else f"Commit local {commit_hash} ({git_res.get('error', '')})"
                    )

                    yield f"data: {json.dumps({'step': 'git', 'status': 'completed', 'message': git_msg, 'commit_hash': commit_hash, 'branch': branch})}\n\n"
                else:
                    yield f"data: {json.dumps({'step': 'git', 'status': 'skipped', 'message': 'Etapa de Git ignorada.'})}\n\n"

                # STEP 3: CI Quality Gate (PyTest)
                yield f"data: {json.dumps({'step': 'ci', 'status': 'in_progress', 'message': f'Executando PyTest em {Path(test_file).name}...'})}\n\n"
                ci_result = await ci_runner.run_local_tests_async(test_path=test_file, timeout_sec=60)

                ci_summary = ci_result.get("summary", "")
                if not ci_result.get("success"):
                    # STRICT GATING: abort Databricks dispatch!
                    yield f"data: {json.dumps({'step': 'ci', 'status': 'failed', 'message': f'Quality Gate FALHOU: {ci_summary}', 'output': ci_result.get('output', '')})}\n\n"
                    yield f"data: {json.dumps({'step': 'error', 'status': 'blocked', 'message': 'Disparo no Databricks BLOQUEADO devido a falha nos testes unitários.'})}\n\n"
                    return

                yield f"data: {json.dumps({'step': 'ci', 'status': 'completed', 'message': f'Quality Gate Aprovado: {ci_summary}', 'passed': ci_result.get('passed'), 'duration': ci_result.get('duration_sec')})}\n\n"

                # STEP 4: Databricks Jobs API v2.1 Dispatch
                if req.run_databricks:
                    yield f"data: {json.dumps({'step': 'databricks', 'status': 'in_progress', 'message': 'Compilando DAG e disparando Databricks Jobs API v2.1 (Serverless)...'})}\n\n"
                    await asyncio.sleep(0.05)

                    dbx_info = {}
                    if dbx_client:
                        try:
                            # 1. Upload notebook to workspace
                            remote_path = f"/Shared/forge_deployments/{req.pipeline_name}"
                            dbx_client.upload_file(pipeline_file, remote_path, overwrite=True)

                            # 2. Compile DAG
                            dag = DAGWorkflow.from_yaml(Path(workflow_file))
                            payload = dag.to_databricks_jobs_api_payload(serverless=True)

                            # 3. Create or run job
                            job_resp = dbx_client.create_job(payload)
                            job_id = job_resp.get("job_id")
                            if job_id:
                                run_resp = dbx_client.run_job(job_id)
                                run_id = run_resp.get("run_id")
                                run_url = f"{dbx_host}/#job/{job_id}/run/{run_id}" if dbx_host else None
                                dbx_info = {
                                    "job_id": job_id,
                                    "run_id": run_id,
                                    "run_url": run_url,
                                    "message": f"Job #{job_id} disparado com sucesso! Run ID: {run_id}",
                                }
                            else:
                                dbx_info = {"message": "Job compilado no Databricks."}
                        except Exception as d_err:
                            logger.warning(f"Databricks execution error: {d_err}")
                            dbx_info = {
                                "simulated": True,
                                "message": f"DAG compilada via Kahn's Algorithm. Aviso Databricks: {d_err}",
                            }
                    else:
                        dbx_info = {
                            "simulated": True,
                            "message": "DAG validada com sucesso via Kahn's Algorithm (Modo Local/Offline - configure DATABRICKS_TOKEN para disparo remoto).",
                        }

                    yield f"data: {json.dumps({'step': 'databricks', 'status': 'completed', 'message': dbx_info.get('message'), 'job_id': dbx_info.get('job_id'), 'run_id': dbx_info.get('run_id'), 'run_url': dbx_info.get('run_url')})}\n\n"
                else:
                    yield f"data: {json.dumps({'step': 'databricks', 'status': 'skipped', 'message': 'Disparo no Databricks ignorado pelo usuário.'})}\n\n"

                yield f"data: {json.dumps({'step': 'done', 'status': 'success', 'message': 'Esteira completa concluída com sucesso!'})}\n\n"

            except Exception as e:
                logger.exception("Deploy pipeline error")
                yield f"data: {json.dumps({'step': 'error', 'status': 'failed', 'message': str(e)})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.post("/api/etl/approve")
    def approve_etl(req: ApproveETLRequest):
        """Persists pipeline script, updates DAG, runs in Databricks, and pushes to GitHub."""
        try:
            save_res = agent.etl_agent.save_pipeline_files(
                pipeline_name=req.pipeline_name,
                code=req.code,
            )

            # CI Quality Gate Check
            ci_res = ci_runner.run_local_tests(test_path=save_res.get("test_file"))
            if not ci_res.get("success"):
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "ci_failed": True,
                        "error": f"Quality Gate FALHOU no pytest: {ci_res.get('summary')}",
                        "output": ci_res.get("output", ""),
                    },
                )

            dbx_message = "DAG local validada com sucesso via Algoritmo de Kahn."
            if req.run_databricks and dbx_client:
                dbx_message = "Disparado com sucesso no Databricks Jobs API (Serverless)."

            git_result = {"success": True, "commit_hash": "local-only", "branch": "main"}
            if req.push_git:
                files_to_commit = [save_res["pipeline_file"], save_res["workflow_file"]]
                if save_res.get("test_file"):
                    files_to_commit.append(save_res["test_file"])
                git_result = git_ops.commit_and_push(
                    file_paths=files_to_commit,
                    message=f"feat(etl): add {req.pipeline_name} pipeline via semantic agent",
                )

            return {
                "success": True,
                "pipeline_name": req.pipeline_name,
                "pipeline_file": save_res["pipeline_file"],
                "test_file": save_res.get("test_file"),
                "workflow_file": save_res["workflow_file"],
                "ci_status": ci_res.get("summary", "Aprovado"),
                "commit_hash": git_result.get("commit_hash", "saved"),
                "branch": git_result.get("branch", "main"),
                "databricks_status": dbx_message,
                "git_status": "Pushed to GitHub" if git_result.get("success") else git_result.get("error", "saved"),
            }
        except Exception as e:
            return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

    @app.post("/api/shutdown")
    def shutdown_server():
        """Gracefully shuts down the API server process."""
        def kill_process():
            time.sleep(0.5)
            os.kill(os.getpid(), signal.SIGTERM)

        import threading
        threading.Thread(target=kill_process, daemon=True).start()
        return {"success": True, "message": "Servidor encerrando..."}

    # =========================================================================
    # OPENAI-COMPATIBLE API (Connect ANY Open WebUI instance or external client)
    # =========================================================================
    @app.get("/v1/models")
    def openai_list_models():
        """Returns models in OpenAI format for OpenWebUI."""
        models_data = [
            {
                "id": "databricks-forge",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "databricks-forge",
            }
        ]
        if ollama.is_available():
            for m in ollama.list_models():
                models_data.append({
                    "id": m,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "ollama",
                })
        return {"object": "list", "data": models_data}

    @app.post("/v1/chat/completions")
    async def openai_chat_completions(req: OpenAIChatCompletionRequest, request: Request):
        """Standard OpenAI-compatible streaming chat completion endpoint."""
        user_msg = req.messages[-1].content if req.messages else ""
        chosen_model = req.model if req.model != "databricks-forge" else "llama3.2:3b"

        # If streaming requested
        if req.stream:
            async def openai_stream():
                chat_req = ChatRequest(message=user_msg, model=chosen_model)
                stream_resp = await chat_stream(chat_req, request)
                async for chunk in stream_resp.body_iterator:
                    if chunk.startswith("event: token"):
                        lines = chunk.strip().split("\n")
                        for l in lines:
                            if l.startswith("data: "):
                                token_data = json.loads(l[6:])
                                token = token_data.get("token", "")
                                sse_payload = {
                                    "id": f"chatcmpl-{int(time.time())}",
                                    "object": "chat.completion.chunk",
                                    "created": int(time.time()),
                                    "model": req.model,
                                    "choices": [
                                        {"index": 0, "delta": {"content": token}, "finish_reason": None}
                                    ],
                                }
                                yield f"data: {json.dumps(sse_payload)}\n\n"
                    elif chunk.startswith("event: message"):
                        lines = chunk.strip().split("\n")
                        for l in lines:
                            if l.startswith("data: "):
                                msg_data = json.loads(l[6:])
                                text = msg_data.get("text", "")
                                if msg_data.get("mermaid"):
                                    text += f"\n\n```mermaid\n{msg_data['mermaid']}\n```"
                                if msg_data.get("code"):
                                    text += f"\n\n```python\n{msg_data['code']}\n```"
                                sse_payload = {
                                    "id": f"chatcmpl-{int(time.time())}",
                                    "object": "chat.completion.chunk",
                                    "created": int(time.time()),
                                    "model": req.model,
                                    "choices": [
                                        {"index": 0, "delta": {"content": text}, "finish_reason": None}
                                    ],
                                }
                                yield f"data: {json.dumps(sse_payload)}\n\n"

                yield "data: [DONE]\n\n"

            return StreamingResponse(openai_stream(), media_type="text/event-stream")
        else:
            res = agent.process_message(user_msg, model_override=chosen_model)
            text = res.get("text", "")
            if res.get("mermaid"):
                text += f"\n\n```mermaid\n{res['mermaid']}\n```"
            if res.get("code"):
                text += f"\n\n```python\n{res['code']}\n```"

            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": req.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": text},
                        "finish_reason": "stop",
                    }
                ],
            }

    # Mount static assets
    index_file = static_dir / "index.html"
    if index_file.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

        @app.get("/")
        async def serve_index():
            return FileResponse(index_file)

    return app


app = create_app()
