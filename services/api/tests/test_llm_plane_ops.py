"""Tests for LLM plane ops BFF (Control Room — no live gateway required)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from aegisai.product.llm_plane_ops import cache_ops_payload, fetch_plane_metrics, gateway_ops_payload


class LlmPlaneOpsTests(unittest.TestCase):
    def test_fetch_unreachable_returns_stub(self) -> None:
        with patch("aegisai.product.llm_plane_ops.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = RuntimeError("down")
            result = fetch_plane_metrics("http://127.0.0.1:9/v1/ops/metrics")
        self.assertFalse(result["reachable"])
        self.assertEqual(result["error"], "RuntimeError")

    def test_fetch_success_wraps_metrics(self) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = lambda: None
        mock_resp.json.return_value = {"service": "aegis-llm-gateway", "completions": 3}
        with patch("aegisai.product.llm_plane_ops.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_resp
            result = fetch_plane_metrics("http://gw.test/v1/ops/metrics")
        self.assertTrue(result["reachable"])
        self.assertEqual(result["metrics"]["completions"], 3)

    def test_gateway_and_cache_payload_include_plane(self) -> None:
        with patch(
            "aegisai.product.llm_plane_ops.fetch_plane_metrics",
            return_value={"reachable": False, "error": "url_not_configured"},
        ):
            gw = gateway_ops_payload()
            cache = cache_ops_payload()
        self.assertEqual(gw["plane"], "aegis-llm-gateway")
        self.assertEqual(cache["plane"], "aegis-semantic-cache")


if __name__ == "__main__":
    unittest.main()
