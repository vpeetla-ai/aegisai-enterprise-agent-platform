from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from aegisai.application.orchestration.multi_agent import OrchestrationResult
from aegisai.application.execution.broker import ExecutionReadiness
from aegisai.domain import AgentTrace, AuditEvent, ExecutionResult, GovernanceDecision


SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
  case_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  requester_user_id TEXT NOT NULL,
  workflow_type TEXT NOT NULL,
  status TEXT NOT NULL,
  data_classification TEXT NOT NULL,
  customer_impact INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_traces (
  trace_id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  agent_name TEXT NOT NULL,
  step_name TEXT NOT NULL,
  status TEXT NOT NULL,
  input_ref TEXT NOT NULL,
  output_ref TEXT NOT NULL,
  policy_findings TEXT NOT NULL,
  started_at TEXT NOT NULL,
  completed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS action_proposals (
  proposal_id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  action_type TEXT NOT NULL,
  target_system TEXT NOT NULL,
  amount_usd REAL NOT NULL,
  data_classification TEXT NOT NULL,
  reversible INTEGER NOT NULL,
  customer_impact INTEGER NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS governance_decisions (
  decision_id TEXT PRIMARY KEY,
  proposal_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  decision TEXT NOT NULL,
  risk_score INTEGER NOT NULL,
  risk_level TEXT NOT NULL,
  reason_codes TEXT NOT NULL,
  evaluation_passed INTEGER NOT NULL,
  failed_checks TEXT NOT NULL,
  approval_role TEXT,
  policy_version TEXT NOT NULL,
  decided_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS approval_tasks (
  approval_task_id TEXT PRIMARY KEY,
  proposal_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  assigned_role TEXT NOT NULL,
  status TEXT NOT NULL,
  due_at TEXT NOT NULL,
  escalation_path TEXT NOT NULL,
  decision_reason TEXT,
  decided_by TEXT,
  decided_at TEXT
);

CREATE TABLE IF NOT EXISTS action_executions (
  execution_id TEXT PRIMARY KEY,
  proposal_id TEXT NOT NULL,
  case_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  status TEXT NOT NULL,
  target_system TEXT NOT NULL,
  action_type TEXT NOT NULL,
  connector TEXT NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  external_reference TEXT,
  rollback_reference TEXT,
  message TEXT NOT NULL,
  executed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_events (
  event_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  case_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  subject_id TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  previous_hash TEXT NOT NULL,
  event_hash TEXT NOT NULL,
  occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kill_switch_rules (
  rule_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  scope_type TEXT NOT NULL,
  scope_value TEXT NOT NULL,
  reason TEXT NOT NULL,
  created_by TEXT NOT NULL,
  active INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  deactivated_at TEXT
);
"""


class SQLiteControlPlaneStore:
    """Durable reference store for workflow state and tamper-evident audit events."""

    def persistence_backend(self) -> dict[str, str]:
        return {"mode": "sqlite", "system_of_record": "sqlite"}

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)

    def save_orchestration(self, result: OrchestrationResult) -> None:
        request = result.context.request
        status = self._case_status(result.context.governance_decisions)
        with self.connection:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO cases (
                  case_id, tenant_id, requester_user_id, workflow_type, status,
                  data_classification, customer_impact, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    request.request_id,
                    request.tenant_id,
                    request.user_id,
                    result.workflow_type.value,
                    status,
                    request.data_classification.value,
                    int(request.customer_impact),
                ),
            )
            self._insert_traces(result.context.agent_traces)
            self._insert_proposals(result)
            self._insert_decisions(request.tenant_id, result.context.governance_decisions)
            self._insert_approval_tasks(request.tenant_id, result.context.governance_decisions)
            self.append_audit_event(
                tenant_id=request.tenant_id,
                case_id=request.request_id,
                event_type="case.orchestrated",
                subject_id=request.request_id,
                actor_id="multi_agent_orchestrator",
                payload={
                    "workflow_type": result.workflow_type.value,
                    "agents_run": [agent.value for agent in result.agents_run],
                    "status": status,
                },
            )

    def append_audit_event(
        self,
        tenant_id: str,
        case_id: str,
        event_type: str,
        subject_id: str,
        actor_id: str,
        payload: dict[str, object],
    ) -> AuditEvent:
        previous_hash = self._latest_hash(tenant_id)
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        event_hash = self._hash_event(
            tenant_id=tenant_id,
            case_id=case_id,
            event_type=event_type,
            subject_id=subject_id,
            actor_id=actor_id,
            payload_json=payload_json,
            previous_hash=previous_hash,
        )
        event_id = f"evt-{uuid4()}"
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO audit_events (
                  event_id, tenant_id, case_id, event_type, subject_id, actor_id,
                  payload_json, previous_hash, event_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    tenant_id,
                    case_id,
                    event_type,
                    subject_id,
                    actor_id,
                    payload_json,
                    previous_hash,
                    event_hash,
                ),
            )
        row = self.connection.execute(
            "SELECT * FROM audit_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        return AuditEvent(**dict(row))

    def record_reviewer_action(
        self,
        tenant_id: str,
        case_id: str,
        proposal_id: str,
        reviewer_id: str,
        action: str,
        reason: str,
    ) -> None:
        status_by_action = {
            "approve": "approved",
            "reject": "rejected",
            "request_info": "info_requested",
            "escalate": "escalated",
        }
        if action not in status_by_action:
            raise ValueError(f"unsupported reviewer action: {action}")
        with self.connection:
            self.connection.execute(
                """
                UPDATE approval_tasks
                SET status = ?, decision_reason = ?, decided_by = ?, decided_at = CURRENT_TIMESTAMP
                WHERE proposal_id = ? AND tenant_id = ?
                """,
                (status_by_action[action], reason, reviewer_id, proposal_id, tenant_id),
            )
            self.connection.execute(
                "UPDATE cases SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE case_id = ? AND tenant_id = ?",
                (status_by_action[action], case_id, tenant_id),
            )
        self.append_audit_event(
            tenant_id=tenant_id,
            case_id=case_id,
            event_type=f"reviewer.{action}",
            subject_id=proposal_id,
            actor_id=reviewer_id,
            payload={"reason": reason, "status": status_by_action[action]},
        )

    def approval_role_for_proposal(self, tenant_id: str, proposal_id: str) -> str | None:
        row = self.connection.execute(
            """
            SELECT approval_role
            FROM governance_decisions
            WHERE tenant_id = ? AND proposal_id = ?
            """,
            (tenant_id, proposal_id),
        ).fetchone()
        if row is None:
            return None
        return str(row["approval_role"]) if row["approval_role"] else None

    def get_execution_readiness(self, tenant_id: str, proposal_id: str) -> ExecutionReadiness | None:
        row = self.connection.execute(
            """
            SELECT
              proposal.action_type,
              proposal.target_system,
              proposal.amount_usd,
              proposal.reversible,
              decision.decision,
              approval.status AS approval_status
            FROM action_proposals proposal
            LEFT JOIN governance_decisions decision
              ON decision.proposal_id = proposal.proposal_id
              AND decision.tenant_id = proposal.tenant_id
            LEFT JOIN approval_tasks approval
              ON approval.proposal_id = proposal.proposal_id
              AND approval.tenant_id = proposal.tenant_id
            WHERE proposal.tenant_id = ? AND proposal.proposal_id = ?
            """,
            (tenant_id, proposal_id),
        ).fetchone()
        if row is None:
            return None
        return ExecutionReadiness(
            action_type=str(row["action_type"]),
            target_system=str(row["target_system"]),
            amount_usd=float(row["amount_usd"]),
            reversible=bool(row["reversible"]),
            decision=str(row["decision"]),
            approval_status=str(row["approval_status"]) if row["approval_status"] is not None else None,
        )

    def record_execution_result(self, result: ExecutionResult, actor_id: str) -> None:
        with self.connection:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO action_executions (
                  execution_id, proposal_id, case_id, tenant_id, status, target_system,
                  action_type, connector, idempotency_key, external_reference,
                  rollback_reference, message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.execution_id,
                    result.proposal_id,
                    result.case_id,
                    result.tenant_id,
                    result.status.value,
                    result.target_system,
                    result.action_type,
                    result.connector,
                    result.idempotency_key,
                    result.external_reference,
                    result.rollback_reference,
                    result.message,
                ),
            )
            if result.status.value == "executed":
                self.connection.execute(
                    """
                    UPDATE cases
                    SET status = 'executed', updated_at = CURRENT_TIMESTAMP
                    WHERE tenant_id = ? AND case_id = ?
                    """,
                    (result.tenant_id, result.case_id),
                )
        self.append_audit_event(
            tenant_id=result.tenant_id,
            case_id=result.case_id,
            event_type=f"execution.{result.status.value}",
            subject_id=result.proposal_id,
            actor_id=actor_id,
            payload={
                "execution_id": result.execution_id,
                "target_system": result.target_system,
                "action_type": result.action_type,
                "connector": result.connector,
                "external_reference": result.external_reference,
                "rollback_reference": result.rollback_reference,
                "message": result.message,
            },
        )

    def case_audit_snapshot(self, tenant_id: str, case_id: str) -> dict[str, object]:
        case = self._one(
            "SELECT * FROM cases WHERE tenant_id = ? AND case_id = ?",
            (tenant_id, case_id),
        )
        return {
            "case": case,
            "agent_traces": self._many(
                "SELECT * FROM agent_traces WHERE tenant_id = ? AND case_id = ? ORDER BY rowid",
                (tenant_id, case_id),
            ),
            "action_proposals": self._many(
                "SELECT * FROM action_proposals WHERE tenant_id = ? AND case_id = ? ORDER BY rowid",
                (tenant_id, case_id),
            ),
            "governance_decisions": self._many(
                """
                SELECT decision.*
                FROM governance_decisions decision
                JOIN action_proposals proposal
                  ON proposal.proposal_id = decision.proposal_id
                 AND proposal.tenant_id = decision.tenant_id
                WHERE proposal.tenant_id = ? AND proposal.case_id = ?
                ORDER BY decision.rowid
                """,
                (tenant_id, case_id),
            ),
            "approval_tasks": self._many(
                """
                SELECT approval.*
                FROM approval_tasks approval
                JOIN action_proposals proposal
                  ON proposal.proposal_id = approval.proposal_id
                 AND proposal.tenant_id = approval.tenant_id
                WHERE proposal.tenant_id = ? AND proposal.case_id = ?
                ORDER BY approval.rowid
                """,
                (tenant_id, case_id),
            ),
            "action_executions": self._many(
                "SELECT * FROM action_executions WHERE tenant_id = ? AND case_id = ? ORDER BY rowid",
                (tenant_id, case_id),
            ),
            "audit_events": self._many(
                "SELECT * FROM audit_events WHERE tenant_id = ? AND case_id = ? ORDER BY rowid",
                (tenant_id, case_id),
            ),
            "audit_chain_valid": self.verify_audit_chain(tenant_id),
        }

    def verify_audit_chain(self, tenant_id: str) -> bool:
        rows = self.connection.execute(
            "SELECT * FROM audit_events WHERE tenant_id = ? ORDER BY rowid",
            (tenant_id,),
        ).fetchall()
        previous_hash = "GENESIS"
        for row in rows:
            expected = self._hash_event(
                tenant_id=row["tenant_id"],
                case_id=row["case_id"],
                event_type=row["event_type"],
                subject_id=row["subject_id"],
                actor_id=row["actor_id"],
                payload_json=row["payload_json"],
                previous_hash=previous_hash,
            )
            if row["previous_hash"] != previous_hash or row["event_hash"] != expected:
                return False
            previous_hash = row["event_hash"]
        return True

    def count(self, table: str) -> int:
        allowed = {
            "cases",
            "agent_traces",
            "action_proposals",
            "governance_decisions",
            "approval_tasks",
            "action_executions",
            "audit_events",
            "kill_switch_rules",
        }
        if table not in allowed:
            raise ValueError(f"unsupported table: {table}")
        row = self.connection.execute(f"SELECT COUNT(*) AS total FROM {table}").fetchone()
        return int(row["total"])

    def count_approval_tasks(
        self, tenant_id: str | None = None, *, status: str | None = "pending"
    ) -> int:
        clauses: list[str] = []
        params: list[object] = []
        if tenant_id:
            clauses.append("tenant_id = ?")
            params.append(tenant_id)
        if status:
            clauses.append("status = ?")
            params.append(status)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        row = self.connection.execute(
            f"SELECT COUNT(*) AS total FROM approval_tasks {where}",
            tuple(params),
        ).fetchone()
        return int(row["total"]) if row else 0

    def list_approval_tasks(
        self, tenant_id: str, *, status: str | None = "pending"
    ) -> list[dict[str, object]]:
        clauses = ["t.tenant_id = ?"]
        params: list[object] = [tenant_id]
        if status:
            clauses.append("t.status = ?")
            params.append(status)
        where = " AND ".join(clauses)
        rows = self.connection.execute(
            f"""
            SELECT
              t.approval_task_id, t.proposal_id, t.tenant_id, t.assigned_role, t.status,
              t.due_at, t.escalation_path, t.decision_reason, t.decided_by, t.decided_at,
              p.case_id, p.agent_id, p.action_type, p.target_system, p.amount_usd,
              d.decision AS governance_decision, d.risk_score, d.risk_level, d.reason_codes
            FROM approval_tasks t
            LEFT JOIN action_proposals p ON p.proposal_id = t.proposal_id
            LEFT JOIN governance_decisions d ON d.proposal_id = t.proposal_id
            WHERE {where}
            ORDER BY t.due_at ASC
            """,
            tuple(params),
        ).fetchall()
        result: list[dict[str, object]] = []
        for row in rows:
            item = dict(row)
            if isinstance(item.get("reason_codes"), str):
                try:
                    item["reason_codes"] = json.loads(item["reason_codes"])
                except json.JSONDecodeError:
                    item["reason_codes"] = []
            result.append(item)
        return result

    def persist_gateway_hitl(
        self,
        *,
        tenant_id: str,
        case_id: str,
        proposal_id: str,
        agent_id: str,
        action_type: str,
        target_system: str,
        tool_name: str,
        workflow_type: str = "gateway_hitl",
        approval_role: str = "workflow_owner",
        business_explanation: str = "",
        amount_usd: float = 0.0,
    ) -> dict[str, object]:
        from aegisai.product.hitl_queue import due_at_iso

        due_at = due_at_iso()
        with self.connection:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO cases (
                  case_id, tenant_id, requester_user_id, workflow_type, status,
                  data_classification, customer_impact, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    case_id,
                    tenant_id,
                    agent_id,
                    workflow_type,
                    "pending_approval",
                    "internal",
                    0,
                ),
            )
            self.connection.execute(
                """
                INSERT OR REPLACE INTO action_proposals (
                  proposal_id, case_id, tenant_id, agent_id, action_type, target_system,
                  amount_usd, data_classification, reversible, customer_impact, idempotency_key
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proposal_id,
                    case_id,
                    tenant_id,
                    agent_id,
                    action_type,
                    target_system,
                    amount_usd,
                    "internal",
                    1,
                    0,
                    f"idem-{proposal_id}",
                ),
            )
            self.connection.execute(
                """
                INSERT OR REPLACE INTO governance_decisions (
                  decision_id, proposal_id, tenant_id, decision, risk_score, risk_level,
                  reason_codes, evaluation_passed, failed_checks, approval_role, policy_version
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"decision:{proposal_id}",
                    proposal_id,
                    tenant_id,
                    "approval_required",
                    70,
                    "high",
                    json.dumps(["gateway_hitl", tool_name]),
                    1,
                    json.dumps([]),
                    approval_role,
                    "gateway-v1",
                ),
            )
            self.connection.execute(
                """
                INSERT OR REPLACE INTO approval_tasks (
                  approval_task_id, proposal_id, tenant_id, assigned_role, status, due_at, escalation_path
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"approval:{proposal_id}",
                    proposal_id,
                    tenant_id,
                    approval_role,
                    "pending",
                    due_at,
                    "workflow_owner>senior_domain_approver>compliance",
                ),
            )
        self.append_audit_event(
            tenant_id=tenant_id,
            case_id=case_id,
            event_type="hitl.task_created",
            subject_id=proposal_id,
            actor_id=agent_id,
            payload={
                "tool_name": tool_name,
                "action_type": action_type,
                "target_system": target_system,
                "explanation": business_explanation,
            },
        )
        return {
            "case_id": case_id,
            "proposal_id": proposal_id,
            "approval_task_id": f"approval:{proposal_id}",
            "status": "pending",
            "tool_name": tool_name,
        }

    def list_kill_switch_rules(self) -> list[dict[str, object]]:
        rows = self.connection.execute(
            "SELECT * FROM kill_switch_rules ORDER BY created_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]

    def upsert_kill_switch_rule(self, rule: dict[str, object]) -> None:
        with self.connection:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO kill_switch_rules (
                  rule_id, tenant_id, scope_type, scope_value, reason, created_by,
                  active, created_at, deactivated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rule["rule_id"],
                    rule.get("tenant_id", "bank-demo"),
                    rule["scope_type"],
                    rule["scope_value"],
                    rule["reason"],
                    rule["created_by"],
                    int(bool(rule["active"])),
                    rule["created_at"],
                    rule.get("deactivated_at"),
                ),
            )

    def deactivate_kill_switch_rule(self, rule_id: str) -> dict[str, object] | None:
        row = self.connection.execute(
            "SELECT * FROM kill_switch_rules WHERE rule_id = ?",
            (rule_id,),
        ).fetchone()
        if row is None:
            return None
        from datetime import UTC, datetime

        deactivated_at = datetime.now(UTC).isoformat()
        with self.connection:
            self.connection.execute(
                """
                UPDATE kill_switch_rules
                SET active = 0, deactivated_at = ?
                WHERE rule_id = ?
                """,
                (deactivated_at, rule_id),
            )
        updated = dict(row)
        updated["active"] = 0
        updated["deactivated_at"] = deactivated_at
        return updated

    def list_recent_audit_events(self, tenant_id: str, *, limit: int = 20) -> list[dict[str, object]]:
        return self._many(
            """
            SELECT event_id, tenant_id, case_id, event_type, subject_id, actor_id,
                   payload_json, occurred_at AS created_at
            FROM audit_events
            WHERE tenant_id = ?
            ORDER BY rowid DESC
            LIMIT ?
            """,
            (tenant_id, limit),
        )

    def list_undoable_executions(self, tenant_id: str) -> list[dict[str, object]]:
        return self._many(
            """
            SELECT *
            FROM action_executions
            WHERE tenant_id = ?
              AND status = 'executed'
              AND rollback_reference IS NOT NULL
            ORDER BY rowid DESC
            """,
            (tenant_id,),
        )

    def get_execution_by_id(self, execution_id: str) -> dict[str, object] | None:
        return self._one(
            "SELECT * FROM action_executions WHERE execution_id = ?",
            (execution_id,),
        )

    def mark_execution_rolled_back(self, execution_id: str, rollback_id: str) -> None:
        with self.connection:
            self.connection.execute(
                """
                UPDATE action_executions
                SET status = 'rolled_back',
                    message = COALESCE(message, '') || ' [rolled_back:' || ? || ']'
                WHERE execution_id = ?
                """,
                (rollback_id, execution_id),
            )

    def count_audit_events(
        self,
        tenant_id: str,
        *,
        event_type: str | None = None,
        event_type_prefix: str | None = None,
    ) -> int:
        query = "SELECT COUNT(*) AS total FROM audit_events WHERE tenant_id = ?"
        params: list[object] = [tenant_id]
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        elif event_type_prefix:
            query += " AND event_type LIKE ?"
            params.append(f"{event_type_prefix}%")
        row = self.connection.execute(query, tuple(params)).fetchone()
        return int(row["total"])

    def _one(self, query: str, params: tuple[object, ...]) -> dict[str, object] | None:
        row = self.connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def _many(self, query: str, params: tuple[object, ...]) -> list[dict[str, object]]:
        return [dict(row) for row in self.connection.execute(query, params).fetchall()]

    def _insert_traces(self, traces: Iterable[AgentTrace]) -> None:
        self.connection.executemany(
            """
            INSERT OR REPLACE INTO agent_traces (
              trace_id, case_id, tenant_id, agent_name, step_name, status,
              input_ref, output_ref, policy_findings, started_at, completed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    trace.trace_id,
                    trace.case_id,
                    trace.tenant_id,
                    trace.agent_name,
                    trace.step_name,
                    trace.status,
                    trace.input_ref,
                    trace.output_ref,
                    json.dumps(trace.policy_findings),
                    trace.started_at,
                    trace.completed_at,
                )
                for trace in traces
            ],
        )

    def _insert_proposals(self, result: OrchestrationResult) -> None:
        self.connection.executemany(
            """
            INSERT OR REPLACE INTO action_proposals (
              proposal_id, case_id, tenant_id, agent_id, action_type, target_system,
              amount_usd, data_classification, reversible, customer_impact, idempotency_key
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    proposal.proposal_id,
                    result.request_id,
                    proposal.tenant_id,
                    proposal.agent_id,
                    proposal.action_type,
                    proposal.target_system,
                    proposal.amount_usd,
                    proposal.data_classification.value,
                    int(proposal.reversible),
                    int(proposal.customer_impact),
                    f"{proposal.tenant_id}:{proposal.proposal_id}:{proposal.action_type}",
                )
                for proposal in result.context.proposed_actions
            ],
        )

    def _insert_decisions(
        self,
        tenant_id: str,
        decisions: Iterable[GovernanceDecision],
    ) -> None:
        self.connection.executemany(
            """
            INSERT OR REPLACE INTO governance_decisions (
              decision_id, proposal_id, tenant_id, decision, risk_score, risk_level,
              reason_codes, evaluation_passed, failed_checks, approval_role, policy_version
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    f"decision:{decision.proposal_id}",
                    decision.proposal_id,
                    tenant_id,
                    decision.decision.value,
                    decision.risk.score,
                    decision.risk.level.value,
                    json.dumps(decision.risk.reason_codes),
                    int(decision.evaluation.passed),
                    json.dumps(decision.evaluation.failed_checks),
                    decision.approval_role,
                    decision.policy_version,
                )
                for decision in decisions
            ],
        )

    def _insert_approval_tasks(
        self,
        tenant_id: str,
        decisions: Iterable[GovernanceDecision],
    ) -> None:
        rows = []
        for decision in decisions:
            if decision.approval_role:
                rows.append(
                    (
                        f"approval:{decision.proposal_id}",
                        decision.proposal_id,
                        tenant_id,
                        decision.approval_role,
                        "pending",
                        "2026-05-24T18:00:00Z",
                        "workflow_owner>senior_domain_approver>compliance",
                    )
                )
        self.connection.executemany(
            """
            INSERT OR REPLACE INTO approval_tasks (
              approval_task_id, proposal_id, tenant_id, assigned_role, status, due_at, escalation_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

    def _latest_hash(self, tenant_id: str) -> str:
        row = self.connection.execute(
            """
            SELECT event_hash FROM audit_events
            WHERE tenant_id = ?
            ORDER BY rowid DESC
            LIMIT 1
            """,
            (tenant_id,),
        ).fetchone()
        return str(row["event_hash"]) if row else "GENESIS"

    @staticmethod
    def _hash_event(
        tenant_id: str,
        case_id: str,
        event_type: str,
        subject_id: str,
        actor_id: str,
        payload_json: str,
        previous_hash: str,
    ) -> str:
        material = "|".join(
            [tenant_id, case_id, event_type, subject_id, actor_id, payload_json, previous_hash]
        )
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    @staticmethod
    def _case_status(decisions: list[GovernanceDecision]) -> str:
        if not decisions:
            return "no_action"
        return decisions[0].decision.value
