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
