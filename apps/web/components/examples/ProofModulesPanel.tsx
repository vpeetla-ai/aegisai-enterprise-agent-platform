"use client";

import {
  CheckCircle2,
  Database,
  Gauge,
  LockKeyhole,
  ShieldAlert
} from "lucide-react";
import { safeArray } from "@/lib/api/safe";
import { policySimulatorScenarios } from "@/lib/controlPlaneData";
import type {
  AgentRegistryPayload,
  AuditPacketPayload,
  GoldenEvalPayload,
  IdentityPosturePayload,
  KillSwitchPayload,
  PolicySimulationPayload
} from "@/lib/api/types";

type ProofModulesPanelProps = {
  runAgentRegistryApi: () => void;
  agentRegistryResult: AgentRegistryPayload | null;
  runPolicySimulatorApi: (index?: number) => void;
  policySimulationResult: PolicySimulationPayload | null;
  runAuditPacketApi: () => void;
  auditPacketResult: AuditPacketPayload | null;
  onCheckPdf: () => void;
  runIdentityPostureApi: () => void;
  identityPostureResult: IdentityPosturePayload | null;
  runKillSwitchApi: () => void;
  runKillSwitchPostureApi: () => void;
  killSwitchResult: KillSwitchPayload | null;
  runGoldenEvalApi: () => void;
  goldenEvalResult: GoldenEvalPayload | null;
};

function Empty({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="proof-module-empty">
      <strong>{title}</strong>
      <p>{detail}</p>
    </div>
  );
}

export function ProofModulesPanel({
  runAgentRegistryApi,
  agentRegistryResult,
  runPolicySimulatorApi,
  policySimulationResult,
  runAuditPacketApi,
  auditPacketResult,
  onCheckPdf,
  runIdentityPostureApi,
  identityPostureResult,
  runKillSwitchApi,
  runKillSwitchPostureApi,
  killSwitchResult,
  runGoldenEvalApi,
  goldenEvalResult
}: ProofModulesPanelProps) {
  return (
    <div className="proof-modules-grid">
      <article className="proof-module-card">
        <header>
          <Database size={18} />
          <div>
            <h3>Discover · Registry</h3>
            <p>Agent ownership, tools, risk, cost</p>
          </div>
          <button type="button" className="btn-secondary" onClick={() => void runAgentRegistryApi()}>
            Show
          </button>
        </header>
        {agentRegistryResult?.summary ? (
          <div className="proof-module-body">
            <div className="proof-mini-stats">
              <span>{agentRegistryResult.summary.total_agents} agents</span>
              <span>{agentRegistryResult.summary.high_or_critical_risk} high risk</span>
              <span>${agentRegistryResult.summary.monthly_cost_usd}/mo</span>
            </div>
          </div>
        ) : (
          <Empty title="Registry ready" detail="Show sprawl controls for the pilot inventory." />
        )}
      </article>

      <article className="proof-module-card">
        <header>
          <ShieldAlert size={18} />
          <div>
            <h3>Govern · Policy simulator</h3>
            <p>Dry-run before execution</p>
          </div>
        </header>
        <div className="proof-scenario-chips">
          {policySimulatorScenarios.map((scenario, index) => (
            <button
              key={scenario.label}
              type="button"
              className="proof-chip"
              onClick={() => void runPolicySimulatorApi(index)}
            >
              {scenario.label}
            </button>
          ))}
        </div>
        {policySimulationResult ? (
          <div className="proof-module-body">
            <strong>{policySimulationResult.decision}</strong>
            <p>{policySimulationResult.explanation}</p>
          </div>
        ) : (
          <Empty title="Choose a policy scenario" detail="Pick a scenario chip to preview routing." />
        )}
      </article>

      <article className="proof-module-card">
        <header>
          <CheckCircle2 size={18} />
          <div>
            <h3>Assure · Audit packet</h3>
            <p>JSON / PDF for compliance</p>
          </div>
          <div className="proof-module-actions">
            <button type="button" className="btn-secondary" onClick={() => void runAuditPacketApi()}>
              JSON
            </button>
            <button type="button" className="btn-secondary" onClick={onCheckPdf}>
              PDF
            </button>
          </div>
        </header>
        {auditPacketResult ? (
          <div className="proof-module-body proof-mini-stats">
            <span>Chain {auditPacketResult.audit_chain_valid ? "valid" : "invalid"}</span>
            <span>{safeArray(auditPacketResult.audit_events).length} events</span>
          </div>
        ) : (
          <Empty title="Audit packet ready" detail="Generate JSON or PDF evidence after a scenario run." />
        )}
      </article>

      <article className="proof-module-card">
        <header>
          <LockKeyhole size={18} />
          <div>
            <h3>Secure · Identity</h3>
            <p>Reviewers and tool grants</p>
          </div>
          <button type="button" className="btn-secondary" onClick={() => void runIdentityPostureApi()}>
            Show
          </button>
        </header>
        {identityPostureResult ? (
          <div className="proof-module-body proof-mini-stats">
            <span>{identityPostureResult.principal_count} principals</span>
            <span>{identityPostureResult.tool_grants} grants</span>
          </div>
        ) : (
          <Empty title="Identity posture ready" detail="Show RBAC posture for reviewer paths." />
        )}
      </article>

      <article className="proof-module-card">
        <header>
          <ShieldAlert size={18} />
          <div>
            <h3>Respond · Kill switch</h3>
            <p>Freeze tools or workflows</p>
          </div>
          <div className="proof-module-actions">
            <button type="button" className="btn-secondary" onClick={() => void runKillSwitchApi()}>
              Freeze
            </button>
            <button type="button" className="btn-secondary" onClick={() => void runKillSwitchPostureApi()}>
              Status
            </button>
          </div>
        </header>
        {killSwitchResult ? (
          <div className="proof-module-body">
            <strong>{killSwitchResult.rule?.scope_value ?? `${killSwitchResult.active_rule_count ?? 0} active`}</strong>
            <p>{killSwitchResult.rule?.reason ?? "Posture loaded."}</p>
          </div>
        ) : (
          <Empty title="Incident control ready" detail="Freeze a tool or review current kill-switch status." />
        )}
      </article>

      <article className="proof-module-card">
        <header>
          <Gauge size={18} />
          <div>
            <h3>Evaluate · Golden evals</h3>
            <p>Release gate before promotion</p>
          </div>
          <button type="button" className="btn-secondary" onClick={() => void runGoldenEvalApi()}>
            Run
          </button>
        </header>
        {goldenEvalResult ? (
          <div className="proof-module-body">
            <strong>{goldenEvalResult.gate}</strong>
            <p>{goldenEvalResult.release_recommendation}</p>
          </div>
        ) : (
          <Empty title="No eval run" detail="Regression gate for prompts and tools." />
        )}
      </article>
    </div>
  );
}
