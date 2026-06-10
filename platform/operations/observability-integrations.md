# Observability Integrations

## Positioning

AegisAI is the enterprise system of record for policy, HITL approvals, audit events, workflow state, and side-effect governance.

Langfuse and LangSmith are integrated as optional trace and evaluation exporters:

- Langfuse: open-source/self-hostable LLM observability, prompt management, datasets, evals, latency, and cost analytics.
- LangSmith: LangGraph/LangChain-friendly tracing, datasets, evals, prompt debugging, and developer workflow analysis.

## Code Ownership

```text
aegisai.observability/
  models.py      # ExporterStatus and TraceEvent contracts
  exporters.py   # LangfuseExporter and LangSmithExporter adapters
  service.py     # Vendor-neutral ObservabilityService facade
```

Application services call `ObservabilityService`; they do not import Langfuse or LangSmith SDKs directly. This keeps observability replaceable and prevents vendor SDK failures from breaking governed agent execution.

## Runtime Configuration

The API runs without either SDK installed. Exporters report `not_configured` or `sdk_missing` until the environment is ready.

Langfuse:

```bash
export LANGFUSE_PUBLIC_KEY=...
export LANGFUSE_SECRET_KEY=...
export LANGFUSE_HOST=https://cloud.langfuse.com
```

LangSmith:

```bash
export LANGSMITH_API_KEY=...
export LANGSMITH_PROJECT=aegisai-agent-governance-control-plane
export LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

Install optional SDKs:

```bash
UV_CACHE_DIR=.uv-cache uv pip install -r services/api/requirements-observability.txt
```

## API Surface

- `GET /api/observability/status`: exporter health and configuration posture.
- `POST /api/agents/run`: returns the agent decision plus per-exporter status for that run.

## Tradeoff

Do not make Langfuse or LangSmith the approval/audit source of truth. Treat them as observability destinations. This prevents vendor coupling while still giving engineering teams rich LLM trace and evaluation workflows.
