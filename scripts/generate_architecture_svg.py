"""
Generator for docs/architecture.svg representing the Data Solution Architecture (Databricks & AWS) with official vector icons.
"""

def generate_svg():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1680 980" width="100%" height="100%" style="background:#090D16; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <defs>
    <!-- Gradients -->
    <linearGradient id="titleGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#FF3621" />
      <stop offset="50%" stop-color="#FF7A00" />
      <stop offset="100%" stop-color="#38BDF8" />
    </linearGradient>
    <linearGradient id="cardGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#151D2F" />
      <stop offset="100%" stop-color="#0D1424" />
    </linearGradient>
    <linearGradient id="boxGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#1E293B" />
      <stop offset="100%" stop-color="#0F172A" />
    </linearGradient>

    <!-- Filters -->
    <filter id="dropShadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="8" stdDeviation="6" flood-color="#000000" flood-opacity="0.6" />
    </filter>

    <!-- Markers -->
    <marker id="arrowBlue" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#38BDF8" />
    </marker>
    <marker id="arrowRed" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#FF3621" />
    </marker>
    <marker id="arrowGreen" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#10B981" />
    </marker>
    <marker id="arrowPurple" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#8C4FFF" />
    </marker>
  </defs>

  <!-- ==================== HEADER ==================== -->
  <g transform="translate(45, 25)">
    <!-- Databricks Logo Icon -->
    <g transform="translate(0, 4) scale(0.65)">
      <polygon points="50,6 94,28 50,50 6,28" fill="#FF3621"/>
      <polygon points="6,42 50,64 94,42 82,36 50,52 18,36" fill="#E02917"/>
      <polygon points="6,56 50,78 94,56 82,50 50,66 18,50" fill="#C42010"/>
      <polygon points="6,70 50,92 94,70 82,64 50,80 18,64" fill="#991509"/>
    </g>
    <text x="75" y="32" font-size="26" font-weight="900" fill="url(#titleGrad)" letter-spacing="1">DATABRICKS FORGE CLI — ARQUITETURA DE DADOS NA AWS</text>
    <text x="75" y="54" font-size="13" fill="#94A3B8">Solução de Dados com Ícones Oficiais: Ingestão Multi-Banco · Serverless Compute · Medallion Delta &amp; Iceberg UniForm · Unity Catalog</text>
  </g>

  <!-- ==================== ZONE 1: INGESTION ==================== -->
  <g transform="translate(45, 95)">
    <rect width="295" height="800" rx="14" fill="url(#cardGrad)" stroke="#3B82F6" stroke-width="2" filter="url(#dropShadow)" />
    <rect width="295" height="38" rx="14" fill="#1E3A8A" />
    <rect y="24" width="295" height="14" fill="#1E3A8A" />
    <text x="20" y="25" font-size="13" font-weight="800" fill="#FFFFFF">1. FONTES &amp; INGESTÃO</text>

    <!-- RDS -->
    <g transform="translate(15, 55)">
      <rect width="265" height="75" rx="8" fill="url(#boxGrad)" stroke="#3B82F6" stroke-width="1.2" />
      <rect x="12" y="14" width="46" height="46" rx="8" fill="#3B48CC"/>
      <ellipse cx="35" cy="27" rx="16" ry="6" fill="#FFFFFF" opacity="0.95"/>
      <path d="M19,27 v10 c0,4 7,6 16,6 s16,-2 16,-6 v-10" fill="none" stroke="#FFFFFF" stroke-width="2.5"/>
      <path d="M19,37 v10 c0,4 7,6 16,6 s16,-2 16,-6 v-10" fill="none" stroke="#FFFFFF" stroke-width="2.5"/>
      <text x="68" y="30" font-size="12" font-weight="700" fill="#60A5FA">AWS RDS / Aurora</text>
      <text x="68" y="47" font-size="10" fill="#CBD5E1">PostgreSQL &amp; MySQL</text>
      <text x="68" y="61" font-size="9" fill="#94A3B8">Transações OLTP contínuas</text>
    </g>

    <!-- Enterprise DB -->
    <g transform="translate(15, 140)">
      <rect width="265" height="75" rx="8" fill="url(#boxGrad)" stroke="#0284C7" stroke-width="1.2" />
      <rect x="12" y="14" width="46" height="46" rx="8" fill="#0284C7"/>
      <ellipse cx="35" cy="26" rx="16" ry="6" fill="#FFFFFF" opacity="0.95"/>
      <path d="M19,26 v11 c0,4 7,6 16,6 s16,-2 16,-6 v-11" fill="none" stroke="#FFFFFF" stroke-width="2.5"/>
      <path d="M19,38 v11 c0,4 7,6 16,6 s16,-2 16,-6 v-11" fill="none" stroke="#FFFFFF" stroke-width="2.5"/>
      <text x="68" y="30" font-size="12" font-weight="700" fill="#38BDF8">Enterprise RDBMS</text>
      <text x="68" y="47" font-size="10" fill="#CBD5E1">Oracle &amp; SQL Server</text>
      <text x="68" y="61" font-size="9" fill="#94A3B8">Conectores JDBC Forge CLI</text>
    </g>

    <!-- Kinesis -->
    <g transform="translate(15, 225)">
      <rect width="265" height="75" rx="8" fill="url(#boxGrad)" stroke="#8C4FFF" stroke-width="1.2" />
      <rect x="12" y="14" width="46" height="46" rx="8" fill="#8C4FFF"/>
      <path d="M22,23 L35,31 L48,23 L48,51 L35,59 L22,51 Z" fill="none" stroke="#FFFFFF" stroke-width="3"/>
      <line x1="35" y1="31" x2="35" y2="59" stroke="#FFFFFF" stroke-width="3"/>
      <text x="68" y="30" font-size="12" font-weight="700" fill="#C084FC">AWS Kinesis Streams</text>
      <text x="68" y="47" font-size="10" fill="#CBD5E1">Streaming &amp; Eventos IoT</text>
      <text x="68" y="61" font-size="9" fill="#94A3B8">Ingestão contínua em tempo real</text>
    </g>

    <!-- S3 Landing -->
    <g transform="translate(15, 310)">
      <rect width="265" height="75" rx="8" fill="url(#boxGrad)" stroke="#E05243" stroke-width="1.2" />
      <rect x="12" y="14" width="46" height="46" rx="8" fill="#E05243"/>
      <ellipse cx="35" cy="27" rx="16" ry="6" fill="#FFFFFF" opacity="0.95"/>
      <path d="M19,27 v11 c0,4 7,6 16,6 s16,-2 16,-6 v-11" fill="none" stroke="#FFFFFF" stroke-width="2.5"/>
      <path d="M19,40 v11 c0,4 7,6 16,6 s16,-2 16,-6 v-11" fill="none" stroke="#FFFFFF" stroke-width="2.5"/>
      <text x="68" y="30" font-size="12" font-weight="700" fill="#F87171">AWS S3 Landing Zone</text>
      <text x="68" y="47" font-size="10" fill="#CBD5E1">s3://lakehouse-landing/</text>
      <text x="68" y="61" font-size="9" fill="#94A3B8">Parquet, CSV, JSON, Avro</text>
    </g>

    <!-- Engine Box -->
    <g transform="translate(15, 400)">
      <rect width="265" height="375" rx="8" fill="#0F172A" stroke="#3B82F6" stroke-width="1.5" />
      <text x="16" y="28" font-size="12" font-weight="800" fill="#60A5FA">⚡ Forge CLI Ingestion Engine</text>
      <text x="16" y="55" font-size="10" fill="#E2E8F0">• <tspan fill="#38BDF8">forge connector plan-ingest</tspan></text>
      <text x="16" y="75" font-size="10" fill="#CBD5E1">• Leitura JDBC particionada (fetchsize)</text>
      <text x="16" y="95" font-size="10" fill="#CBD5E1">• Auto Loader com schema evolution</text>
      <text x="16" y="115" font-size="10" fill="#CBD5E1">• Conversão direta para Delta Bronze</text>
      <text x="16" y="145" font-size="11" font-weight="700" fill="#F59E0B">Suporte a Bancos Homologados:</text>
      <text x="16" y="168" font-size="10" fill="#94A3B8">✔ PostgreSQL 12+</text>
      <text x="16" y="188" font-size="10" fill="#94A3B8">✔ MySQL 8.0+</text>
      <text x="16" y="208" font-size="10" fill="#94A3B8">✔ Oracle Database 19c+</text>
      <text x="16" y="228" font-size="10" fill="#94A3B8">✔ Microsoft SQL Server 2019+</text>
      <text x="16" y="258" font-size="10" fill="#CBD5E1">• Teste de conexão: <tspan fill="#34D399">forge connector test</tspan></text>
      <text x="16" y="278" font-size="10" fill="#CBD5E1">• Plano de export: <tspan fill="#34D399">forge connector plan-export</tspan></text>
      <text x="16" y="308" font-size="10" fill="#E2E8F0">Garante ingestão auditada com colunas:</text>
      <text x="16" y="328" font-size="9" fill="#FDE68A"><tspan fill="#F59E0B">_ingested_at</tspan> · <tspan fill="#F59E0B">_source_engine</tspan></text>
    </g>
  </g>

  <!-- ==================== ZONE 2: CONTROL PLANE & SECURITY ==================== -->
  <g transform="translate(365, 95)">
    <rect width="295" height="800" rx="14" fill="url(#cardGrad)" stroke="#10B981" stroke-width="2" filter="url(#dropShadow)" />
    <rect width="295" height="38" rx="14" fill="#065F46" />
    <rect y="24" width="295" height="14" fill="#065F46" />
    <text x="20" y="25" font-size="13" font-weight="800" fill="#FFFFFF">2. ORQUESTRAÇÃO &amp; SEGURANÇA</text>

    <!-- AWS Secrets -->
    <g transform="translate(15, 55)">
      <rect width="265" height="75" rx="8" fill="url(#boxGrad)" stroke="#DD344C" stroke-width="1.2" />
      <rect x="12" y="14" width="46" height="46" rx="8" fill="#DD344C"/>
      <circle cx="35" cy="32" r="9" fill="none" stroke="#FFFFFF" stroke-width="3"/>
      <rect x="25" y="33" width="20" height="18" rx="3" fill="#FFFFFF"/>
      <text x="68" y="30" font-size="12" font-weight="700" fill="#F87171">AWS Secrets Manager</text>
      <text x="68" y="47" font-size="10" fill="#CBD5E1">Credenciais encriptadas</text>
      <text x="68" y="61" font-size="9" fill="#94A3B8">Sincronização com forge secret</text>
    </g>

    <!-- AWS IAM -->
    <g transform="translate(15, 140)">
      <rect width="265" height="75" rx="8" fill="url(#boxGrad)" stroke="#DD344C" stroke-width="1.2" />
      <rect x="12" y="14" width="46" height="46" rx="8" fill="#DD344C"/>
      <circle cx="35" cy="28" r="8" fill="#FFFFFF"/>
      <path d="M21,50 c0,-8 7,-13 14,-13 s14,5 14,13 Z" fill="#FFFFFF"/>
      <text x="68" y="30" font-size="12" font-weight="700" fill="#F87171">AWS IAM Roles</text>
      <text x="68" y="47" font-size="10" fill="#CBD5E1">Instance Profiles Databricks</text>
      <text x="68" y="61" font-size="9" fill="#94A3B8">Acesso seguro ao bucket S3</text>
    </g>

    <!-- Databricks Control Plane -->
    <g transform="translate(15, 225)">
      <rect width="265" height="75" rx="8" fill="url(#boxGrad)" stroke="#FF3621" stroke-width="1.2" />
      <rect x="12" y="14" width="46" height="46" rx="8" fill="#FF3621"/>
      <polygon points="35,18 51,26 35,34 19,26" fill="#FFFFFF"/>
      <polygon points="19,31 35,39 51,31 47,29 35,35 23,29" fill="#FFE4E1"/>
      <polygon points="19,37 35,45 51,37 47,35 35,41 23,35" fill="#FFE4E1"/>
      <text x="68" y="30" font-size="12" font-weight="700" fill="#FF6B59">Databricks Control Plane</text>
      <text x="68" y="47" font-size="10" fill="#CBD5E1">Jobs API v2.1 &amp; Workspace</text>
      <text x="68" y="61" font-size="9" fill="#94A3B8">Secret Scopes (/api/2.0/secrets)</text>
    </g>

    <!-- GitHub Actions -->
    <g transform="translate(15, 310)">
      <rect width="265" height="75" rx="8" fill="url(#boxGrad)" stroke="#64748B" stroke-width="1.2" />
      <rect x="12" y="14" width="46" height="46" rx="8" fill="#334155"/>
      <circle cx="35" cy="37" r="14" fill="#FFFFFF" opacity="0.9"/>
      <text x="68" y="30" font-size="12" font-weight="700" fill="#CBD5E1">GitHub Actions CI/CD</text>
      <text x="68" y="47" font-size="10" fill="#CBD5E1">Matriz Python 3.10, 3.11, 3.12</text>
      <text x="68" y="61" font-size="9" fill="#94A3B8">Compilação e Deploy do Wheel</text>
    </g>

    <!-- DAG Engine Box -->
    <g transform="translate(15, 400)">
      <rect width="265" height="375" rx="8" fill="#0F172A" stroke="#10B981" stroke-width="1.5" />
      <text x="16" y="28" font-size="12" font-weight="800" fill="#34D399">🌐 Forge DAG Orchestrator</text>
      <text x="16" y="55" font-size="10" fill="#E2E8F0">• <tspan fill="#34D399">Algoritmo de Kahn</tspan> (Ordenação)</text>
      <text x="16" y="75" font-size="10" fill="#CBD5E1">• Detecção de ciclos (Zero deadlocks)</text>
      <text x="16" y="95" font-size="10" fill="#CBD5E1">• Compilador Jobs API v2.1 payload</text>
      <text x="16" y="115" font-size="10" fill="#CBD5E1">• Execução Remota: <tspan fill="#34D399">forge job run-dag</tspan></text>
      <text x="16" y="145" font-size="11" font-weight="700" fill="#34D399">Grafo de Dependências Resolvido:</text>
      <text x="16" y="170" font-size="10" fill="#94A3B8">1. [Bronze Ingestion] (Spark/Wheel)</text>
      <text x="36" y="188" font-size="10" fill="#64748B">↓ depends_on: bronze</text>
      <text x="16" y="208" font-size="10" fill="#94A3B8">2. [Silver Cleaning] (Spark SQL)</text>
      <text x="36" y="226" font-size="10" fill="#64748B">↓ depends_on: silver</text>
      <text x="16" y="246" font-size="10" fill="#94A3B8">3. [Gold Analytics] (KPIs &amp; UniForm)</text>
      <text x="16" y="280" font-size="10" fill="#CBD5E1">• Polling assíncrono com feedback</text>
      <text x="16" y="300" font-size="10" fill="#CBD5E1">• Master DAG Runner para CE gratuito</text>
      <text x="16" y="325" font-size="10" fill="#A7F3D0">✔ Execução validada em nuvem real</text>
    </g>
  </g>

  <!-- ==================== ZONE 3: DATABRICKS COMPUTE ==================== -->
  <g transform="translate(685, 95)">
    <rect width="310" height="800" rx="14" fill="url(#cardGrad)" stroke="#FF3621" stroke-width="2" filter="url(#dropShadow)" />
    <rect width="310" height="38" rx="14" fill="#991B1B" />
    <rect y="24" width="310" height="14" fill="#991B1B" />
    <text x="20" y="25" font-size="13" font-weight="800" fill="#FFFFFF">3. COMPUTAÇÃO LAKEHOUSE (DATABRICKS)</text>

    <!-- Serverless Compute -->
    <g transform="translate(15, 55)">
      <rect width="280" height="75" rx="8" fill="url(#boxGrad)" stroke="#FF3621" stroke-width="1.2" />
      <rect x="12" y="14" width="46" height="46" rx="8" fill="#FF3621"/>
      <path d="M22,42 C18,42 15,39 15,35 C15,31 18,28 21,27 C22,21 27,17 33,17 C39,17 44,21 45,26 C47,26 50,29 50,32 C54,33 56,36 56,40 C56,44 53,48 48,48 L22,48 Z" fill="#FFE4E1"/>
      <text x="68" y="30" font-size="12" font-weight="700" fill="#FF6B59">Serverless Compute</text>
      <text x="68" y="47" font-size="10" fill="#CBD5E1">Inicialização em segundos</text>
      <text x="68" y="61" font-size="9" fill="#94A3B8">Cobrança por segundo · Zero idle</text>
    </g>

    <!-- AWS EC2 Managed -->
    <g transform="translate(15, 140)">
      <rect width="280" height="75" rx="8" fill="url(#boxGrad)" stroke="#ED7100" stroke-width="1.2" />
      <rect x="12" y="14" width="46" height="46" rx="8" fill="#ED7100"/>
      <rect x="22" y="22" width="26" height="26" fill="none" stroke="#FFFFFF" stroke-width="3"/>
      <rect x="30" y="30" width="10" height="10" fill="#FFFFFF"/>
      <text x="68" y="30" font-size="12" font-weight="700" fill="#FB923C">AWS EC2 Clusters</text>
      <text x="68" y="47" font-size="10" fill="#CBD5E1">i3.xlarge (NVMe SSD local)</text>
      <text x="68" y="61" font-size="9" fill="#94A3B8">Auto-scaling &amp; Spot support</text>
    </g>

    <!-- Apache Spark Engine -->
    <g transform="translate(15, 225)">
      <rect width="280" height="75" rx="8" fill="url(#boxGrad)" stroke="#E25A1C" stroke-width="1.2" />
      <rect x="12" y="14" width="46" height="46" rx="8" fill="#E25A1C"/>
      <path d="M35,16 C37,27 45,31 52,32 C45,36 42,41 43,50 C38,42 32,42 27,50 C29,41 25,36 17,32 C24,31 33,27 35,16 Z" fill="#FFFFFF"/>
      <text x="68" y="30" font-size="12" font-weight="700" fill="#FB923C">Apache Spark 3.5.x</text>
      <text x="68" y="47" font-size="10" fill="#CBD5E1">DBR 14.3 LTS Runtime</text>
      <text x="68" y="61" font-size="9" fill="#94A3B8">Structured Streaming &amp; Batch</text>
    </g>

    <!-- Local Docker Spark -->
    <g transform="translate(15, 310)">
      <rect width="280" height="75" rx="8" fill="url(#boxGrad)" stroke="#38BDF8" stroke-width="1.2" />
      <rect x="12" y="14" width="46" height="46" rx="8" fill="#0284C7"/>
      <text x="35" y="44" font-size="24" text-anchor="middle" fill="#FFFFFF">🐳</text>
      <text x="68" y="30" font-size="12" font-weight="700" fill="#38BDF8">Docker Dev Runtime</text>
      <text x="68" y="47" font-size="10" fill="#CBD5E1">OpenJDK 11 + PySpark local</text>
      <text x="68" y="61" font-size="9" fill="#94A3B8">Zero DBU em testes Chispa</text>
    </g>

    <!-- Tuning Engine Box -->
    <g transform="translate(15, 400)">
      <rect width="280" height="375" rx="8" fill="#0F172A" stroke="#FF3621" stroke-width="1.5" />
      <text x="16" y="28" font-size="12" font-weight="800" fill="#FF6B59">⚙ Forge Tuning &amp; Optimizer</text>
      <text x="16" y="55" font-size="10" fill="#E2E8F0">• <tspan fill="#FF6B59">forge tune optimize</tspan></text>
      <text x="16" y="75" font-size="10" fill="#CBD5E1">• Z-Order clustering multidimensional</text>
      <text x="16" y="95" font-size="10" fill="#CBD5E1">• Liquid Clustering automático</text>
      <text x="16" y="115" font-size="10" fill="#CBD5E1">• <tspan fill="#FF6B59">forge tune vacuum</tspan> (168h retention)</text>
      <text x="16" y="145" font-size="11" font-weight="700" fill="#F87171">Perfis de Otimização Homologados:</text>
      <text x="16" y="168" font-size="10" fill="#94A3B8">⚡ Balanced (Padrão para ETL misto)</text>
      <text x="16" y="188" font-size="10" fill="#94A3B8">🚀 Aggressive (Alta frequência / BI rápido)</text>
      <text x="16" y="208" font-size="10" fill="#94A3B8">💰 Cost-Saving (Mínimo consumo I/O)</text>
      <text x="16" y="240" font-size="10" fill="#CBD5E1">• Compactação de pequenos arquivos</text>
      <text x="16" y="260" font-size="10" fill="#CBD5E1">• Data skipping com estatísticas de coluna</text>
      <text x="16" y="280" font-size="10" fill="#CBD5E1">• Redução drástica de tempo de scan S3</text>
      <text x="16" y="315" font-size="10" fill="#FCA5A5">✔ Consultas analíticas até 5x mais rápidas</text>
    </g>
  </g>

  <!-- ==================== ZONE 4: STORAGE & UNITY CATALOG ==================== -->
  <g transform="translate(1025, 95)">
    <rect width="310" height="800" rx="14" fill="url(#cardGrad)" stroke="#0284C7" stroke-width="2" filter="url(#dropShadow)" />
    <rect width="310" height="38" rx="14" fill="#0369A1" />
    <rect y="24" width="310" height="14" fill="#0369A1" />
    <text x="20" y="25" font-size="13" font-weight="800" fill="#FFFFFF">4. ARMAZENAMENTO &amp; GOVERNANÇA</text>

    <!-- Unity Catalog -->
    <g transform="translate(15, 55)">
      <rect width="280" height="75" rx="8" fill="url(#boxGrad)" stroke="#0284C7" stroke-width="1.2" />
      <rect x="12" y="14" width="46" height="46" rx="8" fill="#1B2559" stroke="#FF3621" stroke-width="1.5"/>
      <circle cx="35" cy="30" r="5" fill="#FF3621"/>
      <circle cx="28" cy="42" r="3.5" fill="#00A8FF"/>
      <circle cx="42" cy="42" r="3.5" fill="#10B981"/>
      <text x="68" y="30" font-size="12" font-weight="700" fill="#38BDF8">Databricks Unity Catalog</text>
      <text x="68" y="47" font-size="10" fill="#CBD5E1">Governança unificada &amp; ACLs</text>
      <text x="68" y="61" font-size="9" fill="#94A3B8">Data Lineage &amp; Auditoria</text>
    </g>

    <!-- Bronze Delta -->
    <g transform="translate(15, 140)">
      <rect width="280" height="75" rx="8" fill="url(#boxGrad)" stroke="#D97706" stroke-width="1.2" />
      <rect x="12" y="14" width="46" height="46" rx="8" fill="#FEF3C7"/>
      <polygon points="35,20 52,48 18,48" fill="#00A8FF"/>
      <polygon points="35,32 46,46 24,46" fill="#004D80"/>
      <text x="68" y="30" font-size="12" font-weight="700" fill="#FBBF24">Bronze Layer (Delta Lake)</text>
      <text x="68" y="47" font-size="10" fill="#CBD5E1">s3://lakehouse-data/bronze/</text>
      <text x="68" y="61" font-size="9" fill="#94A3B8">Append-only · Auditoria original</text>
    </g>

    <!-- Silver Delta -->
    <g transform="translate(15, 225)">
      <rect width="280" height="75" rx="8" fill="url(#boxGrad)" stroke="#0284C7" stroke-width="1.2" />
      <rect x="12" y="14" width="46" height="46" rx="8" fill="#E0F2FE"/>
      <polygon points="35,20 52,48 18,48" fill="#00A8FF"/>
      <polygon points="35,32 46,46 24,46" fill="#004D80"/>
      <text x="68" y="30" font-size="12" font-weight="700" fill="#38BDF8">Silver Layer (Delta Lake)</text>
      <text x="68" y="47" font-size="10" fill="#CBD5E1">s3://lakehouse-data/silver/</text>
      <text x="68" y="61" font-size="9" fill="#94A3B8">Cleaned · Deduplicada · ACID</text>
    </g>

    <!-- Gold Delta + Iceberg -->
    <g transform="translate(15, 310)">
      <rect width="280" height="75" rx="8" fill="url(#boxGrad)" stroke="#CA8A04" stroke-width="1.2" />
      <rect x="12" y="14" width="46" height="46" rx="8" fill="#FEF9C3"/>
      <circle cx="35" cy="37" r="18" fill="#EBF8FF" stroke="#0284C7" stroke-width="2"/>
      <polygon points="35,24 45,35 25,35" fill="#38BDF8"/>
      <polygon points="35,50 45,36 25,36" fill="#0284C7"/>
      <text x="68" y="30" font-size="12" font-weight="700" fill="#FACC15">Gold Layer (Delta + Iceberg)</text>
      <text x="68" y="47" font-size="10" fill="#CBD5E1">s3://lakehouse-data/gold/</text>
      <text x="68" y="61" font-size="9" fill="#94A3B8">UniForm: Leitura universal sem cópia</text>
    </g>

    <!-- Iceberg & Formats Engine Box -->
    <g transform="translate(15, 400)">
      <rect width="280" height="375" rx="8" fill="#0F172A" stroke="#0284C7" stroke-width="1.5" />
      <text x="16" y="28" font-size="12" font-weight="800" fill="#38BDF8">🧊 Iceberg UniForm Engine</text>
      <text x="16" y="55" font-size="10" fill="#E2E8F0">• <tspan fill="#38BDF8">forge iceberg enable-uniform</tspan></text>
      <text x="16" y="75" font-size="10" fill="#CBD5E1">• Geração assíncrona de Iceberg Metadata</text>
      <text x="16" y="95" font-size="10" fill="#CBD5E1">• Parquet único compartilhado no S3</text>
      <text x="16" y="115" font-size="10" fill="#CBD5E1">• Inspeção: <tspan fill="#38BDF8">forge iceberg inspect</tspan></text>
      <text x="16" y="135" font-size="10" fill="#CBD5E1">• Histórico: <tspan fill="#38BDF8">forge iceberg snapshots</tspan></text>
      <text x="16" y="165" font-size="11" font-weight="700" fill="#38BDF8">Conversor Universal de Formatos:</text>
      <text x="16" y="188" font-size="10" fill="#94A3B8">• forge data convert --format parquet</text>
      <text x="16" y="208" font-size="10" fill="#94A3B8">• forge data convert --format csv</text>
      <text x="16" y="228" font-size="10" fill="#94A3B8">• forge data convert --format json</text>
      <text x="16" y="260" font-size="10" fill="#CBD5E1">• Zero replicação de dados</text>
      <text x="16" y="280" font-size="10" fill="#CBD5E1">• Zero custo de egress entre nuvens</text>
      <text x="16" y="315" font-size="10" fill="#BAE6FD">✔ Compatível com Snowflake, Athena e Trino</text>
    </g>
  </g>

  <!-- ==================== ZONE 5: ANALYTICS & TELEMETRY ==================== -->
  <g transform="translate(1365, 95)">
    <rect width="270" height="800" rx="14" fill="url(#cardGrad)" stroke="#8C4FFF" stroke-width="2" filter="url(#dropShadow)" />
    <rect width="270" height="38" rx="14" fill="#581C87" />
    <rect y="24" width="270" height="14" fill="#581C87" />
    <text x="20" y="25" font-size="13" font-weight="800" fill="#FFFFFF">5. CONSUMO ANALÍTICO &amp; LOGS</text>

    <!-- Databricks SQL -->
    <g transform="translate(15, 55)">
      <rect width="240" height="75" rx="8" fill="url(#boxGrad)" stroke="#FF3621" stroke-width="1.2" />
      <rect x="12" y="14" width="46" height="46" rx="8" fill="#FF3621"/>
      <text x="35" y="44" font-size="20" text-anchor="middle" fill="#FFFFFF">⚡</text>
      <text x="68" y="30" font-size="12" font-weight="700" fill="#FF6B59">Databricks SQL</text>
      <text x="68" y="47" font-size="10" fill="#CBD5E1">Serverless Warehouses</text>
      <text x="68" y="61" font-size="9" fill="#94A3B8">Power BI / Tableau BI</text>
    </g>

    <!-- AWS Athena -->
    <g transform="translate(15, 140)">
      <rect width="240" height="75" rx="8" fill="url(#boxGrad)" stroke="#8C4FFF" stroke-width="1.2" />
      <rect x="12" y="14" width="46" height="46" rx="8" fill="#8C4FFF"/>
      <circle cx="33" cy="35" r="11" fill="none" stroke="#FFFFFF" stroke-width="2.5"/>
      <line x1="41" y1="43" x2="51" y2="53" stroke="#FFFFFF" stroke-width="3.5" stroke-linecap="round"/>
      <text x="68" y="30" font-size="12" font-weight="700" fill="#C084FC">AWS Athena</text>
      <text x="68" y="47" font-size="10" fill="#CBD5E1">Lê Iceberg UniForm</text>
      <text x="68" y="61" font-size="9" fill="#94A3B8">Serverless ad-hoc queries</text>
    </g>

    <!-- Amazon Redshift Spectrum -->
    <g transform="translate(15, 225)">
      <rect width="240" height="75" rx="8" fill="url(#boxGrad)" stroke="#8C4FFF" stroke-width="1.2" />
      <rect x="12" y="14" width="46" height="46" rx="8" fill="#8C4FFF"/>
      <polygon points="35,21 49,29 49,45 35,53 21,45 21,29" fill="none" stroke="#FFFFFF" stroke-width="2.5"/>
      <text x="68" y="30" font-size="12" font-weight="700" fill="#C084FC">Amazon Redshift</text>
      <text x="68" y="47" font-size="10" fill="#CBD5E1">Redshift Spectrum</text>
      <text x="68" y="61" font-size="9" fill="#94A3B8">Data Warehouse queries</text>
    </g>

    <!-- AWS CloudWatch -->
    <g transform="translate(15, 310)">
      <rect width="240" height="75" rx="8" fill="url(#boxGrad)" stroke="#E7157B" stroke-width="1.2" />
      <rect x="12" y="14" width="46" height="46" rx="8" fill="#E7157B"/>
      <circle cx="35" cy="37" r="16" fill="none" stroke="#FFFFFF" stroke-width="2.5"/>
      <polyline points="24,42 32,31 38,39 46,27" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round"/>
      <text x="68" y="30" font-size="12" font-weight="700" fill="#F472B6">AWS CloudWatch</text>
      <text x="68" y="47" font-size="10" fill="#CBD5E1">Métricas e Alertas</text>
      <text x="68" y="61" font-size="9" fill="#94A3B8">Auditoria em tempo real</text>
    </g>

    <!-- Logging Box -->
    <g transform="translate(15, 400)">
      <rect width="240" height="375" rx="8" fill="#0F172A" stroke="#8C4FFF" stroke-width="1.5" />
      <text x="16" y="28" font-size="12" font-weight="800" fill="#C084FC">📊 Structured JSON Logs</text>
      <text x="16" y="55" font-size="10" fill="#E2E8F0">• <tspan fill="#C084FC">pipeline_audit_step()</tspan></text>
      <text x="16" y="75" font-size="10" fill="#CBD5E1">• Context manager com métricas</text>
      <text x="16" y="95" font-size="10" fill="#CBD5E1">• Rastreamento de rows processadas</text>
      <text x="16" y="115" font-size="10" fill="#CBD5E1">• Duração em milissegundos</text>
      <text x="16" y="145" font-size="11" font-weight="700" fill="#C084FC">Exemplo de Payload Emitido:</text>
      <rect x="12" y="160" width="216" height="110" rx="6" fill="#1E1E2E" />
      <text x="20" y="180" font-size="9" font-family="monospace" fill="#94A3B8">{"step": "gold_kpis",</text>
      <text x="20" y="196" font-size="9" font-family="monospace" fill="#94A3B8"> "status": "SUCCESS",</text>
      <text x="20" y="212" font-size="9" font-family="monospace" fill="#94A3B8"> "duration_ms": 14200,</text>
      <text x="20" y="228" font-size="9" font-family="monospace" fill="#94A3B8"> "rows_affected": 850,</text>
      <text x="20" y="244" font-size="9" font-family="monospace" fill="#94A3B8"> "timestamp": "2026-09-08"}</text>
      <text x="16" y="295" font-size="10" fill="#CBD5E1">• Exportação para CloudWatch</text>
      <text x="16" y="315" font-size="10" fill="#E9D5FF">✔ Observabilidade completa</text>
    </g>
  </g>

  <!-- ==================== FLOW CONNECTORS ==================== -->
  <!-- Ingest to Compute -->
  <path d="M 340 500 L 685 500" stroke="#38BDF8" stroke-width="2.5" stroke-dasharray="4,4" marker-end="url(#arrowBlue)" />
  <!-- Control to Compute -->
  <path d="M 660 470 L 685 470" stroke="#10B981" stroke-width="2.5" marker-end="url(#arrowGreen)" />
  <!-- Compute to Storage -->
  <path d="M 995 500 L 1025 500" stroke="#FF3621" stroke-width="2.5" marker-end="url(#arrowRed)" />
  <!-- Storage to Analytics -->
  <path d="M 1335 500 L 1365 500" stroke="#8C4FFF" stroke-width="2.5" marker-end="url(#arrowPurple)" />

  <!-- ==================== FOOTER ==================== -->
  <g transform="translate(45, 915)">
    <rect width="1590" height="42" rx="8" fill="#151D2F" stroke="#334155" stroke-width="1" />
    <text x="795" y="26" font-size="12" font-weight="700" fill="#94A3B8" text-anchor="middle">
      Garantias: Arquitetura Lakehouse sem vendor lock-in · 100% de conformidade ACID no AWS S3 com Delta Lake e Apache Iceberg UniForm · Orquestração resiliente e Governança centralizada com Unity Catalog
    </text>
  </g>
</svg>"""
    return svg

def main():
    content = generate_svg()
    target = "docs/architecture.svg"
    with open(target, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"File successfully written to {target} ({len(content)} bytes)")

if __name__ == "__main__":
    main()
