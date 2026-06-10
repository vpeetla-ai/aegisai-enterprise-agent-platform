from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from aegisai.application.guardrails import DecisionEngine
from aegisai.domain import ActionProposal, AgentTrace, DataClassification, GovernanceDecision


class WorkflowType(StrEnum):
    REFUND = "refund"
    DISPUTE = "dispute"
    DATA_OPERATION = "data_operation"
    IT_OPERATION = "it_operation"
    CUSTOMER_MESSAGE = "customer_message"


class AgentName(StrEnum):
    PLANNER = "planner_agent"
    INTAKE = "intake_triage_agent"
    EVIDENCE = "evidence_retrieval_agent"
    COMPLIANCE = "risk_compliance_agent"
    REFUND = "refund_agent"
    DISPUTE = "payment_dispute_agent"
    DATA_OPS = "data_operations_agent"
    IT_OPS = "it_operations_agent"
    COMMS = "customer_communication_agent"


@dataclass(frozen=True)
class BusinessRequest:
    request_id: str
    tenant_id: str
    user_id: str
    text: str
    amount_usd: float = 0
    data_classification: DataClassification = DataClassification.INTERNAL
    customer_impact: bool = True


@dataclass
class SharedCaseContext:
    request: BusinessRequest
    workflow_type: WorkflowType | None = None
    evidence_refs: list[str] = field(default_factory=list)
    agent_notes: dict[str, str] = field(default_factory=dict)
    agent_traces: list[AgentTrace] = field(default_factory=list)
    proposed_actions: list[ActionProposal] = field(default_factory=list)
    governance_decisions: list[GovernanceDecision] = field(default_factory=list)

    def write_note(self, agent: AgentName, note: str) -> None:
        self.agent_notes[agent.value] = note

    def record_trace(
        self,
        agent: AgentName,
        step_name: str,
        output_ref: str,
        policy_findings: tuple[str, ...] = (),
    ) -> None:
        now = datetime.now(UTC).isoformat()
        self.agent_traces.append(
            AgentTrace(
                trace_id=f"trace-{uuid4()}",
                case_id=self.request.request_id,
                tenant_id=self.request.tenant_id,
                agent_name=agent.value,
                step_name=step_name,
                status="completed",
                input_ref=f"case://{self.request.request_id}",
                output_ref=output_ref,
                policy_findings=policy_findings,
                started_at=now,
                completed_at=now,
            )
        )


@dataclass(frozen=True)
class AgentResult:
    agent: AgentName
    note: str
    proposed_action: ActionProposal | None = None


@dataclass(frozen=True)
class OrchestrationResult:
    request_id: str
    workflow_type: WorkflowType
    agents_run: tuple[AgentName, ...]
    context: SharedCaseContext


class IntakeTriageAgent:
    name = AgentName.INTAKE

    def run(self, context: SharedCaseContext) -> AgentResult:
        text = context.request.text.lower()
        if "refund" in text or "cancel" in text or "credit" in text:
            context.workflow_type = WorkflowType.REFUND
        elif "dispute" in text or "chargeback" in text:
            context.workflow_type = WorkflowType.DISPUTE
        elif "delete" in text or "deletion" in text or "export" in text or "modify data" in text:
            context.workflow_type = WorkflowType.DATA_OPERATION
        elif "access" in text or "deploy" in text or "config" in text:
            context.workflow_type = WorkflowType.IT_OPERATION
        else:
            context.workflow_type = WorkflowType.CUSTOMER_MESSAGE

        note = f"classified_workflow={context.workflow_type.value}"
        context.write_note(self.name, note)
        context.record_trace(
            self.name,
            "classify_request",
            f"workflow://{context.workflow_type.value}",
        )
        return AgentResult(agent=self.name, note=note)


class PlannerAgent:
    name = AgentName.PLANNER

    def run(self, context: SharedCaseContext) -> AgentResult:
        workflow = context.workflow_type or WorkflowType.CUSTOMER_MESSAGE
        agent_plan = {
            WorkflowType.REFUND: "evidence->refund->compliance->communication->control_plane",
            WorkflowType.DISPUTE: "evidence->dispute->compliance->communication->control_plane",
            WorkflowType.DATA_OPERATION: "evidence->data_operations->compliance->control_plane",
            WorkflowType.IT_OPERATION: "evidence->it_operations->compliance->control_plane",
            WorkflowType.CUSTOMER_MESSAGE: "evidence->communication->control_plane_if_side_effecting",
        }[workflow]
        note = f"plan={agent_plan}"
        context.write_note(self.name, note)
        context.record_trace(self.name, "create_agent_plan", f"plan://{workflow.value}")
        return AgentResult(agent=self.name, note=note)


