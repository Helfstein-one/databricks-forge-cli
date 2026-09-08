<div align="center">

![Databricks Forge Hero Banner](assets/hero_banner.png)

# ⚡ Databricks Forge CLI

**Industrial-grade CLI for scaffolding, testing, packaging, DAG orchestrating, and deploying Lakehouse projects to Databricks Community Edition & Enterprise.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-3.5.0-E25A1C.svg?logo=apachespark&logoColor=white)](https://spark.apache.org/)
[![Delta Lake](https://img.shields.io/badge/Delta%20Lake-3.0.0-00ADEF.svg)](https://delta.io/)
[![Chispa](https://img.shields.io/badge/Testing-Chispa%20%2B%20pytest-brightgreen.svg)](https://github.com/MrPowers/chispa)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF.svg?logo=githubactions&logoColor=white)](https://github.com/Helfstein-one/databricks-forge-cli/actions)

</div>

---

## 🎯 Visão Geral & Proposta de Valor

O **`databricks-forge-cli`** é a ferramenta definitiva de engenharia de dados moderna para criar, testar, orquestrar e implantar projetos PySpark e SQL no Databricks.

### Principais Pilares:
- 🎨 **CLI Visual & Interativa**: Banner ASCII estilizado (`DATABRICKS FORGE CLI`) e feedback rico no terminal via Rich.
- ⚡ **Template Structured Streaming**: Ingestão contínua e micro-batch (`trigger(availableNow=True)`) com Delta Lake, watermarking de 10 minutos, janelas deslizantes/tumbling de 5 minutos e checkpoints tolerantes a falhas.
- 🚀 **Tuning & Otimização de Performance**: Comandos `forge tune` para compactação de arquivos Delta (`OPTIMIZE`), clustering multidimensional (`ZORDER BY`), limpeza segura de snapshots (`VACUUM`) e perfis de Spark AQE (`balanced`, `write_heavy`, `read_heavy`).
- 📊 **Logging Estruturado & Observabilidade**: Formatador JSON ISO 8601 para agregadores de logs (Datadog, CloudWatch), decorator de auditoria `@pipeline_audit_step` para medição automática de latência e contagem de linhas, e gravação em tabela Delta de auditoria (`pipeline_execution_audit`).
- 🌐 **Orquestração de Múltiplos Jobs em DAG**: Defina grafos de tarefas com dependências (`depends_on`) no `workflow.yaml`, com validação topológica, detecção de ciclos e geração de **Master DAG Runner** para o Databricks Community Edition ou payload nativo da Jobs API v2.1.
- 🗄️ **Suporte Nativo a Jobs SQL**: Execute scripts `.sql` localmente em Delta Lake ou faça deploy de consultas diretamente no Databricks Workspace.
- 💻 **Catálogo de Máquinas & Compute**: Escolha nós para **AWS** (`i3.xlarge`, `m5d.large`), **Azure** (`Standard_DS3_v2`, `D4s_v5`), **GCP** (`n1-standard-4`) e **Community Edition** (`SingleNode` gratuito, 0 workers).
- 🔒 **Secrets & Variáveis de Ambiente**: Sincronização automática do arquivo local `.env` com os Secret Scopes do Databricks (`forge secret sync-env`) e função híbrida `get_secret(scope, key)`.
- 🐳 **Ambiente Docker Local**: Desenvolva e teste com PySpark 3.5, Delta Lake 3.0 e Chispa com volume local persistente sem custo de cloud.
- 🔌 **Databricks Connect v2**: Alterne para modo remoto com `EXECUTION_MODE=remote` conectando sua IDE diretamente ao cluster ativo.

---

## 🏛️ Desenho de Solução & Arquitetura

O projeto conta com uma arquitetura modelada em 3 perspectivas integradas:

![Databricks Forge Architecture](docs/architecture.svg)

### 📑 Estrutura Multi-Aba no Draw.io ([`docs/architecture.drawio`](docs/architecture.drawio))

O arquivo [`docs/architecture.drawio`](docs/architecture.drawio) contém **3 abas dedicadas**, prontas para visualização no [diagrams.net (Draw.io)](https://app.diagrams.net/):

1. **Aba 1: Experiência do Usuário (Funcional)**: Mapeamento completo da jornada do desenvolvedor, desde a inicialização com banner 3D, ciclo local sem custos no Docker, gestão de secrets até a execução da pipeline no Databricks CE.
2. **Aba 2: Visão de Negócio (Business & ROI)**: Demonstração de FinOps (redução de 80%+ do compute bill de desenvolvimento), mitigação de riscos de segurança, aceleração de time-to-market e governança da cadeia de valor Medallion.
3. **Aba 3: Visão Técnica & Cloud Architecture**: Visão detalhada de engenharia com Control Plane (REST APIs), Compute Plane (AWS `i3.xlarge`, Azure `DS3_v2`, GCP `n1-standard`, CE `SingleNode`), persistência ACID Delta Lake e CI/CD.

---

## 📦 Instalação

```bash
# Instalação direta via pip do repositório
pip install git+https://github.com/Helfstein-one/databricks-forge-cli.git

# Ou clone para desenvolvimento local
git clone https://github.com/Helfstein-one/databricks-forge-cli.git
cd databricks-forge-cli
pip install -e ".[dev]"
```

Comandos disponíveis no terminal: `forge` ou `databricks-forge`.

---

## 🚀 Guia Rápido (Quickstart)

### 1. Criar um Novo Projeto com Compute & Banner ASCII
```bash
forge init retail-lakehouse --cloud aws --node-type i3.xlarge --workers 2
cd retail-lakehouse
```
Ao rodar, o banner ASCII estilizado **`DATABRICKS FORGE CLI`** é exibido no terminal e o scaffolding completo é montado.

### 2. Validar e Executar o Grafo de Tarefas (DAG)
```bash
# Valida se o workflow.yaml não possui dependências circulares
forge dag validate

# Executa o grafo de tarefas em ordem topológica (Wheel -> SQL -> Notebook)
forge dag run --mode local
```

### 3. Gerenciar Secrets e Variáveis de Ambiente
```bash
# Sincroniza seu .env local diretamente com um Secret Scope no Databricks
forge secret sync-env --scope-name "retail_scope"

# Lista scopes existentes no Databricks
forge secret list
```

No código Python do projeto, utilize a função universal `get_secret`:
```python
from retail_lakehouse.secrets import get_secret

# No Databricks lê via dbutils.secrets.get("retail_scope", "api_key")
# Localmente ou em Docker lê via os.getenv("API_KEY") do seu .env
api_key = get_secret("retail_scope", "api_key")
```

### 4. Executar e Implantar Scripts SQL
```bash
# Executa localmente contra o Delta Lake
forge sql run sql/01_clean_transactions.sql

# Faz deploy no Databricks Workspace
forge sql deploy sql/01_clean_transactions.sql --target-path "/Shared/retail_lakehouse/sql/clean"
```

### 5. Compilar o Wheel e Fazer o Deploy no Databricks CE
```bash
forge build
forge deploy --target-path "/Shared/forge_deployments/retail_lakehouse"
```

### 6. Executar Ingestão Streaming com Delta Lake & Watermarking
O projeto scaffolded vem com template completo de **Structured Streaming**:
```bash
# Executa localmente em modo micro-batch (AvailableNow)
make stream-run
```
No Databricks CE, execute o notebook `notebooks/run_streaming_notebook.py` com widgets interativos:
- **`trigger_mode`**: `available_now` (ótimo para agendamentos econômicos), `continuous`, ou `processing_time`.
- **`watermark_delay`**: atraso tolerado para dados tardios (ex: `10 minutes`).
- **`checkpoint_dir`**: diretório de checkpoint para garantia *exactly-once*.

### 7. Otimização de Performance Delta & Spark AQE
```bash
# Inspeciona perfis de configuração recomendados (AQE, Auto-Compact, Coalescing)
forge tune config --profile balanced

# Gera o plano de compactação (OPTIMIZE) com Z-ORDER em colunas de alta cardinalidade
forge tune optimize transactions_silver --zorder user_id,date

# Gera rotina de expurgo seguro de snapshots históricos (VACUUM)
forge tune vacuum transactions_silver --retention 168
```

### 8. Logging Estruturado & Auditoria de Pipelines
O módulo `logging.py` do projeto scaffolded fornece telemetria pronta para produção:
```python
from retail_lakehouse.logging import setup_pipeline_logging, pipeline_audit_step

# Configura logs em formato JSON padronizado ISO 8601
logger = setup_pipeline_logging(level="INFO", json_format=True)

# Decorator mede latência automaticamente, conta linhas de DataFrames e registra falhas
@pipeline_audit_step(step_name="transform_silver_customers")
def process_customers(df):
    return df.filter("active = true")
```
As métricas também podem ser persistidas na tabela Delta `pipeline_execution_audit`.

---

## 🧰 Referência Completa de Comandos

### Comandos Centrais
| Comando | Descrição |
|---|---|
| `forge init <name>` | Gera novo projeto Lakehouse com DAG, Docker, Chispa, Streaming e CI/CD |
| `forge build` | Compila o pacote `.whl` do projeto |
| `forge deploy` | Envia Wheel, SQLs e Master DAG Runner para o Databricks Workspace |
| `forge check` | Diagnóstico de pré-requisitos (Python, Java, Docker, Databricks API) |
| `forge run-notebook` | Gera URL direta e guia de execução para o notebook no Databricks CE |

### Tuning & Otimização (`forge tune`)
| Comando | Descrição |
|---|---|
| `forge tune optimize <table>` | Gera e executa plano de compactação (`OPTIMIZE`) com `ZORDER BY` |
| `forge tune vacuum <table>` | Gera e executa plano de retenção e limpeza de arquivos obsoletos (`VACUUM`) |
| `forge tune config` | Exibe parâmetros ótimos de Spark AQE, Auto-Compaction e Shuffling |

### DAG & Workflows (`forge dag`)
| Comando | Descrição |
|---|---|
| `forge dag validate` | Valida o grafo, resolve dependências e detecta ciclos |
| `forge dag run` | Executa localmente as tarefas na ordem topológica resolvida |
| `forge dag export` | Exporta o DAG para payload JSON nativo da Databricks Jobs API v2.1 |

### Jobs SQL (`forge sql`)
| Comando | Descrição |
|---|---|
| `forge sql run <file.sql>` | Executa script SQL em PySpark Local Delta ou Databricks Connect |
| `forge sql deploy <file.sql>` | Publica o script SQL no Workspace da Databricks |

### Secrets & .env (`forge secret`)
| Comando | Descrição |
|---|---|
| `forge secret list` | Lista Secret Scopes ou chaves em um scope |
| `forge secret create-scope <name>` | Cria um novo Secret Scope no Databricks |
| `forge secret set <scope> <key>` | Define um secret de forma segura |
| `forge secret sync-env` | Sincroniza chaves do `.env` local para o Databricks Secret Scope |

### Compute & Máquinas (`forge compute`)
| Comando | Descrição |
|---|---|
| `forge compute list --cloud aws` | Lista nós suportados da AWS (i3.xlarge, m5d, c5, r5) |
| `forge compute list --cloud azure` | Lista VMs Azure (Standard_DS3_v2, D4s_v5, E4ds_v4) |
| `forge compute list --cloud gcp` | Lista instâncias GCP (n1-standard, n2-highmem) |
| `forge compute list --cloud ce` | Exibe perfil Single-Node gratuito do Community Edition |

---

## 🌐 Exemplo de Orquestração: `workflow.yaml`

```yaml
name: "ecommerce_pipeline_dag"
description: "Pipeline Medallion com Python Wheel, SQL e Notebook"

compute:
  cloud: "aws"
  node_type_id: "i3.xlarge"
  spark_version: "14.3.x-scala2.12"
  single_node: false
  num_workers: 2

tasks:
  - name: "ingest_bronze"
    type: "python_wheel"
    entrypoint: "ecommerce.entrypoint:main"
    parameters:
      rows: 1000

  - name: "clean_silver_sql"
    type: "sql"
    depends_on: ["ingest_bronze"]
    file: "sql/01_clean_transactions.sql"

  - name: "aggregate_gold_sql"
    type: "sql"
    depends_on: ["clean_silver_sql"]
    file: "sql/02_gold_metrics.sql"

  - name: "analytics_dashboard"
    type: "notebook"
    depends_on: ["aggregate_gold_sql"]
    path: "notebooks/run_pipeline_notebook.py"
```

---

## 🧪 Testes Automatizados

A CLI conta com cobertura de testes unitários e de integração:

```bash
# Executa todos os testes
pytest tests/ -v
```

---

## 📄 Licença

Este projeto é distribuído sob a licença [Apache 2.0](LICENSE).
