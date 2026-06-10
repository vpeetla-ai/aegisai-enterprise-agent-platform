from aegisai.application.guardrails import DecisionEngine
from aegisai.application.knowledge import SQLiteVectorMemoryStore
from aegisai.application.orchestration import BusinessRequest, MultiAgentOrchestrator
from aegisai.domain import ActionProposal, DataClassification
from aegisai.infrastructure.persistence import SQLiteControlPlaneStore


def main() -> None:
    engine = DecisionEngine()
    proposal = ActionProposal(
        proposal_id="proposal-001",
        tenant_id="bank-demo",
        agent_id="refund-agent",
        action_type="issue_refund",
        target_system="payments",
        amount_usd=2_500,
        data_classification=DataClassification.CONFIDENTIAL,
        reversible=True,
        customer_impact=True,
        model_confidence=0.82,
        evaluation_scores={
            "grounding": 0.91,
            "safety": 0.96,
            "policy_compliance": 0.88,
        },
    )
    decision = engine.decide(proposal)
    print("Single-agent control-plane decision:")
    print(decision)

    orchestrator = MultiAgentOrchestrator()
    result = orchestrator.run(
        BusinessRequest(
            request_id="case-portfolio-001",
            tenant_id="bank-demo",
            user_id="customer-123",
            text="Customer is requesting a refund for a failed booking",
            amount_usd=2_500,
            data_classification=DataClassification.CONFIDENTIAL,
        )
    )
    print("\nMulti-agent orchestration result:")
    print(f"workflow_type={result.workflow_type.value}")
    print(f"agents_run={[agent.value for agent in result.agents_run]}")
    print(f"governance_decisions={result.context.governance_decisions}")

    store = SQLiteControlPlaneStore()
    store.save_orchestration(result)
    print("\nPersistence and audit:")
    print(f"cases={store.count('cases')}")
    print(f"agent_traces={store.count('agent_traces')}")
    print(f"audit_chain_valid={store.verify_audit_chain('bank-demo')}")

    memory = SQLiteVectorMemoryStore()
    memory.seed_enterprise_memory()
    results = memory.search("bank-demo", "refund_policy", "refund above 2500 approval")
    print("\nAgent memory retrieval:")
    print(f"memory_documents={memory.count()}")
    print(f"top_memory={results[0][0].source_uri} score={results[0][1]:.3f}")


if __name__ == "__main__":
    main()
