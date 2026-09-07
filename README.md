<div align="center">

![Databricks Forge Hero Banner](assets/hero_banner.png)

# ⚡ Databricks Forge CLI

**Industrial-grade CLI for scaffolding, testing, packaging, and deploying PySpark Lakehouse projects to Databricks Community Edition & Databricks Connect.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-3.5.0-E25A1C.svg?logo=apachespark&logoColor=white)](https://spark.apache.org/)
[![Delta Lake](https://img.shields.io/badge/Delta%20Lake-3.0.0-00ADEF.svg)](https://delta.io/)
[![Chispa](https://img.shields.io/badge/Testing-Chispa%20%2B%20pytest-brightgreen.svg)](https://github.com/MrPowers/chispa)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF.svg?logo=githubactions&logoColor=white)](https://github.com/Helfstein-one/databricks-forge-cli/actions)

</div>

---

## 🎯 Por que o Databricks Forge?

Desenvolver para Databricks tradicionalmente apresenta dores conhecidas:
1. **Dependência excessiva de nuvem**: Rodar cada iteração de código em clusters custa tempo e dinheiro.
2. **Databricks Community Edition (CE)**: Embora gratuito e ideal para estudos e protótipos, **não possui a Jobs API v2.1**, dificultando a automação de pipelines e CI/CD.
3. **Diferenças de runtime**: O código roda de forma diferente localmente vs. no cluster remoto.

O **`databricks-forge-cli`** resolve esses desafios entregando a **Tríade de Execução**:

- 🐳 **Ambiente Docker Local**: Teste PySpark 3.5 + Delta Lake 3.0 em container com volume persistente para ACID Lakehouse sem nenhum custo de cloud.
- 🔌 **Databricks Connect v2**: Programe na sua IDE favorita (VS Code, Cursor, PyCharm) conectado diretamente ao driver do seu cluster remoto.
- 🚀 **Automação Databricks CE**: Empacotamento em Wheels (`.whl`) e sincronização automatizada no Workspace do Databricks CE via REST Workspace Import API (`/api/2.0/workspace/import`), acompanhado de um **Runner Notebook** interativo com Databricks Widgets.

---

## 🏛️ Desenho de Solução & Arquitetura

O diagrama abaixo ilustra o ciclo de vida completo orquestrado pelo Databricks Forge CLI:

![Databricks Forge Architecture](docs/architecture.svg)

> 💡 **Nota**: O diagrama editável está disponível em [`docs/architecture.drawio`](docs/architecture.drawio). Abra-o diretamente no [diagrams.net (Draw.io)](https://app.diagrams.net/).

---

## 📦 Instalação

```bash
# Via pip diretamente do repositório
pip install git+https://github.com/Helfstein-one/databricks-forge-cli.git

# Ou clone para desenvolvimento local
git clone https://github.com/Helfstein-one/databricks-forge-cli.git
cd databricks-forge-cli
pip install -e ".[dev]"
```

Comandos disponíveis no terminal: `forge` ou `databricks-forge`.

---

## 🚀 Guia Rápido (Quickstart)

### 1. Diagnóstico do Ambiente Local
Verifique se sua máquina possui Python, Java Runtime, Docker/Podman e credenciais do Databricks:
```bash
forge check
```

### 2. Criar um Novo Projeto Lakehouse
Gere a estrutura completa com Docker, Chispa, Databricks Connect e GitHub Actions:
```bash
forge init customer-analytics-lakehouse
cd customer-analytics-lakehouse
```

### 3. Rodar os Testes Locais com Chispa e Benchmark
```bash
# Executa a suíte de testes com Chispa sem subir cluster
make unit-test

# Ou execute dentro do container Docker (sem precisar de Java local)
make docker-test
```

### 4. Compilar o Pacote Wheel
```bash
forge build
```

### 5. Fazer o Deploy no Databricks Community Edition
```bash
forge deploy \
  --host "https://community.cloud.databricks.com" \
  --token "dapi_seu_token_aqui" \
  --target-path "/Shared/forge_deployments/customer_analytics" \
  --upload-notebook
```

### 6. Executar o Runner Notebook no Databricks CE
```bash
forge run-notebook --target-path "/Shared/forge_deployments/customer_analytics"
```
A CLI fornecerá a URL direta do Workspace e instruções passo-a-passo para execução imediata no Databricks.

---

## 🧰 Referência de Comandos da CLI

| Comando | Descrição | Exemplo de Uso |
|---|---|---|
| `forge init <name>` | Gera um novo repositório com arquitetura Lakehouse e CI/CD | `forge init retail-lakehouse -o ~/dev` |
| `forge build` | Compila o projeto em pacote `.whl` otimizado | `forge build --clean` |
| `forge deploy` | Envia pacote `.whl` e Runner Notebook para o Databricks CE via Workspace API | `forge deploy -t /Shared/deployments` |
| `forge run-notebook` | Gera link direto e guia de execução do notebook no Databricks CE | `forge run-notebook -t /Shared/deployments` |
| `forge check` | Diagnóstico de pré-requisitos (Python, Java, Docker, Databricks CE) | `forge check` |
| `forge --version` | Exibe a versão instalada da CLI | `forge -v` |

---

## 📂 Estrutura do Projeto Gerado (`base_project`)

Ao executar `forge init meu-projeto`, a seguinte estrutura é instanciada:

```text
meu-projeto/
├── .github/workflows/
│   ├── ci.yml                 # Lint (Ruff), Testes (Chispa), Benchmark & Wheel Build
│   └── cd.yml                 # Auto-deploy no Databricks CE na branch main
├── config/
│   ├── local_config.yaml      # Configurações do Lakehouse local
│   └── databricks_ce.yaml     # Configurações do catálogo no Databricks CE
├── docker/
│   ├── Dockerfile             # Imagem com Debian, OpenJDK 11, PySpark 3.5 e Delta 3.0
│   └── docker-compose.yml     # Mapeamento do volume local_data_lake
├── notebooks/
│   └── run_pipeline_notebook.py # Runner Notebook interativo com Widgets para Databricks CE
├── src/meu_projeto/
│   ├── __init__.py
│   ├── session.py             # SparkSession Factory (Local Delta vs Databricks Connect v2)
│   ├── catalog.py             # Abstração de persistência (Delta Local vs Metastore)
│   ├── entrypoint.py          # Script de execução CLI do pipeline
│   └── pipelines/
│       ├── __init__.py
│       └── example_pipeline.py# Medallion Pipeline (Bronze -> Silver -> Gold)
├── tests/
│   ├── conftest.py            # Fixtures de SparkSession local e Lake temporário
│   ├── unit/
│   │   └── test_transforms.py # Testes Chispa (assert_df_equality)
│   ├── integration/
│   │   └── test_catalog.py    # Testes de persistência com CatalogManager
│   └── performance/
│       └── test_throughput.py # Benchmarks de volumetria com pytest-benchmark
├── Makefile                   # Atalhos de desenvolvimento (make install, make test, etc.)
├── pyproject.toml             # Metadados e dependências do projeto gerado
├── .env.example               # Exemplo de variáveis de ambiente
└── README.md
```

---

## 🔄 Camadas Centrais de Abstração

### 1. `session.py`: SparkSession Híbrida

Chaveia automaticamente entre execução local e remota sem alterar nenhuma linha de código:

```python
from meu_projeto.session import get_spark

# Se EXECUTION_MODE=local: inicia PySpark local com Delta Lake
# Se EXECUTION_MODE=remote: conecta via Databricks Connect v2
spark = get_spark()
```

### 2. `catalog.py`: Abstração de Catálogo

Isola o código do pipeline da infraestrutura de armazenamento:

```python
from meu_projeto.catalog import CatalogManager

catalog = CatalogManager(spark)

# Localmente grava em ./data_lake/transactions_silver
# No Databricks grava em default.transactions_silver
catalog.save_table(silver_df, "transactions_silver", mode="overwrite")
```

### 3. `notebooks/run_pipeline_notebook.py`: Databricks CE Runner

Utiliza a sintaxe nativa de Databricks Notebook (`# Databricks notebook source`), com:
- **Widgets de controle**: Altere volume de dados (`row_count`), nível de log (`log_level`) e parâmetros dinamicamente.
- **Auto-instalação**: Instala o Wheel publicado no Workspace via `%pip install`.
- **Relatório e Validação**: Exibe métricas de execução e assertivas de qualidade.

---

## 🔒 Configuração de Secrets para o GitHub Actions

Para ativar a esteira de CD automática (`.github/workflows/cd.yml`) no repositório gerado:

1. No seu repositório GitHub, acesse **Settings** > **Secrets and variables** > **Actions**.
2. Adicione os seguintes segredos:
   - `DATABRICKS_HOST`: URL do seu Databricks CE (ex: `https://community.cloud.databricks.com`).
   - `DATABRICKS_TOKEN`: Seu Personal Access Token (PAT) gerado nas configurações de usuário do Databricks.

Ao fazer push na branch `main`, o GitHub Actions compila o `.whl` e publica automaticamente no seu Workspace do Databricks CE!

---

## 🧪 Executando os Testes da CLI

```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Executar suíte completa de testes
pytest tests/ -v
```

---

## 📄 Licença

Este projeto é distribuído sob a licença [Apache 2.0](LICENSE).
