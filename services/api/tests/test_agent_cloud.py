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


def test_agent_cloud_monitor_skips_seed_when_production_strict(
    monkeypatch,
) -> None:
    """PRODUCTION_STRICT=true: empty audit must not invent demo monitor events."""
    monkeypatch.setenv("PRODUCTION_STRICT", "true")
    monkeypatch.delenv("AEGISAI_ENFORCE_AUTH", raising=False)

    from aegisai.product import agent_cloud as agent_cloud_mod

    real_seed = agent_cloud_mod._seed_monitor_activity

    def _fail_if_seeded(*_args, **_kwargs):
        raise AssertionError("seed monitor must not run under PRODUCTION_STRICT")

    monkeypatch.setattr(agent_cloud_mod, "_seed_monitor_activity", _fail_if_seeded)

    # Force empty audit so the only path to activity would be the seed helper.
    from aegisai.interfaces.http import api as api_mod

    store = api_mod.control_plane_store

    def _empty_audit(tenant_id: str, *, limit: int = 20):
        return []

    monkeypatch.setattr(store, "list_recent_audit_events", _empty_audit)

    response = client.get("/api/agent-cloud/monitor")
    assert response.status_code == 200
    body = response.json()
    assert body["product_module"] == "Agent Monitor"
    assert body["activity"] == []

    # Restore callability for other tests if the module is reused.
    monkeypatch.setattr(agent_cloud_mod, "_seed_monitor_activity", real_seed)


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
