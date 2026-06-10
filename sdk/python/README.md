# AegisAI Gateway SDK (Python)

```bash
pip install httpx
export PYTHONPATH=sdk/python
```

```python
from aegisai_gateway import GatewayClient, GatewayToolRequest

client = GatewayClient(base_url="http://localhost:8000")
result = client.request_tool(
    GatewayToolRequest(
        tenant_id="bank-demo",
        agent_id="agent-refund",
        principal_id="execution-broker",
        tool_name="payments.issue_refund",
        action_type="issue_refund",
        target_system="payments",
        amount_usd=2500,
        data_classification="confidential",
        customer_impact=True,
    )
)
if result.allowed:
    print("Token:", result.execution_token)
elif result.requires_approval:
    print("Paused for HITL:", result.raw["business_explanation"])
else:
    print("Blocked:", result.gateway_decision)
```
