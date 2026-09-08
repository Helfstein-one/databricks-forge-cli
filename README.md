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
- 🌐 **Orquestração de Múltiplos Jobs em DAG**: Defina grafos de tarefas com dependências (`depends_on`) no `workflow.yaml`, com validação topológica, detecção de ciclos e geração de **Master DAG Runner** para o Databricks Community Edition ou payload nativo da Jobs API v2.1.
- 🗄️ **Suporte Nativo a Jobs SQL**: Execute scripts `.sql` localmente em Delta Lake ou faça deploy de consultas diretamente no Databricks Workspace.
- 💻 **Catálogo de Máquinas & Compute**: Escolha nós para **AWS** (`i3.xlarge`, `m5d.large`), **Azure** (`Standard_DS3_v2`, `D4s_v5`), **GCP** (`n1-standard-4`) e **Community Edition** (`SingleNode` gratuito, 0 workers).
- 🔒 **Secrets & Variáveis de Ambiente**: Sincronização automática do arquivo local `.env` com os Secret Scopes do Databricks (`forge secret sync-env`) e função híbrida `get_secret(scope, key)`.
- 🐳 **Ambiente Docker Local**: Desenvolva e teste com PySpark 3.5, Delta Lake 3.0 e Chispa com volume local persistente sem custo de cloud.
- 🔌 **Databricks Connect v2**: Alterne para modo remoto com `EXECUTION_MODE=remote` conectando sua IDE diretamente ao cluster ativo.

---

## 🏛️ Desenho de Solução & Arquitetura

O blueprint técnico abaixo detalha a esteira completa e os fluxos de trabalho do Databricks Forge:

![Databricks Forge Architecture](docs/architecture.svg)

> 💡 **Arquivo Editável**: O diagrama XML correspondente está disponível em [`docs/architecture.drawio`](docs/architecture.drawio). Abra-o no [diagrams.net](https://app.diagrams.net/).

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

---

## 🧰 Referência Completa de Comandos

### Comandos Centrais
| Comando | Descrição |
|---|---|
| `forge init <name>` | Gera novo projeto Lakehouse com DAG, Docker, Chispa e CI/CD |
| `forge build` | Compila o pacote `.whl` do projeto |
| `forge deploy` | Envia Wheel, SQLs e Master DAG Runner para o Databricks Workspace |
| `forge check` | Diagnóstico de pré-requisitos (Python, Java, Docker, Databricks API) |
| `forge run-notebook` | Gera URL direta e guia de execução para o notebook no Databricks CE |

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
