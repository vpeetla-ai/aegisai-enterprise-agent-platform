"""Agent registry persistence backends."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Protocol

from aegisai.infrastructure.persistence.agent_registry_seeds import seed_agents
from aegisai.domain.models import RegisteredAgent


class AgentRegistryStore(Protocol):
    def list_agents(self) -> tuple[RegisteredAgent, ...]: ...

    def get_agent(self, agent_id: str) -> RegisteredAgent | None: ...

    def upsert_agent(self, agent: RegisteredAgent, *, tenant_id: str = "bank-demo") -> RegisteredAgent: ...

    def update_status(self, agent_id: str, status: str) -> RegisteredAgent | None: ...

    def update_cost(self, agent_id: str, monthly_cost_usd: float) -> RegisteredAgent | None: ...

    def count(self) -> int: ...


class InMemoryAgentRegistryStore:
    def __init__(self) -> None:
        self._agents: dict[str, RegisteredAgent] = {
            agent.agent_id: agent for agent in seed_agents()
        }

    def list_agents(self) -> tuple[RegisteredAgent, ...]:
        return tuple(self._agents.values())

    def get_agent(self, agent_id: str) -> RegisteredAgent | None:
        return self._agents.get(agent_id)

    def upsert_agent(self, agent: RegisteredAgent, *, tenant_id: str = "bank-demo") -> RegisteredAgent:
        _ = tenant_id
        self._agents[agent.agent_id] = agent
        return agent

    def update_status(self, agent_id: str, status: str) -> RegisteredAgent | None:
        agent = self._agents.get(agent_id)
        if agent is None:
            return None
        updated = RegisteredAgent(
            agent_id=agent.agent_id,
            name=agent.name,
            owner=agent.owner,
            business_domain=agent.business_domain,
            risk_tier=agent.risk_tier,
            autonomy_level=agent.autonomy_level,
            status=status,
            model_provider=agent.model_provider,
            allowed_tools=agent.allowed_tools,
            data_classes=agent.data_classes,
            last_run_at=agent.last_run_at,
            monthly_cost_usd=agent.monthly_cost_usd,
            open_incidents=agent.open_incidents,
            value_metric=agent.value_metric,
            budget_usd=agent.budget_usd,
        )
        self._agents[agent_id] = updated
        return updated

    def update_cost(self, agent_id: str, monthly_cost_usd: float) -> RegisteredAgent | None:
        agent = self._agents.get(agent_id)
        if agent is None:
            return None
        updated = RegisteredAgent(
            agent_id=agent.agent_id,
            name=agent.name,
            owner=agent.owner,
            business_domain=agent.business_domain,
            risk_tier=agent.risk_tier,
            autonomy_level=agent.autonomy_level,
            status=agent.status,
            model_provider=agent.model_provider,
            allowed_tools=agent.allowed_tools,
            data_classes=agent.data_classes,
            last_run_at=agent.last_run_at,
            monthly_cost_usd=monthly_cost_usd,
            open_incidents=agent.open_incidents,
            value_metric=agent.value_metric,
            budget_usd=agent.budget_usd,
        )
        self._agents[agent_id] = updated
        return updated

    def count(self) -> int:
        return len(self._agents)


class PostgresAgentRegistryStore:
    """Postgres-backed agent registry — system of record in production."""

    def __init__(self, database_url: str) -> None:
        import psycopg

        self.database_url = database_url
        self._psycopg = psycopg
        self._ensure_schema()
        self._seed_if_empty()

    def _migration_sql_path(self) -> Path:
        override = os.getenv("AEGISAI_POSTGRES_MIGRATION_PATH", "").strip()
        if override:
            return Path(override)
        docker_path = Path("/app/migrations/postgres-migration.sql")
        if docker_path.is_file():
            return docker_path
        file_path = Path(__file__).resolve()
        for ancestor in file_path.parents:
            candidate = ancestor / "platform" / "database" / "postgres-migration.sql"
            if candidate.is_file():
                return candidate
        raise FileNotFoundError("postgres-migration.sql not found")

    def _ensure_schema(self) -> None:
        sql = self._migration_sql_path().read_text(encoding="utf-8")
        with self._psycopg.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
            connection.commit()

    def _seed_if_empty(self) -> None:
        if self.count() > 0:
            return
        for agent in seed_agents():
            self.upsert_agent(agent)

    @staticmethod
    def _row_to_agent(row: tuple) -> RegisteredAgent:
        (
            agent_id,
            _tenant_id,
            name,
            owner,
            business_domain,
            risk_tier,
            autonomy_level,
            status,
            model_provider,
            allowed_tools,
            data_classes,
            last_run_at,
            monthly_cost_usd,
            open_incidents,
            value_metric,
            budget_usd,
        ) = row
        return RegisteredAgent(
            agent_id=agent_id,
            name=name,
            owner=owner,
            business_domain=business_domain,
            risk_tier=risk_tier,
            autonomy_level=int(autonomy_level),
            status=status,
            model_provider=model_provider,
            allowed_tools=tuple(json.loads(allowed_tools)),
            data_classes=tuple(json.loads(data_classes)),
            last_run_at=last_run_at,
            monthly_cost_usd=float(monthly_cost_usd),
            open_incidents=int(open_incidents),
            value_metric=value_metric,
            budget_usd=float(budget_usd) if budget_usd is not None else None,
        )

    def list_agents(self) -> tuple[RegisteredAgent, ...]:
        with self._psycopg.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT agent_id, tenant_id, name, owner, business_domain, risk_tier,
                           autonomy_level, status, model_provider, allowed_tools, data_classes,
                           last_run_at, monthly_cost_usd, open_incidents, value_metric, budget_usd
                    FROM agent_registry
                    ORDER BY agent_id
                    """
                )
                rows = cursor.fetchall()
        return tuple(self._row_to_agent(row) for row in rows)

    def get_agent(self, agent_id: str) -> RegisteredAgent | None:
        with self._psycopg.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT agent_id, tenant_id, name, owner, business_domain, risk_tier,
                           autonomy_level, status, model_provider, allowed_tools, data_classes,
                           last_run_at, monthly_cost_usd, open_incidents, value_metric, budget_usd
                    FROM agent_registry WHERE agent_id = %s
                    """,
                    (agent_id,),
                )
                row = cursor.fetchone()
        return self._row_to_agent(row) if row else None

    def upsert_agent(self, agent: RegisteredAgent, *, tenant_id: str = "bank-demo") -> RegisteredAgent:
        with self._psycopg.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO agent_registry (
                      agent_id, tenant_id, name, owner, business_domain, risk_tier,
                      autonomy_level, status, model_provider, allowed_tools, data_classes,
                      last_run_at, monthly_cost_usd, open_incidents, value_metric, budget_usd, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (agent_id) DO UPDATE SET
                      tenant_id = EXCLUDED.tenant_id,
                      name = EXCLUDED.name,
                      owner = EXCLUDED.owner,
                      business_domain = EXCLUDED.business_domain,
                      risk_tier = EXCLUDED.risk_tier,
                      autonomy_level = EXCLUDED.autonomy_level,
                      status = EXCLUDED.status,
                      model_provider = EXCLUDED.model_provider,
                      allowed_tools = EXCLUDED.allowed_tools,
                      data_classes = EXCLUDED.data_classes,
                      last_run_at = EXCLUDED.last_run_at,
                      monthly_cost_usd = EXCLUDED.monthly_cost_usd,
                      open_incidents = EXCLUDED.open_incidents,
                      value_metric = EXCLUDED.value_metric,
                      budget_usd = EXCLUDED.budget_usd,
                      updated_at = NOW()
                    """,
                    (
                        agent.agent_id,
                        tenant_id,
                        agent.name,
                        agent.owner,
                        agent.business_domain,
                        agent.risk_tier,
                        agent.autonomy_level,
                        agent.status,
                        agent.model_provider,
                        json.dumps(list(agent.allowed_tools)),
                        json.dumps(list(agent.data_classes)),
                        agent.last_run_at,
                        agent.monthly_cost_usd,
                        agent.open_incidents,
                        agent.value_metric,
                        agent.budget_usd,
                    ),
                )
            connection.commit()
        return agent

    def update_status(self, agent_id: str, status: str) -> RegisteredAgent | None:
        agent = self.get_agent(agent_id)
        if agent is None:
            return None
        updated = RegisteredAgent(
            agent_id=agent.agent_id,
            name=agent.name,
            owner=agent.owner,
            business_domain=agent.business_domain,
            risk_tier=agent.risk_tier,
            autonomy_level=agent.autonomy_level,
            status=status,
            model_provider=agent.model_provider,
            allowed_tools=agent.allowed_tools,
            data_classes=agent.data_classes,
            last_run_at=agent.last_run_at,
            monthly_cost_usd=agent.monthly_cost_usd,
            open_incidents=agent.open_incidents,
            value_metric=agent.value_metric,
            budget_usd=agent.budget_usd,
        )
        return self.upsert_agent(updated)

    def update_cost(self, agent_id: str, monthly_cost_usd: float) -> RegisteredAgent | None:
        agent = self.get_agent(agent_id)
        if agent is None:
            return None
        updated = RegisteredAgent(
            agent_id=agent.agent_id,
            name=agent.name,
            owner=agent.owner,
            business_domain=agent.business_domain,
            risk_tier=agent.risk_tier,
            autonomy_level=agent.autonomy_level,
            status=agent.status,
            model_provider=agent.model_provider,
            allowed_tools=agent.allowed_tools,
            data_classes=agent.data_classes,
            last_run_at=agent.last_run_at,
            monthly_cost_usd=monthly_cost_usd,
            open_incidents=agent.open_incidents,
            value_metric=agent.value_metric,
            budget_usd=agent.budget_usd,
        )
        return self.upsert_agent(updated)

    def count(self) -> int:
        with self._psycopg.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM agent_registry")
                row = cursor.fetchone()
        return int(row[0]) if row else 0
