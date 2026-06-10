import unittest

from aegisai.application.knowledge import SQLiteVectorMemoryStore


class VectorMemoryTests(unittest.TestCase):
    def test_retrieves_policy_memory_by_tenant_and_namespace(self) -> None:
        memory = SQLiteVectorMemoryStore()
        memory.seed_enterprise_memory()

        results = memory.search(
            tenant_id="bank-demo",
            namespace="refund_policy",
            query="refund above 2500 needs approval",
        )

        self.assertEqual(memory.count(), 3)
        self.assertEqual(results[0][0].source_uri, "policy://refund/thresholds")
        self.assertGreater(results[0][1], 0)


if __name__ == "__main__":
    unittest.main()
