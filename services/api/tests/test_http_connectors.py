import tempfile
import unittest
from pathlib import Path

try:
    from fastapi.testclient import TestClient
    from aegisai.api import app
    from aegisai.interfaces.http import api as api_module
    from aegisai.application.execution.connectors.http_connector import HttpConnectorStore
except ModuleNotFoundError:  # pragma: no cover
    TestClient = None
    app = None
    api_module = None
    HttpConnectorStore = None


@unittest.skipIf(TestClient is None, "FastAPI dependencies are not installed")
class HttpConnectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._store_path = Path(self._tmpdir.name) / "http_connectors.json"
        api_module.http_connector_manager.store = HttpConnectorStore(self._store_path)
        api_module.http_connector_manager.store.load()
        api_module.http_connector_manager._connector_instances.clear()
        api_module.execution_broker.connector_registry._registered_connectors.clear()
        api_module.http_connector_manager.bootstrap()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_register_http_connector_appears_in_catalog(self) -> None:
        response = self.client.post(
            "/api/connectors/http",
            json={
                "display_name": "Acme Billing API",
                "base_url": "https://billing.acme.example",
                "target_system": "acme_billing",
                "tool_names": ["acme_billing.issue_credit"],
                "demo_mode": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        connector_id = response.json()["connector"]["connector_id"]
        self.assertTrue(connector_id.startswith("http_"))

        catalog = self.client.get("/api/connectors/catalog").json()
        ids = {item["connector_id"] for item in catalog["connectors"]}
        self.assertIn(connector_id, ids)
        registered = next(
            item for item in catalog["connectors"] if item["connector_id"] == connector_id
        )
        self.assertEqual(registered["kind"], "http")
        self.assertEqual(registered["display_name"], "Acme Billing API")

    def test_http_connector_test_demo_mode(self) -> None:
        response = self.client.post(
            "/api/connectors/http/test",
            json={
                "base_url": "https://billing.acme.example",
                "demo_mode": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertIn("Demo mode", payload["message"])

    def test_delete_http_connector(self) -> None:
        created = self.client.post(
            "/api/connectors/http",
            json={
                "display_name": "Temp Connector",
                "base_url": "https://temp.example",
                "target_system": "temp_system",
                "demo_mode": True,
            },
        ).json()
        connector_id = created["connector"]["connector_id"]

        deleted = self.client.delete(f"/api/connectors/http/{connector_id}")
        self.assertEqual(deleted.status_code, 200)

        listing = self.client.get("/api/connectors/http").json()
        self.assertEqual(listing["total"], 0)
