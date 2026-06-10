import {
  BadgeCheck,
  Boxes,
  Braces,
  FileCheck2,
  GitBranch,
  ShieldCheck,
  Sparkles,
  TerminalSquare
} from "lucide-react";
import {
  BuyerModuleCard,
  type BuyerModuleLoadState
} from "@/components/control-plane/BuyerModuleCard";
import { safeArray } from "@/lib/api/safe";
import type {
  AuditVaultPayload,
  DeveloperQuickstartPayload,
  GatewayStoryPayload,
  IdentityGraphPayload,
  PolicyStudioPayload,
  RegulatedOpsDemoPayload
} from "@/lib/api/types";

export type BuyerModuleStatusMap = {
  gatewayStory: BuyerModuleLoadState;
  quickstart: BuyerModuleLoadState;
  regulatedOps: BuyerModuleLoadState;
  policyStudio: BuyerModuleLoadState;
  identityGraph: BuyerModuleLoadState;
  auditVault: BuyerModuleLoadState;
};

type TopTierProductPanelsProps = {
  gatewayStory: GatewayStoryPayload | null;
  developerQuickstart: DeveloperQuickstartPayload | null;
  regulatedOpsDemo: RegulatedOpsDemoPayload | null;
  policyStudio: PolicyStudioPayload | null;
  identityGraph: IdentityGraphPayload | null;
  auditVault: AuditVaultPayload | null;
  moduleStatus: BuyerModuleStatusMap;
  moduleErrors: Partial<Record<keyof BuyerModuleStatusMap, string>>;
  onLoadGatewayStory: () => void;
  onLoadDeveloperQuickstart: () => void;
  onLoadRegulatedOpsDemo: () => void;
  onRunPolicyStudio: () => void;
  onLoadIdentityGraph: () => void;
  onLoadAuditVault: () => void;
};

