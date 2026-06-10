import os
import unittest
from unittest.mock import Mock, patch

from aegisai.application.knowledge import LLMGateway


class LLMGatewayTests(unittest.TestCase):
    def test_local_provider_remains_offline_default(self) -> None:
        gateway = LLMGateway(provider="local")

        response = gateway.complete("system", "refund request")

        self.assertEqual(response.provider, "local")
        self.assertIn("Refund workflow", response.content)

    def test_openai_provider_requires_api_key(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            gateway = LLMGateway(provider="openai", model="gpt-test")

            response = gateway.complete("system", "hello")

        self.assertEqual(response.provider, "openai")
        self.assertEqual(response.confidence, 0.0)
        self.assertIn("OPENAI_API_KEY", response.content)

    @patch("aegisai.application.knowledge.llm_gateway.httpx.Client")
    def test_openai_provider_uses_responses_api(self, client_cls: Mock) -> None:
        response = Mock()
        response.json.return_value = {"output_text": "Grounded OpenAI answer."}
        response.raise_for_status.return_value = None
        client = client_cls.return_value.__enter__.return_value
        client.post.return_value = response

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            gateway = LLMGateway(provider="openai", model="gpt-test")
            result = gateway.complete("system prompt", "user prompt")

        self.assertEqual(result.provider, "openai")
        self.assertEqual(result.content, "Grounded OpenAI answer.")
        client.post.assert_called_once()
        call = client.post.call_args
        self.assertTrue(call.args[0].endswith("/responses"))
        self.assertEqual(call.kwargs["json"]["instructions"], "system prompt")
        self.assertEqual(call.kwargs["json"]["input"], "user prompt")


if __name__ == "__main__":
    unittest.main()
