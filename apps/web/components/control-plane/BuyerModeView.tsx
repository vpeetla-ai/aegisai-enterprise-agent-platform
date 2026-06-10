"use client";

import { FileDown, MessageSquare, Play, Shield, Zap } from "lucide-react";
import { CollapsibleSection } from "@/components/control-plane/CollapsibleSection";
import { ConnectorCatalogPanel } from "@/components/control-plane/ConnectorCatalogPanel";
import {
  BuyerProofBrief,
  ControlPlaneStoryRail
} from "@/components/control-plane/ControlPlaneStoryRail";
import { DesignPartnerChecklist } from "@/components/control-plane/DesignPartnerChecklist";
import { GatewaySdkSnippet } from "@/components/control-plane/GatewaySdkSnippet";
import { GuidedBuyerDemo, type GuidedDemoStep } from "@/components/control-plane/GuidedBuyerDemo";
import { GovernanceNorthStarPanel } from "@/components/control-plane/GovernanceNorthStarPanel";
import { IdentityGraphViz } from "@/components/control-plane/IdentityGraphViz";
import { PersonaChips } from "@/components/control-plane/PersonaChips";
import { PolicyReplayDiff } from "@/components/control-plane/PolicyReplayDiff";
import { personaById, type BuyerPersona } from "@/lib/controlPlanePersonas";
import { safeArray } from "@/lib/api/safe";
import type {
  AuditVerificationPayload,
  ConnectorCatalogPayload,
  ExecutionPayload,
  FinOpsDashboardPayload,
  FlagshipDemoPayload,
  GatewayPayload,
  GatewaySdkPayload,
  GovernanceMetricsPayload,
  McpProxyPayload,
  PolicyReplayPayload,
  PolicyStudioPayload,
  RegulatedOpsDemoPayload,
  IdentityGraphPayload
} from "@/lib/api/types";

const SLACK_APPROVAL_DEMO_URL =
  "https://slack.com/app_redirect?channel=aegisai-hitl&tab=messages";

type BuyerModeViewProps = {
  persona: BuyerPersona;
  setPersona: (p: BuyerPersona) => void;
  persistenceMode?: string;
  governanceMetrics: GovernanceMetricsPayload | null;
  isLoadingMetrics: boolean;
  runGovernanceMetricsApi: () => void;
  flagshipDemo: FlagshipDemoPayload | null;
  guidedDemoSteps: GuidedDemoStep[];
  demoTimeline: string[];
  buyerDemoState: "idle" | "preparing" | "running" | "evidence_ready" | "failed";
  isRunningPlatformDemo: boolean;
  runBuyerDemo: () => void;
  retryBuyerDemoStep: (stepId: GuidedDemoStep["id"]) => void;
  copyBuyerDemoReport: () => void;
  copyBuyerDemoJsonReport: () => void;
  downloadBuyerDemoJsonReport: () => void;
  gatewayResult: GatewayPayload | null;
  executionResult: ExecutionPayload | null;
  auditVerification: AuditVerificationPayload | null;
  regulatedOpsDemo: RegulatedOpsDemoPayload | null;
  policyStudio: PolicyStudioPayload | null;
  policyReplay: PolicyReplayPayload | null;
  identityGraph: IdentityGraphPayload | null;
  connectorCatalog: ConnectorCatalogPayload | null;
  isLoadingCatalog: boolean;
  runConnectorCatalogApi: () => void;
  finopsResult: FinOpsDashboardPayload | null;
  gatewaySdk: GatewaySdkPayload | null;
  mcpResult: McpProxyPayload | null;
  runMcpProxyApi: () => void;
  isLoadingMcp: boolean;
  onDownloadAuditPdf: () => void;
  openProofWorkloads: () => void;
};