export function TopTierProductPanels({
  gatewayStory,
  developerQuickstart,
  regulatedOpsDemo,
  policyStudio,
  identityGraph,
  auditVault,
  moduleStatus,
  moduleErrors,
  onLoadGatewayStory,
  onLoadDeveloperQuickstart,
  onLoadRegulatedOpsDemo,
  onRunPolicyStudio,
  onLoadIdentityGraph,
  onLoadAuditVault
}: TopTierProductPanelsProps) {
  const visibleNodes = safeArray(identityGraph?.nodes).slice(0, 10);
  const visibleEdges = safeArray(identityGraph?.edges).slice(0, 9);

  return (
    <>
      <section className="gateway-first-panel">
        <div className="gateway-first-copy">
          <p className="eyebrow">Runtime Product Wedge</p>
          <h2>{gatewayStory?.headline ?? "Stop unsafe agent actions before production impact"}</h2>
          <p>
            {gatewayStory?.buyer_promise ??
              "AegisAI is the policy, identity, eval, HITL, execution-token, and audit layer between any AI agent and enterprise tools."}
          </p>
          <div className="gateway-runtimes">
            {(gatewayStory?.supported_runtimes ?? [
              "LangGraph",
              "OpenAI Agents SDK",
              "AWS Bedrock Agents",
              "MCP servers",
              "Custom agents"
            ]).map((runtime) => (
              <span key={runtime}>{runtime}</span>
            ))}
          </div>
        </div>
        <div className="gateway-flow">
          {(gatewayStory?.flow ?? fallbackGatewayFlow).map((item, index) => (
            <article key={item.step}>
              <span>{index + 1}</span>
              <div>
                <strong>{item.step}</strong>
                <p>{item.control}</p>
              </div>
            </article>
          ))}
        </div>
        <button type="button" className="btn-secondary" onClick={() => void onLoadGatewayStory()}>
          <Sparkles size={16} />
          {moduleStatus.gatewayStory === "loading" ? "Refreshing…" : "Refresh Gateway Story"}
        </button>
        {moduleStatus.gatewayStory === "error" ? (
          <p className="buyer-module-error" role="alert">
            {moduleErrors.gatewayStory}
          </p>
        ) : null}
      </section>

      <section className="top-tier-grid">
        <BuyerModuleCard
          eyebrow="15-Minute Integration"
          title="Developer quickstart"
          icon={<TerminalSquare size={18} />}
          loadLabel="Refresh quickstart"
          loadState={moduleStatus.quickstart}
          errorMessage={moduleErrors.quickstart}
          onLoad={onLoadDeveloperQuickstart}
          emptyHint="Show how any agent team plugs into the gateway quickly."
        >
          <ol className="numbered-list">
            {safeArray(developerQuickstart?.steps).map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
          <pre className="code-sample">{developerQuickstart?.typescript}</pre>
        </BuyerModuleCard>

        <BuyerModuleCard
          eyebrow="Killer Demo Scenario"
          title="Regulated customer operations"
          icon={<ShieldCheck size={18} />}
          loadLabel="Refresh scenario"
          loadState={moduleStatus.regulatedOps}
          errorMessage={moduleErrors.regulatedOps}
          onLoad={onLoadRegulatedOpsDemo}
          emptyHint="Prove the platform with refunds, CRM, customer messaging, RAG, and audit."
        >
          <p className="scenario-copy">{regulatedOpsDemo?.story}</p>
          <div className="decision-stack">
            {safeArray(regulatedOpsDemo?.governed_steps).map((step) => (
              <div key={step.action}>
                <span>{step.decision}</span>
                <strong>{step.action}</strong>
                <p>{step.why}</p>
              </div>
            ))}
          </div>
        </BuyerModuleCard>
      </section>

      <section className="top-tier-grid">
        <BuyerModuleCard
          eyebrow="Policy Studio"
          title="Dry-run policy changes before rollout"
          icon={<Braces size={18} />}
          loadLabel="Run policy dry run"
          loadState={moduleStatus.policyStudio}
          errorMessage={moduleErrors.policyStudio}
          onLoad={onRunPolicyStudio}
          emptyHint="Simulate policy, review blast radius, then promote with evidence."
          wide
        >
          <div className="policy-studio-layout">
            <div>
              <span className={`pill pill-${policyStudio?.dry_run_decision ?? "pending"}`}>
                {policyStudio?.dry_run_decision}
              </span>
              <p className="scenario-copy">{policyStudio?.draft_rule}</p>
              <pre className="code-sample">
                {JSON.stringify(policyStudio?.generated_policy_preview ?? {}, null, 2)}
              </pre>
            </div>
            <div className="blast-card">
              <strong>Blast radius</strong>
              <p>{policyStudio?.blast_radius.estimated_monthly_intercepts} monthly intercepts</p>
              <p>{policyStudio?.blast_radius.expected_review_increase_percent}% review increase</p>
              <ul>
                {safeArray(policyStudio?.promotion_checklist).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </BuyerModuleCard>

        <BuyerModuleCard
          eyebrow="Identity Graph"
          title="Agent and tool blast radius"
          icon={<GitBranch size={18} />}
          loadLabel="Refresh graph"
          loadState={moduleStatus.identityGraph}
          errorMessage={moduleErrors.identityGraph}
          onLoad={onLoadIdentityGraph}
          emptyHint="Reveal what each agent, owner, identity, and tool can touch."
        >
          <div className="graph-stats">
            <span>{identityGraph?.blast_radius.privileged_principals ?? 0} privileged principals</span>
            <span>{identityGraph?.blast_radius.side_effecting_tools ?? 0} side-effecting tools</span>
          </div>
          <div className="identity-graph">
            {visibleNodes.map((node) => (
              <div className={`graph-node ${node.kind}`} key={node.id}>
                <strong>{node.label}</strong>
                <span>
                  {node.kind} · {node.risk}
                </span>
              </div>
            ))}
          </div>
          <div className="edge-list">
            {visibleEdges.map((edge) => (
              <small key={`${edge.from}-${edge.to}-${edge.relationship}`}>
                {`${edge.from.replace(/^.*:/, "")} -> ${edge.relationship} -> ${edge.to.replace(/^.*:/, "")}`}
              </small>
            ))}
          </div>
        </BuyerModuleCard>
      </section>

      <section className="top-tier-grid">
        <BuyerModuleCard
          eyebrow="Assurance Vault"
          title="Board-ready evidence packets"
          icon={<FileCheck2 size={18} />}
          loadLabel="Refresh audit vault"
          loadState={moduleStatus.auditVault}
          errorMessage={moduleErrors.auditVault}
          onLoad={onLoadAuditVault}
          emptyHint="Map traces, policy, HITL, cost, and signatures to audit evidence."
        >
          <p className="scenario-copy">{auditVault?.retention_policy}</p>
          <div className="evidence-grid">
            {safeArray(auditVault?.evidence_types).map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
          <div className="compliance-list">
            {safeArray(auditVault?.compliance_mapping).map((mapping) => (
              <div key={mapping.framework}>
                <strong>{mapping.framework}</strong>
                <p>{safeArray(mapping.controls).join(", ")}</p>
              </div>
            ))}
          </div>
        </BuyerModuleCard>

        <article className="panel top-tier-card">
          <div className="panel-heading compact">
            <div>
              <p className="eyebrow">Product Consolidation</p>
              <h2>What makes this buyable</h2>
            </div>
            <Boxes size={18} />
          </div>
          <div className="buyable-list">
            {[
              "Runtime gateway, not only dashboards",
              "One governed vertical scenario anyone can understand",
              "Policy Studio for non-engineering rollout decisions",
              "Identity graph for agent/tool blast radius",
              "Signed audit packets for compliance and board review",
              "FinOps ROI tied to workflow outcomes"
            ].map((item) => (
              <div key={item}>
                <BadgeCheck size={16} />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </article>
      </section>
    </>
  );
}

const fallbackGatewayFlow = [
  { step: "Agent requests tool", control: "Normalize tool call and agent identity." },
  { step: "Gateway intercepts", control: "Check identity, policy, evals, and kill switches." },
  { step: "HITL or token", control: "Pause for approval or issue a scoped execution token." },
  { step: "Signed evidence", control: "Persist trace, decision, cost, and audit signature." }
];
