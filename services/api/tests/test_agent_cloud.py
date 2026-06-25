"""Agent Cloud routes — Monitor, Govern, Remediate (Rubrik / Guild inspired)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aegisai.interfaces.http.api import app

client = TestClient(app)


def test_agent_cloud_posture_route() -> None:
    response = client.get("/api/agent-cloud/posture")
    assert response.status_code == 200
    body = response.json()
    assert body["product_module"] == "Agent Cloud"
    assert len(body["pillars"]) == 3
    pillar_ids = {pillar["id"] for pillar in body["pillars"]}
    assert pillar_ids == {"monitor", "govern", "remediate"}


def test_agent_cloud_monitor_route() -> None:
    response = client.get("/api/agent-cloud/monitor")
    assert response.status_code == 200
    body = response.json()
    assert body["product_module"] == "Agent Monitor"
    assert body["agents"]
    assert body["activity"]


def test_agent_cloud_govern_route() -> None:
    response = client.get("/api/agent-cloud/govern")
    assert response.status_code == 200
    body = response.json()
    assert body["product_module"] == "Agent Govern"
    assert body["zero_trust_controls"]


def test_agent_cloud_undoable_route() -> None:
    response = client.get("/api/agent-cloud/undoable")
    assert response.status_code == 200
    body = response.json()
    assert body["product_module"] == "Agent Remediate"
    assert body["actions"]


def test_agent_cloud_undo_demo_execution() -> None:
    undoable = client.get("/api/agent-cloud/undoable").json()
    demo_execution = next(
        (action for action in undoable["actions"] if action["execution_id"] == "exec-demo-rollback-001"),
        None,
    )
    assert demo_execution is not None

    response = client.post(
        "/api/agent-cloud/undo",
        json={
            "tenant_id": "bank-demo",
            "execution_id": "exec-demo-rollback-001",
            "reason": "Buyer demo rollback",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "rolled_back"
    assert body["recovery_time_seconds"] == 45

    repeat = client.post(
        "/api/agent-cloud/undo",
        json={
            "tenant_id": "bank-demo",
            "execution_id": "exec-demo-rollback-001",
            "reason": "Idempotent undo check",
        },
    )
    assert repeat.json()["status"] == "rolled_back"
