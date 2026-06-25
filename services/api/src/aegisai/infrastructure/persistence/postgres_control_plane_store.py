from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator
from uuid import uuid4

from aegisai.application.execution.broker import ExecutionReadiness
from aegisai.application.orchestration.multi_agent import OrchestrationResult
from aegisai.domain import AgentTrace, AuditEvent, ExecutionResult, GovernanceDecision


class PostgresControlPlaneStore:
    """Production control-plane persistence — all reads and writes go to Postgres only."""

    def __init__(self, database_url: str) -> None:
        import psycopg

        self.database_url = database_url
        self._psycopg = psycopg
        self._ensure_schema()
        self._seed_tenant()

    def persistence_backend(self) -> dict[str, str]:
        return {"mode": "postgres", "system_of_record": "postgresql"}

    @contextmanager
    def _connection(self) -> Iterator[object]:
        with self._psycopg.connect(self.database_url) as connection:
            yield connection

    def _ensure_schema(self) -> None:
        migration = (
            Path(__file__).resolve().parents[6]
            / "platform"
            / "database"
            / "postgres-migration.sql"
        )
        sql = migration.read_text(encoding="utf-8")
        with self._connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
            connection.commit()

    def _seed_tenant(self) -> None:
        with self._connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO cases (
                      case_id, tenant_id, requester_user_id, workflow_type, status,
                      data_classification, customer_impact
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (case_id) DO NOTHING
                    """,
                    (
                        "seed-case",
                        "bank-demo",
                        "seed-user",
                        "seed",
                        "seed",
                        "internal",
                        False,
                    ),
                )
            connection.commit()

    def save_orchestration(self, result: OrchestrationResult) -> None:
        request = result.context.request
        status = self._case_status(result.context.governance_decisions)
        with self._connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO cases (
                      case_id, tenant_id, requester_user_id, workflow_type, status,
                      data_classification, customer_impact, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (case_id) DO UPDATE SET
                      status = EXCLUDED.status,
                      updated_at = NOW()
                    """,
                    (
                        request.request_id,
                        request.tenant_id,
                        request.user_id,
                        result.workflow_type.value,
                        status,
                        request.data_classification.value,
                        request.customer_impact,
                    ),
                )
            connection.commit()
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
        with self._connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO audit_events (
                      event_id, tenant_id, case_id, event_type, subject_id, actor_id,
                      payload_json, previous_hash, event_hash
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            connection.commit()
        row = self._one(
            "SELECT * FROM audit_events WHERE event_id = %s",
            (event_id,),
        )
        assert row is not None
        return AuditEvent(
            event_id=str(row["event_id"]),
            tenant_id=str(row["tenant_id"]),
            case_id=str(row["case_id"]),
            event_type=str(row["event_type"]),
            subject_id=str(row["subject_id"]),
            actor_id=str(row["actor_id"]),
            payload_json=str(row["payload_json"]),
            previous_hash=str(row["previous_hash"]),
            event_hash=str(row["event_hash"]),
            occurred_at=str(row["occurred_at"]),
        )

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
        with self._connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE approval_tasks
                    SET status = %s, decision_reason = %s, decided_by = %s, decided_at = NOW()::text
                    WHERE proposal_id = %s AND tenant_id = %s
                    """,
                    (status_by_action[action], reason, reviewer_id, proposal_id, tenant_id),
                )
                cursor.execute(
                    """
                    UPDATE cases SET status = %s, updated_at = NOW()
                    WHERE case_id = %s AND tenant_id = %s
                    """,
                    (status_by_action[action], case_id, tenant_id),
                )
            connection.commit()
        self.append_audit_event(
            tenant_id=tenant_id,
            case_id=case_id,
            event_type=f"reviewer.{action}",
            subject_id=proposal_id,
            actor_id=reviewer_id,
            payload={"reason": reason, "status": status_by_action[action]},
        )

    def approval_role_for_proposal(self, tenant_id: str, proposal_id: str) -> str | None:
        row = self._one(
            """
            SELECT approval_role FROM governance_decisions
            WHERE tenant_id = %s AND proposal_id = %s
            """,
            (tenant_id, proposal_id),
        )
        if row is None:
            return None
        return str(row["approval_role"]) if row["approval_role"] else None

    def get_execution_readiness(self, tenant_id: str, proposal_id: str) -> ExecutionReadiness | None:
        row = self._one(
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
            WHERE proposal.tenant_id = %s AND proposal.proposal_id = %s
            """,
            (tenant_id, proposal_id),
        )
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
        with self._connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO action_executions (
                      execution_id, proposal_id, case_id, tenant_id, status, target_system,
                      action_type, connector, idempotency_key, external_reference,
                      rollback_reference, message
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (execution_id) DO UPDATE SET
                      status = EXCLUDED.status,
                      external_reference = EXCLUDED.external_reference,
                      message = EXCLUDED.message
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
                    cursor.execute(
                        """
                        UPDATE cases SET status = 'executed', updated_at = NOW()
                        WHERE tenant_id = %s AND case_id = %s
                        """,
                        (result.tenant_id, result.case_id),
                    )
            connection.commit()
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
        return {
            "case": self._one(
                "SELECT * FROM cases WHERE tenant_id = %s AND case_id = %s",
                (tenant_id, case_id),
            ),
            "agent_traces": self._many(
                """
                SELECT * FROM agent_traces
                WHERE tenant_id = %s AND case_id = %s
                ORDER BY started_at
                """,
                (tenant_id, case_id),
            ),
            "action_proposals": self._many(
                """
                SELECT * FROM action_proposals
                WHERE tenant_id = %s AND case_id = %s
                ORDER BY created_at
                """,
                (tenant_id, case_id),
            ),
            "governance_decisions": self._many(
                """
                SELECT decision.*
                FROM governance_decisions decision
                JOIN action_proposals proposal
                  ON proposal.proposal_id = decision.proposal_id
                 AND proposal.tenant_id = decision.tenant_id
                WHERE proposal.tenant_id = %s AND proposal.case_id = %s
                ORDER BY decision.decided_at
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
                WHERE proposal.tenant_id = %s AND proposal.case_id = %s
                ORDER BY approval.due_at
                """,
                (tenant_id, case_id),
            ),
            "action_executions": self._many(
                """
                SELECT * FROM action_executions
                WHERE tenant_id = %s AND case_id = %s
                ORDER BY executed_at
                """,
                (tenant_id, case_id),
            ),
            "audit_events": self._many(
                """
                SELECT * FROM audit_events
                WHERE tenant_id = %s AND case_id = %s
                ORDER BY occurred_at
                """,
                (tenant_id, case_id),
            ),
            "audit_chain_valid": self.verify_audit_chain(tenant_id),
        }

    def verify_audit_chain(self, tenant_id: str) -> bool:
        rows = self._many(
            "SELECT * FROM audit_events WHERE tenant_id = %s ORDER BY occurred_at ASC",
            (tenant_id,),
        )
        previous_hash = "GENESIS"
        for row in rows:
            expected = self._hash_event(
                tenant_id=str(row["tenant_id"]),
                case_id=str(row["case_id"]),
                event_type=str(row["event_type"]),
                subject_id=str(row["subject_id"]),
                actor_id=str(row["actor_id"]),
                payload_json=str(row["payload_json"]),
                previous_hash=previous_hash,
            )
            if row["previous_hash"] != previous_hash or row["event_hash"] != expected:
                return False
            previous_hash = str(row["event_hash"])
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
        }
        if table not in allowed:
            raise ValueError(f"unsupported table: {table}")
        row = self._one(f"SELECT COUNT(*) AS total FROM {table}", ())
        return int(row["total"]) if row else 0

    def list_recent_audit_events(self, tenant_id: str, *, limit: int = 20) -> list[dict[str, object]]:
        return self._many(
            """
            SELECT event_id, tenant_id, case_id, event_type, subject_id, actor_id,
                   payload_json, occurred_at AS created_at
            FROM audit_events
            WHERE tenant_id = %s
            ORDER BY occurred_at DESC
            LIMIT %s
            """,
            (tenant_id, limit),
        )

    def list_undoable_executions(self, tenant_id: str) -> list[dict[str, object]]:
        return self._many(
            """
            SELECT *
            FROM action_executions
            WHERE tenant_id = %s
              AND status = 'executed'
              AND rollback_reference IS NOT NULL
            ORDER BY execution_id DESC
            """,
            (tenant_id,),
        )

    def get_execution_by_id(self, execution_id: str) -> dict[str, object] | None:
        return self._one(
            "SELECT * FROM action_executions WHERE execution_id = %s",
            (execution_id,),
        )

    def mark_execution_rolled_back(self, execution_id: str, rollback_id: str) -> None:
        with self._connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE action_executions
                    SET status = 'rolled_back',
                        message = COALESCE(message, '') || ' [rolled_back:' || %s || ']'
                    WHERE execution_id = %s
                    """,
                    (rollback_id, execution_id),
                )
            connection.commit()

    def count_audit_events(
        self,
        tenant_id: str,
        *,
        event_type: str | None = None,
        event_type_prefix: str | None = None,
    ) -> int:
        query = "SELECT COUNT(*) AS total FROM audit_events WHERE tenant_id = %s"
        params: list[object] = [tenant_id]
        if event_type:
            query += " AND event_type = %s"
            params.append(event_type)
        elif event_type_prefix:
            query += " AND event_type LIKE %s"
            params.append(f"{event_type_prefix}%")
        row = self._one(query, tuple(params))
        return int(row["total"]) if row else 0

    def _one(self, query: str, params: tuple[object, ...]) -> dict[str, object] | None:
        with self._connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                row = cursor.fetchone()
                if row is None:
                    return None
                columns = [desc.name for desc in cursor.description]
                return dict(zip(columns, row))

    def _many(self, query: str, params: tuple[object, ...]) -> list[dict[str, object]]:
        with self._connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                columns = [desc.name for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def _insert_traces(self, traces: Iterable[AgentTrace]) -> None:
        rows = [
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
        ]
        if not rows:
            return
        with self._connection() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO agent_traces (
                      trace_id, case_id, tenant_id, agent_name, step_name, status,
                      input_ref, output_ref, policy_findings, started_at, completed_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (trace_id) DO UPDATE SET status = EXCLUDED.status
                    """,
                    rows,
                )
            connection.commit()

    def _insert_proposals(self, result: OrchestrationResult) -> None:
        rows = [
            (
                proposal.proposal_id,
                result.request_id,
                proposal.tenant_id,
                proposal.agent_id,
                proposal.action_type,
                proposal.target_system,
                proposal.amount_usd,
                proposal.data_classification.value,
                proposal.reversible,
                proposal.customer_impact,
                f"{proposal.tenant_id}:{proposal.proposal_id}:{proposal.action_type}",
            )
            for proposal in result.context.proposed_actions
        ]
        if not rows:
            return
        with self._connection() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO action_proposals (
                      proposal_id, case_id, tenant_id, agent_id, action_type, target_system,
                      amount_usd, data_classification, reversible, customer_impact, idempotency_key
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (proposal_id) DO UPDATE SET amount_usd = EXCLUDED.amount_usd
                    """,
                    rows,
                )
            connection.commit()

    def _insert_decisions(
        self,
        tenant_id: str,
        decisions: Iterable[GovernanceDecision],
    ) -> None:
        rows = [
            (
                f"decision:{decision.proposal_id}",
                decision.proposal_id,
                tenant_id,
                decision.decision.value,
                decision.risk.score,
                decision.risk.level.value,
                json.dumps(decision.risk.reason_codes),
                decision.evaluation.passed,
                json.dumps(decision.evaluation.failed_checks),
                decision.approval_role,
                decision.policy_version,
            )
            for decision in decisions
        ]
        if not rows:
            return
        with self._connection() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO governance_decisions (
                      decision_id, proposal_id, tenant_id, decision, risk_score, risk_level,
                      reason_codes, evaluation_passed, failed_checks, approval_role, policy_version
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (decision_id) DO UPDATE SET decision = EXCLUDED.decision
                    """,
                    rows,
                )
            connection.commit()

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
        if not rows:
            return
        with self._connection() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO approval_tasks (
                      approval_task_id, proposal_id, tenant_id, assigned_role, status, due_at, escalation_path
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (approval_task_id) DO UPDATE SET status = EXCLUDED.status
                    """,
                    rows,
                )
            connection.commit()

    def _latest_hash(self, tenant_id: str) -> str:
        row = self._one(
            """
            SELECT event_hash FROM audit_events
            WHERE tenant_id = %s
            ORDER BY occurred_at DESC
            LIMIT 1
            """,
            (tenant_id,),
        )
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
