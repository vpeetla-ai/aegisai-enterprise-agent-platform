"""Dashboard and orchestrator route tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aegisai.interfaces.http.api import app

client = TestClient(app)


def test_dashboard_summary() -> None:
    body = client.get("/api/dashboard/summary").json()
    assert body["product_module"] == "Main Dashboard"
    assert len(body["tiles"]) >= 6


def test_orchestrators_registry() -> None:
    body = client.get("/api/orchestrators").json()
    assert len(body["orchestrators"]) == 3


def test_website_build_run() -> None:
    body = client.post("/api/orchestrators/website-build/run").json()
    assert body["status"] in {"completed", "pending_hitl"}
    assert body["requirements_doc"]
    assert len(body["agent_traces"]) == 5
    assert body["gateway_events"]


def test_ai_content_pipeline_run() -> None:
    body = client.post("/api/orchestrators/ai-content/run").json()
    assert body["status"] == "completed"
    assert body["topics"]


def test_stock_research_run() -> None:
    body = client.post("/api/orchestrators/stock-research/run").json()
    assert body["status"] == "completed"
    assert "DAILY MORNING STOCK INTELLIGENCE BRIEFING" in body["briefing_markdown"]


def test_orchestrator_runs_require_auth_when_enforced(monkeypatch) -> None:
    """These 3 routes previously had no AuthRequired dependency at all — anyone could
    trigger a real LLM-calling pipeline with zero credentials. Confirm they now honor
    the same AEGISAI_ENFORCE_AUTH gate every other mutating route already respects."""
    monkeypatch.setenv("AEGISAI_ENFORCE_AUTH", "true")
    for path in (
        "/api/orchestrators/ai-content/run",
        "/api/orchestrators/stock-research/run",
        "/api/orchestrators/website-build/run",
    ):
        resp = client.post(path)
        assert resp.status_code == 403, path


def test_orchestrator_runs_allowed_with_principal_header_when_enforced(monkeypatch) -> None:
    monkeypatch.setenv("AEGISAI_ENFORCE_AUTH", "true")
    resp = client.post(
        "/api/orchestrators/ai-content/run",
        headers={"X-AegisAI-Principal": "scheduler-bot"},
    )
    assert resp.status_code == 200
