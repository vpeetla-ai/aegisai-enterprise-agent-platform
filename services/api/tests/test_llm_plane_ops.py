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

    def test_unreachable_uses_demo_fallback_by_default(self) -> None:
        with patch(
            "aegisai.product.llm_plane_ops.fetch_plane_metrics",
            return_value={"reachable": False, "error": "ConnectError", "detail": "down"},
        ):
            gw = gateway_ops_payload()
            cache = cache_ops_payload()
        self.assertTrue(gw["reachable"])
        self.assertEqual(gw["source"], "demo_fallback")
        self.assertEqual(gw["metrics"]["service"], "aegis-llm-gateway")
        self.assertEqual(gw["live_error"], "ConnectError")
        self.assertTrue(cache["reachable"])
        self.assertEqual(cache["source"], "demo_fallback")
        self.assertEqual(cache["metrics"]["service"], "aegis-semantic-cache")

    def test_demo_fallback_can_be_disabled(self) -> None:
        with (
            patch.dict("os.environ", {"LLM_PLANE_DEMO_FALLBACK": "false"}),
            patch(
                "aegisai.product.llm_plane_ops.fetch_plane_metrics",
                return_value={"reachable": False, "error": "ConnectError"},
            ),
        ):
            gw = gateway_ops_payload()
        self.assertFalse(gw["reachable"])
        self.assertNotEqual(gw.get("source"), "demo_fallback")

    def test_live_metrics_skip_demo_fallback(self) -> None:
        with patch(
            "aegisai.product.llm_plane_ops.fetch_plane_metrics",
            return_value={
                "reachable": True,
                "source": "live",
                "metrics": {"completions": 9},
            },
        ):
            gw = gateway_ops_payload()
        self.assertEqual(gw["source"], "live")
        self.assertEqual(gw["metrics"]["completions"], 9)


if __name__ == "__main__":
    unittest.main()