class EvidenceRetrievalAgent:
    name = AgentName.EVIDENCE

    def run(self, context: SharedCaseContext) -> AgentResult:
        workflow = context.workflow_type or WorkflowType.CUSTOMER_MESSAGE
        context.evidence_refs.extend(
            [
                f"crm://cases/{context.request.request_id}",
                f"policy://{workflow.value}/standard-operating-policy",
            ]
        )
        if workflow in {WorkflowType.REFUND, WorkflowType.DISPUTE}:
            context.evidence_refs.append(f"payments://transactions/{context.request.request_id}")

        note = f"evidence_refs={len(context.evidence_refs)}"
        context.write_note(self.name, note)
        context.record_trace(
            self.name,
            "retrieve_evidence",
            f"evidence://{context.request.request_id}/{len(context.evidence_refs)}",
        )
        return AgentResult(agent=self.name, note=note)


class RiskComplianceAgent:
    name = AgentName.COMPLIANCE

    def run(self, context: SharedCaseContext) -> AgentResult:
        findings: list[str] = []
        request = context.request

        if request.data_classification == DataClassification.RESTRICTED:
            findings.append("restricted_data")
        if request.amount_usd >= 10_000:
            findings.append("senior_financial_approval_required")
        if "fraud" in request.text.lower() or "legal" in request.text.lower():
            findings.append("compliance_escalation_required")

        note = "findings=" + (",".join(findings) if findings else "none")
        context.write_note(self.name, note)
        context.record_trace(
            self.name,
            "check_compliance_findings",
            f"findings://{context.request.request_id}",
            tuple(findings),
        )
        return AgentResult(agent=self.name, note=note)


class RefundAgent:
    name = AgentName.REFUND

    def run(self, context: SharedCaseContext) -> AgentResult:
        request = context.request
        action = ActionProposal(
            proposal_id=f"{request.request_id}:refund",
            tenant_id=request.tenant_id,
            agent_id=self.name.value,
            action_type="issue_refund",
            target_system="payments",
            amount_usd=request.amount_usd,
            data_classification=request.data_classification,
            reversible=True,
            customer_impact=request.customer_impact,
            model_confidence=0.86,
            evaluation_scores={"grounding": 0.9, "safety": 0.95, "policy_compliance": 0.88},
        )
        context.proposed_actions.append(action)
        note = f"proposed_refund_amount={request.amount_usd:.2f}"
        context.write_note(self.name, note)
        context.record_trace(self.name, "propose_refund_action", f"proposal://{action.proposal_id}")
        return AgentResult(agent=self.name, note=note, proposed_action=action)


class PaymentDisputeAgent:
    name = AgentName.DISPUTE

    def run(self, context: SharedCaseContext) -> AgentResult:
        request = context.request
        action = ActionProposal(
            proposal_id=f"{request.request_id}:dispute",
            tenant_id=request.tenant_id,
            agent_id=self.name.value,
            action_type="submit_dispute_evidence",
            target_system="payment_processor",
            amount_usd=request.amount_usd,
            data_classification=DataClassification.CONFIDENTIAL,
            reversible=False,
            customer_impact=True,
            model_confidence=0.82,
            evaluation_scores={"grounding": 0.88, "safety": 0.93, "policy_compliance": 0.9},
        )
        context.proposed_actions.append(action)
        note = "proposed_dispute_evidence_submission"
        context.write_note(self.name, note)
        context.record_trace(self.name, "propose_dispute_action", f"proposal://{action.proposal_id}")
        return AgentResult(agent=self.name, note=note, proposed_action=action)


