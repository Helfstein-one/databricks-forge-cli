"""
Complete Generator for docs/architecture.drawio
Creates 3 distinct, high-impact architecture tabs:
1. Experiência do Desenvolvedor (Funcional)
2. Visão de Negócio (FinOps, ROI & Governança)
3. Solução de Dados (Databricks & AWS com Ícones Oficiais)
"""

import base64
import html
import os
import xml.etree.ElementTree as ET

def make_svg_data_uri(svg_content: str) -> str:
    clean = svg_content.strip()
    encoded = base64.b64encode(clean.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"

# --- OFFICIAL SVG DEFINITIONS ---

SVG_DATABRICKS = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <polygon points="50,6 94,28 50,50 6,28" fill="#FF3621"/>
  <polygon points="6,42 50,64 94,42 82,36 50,52 18,36" fill="#E02917"/>
  <polygon points="6,56 50,78 94,56 82,50 50,66 18,50" fill="#C42010"/>
  <polygon points="6,70 50,92 94,70 82,64 50,80 18,64" fill="#991509"/>
</svg>"""

SVG_AWS_S3 = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="12" y="12" width="76" height="76" rx="10" fill="#E05243"/>
  <ellipse cx="50" cy="34" rx="28" ry="10" fill="#FFFFFF" opacity="0.95"/>
  <path d="M22,34 v18 c0,7 13,11 28,11 s28,-4 28,-11 v-18" fill="none" stroke="#FFFFFF" stroke-width="4.5"/>
  <path d="M22,54 v18 c0,7 13,11 28,11 s28,-4 28,-11 v-18" fill="none" stroke="#FFFFFF" stroke-width="4.5"/>
</svg>"""

SVG_AWS_RDS = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="12" y="12" width="76" height="76" rx="10" fill="#3B48CC"/>
  <ellipse cx="50" cy="32" rx="26" ry="9" fill="#FFFFFF" opacity="0.95"/>
  <path d="M24,32 v16 c0,6 12,10 26,10 s26,-4 26,-10 v-16" fill="none" stroke="#FFFFFF" stroke-width="4"/>
  <path d="M24,49 v16 c0,6 12,10 26,10 s26,-4 26,-10 v-16" fill="none" stroke="#FFFFFF" stroke-width="4"/>
  <path d="M24,66 v16 c0,6 12,10 26,10 s26,-4 26,-10 v-16" fill="none" stroke="#FFFFFF" stroke-width="4"/>
</svg>"""

SVG_AWS_KINESIS = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="12" y="12" width="76" height="76" rx="10" fill="#8C4FFF"/>
  <path d="M28,28 L50,40 L72,28 L72,72 L50,84 L28,72 Z" fill="none" stroke="#FFFFFF" stroke-width="4.5"/>
  <line x1="50" y1="40" x2="50" y2="84" stroke="#FFFFFF" stroke-width="4.5"/>
  <line x1="28" y1="50" x2="50" y2="62" stroke="#FFFFFF" stroke-width="3.5"/>
  <line x1="72" y1="50" x2="50" y2="62" stroke="#FFFFFF" stroke-width="3.5"/>
</svg>"""

SVG_AWS_SECRETS = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="12" y="12" width="76" height="76" rx="10" fill="#DD344C"/>
  <circle cx="50" cy="42" r="14" fill="none" stroke="#FFFFFF" stroke-width="4.5"/>
  <rect x="34" y="44" width="32" height="30" rx="5" fill="#FFFFFF"/>
  <circle cx="50" cy="56" r="4" fill="#DD344C"/>
  <line x1="50" y1="58" x2="50" y2="68" stroke="#DD344C" stroke-width="3.5"/>
</svg>"""

SVG_AWS_IAM = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="12" y="12" width="76" height="76" rx="10" fill="#DD344C"/>
  <circle cx="50" cy="38" r="13" fill="#FFFFFF"/>
  <path d="M26,76 c0,-13 11,-21 24,-21 s24,8 24,21 Z" fill="#FFFFFF"/>
  <circle cx="70" cy="64" r="9" fill="#FFD700" stroke="#DD344C" stroke-width="2.5"/>
  <rect x="68" y="70" width="4" height="10" fill="#FFD700"/>
</svg>"""

SVG_AWS_EC2 = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="12" y="12" width="76" height="76" rx="10" fill="#ED7100"/>
  <rect x="30" y="30" width="40" height="40" fill="none" stroke="#FFFFFF" stroke-width="4.5"/>
  <rect x="42" y="42" width="16" height="16" fill="#FFFFFF"/>
  <line x1="30" y1="38" x2="18" y2="38" stroke="#FFFFFF" stroke-width="4"/>
  <line x1="30" y1="50" x2="18" y2="50" stroke="#FFFFFF" stroke-width="4"/>
  <line x1="30" y1="62" x2="18" y2="62" stroke="#FFFFFF" stroke-width="4"/>
  <line x1="70" y1="38" x2="82" y2="38" stroke="#FFFFFF" stroke-width="4"/>
  <line x1="70" y1="50" x2="82" y2="50" stroke="#FFFFFF" stroke-width="4"/>
  <line x1="70" y1="62" x2="82" y2="62" stroke="#FFFFFF" stroke-width="4"/>
</svg>"""

SVG_AWS_CLOUDWATCH = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="12" y="12" width="76" height="76" rx="10" fill="#E7157B"/>
  <circle cx="50" cy="50" r="28" fill="none" stroke="#FFFFFF" stroke-width="4.5"/>
  <polyline points="30,58 44,40 54,54 70,34" fill="none" stroke="#FFFFFF" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>"""

SVG_AWS_ATHENA = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="12" y="12" width="76" height="76" rx="10" fill="#8C4FFF"/>
  <circle cx="45" cy="45" r="20" fill="none" stroke="#FFFFFF" stroke-width="4.5"/>
  <line x1="60" y1="60" x2="78" y2="78" stroke="#FFFFFF" stroke-width="6" stroke-linecap="round"/>
  <line x1="33" y1="45" x2="57" y2="45" stroke="#FFFFFF" stroke-width="3.5"/>
  <line x1="45" y1="33" x2="45" y2="57" stroke="#FFFFFF" stroke-width="3.5"/>
</svg>"""

SVG_AWS_REDSHIFT = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="12" y="12" width="76" height="76" rx="10" fill="#8C4FFF"/>
  <polygon points="50,22 80,39 80,71 50,88 20,71 20,39" fill="none" stroke="#FFFFFF" stroke-width="4.5"/>
  <polygon points="50,36 70,48 70,69 50,79 30,69 30,48" fill="#FFFFFF" opacity="0.45"/>
</svg>"""

SVG_DELTA_LAKE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <polygon points="50,10 92,84 8,84" fill="#00A8FF"/>
  <polygon points="50,34 78,80 22,80" fill="#004D80"/>
  <polygon points="50,50 68,77 32,77" fill="#00D2FF"/>
</svg>"""

SVG_ICEBERG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="44" fill="#EBF8FF" stroke="#0284C7" stroke-width="3.5"/>
  <polygon points="50,16 70,45 30,45" fill="#38BDF8"/>
  <polygon points="50,16 50,45 70,45" fill="#0284C7"/>
  <line x1="14" y1="46" x2="86" y2="46" stroke="#0369A1" stroke-width="4" stroke-dasharray="4,3"/>
  <polygon points="50,84 76,47 24,47" fill="#0284C7" opacity="0.85"/>
  <polygon points="50,84 50,47 76,47" fill="#0369A1" opacity="0.9"/>
</svg>"""

SVG_APACHE_SPARK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M50,8 C53,28 69,37 84,39 C70,47 64,57 67,74 C56,60 46,60 35,74 C38,57 32,47 16,39 C31,37 47,28 50,8 Z" fill="#E25A1C"/>
  <circle cx="50" cy="46" r="8.5" fill="#F89C1E"/>
</svg>"""

SVG_UNITY_CATALOG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M50,8 L84,24 L84,58 C84,76 50,92 50,92 C50,92 16,76 16,58 L16,24 Z" fill="#1B2559" stroke="#FF3621" stroke-width="4"/>
  <circle cx="50" cy="42" r="11" fill="#FF3621"/>
  <circle cx="35" cy="64" r="7.5" fill="#00A8FF"/>
  <circle cx="65" cy="64" r="7.5" fill="#10B981"/>
  <line x1="50" y1="42" x2="35" y2="64" stroke="#FFFFFF" stroke-width="3"/>
  <line x1="50" y1="42" x2="65" y2="64" stroke="#FFFFFF" stroke-width="3"/>
  <line x1="35" y1="64" x2="65" y2="64" stroke="#FFFFFF" stroke-width="3"/>
</svg>"""

SVG_SERVERLESS_COMPUTE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M28,68 C21,68 15,62 15,55 C15,48 20,43 25,42 C27,31 36,24 47,24 C57,24 65,30 68,39 C72,39 77,43 78,48 C84,49 88,54 88,61 C88,68 82,74 74,74 L28,74 Z" fill="#FF3621"/>
  <polygon points="52,34 38,54 50,54 44,70 62,48 50,48" fill="#FFFFFF"/>
</svg>"""

SVG_DATABASE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="12" y="12" width="76" height="76" rx="10" fill="#0284C7"/>
  <ellipse cx="50" cy="30" rx="26" ry="9" fill="#FFFFFF" opacity="0.95"/>
  <path d="M24,30 v18 c0,6 12,10 26,10 s26,-4 26,-10 v-18" fill="none" stroke="#FFFFFF" stroke-width="4"/>
  <path d="M24,49 v18 c0,6 12,10 26,10 s26,-4 26,-10 v-18" fill="none" stroke="#FFFFFF" stroke-width="4"/>
  <path d="M24,68 v14 c0,6 12,9 26,9 s26,-3 26,-9 v-14" fill="none" stroke="#FFFFFF" stroke-width="4"/>
</svg>"""

URI_DATABRICKS = make_svg_data_uri(SVG_DATABRICKS)
URI_AWS_S3 = make_svg_data_uri(SVG_AWS_S3)
URI_AWS_RDS = make_svg_data_uri(SVG_AWS_RDS)
URI_AWS_KINESIS = make_svg_data_uri(SVG_AWS_KINESIS)
URI_AWS_SECRETS = make_svg_data_uri(SVG_AWS_SECRETS)
URI_AWS_IAM = make_svg_data_uri(SVG_AWS_IAM)
URI_AWS_EC2 = make_svg_data_uri(SVG_AWS_EC2)
URI_AWS_CLOUDWATCH = make_svg_data_uri(SVG_AWS_CLOUDWATCH)
URI_AWS_ATHENA = make_svg_data_uri(SVG_AWS_ATHENA)
URI_AWS_REDSHIFT = make_svg_data_uri(SVG_AWS_REDSHIFT)
URI_DELTA_LAKE = make_svg_data_uri(SVG_DELTA_LAKE)
URI_ICEBERG = make_svg_data_uri(SVG_ICEBERG)
URI_APACHE_SPARK = make_svg_data_uri(SVG_APACHE_SPARK)
URI_UNITY_CATALOG = make_svg_data_uri(SVG_UNITY_CATALOG)
URI_SERVERLESS = make_svg_data_uri(SVG_SERVERLESS_COMPUTE)
URI_DATABASE = make_svg_data_uri(SVG_DATABASE)

def escape_xml(s: str) -> str:
    return html.escape(s, quote=True)

# Generate Tab 1: Functional
def build_tab1_functional() -> str:
    cells = []
    
    # Header
    cells.append(f"""
      <mxCell id="f_header" value="Databricks Forge CLI — Jornada do Engenheiro de Dados (Visão Funcional)" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=24;fontStyle=1;fontColor=#FF3621;" vertex="1" parent="1">
        <mxGeometry x="250" y="30" width="1300" height="40" as="geometry" />
      </mxCell>
      <mxCell id="f_sub" value="Fluxo completo de engenharia: Scaffolding ➔ Gestão de Secrets ➔ Ingestão Multi-Banco ➔ Dev Local Docker/Chispa ➔ Tunning &amp; Iceberg UniForm ➔ Orquestração DAG ➔ CI/CD &amp; Deploy Remoto" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=13;fontColor=#64748B;" vertex="1" parent="1">
        <mxGeometry x="250" y="70" width="1300" height="25" as="geometry" />
      </mxCell>
    """)

    # Stage 1: Init
    cells.append("""
      <mxCell id="f_s1" value="Etapa 1: Scaffolding Inteligente&#xa;&#xa;Comando:&#xa;forge init customer-lakehouse&#xa;--cloud aws --streaming --iceberg&#xa;&#xa;Entregáveis:&#xa;• Arquitetura Medallion pré-configurada&#xa;• Suporte nativo a Delta &amp; Iceberg UniForm&#xa;• Pipeline Streaming &amp; Batch configurado&#xa;• pyproject.toml, Dockerfile e testes Chispa" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#EFF6FF;strokeColor=#3B82F6;align=left;spacingLeft=15;fontSize=12;fontStyle=0;" vertex="1" parent="1">
        <mxGeometry x="60" y="130" width="370" height="190" as="geometry" />
      </mxCell>
    """)

    # Stage 2: Secrets
    cells.append("""
      <mxCell id="f_s2" value="Etapa 2: Gestão Segura de Secrets&#xa;&#xa;Comando:&#xa;forge secret sync-env --scope-name &quot;retail_scope&quot;&#xa;&#xa;Funcionalidades:&#xa;• Migração bidirecional .env ➔ Databricks Secret Scopes&#xa;• Resolução inteligente: get_secret(scope, key)&#xa;• Zero senhas ou chaves em plain text no Git&#xa;• Suporte a ambientes: dev, staging, prod" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ECFDF5;strokeColor=#10B981;align=left;spacingLeft=15;fontSize=12;fontStyle=0;" vertex="1" parent="1">
        <mxGeometry x="480" y="130" width="370" height="190" as="geometry" />
      </mxCell>
    """)

    # Stage 3: Connectors
    cells.append("""
      <mxCell id="f_s3" value="Etapa 3: Ingestão &amp; Conectores DB&#xa;&#xa;Comandos:&#xa;forge connector list&#xa;forge connector plan-ingest --engine postgres&#xa;&#xa;Capacidades:&#xa;• Catálogo JDBC: PostgreSQL, MySQL, Oracle, SQLServer&#xa;• Verificação ativa de conectividade e portas&#xa;• Planos de leitura particionada otimizada&#xa;• Ingestão direta na camada Bronze Delta" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF3C7;strokeColor=#F59E0B;align=left;spacingLeft=15;fontSize=12;fontStyle=0;" vertex="1" parent="1">
        <mxGeometry x="900" y="130" width="370" height="190" as="geometry" />
      </mxCell>
    """)

    # Stage 4: Local Dev & Chispa
    cells.append("""
      <mxCell id="f_s4" value="Etapa 4: Dev Local &amp; Testes Chispa&#xa;&#xa;Comandos:&#xa;make docker-test (ou make unit-test)&#xa;&#xa;Diferenciais:&#xa;• Container com OpenJDK 11 e PySpark 3.5&#xa;• Testes unitários Chispa (assert_df_equality)&#xa;• Gravação ACID em volume local Delta Lake&#xa;• CUSTO ZERO de DBU e nuvem em testes" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FAF5FF;strokeColor=#A855F7;align=left;spacingLeft=15;fontSize=12;fontStyle=0;" vertex="1" parent="1">
        <mxGeometry x="1320" y="130" width="370" height="190" as="geometry" />
      </mxCell>
    """)

    # Stage 5: Tuning & Iceberg
    cells.append("""
      <mxCell id="f_s5" value="Etapa 5: Tunning &amp; Formatos Abertos&#xa;&#xa;Comandos:&#xa;forge tune optimize --zorder-cols &quot;customer_id&quot;&#xa;forge iceberg enable-uniform --table-name &quot;sales&quot;&#xa;&#xa;Recursos:&#xa;• Compactação de pequenos arquivos Delta&#xa;• Perfis de tuning: Balanced, Aggressive, Cost-Saving&#xa;• Habilitação UniForm (Delta + Apache Iceberg)&#xa;• Interoperabilidade com Athena e Redshift" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F0FDF4;strokeColor=#16A34A;align=left;spacingLeft=15;fontSize=12;fontStyle=0;" vertex="1" parent="1">
        <mxGeometry x="60" y="380" width="370" height="190" as="geometry" />
      </mxCell>
    """)

    # Stage 6: DAG Multi-Job
    cells.append("""
      <mxCell id="f_s6" value="Etapa 6: Orquestração de DAG Multi-Job&#xa;&#xa;Comandos:&#xa;forge dag validate (Kahn Topological Sort)&#xa;forge dag run-dag --dag-path workflow.yaml&#xa;&#xa;Grafo de Tarefas:&#xa;1. Ingestão Bronze (Batch &amp; Streaming)&#xa;2. Limpeza Silver (Deduplicação &amp; Schema)&#xa;3. Agregações Gold (Métricas &amp; KPIs)&#xa;4. Validação de ciclos (Zero DAGCycleError)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFBEB;strokeColor=#D97706;align=left;spacingLeft=15;fontSize=12;fontStyle=0;" vertex="1" parent="1">
        <mxGeometry x="480" y="380" width="370" height="190" as="geometry" />
      </mxCell>
    """)

    # Stage 7: CI/CD & Build
    cells.append("""
      <mxCell id="f_s7" value="Etapa 7: Build &amp; Esteira de CI/CD&#xa;&#xa;Comandos:&#xa;forge build (Empacota dist/*.whl)&#xa;git push origin main&#xa;&#xa;Automação GitHub Actions:&#xa;• Linting estrito com Ruff&#xa;• Matriz de testes Python 3.10, 3.11 e 3.12&#xa;• Benchmarks de performance de dados&#xa;• Upload automatizado do Wheel compilado" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F1F5F9;strokeColor=#64748B;align=left;spacingLeft=15;fontSize=12;fontStyle=0;" vertex="1" parent="1">
        <mxGeometry x="900" y="380" width="370" height="190" as="geometry" />
      </mxCell>
    """)

    # Stage 8: Remote Databricks Execution
    cells.append("""
      <mxCell id="f_s8" value="Etapa 8: Deploy &amp; Execução Remota&#xa;&#xa;Comandos:&#xa;forge job run-dag --dag-path workflow.yaml&#xa;forge deploy --target-path &quot;/Shared/lakehouse&quot;&#xa;&#xa;Execução em Nuvem:&#xa;• Suporte nativo a Databricks Serverless Compute&#xa;• Orquestração via Databricks Jobs API v2.1&#xa;• Logs estruturados em JSON com rastreamento&#xa;• Fallback Master DAG Runner para Community Edition" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF1F2;strokeColor=#E11D48;align=left;spacingLeft=15;fontSize=12;fontStyle=0;" vertex="1" parent="1">
        <mxGeometry x="1320" y="380" width="370" height="190" as="geometry" />
      </mxCell>
    """)

    # Flow connections
    cells.append("""
      <mxCell id="fa1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=3;strokeColor=#3B82F6;" edge="1" parent="1" source="f_s1" target="f_s2"><mxGeometry relative="1" as="geometry" /></mxCell>
      <mxCell id="fa2" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=3;strokeColor=#10B981;" edge="1" parent="1" source="f_s2" target="f_s3"><mxGeometry relative="1" as="geometry" /></mxCell>
      <mxCell id="fa3" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=3;strokeColor=#F59E0B;" edge="1" parent="1" source="f_s3" target="f_s4"><mxGeometry relative="1" as="geometry" /></mxCell>
      <mxCell id="fa4" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=3;strokeColor=#A855F7;" edge="1" parent="1" source="f_s4" target="f_s5">
        <mxGeometry relative="1" as="geometry">
          <Array as="points">
            <mxPoint x="1505" y="350" />
            <mxPoint x="245" y="350" />
          </Array>
        </mxGeometry>
      </mxCell>
      <mxCell id="fa5" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=3;strokeColor=#16A34A;" edge="1" parent="1" source="f_s5" target="f_s6"><mxGeometry relative="1" as="geometry" /></mxCell>
      <mxCell id="fa6" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=3;strokeColor=#D97706;" edge="1" parent="1" source="f_s6" target="f_s7"><mxGeometry relative="1" as="geometry" /></mxCell>
      <mxCell id="fa7" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=3;strokeColor=#64748B;" edge="1" parent="1" source="f_s7" target="f_s8"><mxGeometry relative="1" as="geometry" /></mxCell>
    """)

    # Bottom Summary Banner
    cells.append("""
      <mxCell id="f_summary" value="Impacto na Experiência do Desenvolvedor:&#xa;Padronização corporativa em 100% dos repositórios • Feedback loop de segundos sem custos de nuvem durante o desenvolvimento • Transição transparente do ambiente local para o Databricks em Produção" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1E293B;fontColor=#FFFFFF;fontStyle=1;fontSize=13;align=center;" vertex="1" parent="1">
        <mxGeometry x="60" y="620" width="1630" height="75" as="geometry" />
      </mxCell>
    """)

    return "\n".join(cells)

# Generate Tab 2: Business & ROI
def build_tab2_business() -> str:
    cells = []
    
    # Header
    cells.append("""
      <mxCell id="b_header" value="Arquitetura de Negócio — Proposta de Valor, FinOps, ROI &amp; Governança" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=24;fontStyle=1;fontColor=#059669;" vertex="1" parent="1">
        <mxGeometry x="250" y="30" width="1300" height="40" as="geometry" />
      </mxCell>
      <mxCell id="b_sub" value="Como o Databricks Forge CLI gera valor estratégico: Redução de até 85% nos custos de nuvem, aceleração do Time-to-Market e conformidade corporativa" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=13;fontColor=#64748B;" vertex="1" parent="1">
        <mxGeometry x="250" y="70" width="1300" height="25" as="geometry" />
      </mxCell>
    """)

    # 4 Strategic Pillars
    cells.append("""
      <mxCell id="b_p1" value="FinOps &amp; Otimização de Custos (80-90% Economia)&#xa;&#xa;• Custo Zero de DBU em Desenvolvimento:&#xa;  Testes de transformação e validações de dados&#xa;  rodam 100% no Docker local com PySpark + Chispa.&#xa;• Computação Serverless sob Demanda:&#xa;  Cobrança estritamente por segundo de execução;&#xa;  zero clusters ociosos ou custos ocultos.&#xa;• Auto-Termination &amp; Right-Sizing:&#xa;  Seleção automática de instâncias otimizadas&#xa;  (i3.xlarge com NVMe local) para carga produtiva." style="swimlane;whiteSpace=wrap;html=1;fontSize=13;fontStyle=1;fillColor=#ECFDF5;strokeColor=#10B981;startSize=30;rounded=1;" vertex="1" parent="1">
        <mxGeometry x="60" y="130" width="380" height="260" as="geometry" />
      </mxCell>
      
      <mxCell id="b_p2" value="Aceleração de Time-to-Market (Setup em 5 Minutos)&#xa;&#xa;• Scaffolding Instantâneo Pré-Homologado:&#xa;  Elimina semanas de setup repetitivo de infraestrutura,&#xa;  Docker, bibliotecas e scripts de deploy.&#xa;• Padrões Medallion Prontos para Produção:&#xa;  Templates homologados de Bronze, Silver e Gold&#xa;  com contratos de schema e regras de auditoria.&#xa;• Esteira CI/CD Automatizada:&#xa;  Build automatizado de Wheel e deploy contínuo&#xa;  a cada Pull Request aprovado." style="swimlane;whiteSpace=wrap;html=1;fontSize=13;fontStyle=1;fillColor=#EFF6FF;strokeColor=#3B82F6;startSize=30;rounded=1;" vertex="1" parent="1">
        <mxGeometry x="480" y="130" width="380" height="260" as="geometry" />
      </mxCell>
      
      <mxCell id="b_p3" value="Governança Unificada &amp; Compliance&#xa;&#xa;• Gestão Centralizada com Unity Catalog:&#xa;  Controle de acesso granular (tabela, linha, coluna),&#xa;  linhagem automatizada de dados (data lineage).&#xa;• Segurança Sem Hardcoded Secrets:&#xa;  Sincronização com Secret Scopes e AWS Secrets&#xa;  Manager; zero credenciais expostas no Git.&#xa;• Rastreabilidade &amp; Auditoria Contínua:&#xa;  Campos de governança compulsórios: _ingested_at,&#xa;  _computed_at e logs estruturados em JSON." style="swimlane;whiteSpace=wrap;html=1;fontSize=13;fontStyle=1;fillColor=#FAF5FF;strokeColor=#8B5CF6;startSize=30;rounded=1;" vertex="1" parent="1">
        <mxGeometry x="900" y="130" width="380" height="260" as="geometry" />
      </mxCell>
      
      <mxCell id="b_p4" value="Interoperabilidade Sem Lock-In (Formatos Abertos)&#xa;&#xa;• Delta Lake + Apache Iceberg UniForm:&#xa;  Armazenamento único em AWS S3 acessível por&#xa;  múltiplos motores de consulta.&#xa;• Consumo Multi-Engine Direto:&#xa;  AWS Athena, Amazon Redshift Spectrum, Trino&#xa;  e Snowflake consultam a mesma tabela sem cópia.&#xa;• Zero Duplicação de Armazenamento:&#xa;  Redução massiva de custos de armazenamento e de&#xa;  pipelines redundantes de replicação." style="swimlane;whiteSpace=wrap;html=1;fontSize=13;fontStyle=1;fillColor=#FFF1F2;strokeColor=#E11D48;startSize=30;rounded=1;" vertex="1" parent="1">
        <mxGeometry x="1320" y="130" width="380" height="260" as="geometry" />
      </mxCell>
    """)

    # Medallion Value Chain
    cells.append("""
      <mxCell id="b_chain_title" value="Cadeia de Valor do Dado no Lakehouse (Medallion Value Pipeline)" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=16;fontStyle=1;fontColor=#1E293B;" vertex="1" parent="1">
        <mxGeometry x="60" y="425" width="600" height="30" as="geometry" />
      </mxCell>
      
      <mxCell id="b_bronze" value="Bronze (Ingestão Fiel &amp; Histórica)&#xa;&#xa;• Preservação de 100% do dado de origem&#xa;• Suporte a Batch (JDBC) e Streaming (Kinesis)&#xa;• Particionamento e metadados de auditoria&#xa;• Tabela Delta append-only imutável" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF3C7;strokeColor=#D97706;align=left;spacingLeft=15;fontSize=12;fontStyle=1;" vertex="1" parent="1">
        <mxGeometry x="60" y="465" width="500" height="130" as="geometry" />
      </mxCell>
      
      <mxCell id="b_silver" value="Silver (Higienização &amp; Qualidade)&#xa;&#xa;• Deduplicação e limpeza de registros inconsistentes&#xa;• Conformidade de tipos e regras de validação&#xa;• Preservação de linhagem com Delta ACID&#xa;• Tabelas prontas para Analytics operacional" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E0F2FE;strokeColor=#0284C7;align=left;spacingLeft=15;fontSize=12;fontStyle=1;" vertex="1" parent="1">
        <mxGeometry x="625" y="465" width="500" height="130" as="geometry" />
      </mxCell>
      
      <mxCell id="b_gold" value="Gold (Métricas Executivas &amp; IA)&#xa;&#xa;• Agregações de negócio, receita, clientes e KPIs&#xa;• Modelo dimensional (Star Schema / Data Marts)&#xa;• Suporte a Delta Lake + Apache Iceberg UniForm&#xa;• Prontidão para Power BI, Tableau e Modelos de ML" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF9C3;strokeColor=#CA8A04;align=left;spacingLeft=15;fontSize=12;fontStyle=1;" vertex="1" parent="1">
        <mxGeometry x="1190" y="465" width="510" height="130" as="geometry" />
      </mxCell>
      
      <mxCell id="b_ea1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=3;strokeColor=#D97706;" edge="1" parent="1" source="b_bronze" target="b_silver"><mxGeometry relative="1" as="geometry" /></mxCell>
      <mxCell id="b_ea2" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=3;strokeColor=#0284C7;" edge="1" parent="1" source="b_silver" target="b_gold"><mxGeometry relative="1" as="geometry" /></mxCell>
    """)

    # Comparison Matrix
    cells.append("""
      <mxCell id="b_matrix" value="Matriz de Comparação de ROI: Abordagem Tradicional vs. Databricks Forge CLI&#xa;&#xa;Dimensão                           Desenvolvimento Tradicional                         Com Databricks Forge CLI&#xa;------------------------------------------------------------------------------------------------------------------------------------------&#xa;Custo de Compute em Dev             Alto (Clusters na nuvem para testes unitários)     ZERO DBU (100% Docker local com Chispa)&#xa;Tempo de Setup de Novos Pipelines   2 a 3 semanas de configuração manual               Menos de 5 minutos com forge init&#xa;Governança e Segredos               Risco de credenciais em notebooks ou código        Sincronização nativa com Secret Scopes e AWS&#xa;Interoperabilidade de Dados        Lock-in ou duplicação de dados entre silos         Delta + Apache Iceberg UniForm em storage único&#xa;Orquestração e Execução             Scripts manuais e dependência de UI web            DAG declarativo com Jobs API v2.1 e Serverless" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1E293B;fontColor=#FFFFFF;fontStyle=0;fontSize=12;align=left;spacingLeft=25;fontFamily=monospace;" vertex="1" parent="1">
        <mxGeometry x="60" y="630" width="1640" height="180" as="geometry" />
      </mxCell>
    """)

    return "\n".join(cells)

# Generate Tab 3: Data Solutions with Official Databricks & AWS Icons
def build_tab3_data_solutions() -> str:
    cells = []
    
    # Header
    cells.append(f"""
      <mxCell id="t_header" value="Solução de Dados — Arquitetura Lakehouse Databricks na AWS" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=24;fontStyle=1;fontColor=#1E40AF;" vertex="1" parent="1">
        <mxGeometry x="350" y="25" width="1300" height="40" as="geometry" />
      </mxCell>
      <mxCell id="t_sub" value="Arquitetura técnica com ÍCONES OFICIAIS Databricks e AWS: Ingestão Multi-Banco, Computação Serverless, Medallion Delta &amp; Iceberg UniForm, Governança Unity Catalog e Consumo Analítico" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=13;fontColor=#64748B;" vertex="1" parent="1">
        <mxGeometry x="350" y="65" width="1300" height="25" as="geometry" />
      </mxCell>
    """)

    # 5 Big Swimlanes (Zonas Arquiteturais)
    # Zone 1: Ingestion
    cells.append(f"""
      <mxCell id="z1" value="1. Fontes &amp; Ingestão de Dados" style="swimlane;whiteSpace=wrap;html=1;fontSize=13;fontStyle=1;fillColor=#F8FAFC;strokeColor=#3B82F6;startSize=28;rounded=1;" vertex="1" parent="1">
        <mxGeometry x="50" y="110" width="340" height="880" as="geometry" />
      </mxCell>
      
      <!-- RDS -->
      <mxCell id="i_rds" value="" style="shape=image;html=1;verticalAlign=top;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;imageAspect=0;aspect=fixed;image={URI_AWS_RDS};" vertex="1" parent="z1">
        <mxGeometry x="25" y="45" width="55" height="55" as="geometry" />
      </mxCell>
      <mxCell id="lbl_rds" value="AWS RDS / Aurora&#xa;• PostgreSQL &amp; MySQL&#xa;• Transações OLTP em tempo real" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;fontStyle=1;fontColor=#1E293B;" vertex="1" parent="z1">
        <mxGeometry x="90" y="45" width="230" height="55" as="geometry" />
      </mxCell>

      <!-- Enterprise DB -->
      <mxCell id="i_db" value="" style="shape=image;html=1;verticalAlign=top;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;imageAspect=0;aspect=fixed;image={URI_DATABASE};" vertex="1" parent="z1">
        <mxGeometry x="25" y="125" width="55" height="55" as="geometry" />
      </mxCell>
      <mxCell id="lbl_db" value="Enterprise RDBMS&#xa;• Oracle &amp; SQL Server&#xa;• Conectores JDBC Forge CLI" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;fontStyle=1;fontColor=#1E293B;" vertex="1" parent="z1">
        <mxGeometry x="90" y="125" width="230" height="55" as="geometry" />
      </mxCell>

      <!-- Kinesis -->
      <mxCell id="i_kinesis" value="" style="shape=image;html=1;verticalAlign=top;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;imageAspect=0;aspect=fixed;image={URI_AWS_KINESIS};" vertex="1" parent="z1">
        <mxGeometry x="25" y="205" width="55" height="55" as="geometry" />
      </mxCell>
      <mxCell id="lbl_kinesis" value="AWS Kinesis Data Streams&#xa;• Eventos de telemetria &amp; IoT&#xa;• Ingestão contínua em streaming" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;fontStyle=1;fontColor=#1E293B;" vertex="1" parent="z1">
        <mxGeometry x="90" y="205" width="230" height="55" as="geometry" />
      </mxCell>

      <!-- S3 Landing -->
      <mxCell id="i_s3_raw" value="" style="shape=image;html=1;verticalAlign=top;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;imageAspect=0;aspect=fixed;image={URI_AWS_S3};" vertex="1" parent="z1">
        <mxGeometry x="25" y="285" width="55" height="55" as="geometry" />
      </mxCell>
      <mxCell id="lbl_s3_raw" value="AWS S3 Landing Zone&#xa;• s3://lakehouse-landing/&#xa;• Parquet, CSV, JSON, Avro" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;fontStyle=1;fontColor=#1E293B;" vertex="1" parent="z1">
        <mxGeometry x="90" y="285" width="230" height="55" as="geometry" />
      </mxCell>

      <!-- Ingestion Engine Box -->
      <mxCell id="box_ingest" value="Databricks Forge CLI Ingestion&#xa;&#xa;• forge connector plan-ingest&#xa;• Leitura JDBC particionada (fetchsize)&#xa;• Auto Loader com schema evolution&#xa;• Sincronização direta na Bronze" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#EFF6FF;strokeColor=#3B82F6;align=left;spacingLeft=15;fontSize=11;fontStyle=0;" vertex="1" parent="z1">
        <mxGeometry x="20" y="380" width="300" height="120" as="geometry" />
      </mxCell>
    """)

    # Zone 2: Control Plane & Security
    cells.append(f"""
      <mxCell id="z2" value="2. Orquestração &amp; Segurança" style="swimlane;whiteSpace=wrap;html=1;fontSize=13;fontStyle=1;fillColor=#F8FAFC;strokeColor=#10B981;startSize=28;rounded=1;" vertex="1" parent="1">
        <mxGeometry x="430" y="110" width="340" height="880" as="geometry" />
      </mxCell>

      <!-- AWS Secrets -->
      <mxCell id="i_sec" value="" style="shape=image;html=1;verticalAlign=top;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;imageAspect=0;aspect=fixed;image={URI_AWS_SECRETS};" vertex="1" parent="z2">
        <mxGeometry x="25" y="45" width="55" height="55" as="geometry" />
      </mxCell>
      <mxCell id="lbl_sec" value="AWS Secrets Manager&#xa;• Credenciais &amp; Tokens encriptados&#xa;• Sincronização com forge secret" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;fontStyle=1;fontColor=#1E293B;" vertex="1" parent="z2">
        <mxGeometry x="90" y="45" width="230" height="55" as="geometry" />
      </mxCell>

      <!-- AWS IAM -->
      <mxCell id="i_iam" value="" style="shape=image;html=1;verticalAlign=top;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;imageAspect=0;aspect=fixed;image={URI_AWS_IAM};" vertex="1" parent="z2">
        <mxGeometry x="25" y="125" width="55" height="55" as="geometry" />
      </mxCell>
      <mxCell id="lbl_iam" value="AWS IAM Roles &amp; Policies&#xa;• Instance Profiles para S3 Access&#xa;• Trust Relationship com Databricks" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;fontStyle=1;fontColor=#1E293B;" vertex="1" parent="z2">
        <mxGeometry x="90" y="125" width="230" height="55" as="geometry" />
      </mxCell>

      <!-- Databricks Control Plane -->
      <mxCell id="i_db_cp" value="" style="shape=image;html=1;verticalAlign=top;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;imageAspect=0;aspect=fixed;image={URI_DATABRICKS};" vertex="1" parent="z2">
        <mxGeometry x="25" y="205" width="55" height="55" as="geometry" />
      </mxCell>
      <mxCell id="lbl_db_cp" value="Databricks Control Plane&#xa;• Jobs API v2.1 (/api/2.1/jobs)&#xa;• Workspace API &amp; Secret Scopes" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;fontStyle=1;fontColor=#1E293B;" vertex="1" parent="z2">
        <mxGeometry x="90" y="205" width="230" height="55" as="geometry" />
      </mxCell>

      <!-- DAG Engine Box -->
      <mxCell id="box_dag" value="Databricks Forge CLI DAG Engine&#xa;&#xa;• Algoritmo de Kahn (Topological Sort)&#xa;• Validação de Grafo e Dependências&#xa;• Submissão Remota: forge job run-dag&#xa;• Suporte a Serverless e Single-Node CE" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ECFDF5;strokeColor=#10B981;align=left;spacingLeft=15;fontSize=11;fontStyle=0;" vertex="1" parent="z2">
        <mxGeometry x="20" y="380" width="300" height="120" as="geometry" />
      </mxCell>
    """)

    # Zone 3: Databricks Compute Plane on AWS
    cells.append(f"""
      <mxCell id="z3" value="3. Computação Lakehouse (Databricks on AWS)" style="swimlane;whiteSpace=wrap;html=1;fontSize=13;fontStyle=1;fillColor=#F8FAFC;strokeColor=#FF3621;startSize=28;rounded=1;" vertex="1" parent="1">
        <mxGeometry x="810" y="110" width="360" height="880" as="geometry" />
      </mxCell>

      <!-- Serverless Compute -->
      <mxCell id="i_srv" value="" style="shape=image;html=1;verticalAlign=top;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;imageAspect=0;aspect=fixed;image={URI_SERVERLESS};" vertex="1" parent="z3">
        <mxGeometry x="25" y="45" width="55" height="55" as="geometry" />
      </mxCell>
      <mxCell id="lbl_srv" value="Databricks Serverless Compute&#xa;• Inicialização instantânea em segundos&#xa;• Cobrança por segundo de processamento&#xa;• Zero overhead de gerenciamento de cluster" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;fontStyle=1;fontColor=#1E293B;" vertex="1" parent="z3">
        <mxGeometry x="90" y="45" width="250" height="55" as="geometry" />
      </mxCell>

      <!-- AWS EC2 Classic Compute -->
      <mxCell id="i_ec2" value="" style="shape=image;html=1;verticalAlign=top;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;imageAspect=0;aspect=fixed;image={URI_AWS_EC2};" vertex="1" parent="z3">
        <mxGeometry x="25" y="125" width="55" height="55" as="geometry" />
      </mxCell>
      <mxCell id="lbl_ec2" value="AWS EC2 Managed Clusters&#xa;• Instâncias i3.xlarge (Local NVMe SSD)&#xa;• Auto-scaling inteligente &amp; Spot support&#xa;• DBR 14.3 LTS (Apache Spark 3.5.0)" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;fontStyle=1;fontColor=#1E293B;" vertex="1" parent="z3">
        <mxGeometry x="90" y="125" width="250" height="55" as="geometry" />
      </mxCell>

      <!-- Spark Engine -->
      <mxCell id="i_spark" value="" style="shape=image;html=1;verticalAlign=top;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;imageAspect=0;aspect=fixed;image={URI_APACHE_SPARK};" vertex="1" parent="z3">
        <mxGeometry x="25" y="205" width="55" height="55" as="geometry" />
      </mxCell>
      <mxCell id="lbl_spark" value="Apache Spark 3.5 Engine&#xa;• Structured Streaming com checkpoints S3&#xa;• Photon Acceleration Engine&#xa;• Execução de PySpark Wheels (.whl) &amp; SQL" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;fontStyle=1;fontColor=#1E293B;" vertex="1" parent="z3">
        <mxGeometry x="90" y="205" width="250" height="55" as="geometry" />
      </mxCell>

      <!-- Tuning Box -->
      <mxCell id="box_tune" value="Databricks Forge CLI Tuning Engine&#xa;&#xa;• forge tune optimize --zorder&#xa;• forge tune vacuum --retention-hours 168&#xa;• Liquid Clustering &amp; Data Skipping&#xa;• Redução de I/O e queries 5x mais rápidas" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF1F2;strokeColor=#FF3621;align=left;spacingLeft=15;fontSize=11;fontStyle=0;" vertex="1" parent="z3">
        <mxGeometry x="20" y="380" width="320" height="120" as="geometry" />
      </mxCell>
    """)

    # Zone 4: Storage & Unity Catalog
    cells.append(f"""
      <mxCell id="z4" value="4. Armazenamento Medallion &amp; Governança" style="swimlane;whiteSpace=wrap;html=1;fontSize=13;fontStyle=1;fillColor=#F8FAFC;strokeColor=#0284C7;startSize=28;rounded=1;" vertex="1" parent="1">
        <mxGeometry x="1210" y="110" width="370" height="880" as="geometry" />
      </mxCell>

      <!-- Unity Catalog -->
      <mxCell id="i_uc" value="" style="shape=image;html=1;verticalAlign=top;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;imageAspect=0;aspect=fixed;image={URI_UNITY_CATALOG};" vertex="1" parent="z4">
        <mxGeometry x="25" y="45" width="55" height="55" as="geometry" />
      </mxCell>
      <mxCell id="lbl_uc" value="Databricks Unity Catalog&#xa;• Governança unificada de dados e IA&#xa;• Metastore centralizado (Catalogs/Schemas)&#xa;• Data Lineage &amp; Auditoria de acessos" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;fontStyle=1;fontColor=#1E293B;" vertex="1" parent="z4">
        <mxGeometry x="90" y="45" width="260" height="55" as="geometry" />
      </mxCell>

      <!-- Bronze Delta Table -->
      <mxCell id="i_delta_b" value="" style="shape=image;html=1;verticalAlign=top;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;imageAspect=0;aspect=fixed;image={URI_DELTA_LAKE};" vertex="1" parent="z4">
        <mxGeometry x="25" y="130" width="45" height="45" as="geometry" />
      </mxCell>
      <mxCell id="lbl_b" value="Bronze Layer (Raw Storage)&#xa;• AWS S3: s3://lakehouse-data/bronze/&#xa;• Tabelas Delta Lake com append-only&#xa;• Rastreabilidade técnica: _ingested_at" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;fontStyle=1;fontColor=#1E293B;" vertex="1" parent="z4">
        <mxGeometry x="80" y="130" width="270" height="50" as="geometry" />
      </mxCell>

      <!-- Silver Delta Table -->
      <mxCell id="i_delta_s" value="" style="shape=image;html=1;verticalAlign=top;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;imageAspect=0;aspect=fixed;image={URI_DELTA_LAKE};" vertex="1" parent="z4">
        <mxGeometry x="25" y="210" width="45" height="45" as="geometry" />
      </mxCell>
      <mxCell id="lbl_s" value="Silver Layer (Curated Cleaned)&#xa;• AWS S3: s3://lakehouse-data/silver/&#xa;• Tabelas Delta Lake com ACID e Time-Travel&#xa;• Limpeza, deduplicação e schema enforcement" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;fontStyle=1;fontColor=#1E293B;" vertex="1" parent="z4">
        <mxGeometry x="80" y="210" width="270" height="50" as="geometry" />
      </mxCell>

      <!-- Gold Delta + Iceberg Table -->
      <mxCell id="i_ice_g" value="" style="shape=image;html=1;verticalAlign=top;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;imageAspect=0;aspect=fixed;image={URI_ICEBERG};" vertex="1" parent="z4">
        <mxGeometry x="25" y="290" width="45" height="45" as="geometry" />
      </mxCell>
      <mxCell id="lbl_g" value="Gold Layer (Delta + Apache Iceberg)&#xa;• AWS S3: s3://lakehouse-data/gold/&#xa;• Habilitação UniForm: forge iceberg enable-uniform&#xa;• Agregações analíticas e KPIs de negócio" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;fontStyle=1;fontColor=#1E293B;" vertex="1" parent="z4">
        <mxGeometry x="80" y="290" width="270" height="50" as="geometry" />
      </mxCell>

      <!-- Format Convert Box -->
      <mxCell id="box_formats" value="Formatos Abertos &amp; Iceberg UniForm&#xa;&#xa;• forge data convert (CSV/JSON/Parquet ➔ Delta)&#xa;• Metadados duplos: Delta Log + Iceberg Metadata&#xa;• Zero duplicação de dados em storage S3&#xa;• Consulta universal sem conversão de formato" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F0F9FF;strokeColor=#0284C7;align=left;spacingLeft=15;fontSize=11;fontStyle=0;" vertex="1" parent="z4">
        <mxGeometry x="20" y="380" width="330" height="120" as="geometry" />
      </mxCell>
    """)

    # Zone 5: Analytics Serving & Telemetry
    cells.append(f"""
      <mxCell id="z5" value="5. Consumo Analítico &amp; Telemetria" style="swimlane;whiteSpace=wrap;html=1;fontSize=13;fontStyle=1;fillColor=#F8FAFC;strokeColor=#8C4FFF;startSize=28;rounded=1;" vertex="1" parent="1">
        <mxGeometry x="1620" y="110" width="340" height="880" as="geometry" />
      </mxCell>

      <!-- Databricks SQL -->
      <mxCell id="i_dbsql" value="" style="shape=image;html=1;verticalAlign=top;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;imageAspect=0;aspect=fixed;image={URI_DATABRICKS};" vertex="1" parent="z5">
        <mxGeometry x="25" y="45" width="55" height="55" as="geometry" />
      </mxCell>
      <mxCell id="lbl_dbsql" value="Databricks SQL Warehouses&#xa;• BI de altíssima performance&#xa;• Dashboards executivos e ad-hoc&#xa;• Conectores nativos Power BI / Tableau" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;fontStyle=1;fontColor=#1E293B;" vertex="1" parent="z5">
        <mxGeometry x="90" y="45" width="230" height="55" as="geometry" />
      </mxCell>

      <!-- AWS Athena -->
      <mxCell id="i_athena" value="" style="shape=image;html=1;verticalAlign=top;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;imageAspect=0;aspect=fixed;image={URI_AWS_ATHENA};" vertex="1" parent="z5">
        <mxGeometry x="25" y="125" width="55" height="55" as="geometry" />
      </mxCell>
      <mxCell id="lbl_athena" value="AWS Athena (Serverless SQL)&#xa;• Consulta direta na Gold Iceberg UniForm&#xa;• Zero cópia de dados ou transferência extra" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;fontStyle=1;fontColor=#1E293B;" vertex="1" parent="z5">
        <mxGeometry x="90" y="125" width="230" height="55" as="geometry" />
      </mxCell>

      <!-- AWS Redshift -->
      <mxCell id="i_redshift" value="" style="shape=image;html=1;verticalAlign=top;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;imageAspect=0;aspect=fixed;image={URI_AWS_REDSHIFT};" vertex="1" parent="z5">
        <mxGeometry x="25" y="205" width="55" height="55" as="geometry" />
      </mxCell>
      <mxCell id="lbl_redshift" value="Amazon Redshift Spectrum&#xa;• Data Warehouse corporativo integrado&#xa;• Consultas externas direto nas tabelas S3" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;fontStyle=1;fontColor=#1E293B;" vertex="1" parent="z5">
        <mxGeometry x="90" y="205" width="230" height="55" as="geometry" />
      </mxCell>

      <!-- AWS CloudWatch -->
      <mxCell id="i_cw" value="" style="shape=image;html=1;verticalAlign=top;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;imageAspect=0;aspect=fixed;image={URI_AWS_CLOUDWATCH};" vertex="1" parent="z5">
        <mxGeometry x="25" y="285" width="55" height="55" as="geometry" />
      </mxCell>
      <mxCell id="lbl_cw" value="Amazon CloudWatch &amp; Logs&#xa;• Telemetria e auditoria contínua&#xa;• Alertas de SLA e falhas em tempo real" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;fontStyle=1;fontColor=#1E293B;" vertex="1" parent="z5">
        <mxGeometry x="90" y="285" width="230" height="55" as="geometry" />
      </mxCell>

      <!-- Forge Logging Box -->
      <mxCell id="box_log" value="Logs Estruturados JSON do Forge CLI&#xa;&#xa;• Auditoria de etapas do pipeline (audit_step)&#xa;• Rastreamento de tempo, linhas e exceptions&#xa;• Exportação para CloudWatch e Databricks Audit" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FAF5FF;strokeColor=#8C4FFF;align=left;spacingLeft=15;fontSize=11;fontStyle=0;" vertex="1" parent="z5">
        <mxGeometry x="20" y="380" width="300" height="120" as="geometry" />
      </mxCell>
    """)

    # Architecture Inter-Zone Connectors
    cells.append("""
      <!-- Z1 to Z3 (Ingestion to Compute) -->
      <mxCell id="arr_1_3" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=3;strokeColor=#3B82F6;" edge="1" parent="1" source="box_ingest" target="box_tune">
        <mxGeometry relative="1" as="geometry">
          <Array as="points">
            <mxPoint x="390" y="550" />
            <mxPoint x="810" y="550" />
          </Array>
        </mxGeometry>
      </mxCell>

      <!-- Z2 to Z3 (Orchestration to Compute) -->
      <mxCell id="arr_2_3" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=3;strokeColor=#10B981;" edge="1" parent="1" source="box_dag" target="box_tune">
        <mxGeometry relative="1" as="geometry" />
      </mxCell>

      <!-- Z3 to Z4 (Compute to Medallion Storage) -->
      <mxCell id="arr_3_4" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=3;strokeColor=#FF3621;" edge="1" parent="1" source="box_tune" target="box_formats">
        <mxGeometry relative="1" as="geometry" />
      </mxCell>

      <!-- Z4 to Z5 (Storage to Analytics Consumers) -->
      <mxCell id="arr_4_5" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=3;strokeColor=#8C4FFF;" edge="1" parent="1" source="box_formats" target="box_log">
        <mxGeometry relative="1" as="geometry" />
      </mxCell>
    """)

    # Bottom Architecture Banner
    cells.append("""
      <mxCell id="t_footer" value="Garantias da Solução de Dados: Arquitetura Lakehouse aberta e sem vendor lock-in • 100% de conformidade ACID no AWS S3 com Delta Lake e Apache Iceberg UniForm • Alta disponibilidade com orquestração resiliente e monitoramento unificado" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1E293B;fontColor=#FFFFFF;fontStyle=1;fontSize=13;align=center;" vertex="1" parent="1">
        <mxGeometry x="50" y="1020" width="1910" height="60" as="geometry" />
      </mxCell>
    """)

    return "\n".join(cells)

def generate_full_drawio_xml() -> str:
    tab1_content = build_tab1_functional()
    tab2_content = build_tab2_business()
    tab3_content = build_tab3_data_solutions()

    xml_content = f"""<mxfile host="Electron" modified="2026-09-08T01:55:00.000Z" agent="5.0" version="21.6.8" type="device">
  
  <!-- ========================================================================================== -->
  <!-- ABA 1: EXPERIÊNCIA DO DESENVOLVEDOR (FUNCIONAL)                                           -->
  <!-- ========================================================================================== -->
  <diagram id="tab-functional" name="1. Experiência do Desenvolvedor (Funcional)">
    <mxGraphModel dx="1800" dy="1200" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="2000" pageHeight="1200" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
{tab1_content}
      </root>
    </mxGraphModel>
  </diagram>

  <!-- ========================================================================================== -->
  <!-- ABA 2: VISÃO DE NEGÓCIO, FINOPS & GOVERNANÇA                                              -->
  <!-- ========================================================================================== -->
  <diagram id="tab-business" name="2. Visão de Negócio, FinOps &amp; Governança">
    <mxGraphModel dx="1800" dy="1200" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="2000" pageHeight="1200" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
{tab2_content}
      </root>
    </mxGraphModel>
  </diagram>

  <!-- ========================================================================================== -->
  <!-- ABA 3: SOLUÇÃO DE DADOS (DATABRICKS & AWS COM ÍCONES OFICIAIS)                             -->
  <!-- ========================================================================================== -->
  <diagram id="tab-data-solutions" name="3. Solução de Dados (Databricks &amp; AWS)">
    <mxGraphModel dx="2000" dy="1300" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="2100" pageHeight="1300" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
{tab3_content}
      </root>
    </mxGraphModel>
  </diagram>

</mxfile>
"""
    return xml_content

def main():
    xml_content = generate_full_drawio_xml()
    
    # Validate XML
    try:
        ET.fromstring(xml_content)
        print("XML validation PASSED: syntax is 100% well-formed!")
    except Exception as e:
        print(f"XML validation FAILED: {e}")
        raise

    target_path = "docs/architecture.drawio"
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(xml_content)
    
    print(f"File successfully written to {target_path} ({len(xml_content)} bytes)")

if __name__ == "__main__":
    main()
