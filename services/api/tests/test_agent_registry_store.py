from __future__ import annotations

import unittest

from aegisai.infrastructure.persistence.agent_registry_store import InMemoryAgentRegistryStore
from aegisai.product.agent_registry import AgentRegistryService


class AgentRegistryStoreTests(unittest.TestCase):
    def test_in_memory_store_seeds_agents(self) -> None:
        service = AgentRegistryService(InMemoryAgentRegistryStore())
        agents = service.list_agents()
        self.assertGreaterEqual(len(agents), 13)
        self.assertIsNotNone(service.get_agent("ai-content-factory"))

    def test_update_status_round_trip(self) -> None:
        store = InMemoryAgentRegistryStore()
        service = AgentRegistryService(store)
        updated = service.update_agent_status("venkat-ai-platform", "approved")
        assert updated is not None
        self.assertEqual(updated.status, "approved")


if __name__ == "__main__":
    unittest.main()