export function BuyerModeView({
  persona,
  setPersona,
  persistenceMode,
  governanceMetrics,
  isLoadingMetrics,
  runGovernanceMetricsApi,
  flagshipDemo,
  guidedDemoSteps,
  demoTimeline,
  buyerDemoState,
  isRunningPlatformDemo,
  runBuyerDemo,
  retryBuyerDemoStep,
  copyBuyerDemoReport,
  copyBuyerDemoJsonReport,
  downloadBuyerDemoJsonReport,
  gatewayResult,
  executionResult,
  auditVerification,
  regulatedOpsDemo,
  policyStudio,
  policyReplay,
  identityGraph,
  connectorCatalog,
  isLoadingCatalog,
  runConnectorCatalogApi,
  finopsResult,
  gatewaySdk,
  mcpResult,
  runMcpProxyApi,
  isLoadingMcp,
  onDownloadAuditPdf,
  openProofWorkloads
}: BuyerModeViewProps) {
  const personaConfig = personaById(persona);

  return (
    <div className="buyer-mode-page">
      <section className="buyer-mode-hero">
        <PersonaChips selected={persona} onSelect={setPersona} />
        <p className="eyebrow">Agent Governance Control Plane</p>
        <h1>{personaConfig.headline}</h1>
        <p className="buyer-mode-lead">{personaConfig.proofLine}</p>
        <p className="buyer-mode-connector-focus">
          <Zap size={16} />
          Connector focus: {personaConfig.connectorFocus}
        </p>
        {persistenceMode === "postgres" ? (
          <span className="persistence-badge persistence-badge-prod">Production persistence · Postgres</span>
        ) : (
          <span className="persistence-badge persistence-badge-demo">
            Demo persistence · {persistenceMode ?? "sqlite"} — set AEGISAI_DB_BACKEND=postgres for pilots
          </span>
        )}
      </section>
      <BuyerProofBrief />
      <ControlPlaneStoryRail />

      <div id="command-center">
        <GovernanceNorthStarPanel
          metrics={governanceMetrics}
          onRefresh={runGovernanceMetricsApi}
          isLoading={isLoadingMetrics}
          persistenceMode={persistenceMode}
          buyerMode
        />
      </div>

      <div id="buyer-demo">
        {flagshipDemo ? (
          <section className="flagship-narrative product-panel">
            <p className="eyebrow">Flagship demo narrative</p>
            <h2>{flagshipDemo.headline}</h2>
            <p>{flagshipDemo.talk_track}</p>
            <ol className="flagship-steps">
              {flagshipDemo.steps.map((step, index) => (
                <li key={step.step}>
                  <span>{index + 1}</span>
                  <div>
                    <strong>{step.step}</strong>
                    <p>{step.buyer_message}</p>
                  </div>
                </li>
              ))}
            </ol>
          </section>
        ) : (
          <div className="skeleton-block skeleton-panel" aria-hidden />
        )}
      </div>

      <GuidedBuyerDemo
        steps={guidedDemoSteps}
        isRunning={isRunningPlatformDemo}
        demoState={buyerDemoState}
        timeline={demoTimeline}
        onRun={runBuyerDemo}
        onRetryStep={retryBuyerDemoStep}
        onCopyReport={copyBuyerDemoReport}
        onCopyJsonReport={copyBuyerDemoJsonReport}
        onDownloadJsonReport={downloadBuyerDemoJsonReport}
      />

      <section className="buyer-demo-outcomes product-panel">
        <p className="eyebrow">Live outcomes</p>
        <h2>What just happened in your pilot tenant</h2>
        <div className="outcome-grid">
          <article>
            <Shield size={18} />
            <span>Gateway</span>
            <strong>{gatewayResult?.gateway_decision ?? "Run demo"}</strong>
            <p>{gatewayResult?.tool_name ?? "payments.issue_refund"}</p>
          </article>
          <article>
            <span>Execution</span>
            <strong>{executionResult?.status ?? "Pending"}</strong>
            <p>{executionResult?.connector ?? "Broker path"}</p>
          </article>
          <article>
            <span>Audit verify</span>
            <strong>{auditVerification ? (auditVerification.valid ? "Valid" : "Invalid") : "—"}</strong>
            <p>Tamper-evident packet</p>
          </article>
          {finopsResult?.roi ? (
            <article>
              <span>ROI</span>
              <strong>${finopsResult.roi.estimated_loss_prevented_usd}</strong>
              <p>Loss prevented (demo)</p>
            </article>
          ) : null}
        </div>
        <div className="buyer-demo-actions">
          <button type="button" className="btn-primary" onClick={onDownloadAuditPdf}>
            <FileDown size={16} />
            Download audit PDF
          </button>
          <a
            className="btn-secondary slack-approve-link"
            href={SLACK_APPROVAL_DEMO_URL}
            target="_blank"
            rel="noreferrer"
          >
            <MessageSquare size={16} />
            Open Slack approval (demo)
          </a>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => void runMcpProxyApi()}
            disabled={isLoadingMcp}
          >
            {isLoadingMcp ? "Govern MCP…" : "Govern MCP tool call"}
          </button>
          {mcpResult ? (
            <p className="mcp-inline-result">
              MCP: {mcpResult.gateway_decision} · {mcpResult.canonical_tool_name}
            </p>
          ) : null}
        </div>
      </section>

      <CollapsibleSection
        id="governance-modules"
        title="Technical proof details"
        subtitle="Open only when buyers ask for implementation depth"
        defaultOpen={false}
      >
        <div id="architect-console">
          <ConnectorCatalogPanel
            catalog={connectorCatalog}
            onLoad={runConnectorCatalogApi}
            isLoading={isLoadingCatalog}
          />
        </div>
        <div className="buyer-proof-grid">
          <article className="product-panel">
            <p className="eyebrow">Regulated operations</p>
            <h3>{regulatedOpsDemo?.scenario ?? "Customer operations"}</h3>
            <p>{regulatedOpsDemo?.story}</p>
            <ul className="governed-steps-compact">
              {safeArray(regulatedOpsDemo?.governed_steps).map((step) => (
                <li key={step.action}>
                  <strong>{step.action}</strong>
                  <span>{step.decision}</span>
                </li>
              ))}
            </ul>
          </article>
          <article className="product-panel">
            <p className="eyebrow">Policy studio</p>
            <h3>Before / after rollout</h3>
            <PolicyReplayDiff studio={policyStudio} replay={policyReplay} />
          </article>
          <article className="product-panel">
            <p className="eyebrow">Identity graph</p>
            <h3>Blast radius</h3>
            <IdentityGraphViz graph={identityGraph} />
          </article>
        </div>

        <div id="readiness-center">
          <GatewaySdkSnippet sdk={gatewaySdk} />
          <DesignPartnerChecklist guidedSteps={guidedDemoSteps} persistenceMode={persistenceMode} />
        </div>
      </CollapsibleSection>

      <footer className="pilot-success-footer">
        <p>
          <strong>Pilot north star:</strong> Within 90 days, 100% of side-effecting agent tool calls
          route through the AegisAI gateway in your pilot environment.
        </p>
        <button type="button" className="btn-secondary" onClick={openProofWorkloads}>
          <Play size={16} />
          Open proof workloads (reference agents)
        </button>
      </footer>
    </div>
  );
}
