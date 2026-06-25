"""Buyer-module routes used by TopTierProductPanels in the control plane UI."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aegisai.interfaces.http.api import app

client = TestClient(app)

POLICY_BODY = {
    "tenant_id": "bank-demo",
    "agent_id": "agent-refund",
    "principal_id": "execution-broker",
    "tool_name": "payments.issue_refund",
    "action_type": "issue_refund",
    "target_system": "payments",
    "amount_usd": 2500,
    "data_classification": "confidential",
    "reversible": True,
    "customer_impact": True,
    "grounding_score": 0.9,
    "safety_score": 0.95,
    "policy_compliance_score": 0.88,
}


def test_developer_quickstart_route() -> None:
    response = client.get("/api/platform/developer-quickstart")
    assert response.status_code == 200
    body = response.json()
    assert "steps" in body
    assert len(body["steps"]) >= 4


def test_regulated_customer_ops_demo_route() -> None:
    response = client.get("/api/product/regulatory-customer-ops-demo")
    assert response.status_code == 200
    body = response.json()
    assert body["governed_steps"]
    assert body["story"]


def test_policy_studio_dry_run_route() -> None:
    response = client.post("/api/policy/studio/dry-run", json=POLICY_BODY)
    assert response.status_code == 200
    body = response.json()
    assert body["dry_run_decision"]
    assert body["blast_radius"]["estimated_monthly_intercepts"] > 0


def test_identity_graph_route() -> None:
    response = client.get("/api/identity/graph")
    assert response.status_code == 200
    body = response.json()
    assert body["nodes"]
    assert body["edges"]


def test_top_one_percent_product_routes() -> None:
    assert client.get("/api/platform/gateway-sdks").json()["packages"]
    assert client.get("/api/platform/deployment-posture").json()["tracks"]
    assert client.get("/api/demo/flagship-flow").json()["steps"]
    assert client.get("/api/identity/permission-matrix").json()["rows"]
    assert client.get("/api/incidents/timeline").json()["events"]
    assert client.get("/api/agent-cloud/posture").json()["pillars"]
    assert client.get("/api/agent-cloud/monitor").json()["activity"]

    replay = client.post("/api/policy/replay", json=POLICY_BODY)
    assert replay.status_code == 200
    assert replay.json()["cases_replayed"] >= 3

    release = client.post(
        "/api/release-gates/promote",
        json={"agent_id": "agent-refund", "release_version": "refund-agent-v2"},
    )
    assert release.status_code == 200
    assert release.json()["decision"] == "promote"

    registered = client.post(
        "/api/agent-registry/lifecycle",
        json={
            "agent_id": "agent-route-test",
            "name": "Route Test Agent",
            "owner": "AI Platform",
            "business_domain": "Customer Operations",
            "risk_tier": "medium",
            "autonomy_level": 1,
            "allowed_tools": ["rag.search_policy_memory"],
            "data_classes": ["internal"],
        },
    )
    assert registered.status_code == 200
    assert registered.json()["agent"]["agent_id"] == "agent-route-test"

    status = client.patch(
        "/api/agent-registry/lifecycle/agent-route-test/status",
        json={"status": "approved"},
    )
    assert status.status_code == 200
    assert status.json()["agent"]["status"] == "approved"