class DataOperationsAgent:
    name = AgentName.DATA_OPS

    def run(self, context: SharedCaseContext) -> AgentResult:
        request = context.request
        action = ActionProposal(
            proposal_id=f"{request.request_id}:data-operation",
            tenant_id=request.tenant_id,
            agent_id=self.name.value,
            action_type="modify_or_delete_data",
            target_system="customer_data_platform",
            data_classification=request.data_classification,
            reversible=False,
            customer_impact=True,
            model_confidence=0.8,
            evaluation_scores={"grounding": 0.84, "safety": 0.91, "policy_compliance": 0.86},
        )
        context.proposed_actions.append(action)
        note = "proposed_data_operation_requires_identity_and_entitlement_validation"
        context.write_note(self.name, note)
        context.record_trace(
            self.name,
            "propose_data_operation",
            f"proposal://{action.proposal_id}",
            ("identity_validation_required", "entitlement_validation_required"),
        )
        return AgentResult(agent=self.name, note=note, proposed_action=action)


class ITOperationsAgent:
    name = AgentName.IT_OPS

    def run(self, context: SharedCaseContext) -> AgentResult:
        request = context.request
        action = ActionProposal(
            proposal_id=f"{request.request_id}:it-operation",
            tenant_id=request.tenant_id,
            agent_id=self.name.value,
            action_type="change_production_configuration",
            target_system="infrastructure",
            data_classification=DataClassification.CONFIDENTIAL,
            reversible=True,
            customer_impact=True,
            model_confidence=0.79,
            evaluation_scores={"grounding": 0.82, "safety": 0.89, "policy_compliance": 0.84},
        )
        context.proposed_actions.append(action)
        note = "proposed_operational_change_with_rollback_required"
        context.write_note(self.name, note)
        context.record_trace(
            self.name,
            "propose_operational_change",
            f"proposal://{action.proposal_id}",
            ("rollback_required",),
        )
        return AgentResult(agent=self.name, note=note, proposed_action=action)


class CustomerCommunicationAgent:
    name = AgentName.COMMS

    def run(self, context: SharedCaseContext) -> AgentResult:
        note = "drafted_customer_response_pending_governed_business_action"
        context.write_note(self.name, note)
        context.record_trace(self.name, "draft_customer_response", f"draft://{context.request.request_id}")
        return AgentResult(agent=self.name, note=note)


class MultiAgentOrchestrator:
    def __init__(self, decision_engine: DecisionEngine | None = None) -> None:
        self.decision_engine = decision_engine or DecisionEngine()
        self.intake = IntakeTriageAgent()
        self.planner = PlannerAgent()
        self.evidence = EvidenceRetrievalAgent()
        self.compliance = RiskComplianceAgent()
        self.refund = RefundAgent()
        self.dispute = PaymentDisputeAgent()
        self.data_ops = DataOperationsAgent()
        self.it_ops = ITOperationsAgent()
        self.comms = CustomerCommunicationAgent()

    def run(self, request: BusinessRequest) -> OrchestrationResult:
        context = SharedCaseContext(request=request)
        agents_run: list[AgentName] = []

        for agent in (self.intake, self.planner, self.evidence):
            result = agent.run(context)
            agents_run.append(result.agent)

        domain_agent = self._select_domain_agent(context.workflow_type)
        for agent in (domain_agent, self.compliance, self.comms):
            result = agent.run(context)
            agents_run.append(result.agent)

        for proposal in context.proposed_actions:
            decision = self.decision_engine.decide(proposal)
            context.governance_decisions.append(decision)
            context.record_trace(
                AgentName.COMPLIANCE,
                "control_plane_governance_decision",
                f"decision://{proposal.proposal_id}/{decision.decision.value}",
                decision.risk.reason_codes,
            )

        return OrchestrationResult(
            request_id=request.request_id,
            workflow_type=context.workflow_type or WorkflowType.CUSTOMER_MESSAGE,
            agents_run=tuple(agents_run),
            context=context,
        )

    def _select_domain_agent(
        self,
        workflow_type: WorkflowType | None,
    ) -> RefundAgent | PaymentDisputeAgent | DataOperationsAgent | ITOperationsAgent | CustomerCommunicationAgent:
        if workflow_type == WorkflowType.REFUND:
            return self.refund
        if workflow_type == WorkflowType.DISPUTE:
            return self.dispute
        if workflow_type == WorkflowType.DATA_OPERATION:
            return self.data_ops
        if workflow_type == WorkflowType.IT_OPERATION:
            return self.it_ops
        return self.comms
