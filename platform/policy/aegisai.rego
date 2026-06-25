# AegisAI FinOps policy pack (OPA) — mirrors runtime guardrails for simulation parity
package aegisai.policy

import future.keywords.if
import future.keywords.in

default decision := "auto_approve"
default approval_role := ""

# Block restricted irreversible data operations
decision := "block" if {
    input.data_classification == "restricted"
    not input.reversible
}

decision := "block" if {
    input.risk_level == "critical"
}

decision := "escalate" if {
    input.risk_level == "high"
    decision != "block"
}

approval_role := "senior_domain_approver" if decision == "escalate"

decision := "human_approval" if {
    input.risk_level == "medium"
    decision != "block"
    decision != "escalate"
}

approval_role := "workflow_owner" if decision == "human_approval"

# Evaluation failures on elevated risk
decision := "block" if {
    not input.evaluation_passed
    input.risk_level in {"high", "critical"}
}

decision := "human_approval" if {
    not input.evaluation_passed
    input.risk_level == "medium"
    decision != "block"
}

# Financial thresholds (USD)
decision := "escalate" if {
    input.amount_usd >= 10000
    decision != "block"
}

decision := "human_approval" if {
    input.amount_usd >= 1000
    input.amount_usd < 10000
    decision != "block"
    decision != "escalate"
}

reason_codes contains code if {
    input.amount_usd >= 10000
    code := "large_financial_amount"
}

reason_codes contains code if {
    input.data_classification == "restricted"
    code := "restricted_data"
}

# Deploy tools always require human approval before execution
decision := "human_approval" if {
    input.action_type in {"deploy_frontend", "deploy_backend", "deploy_release"}
    decision != "block"
}

decision := "human_approval" if {
    startswith(input.action_type, "deploy_")
    decision != "block"
}

approval_role := "release_manager" if {
    startswith(input.action_type, "deploy_")
}

reason_codes contains code if {
    startswith(input.action_type, "deploy_")
    code := "production_deploy_requires_hitl"
}
