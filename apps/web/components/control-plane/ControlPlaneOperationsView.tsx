import {
  Activity,
  ArrowRight,
  CheckCircle2,
  Clock3,
  Database,
  Gauge,
  Layers3,
  LockKeyhole,
  Network,
  SlidersHorizontal
} from "lucide-react";
import { ApiHealthBanner } from "@/components/control-plane/ApiHealthBanner";
import { ConnectorRegistrationWizard } from "@/components/control-plane/ConnectorRegistrationWizard";
import { ControlPlaneActionCenter } from "@/components/control-plane/ControlPlaneActionCenter";
import { ControlPlaneHero } from "@/components/control-plane/ControlPlaneHero";
import {
  BuyerProofBrief,
  ControlPlaneStoryRail
} from "@/components/control-plane/ControlPlaneStoryRail";
import { CollapsibleSection } from "@/components/control-plane/CollapsibleSection";
import { DeveloperConsolePanel } from "@/components/control-plane/DeveloperConsolePanel";
import { GovernanceNorthStarPanel } from "@/components/control-plane/GovernanceNorthStarPanel";
import { GuidedBuyerDemo, type GuidedDemoStep } from "@/components/control-plane/GuidedBuyerDemo";
import { EnterpriseValuePanel } from "@/components/control-plane/EnterpriseValuePanel";
import { GatewayOnboardingPanels } from "@/components/control-plane/GatewayOnboardingPanels";
import { ConnectorCatalogPanel } from "@/components/control-plane/ConnectorCatalogPanel";
import type { HttpConnectorFormState } from "@/components/control-plane/HttpConnectorRegistrationPanel";
import { FinOpsPanel } from "@/components/control-plane/FinOpsPanel";
import { McpProxyPanel } from "@/components/control-plane/McpProxyPanel";
import { ObservabilityExportPanel } from "@/components/control-plane/ObservabilityExportPanel";
import { SignedAssurancePanel } from "@/components/control-plane/SignedAssurancePanel";
import {
  TopTierProductPanels,
  type BuyerModuleStatusMap
} from "@/components/control-plane/TopTierProductPanels";
import { ProductionReadinessCenterPanel } from "@/components/control-plane/ProductionReadinessCenterPanel";
import { ReadinessIntegrationsPanels } from "@/components/control-plane/ReadinessIntegrationsPanels";
import {
  agents,
  dataContracts,
  dataPlaneComponents,
  evaluationMetrics,
  governanceTimeline,
  kpis,
  memoryContracts,
  observabilityAdapters,
  observabilitySignals,
  operatingQueues,
  productionControls,
  reviewerActions,
  sharedContext,
  statusMeta,
  systemLayers,
  traceTimeline
} from "@/lib/controlPlaneData";
import type {
  AgentLifecyclePayload,
  AgentOnboardingPayload,
  AuditVaultPayload,
  DeveloperQuickstartPayload,
  DeploymentPosturePayload,
  FlagshipDemoPayload,
  GatewayPayload,
  GatewaySdkPayload,
  GatewayStoryPayload,
  IdentityGraphPayload,
  IncidentTimelinePayload,
  IntegrationsPayload,
  MutableCase,
  PermissionMatrixPayload,
  PolicyReplayPayload,
  PolicyStudioPayload,
  PlatformActionKey,
  PlatformPosturePayload,
  ReleaseGatePayload,
  RegulatedOpsDemoPayload,
  ConnectorCatalogPayload,
  GovernanceMetricsPayload,
  HttpConnectorListPayload,
  HttpConnectorRegisterPayload,
  HttpConnectorTestPayload,
  FinOpsDashboardPayload,
  AuditVerificationPayload,
  McpProxyPayload,
  ReadinessPayload,
  SignedAuditPayload
} from "@/lib/api/types";

type ControlPlaneOperationsViewProps = {
  surfaceMode?: "platform";
  isRunningPlatformDemo: boolean;
  governanceMetrics: GovernanceMetricsPayload | null;
  runGovernanceMetricsApi: () => void;
  isLoadingMetrics: boolean;
  persistenceMode?: string;
  guidedDemoSteps: GuidedDemoStep[];
  demoTimeline: string[];
  buyerDemoState: "idle" | "preparing" | "running" | "evidence_ready" | "failed";
  runBuyerDemo: () => void;
  retryBuyerDemoStep: (stepId: GuidedDemoStep["id"]) => void;
  copyBuyerDemoReport: () => void;
  copyBuyerDemoJsonReport: () => void;
  downloadBuyerDemoJsonReport: () => void;
  platformActionStatus: Record<PlatformActionKey, string>;
  platformPostureResult: PlatformPosturePayload | null;
  gatewayStory: GatewayStoryPayload | null;
  developerQuickstart: DeveloperQuickstartPayload | null;
  regulatedOpsDemo: RegulatedOpsDemoPayload | null;
  policyStudio: PolicyStudioPayload | null;
  identityGraph: IdentityGraphPayload | null;
  auditVault: AuditVaultPayload | null;
  gatewaySdk: GatewaySdkPayload | null;
  policyReplay: PolicyReplayPayload | null;
  agentLifecycle: AgentLifecyclePayload | null;
  permissionMatrix: PermissionMatrixPayload | null;
  releaseGate: ReleaseGatePayload | null;
  incidentTimeline: IncidentTimelinePayload | null;
  deploymentPosture: DeploymentPosturePayload | null;
  flagshipDemo: FlagshipDemoPayload | null;
  gatewayResult: GatewayPayload | null;
  agentOnboardingResult: AgentOnboardingPayload | null;
  readinessResult: ReadinessPayload | null;
  integrationsResult: IntegrationsPayload | null;
  finopsResult: FinOpsDashboardPayload | null;
  runFinOpsApi: () => void;
  connectorCatalog: ConnectorCatalogPayload | null;
  runConnectorCatalogApi: () => void;
  isLoadingCatalog: boolean;
  httpConnectors: HttpConnectorListPayload | null;
  httpConnectorTestResult: HttpConnectorTestPayload | null;
  httpConnectorRegisterResult: HttpConnectorRegisterPayload | null;
  isHttpConnectorBusy: boolean;
  runHttpConnectorsApi: () => void;
  runHttpConnectorTestApi: (form: HttpConnectorFormState) => void;
  runHttpConnectorRegisterApi: (form: HttpConnectorFormState) => void;
  runHttpConnectorDeleteApi: (connectorId: string) => void;
  mcpResult: McpProxyPayload | null;
  runMcpProxyApi: () => void;
  isLoadingMcp: boolean;
  signingPosture: Record<string, unknown> | null;
  signedAuditPacket: SignedAuditPayload | null;
  auditVerification: AuditVerificationPayload | null;
  onLoadSigningPosture: () => void;
  onDownloadSignedAudit: () => void;
  onVerifySignedAudit: () => void;
  isLoadingAssurance: boolean;
  caseRows: MutableCase[];
  selectedCase: MutableCase;
  selectedCaseId: string;
  actionEvents: string[];
  apiResult: string;
  openView: (view: "examples" | "control-plane") => void;
  runPlatformPostureApi: () => void;
  runGatewayStoryApi: () => void;
  runDeveloperQuickstartApi: () => void;
  runRegulatedOpsDemoApi: () => void;
  runPolicyStudioApi: () => void;
  runIdentityGraphApi: () => void;
  runAuditVaultApi: () => void;
  runGatewaySdkApi: () => void;
  runPolicyReplayApi: () => void;
  runAgentLifecycleApi: () => void;
  runPermissionMatrixApi: () => void;
  runReleaseGateApi: () => void;
  runIncidentTimelineApi: () => void;
  runDeploymentPostureApi: () => void;
  runFlagshipDemoApi: () => void;
  buyerModuleStatus: BuyerModuleStatusMap;
  buyerModuleErrors: Partial<Record<keyof BuyerModuleStatusMap, string>>;
  runGatewayApi: () => void;
  runAgentOnboardingApi: () => void;
  runReadinessApi: (agentId?: string) => void;
  runIntegrationsApi: () => void;
  onRefreshObservability: () => void;
  runGovernedExecutionApi: () => void;
  callApi: <T = unknown>(path: string, init?: RequestInit) => Promise<T | null>;
  runAgentApi: () => void;
  runRagApi: () => void;
  runReviewerApi: () => void;
  setSelectedCaseId: (caseId: string) => void;
  applyReviewerAction: (actionLabel: string) => void;
};

export function ControlPlaneOperationsView({
  surfaceMode = "platform",
  isRunningPlatformDemo,
  governanceMetrics,
  runGovernanceMetricsApi,
  isLoadingMetrics,
  persistenceMode,
  guidedDemoSteps,
  demoTimeline,
  buyerDemoState,
  runBuyerDemo,
  retryBuyerDemoStep,
  copyBuyerDemoReport,
  copyBuyerDemoJsonReport,
  downloadBuyerDemoJsonReport,
  platformActionStatus,
  platformPostureResult,
  gatewayStory,
  developerQuickstart,
  regulatedOpsDemo,
  policyStudio,
  identityGraph,
  auditVault,
  gatewaySdk,
  policyReplay,
  agentLifecycle,
  permissionMatrix,
  releaseGate,
  incidentTimeline,
  deploymentPosture,
  flagshipDemo,
  gatewayResult,
  agentOnboardingResult,
  readinessResult,
  integrationsResult,
  finopsResult,
  runFinOpsApi,
  connectorCatalog,
  runConnectorCatalogApi,
  isLoadingCatalog,
  httpConnectors,
  httpConnectorTestResult,
  httpConnectorRegisterResult,
  isHttpConnectorBusy,
  runHttpConnectorsApi,
  runHttpConnectorTestApi,
  runHttpConnectorRegisterApi,
  runHttpConnectorDeleteApi,
  mcpResult,
  runMcpProxyApi,
  isLoadingMcp,
  signingPosture,
  signedAuditPacket,
  auditVerification,
  onLoadSigningPosture,
  onDownloadSignedAudit,
  onVerifySignedAudit,
  isLoadingAssurance,
  caseRows,
  selectedCase,
  selectedCaseId,
  actionEvents,
  apiResult,
  openView,
  runPlatformPostureApi,
  runGatewayStoryApi,
  runDeveloperQuickstartApi,
  runRegulatedOpsDemoApi,
  runPolicyStudioApi,
  runIdentityGraphApi,
  runAuditVaultApi,
  runGatewaySdkApi,
  runPolicyReplayApi,
  runAgentLifecycleApi,
  runPermissionMatrixApi,
  runReleaseGateApi,
  runIncidentTimelineApi,
  runDeploymentPostureApi,
  runFlagshipDemoApi,
  buyerModuleStatus,
  buyerModuleErrors,
  runGatewayApi,
  runAgentOnboardingApi,
  runReadinessApi,
  runIntegrationsApi,
  onRefreshObservability,
  runGovernedExecutionApi,
  callApi,
  runAgentApi,
  runRagApi,
  runReviewerApi,
  setSelectedCaseId,
  applyReviewerAction
}: ControlPlaneOperationsViewProps) {
  return (
    <>
      <ApiHealthBanner />
      <ControlPlaneHero
        isRunningPlatformDemo={isRunningPlatformDemo}
        runBuyerDemo={runBuyerDemo}
        openExamples={() => openView("examples")}
      />
      <BuyerProofBrief />
      <ControlPlaneStoryRail />

      <section className="story-section" id="command-center">
        <div className="story-section-heading">
          <span>1</span>
          <div>
            <p className="eyebrow">Command Center</p>
            <h2>Start with the executive control plane enterprises would buy</h2>
            <p>
              See estate posture, risk, spend, incidents, and the first operational actions
              before opening any implementation detail.
            </p>
          </div>
        </div>
        <GovernanceNorthStarPanel
          metrics={governanceMetrics}
          onRefresh={runGovernanceMetricsApi}
          isLoading={isLoadingMetrics}
          persistenceMode={persistenceMode}
        />
        <EnterpriseValuePanel
          platformPostureResult={platformPostureResult}
          governanceMetrics={governanceMetrics}
        />
        <ControlPlaneActionCenter
          platformActionStatus={platformActionStatus}
          runPlatformPostureApi={runPlatformPostureApi}
          runGatewayApi={runGatewayApi}
          runAgentOnboardingApi={runAgentOnboardingApi}
          runReadinessApi={runReadinessApi}
          runIntegrationsApi={runIntegrationsApi}
        />
      </section>

      <section className="story-section" id="buyer-demo">
        <div className="story-section-heading">
          <span>2</span>
          <div>
            <p className="eyebrow">Buyer Demo</p>
            <h2>Prove the platform controls a real multi-agent workflow</h2>
            <p>
              Run the guided flow to show how an agent request moves through policy,
              evaluation, HITL approval, execution, telemetry, and audit evidence.
            </p>
          </div>
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
      </section>

      <CollapsibleSection
        id="readiness-center"
        title="3. Production Readiness Center"
        subtitle="Adopt, govern, release, operate, and prove enterprise agent control"
        defaultOpen
      >
        <ProductionReadinessCenterPanel
          sdk={gatewaySdk}
          replay={policyReplay}
          lifecycle={agentLifecycle}
          matrix={permissionMatrix}
          releaseGate={releaseGate}
          incident={incidentTimeline}
          deployment={deploymentPosture}
          demo={flagshipDemo}
          onLoadSdk={runGatewaySdkApi}
          onRunReplay={runPolicyReplayApi}
          onLoadLifecycle={runAgentLifecycleApi}
          onLoadMatrix={runPermissionMatrixApi}
          onRunReleaseGate={runReleaseGateApi}
          onLoadIncident={runIncidentTimelineApi}
          onLoadDeployment={runDeploymentPostureApi}
          onLoadDemo={runFlagshipDemoApi}
        />
      </CollapsibleSection>

      <CollapsibleSection
        id="governance-modules"
        title="4. Governance Story Modules"
        subtitle="Gateway story, policy studio, identity graph, regulated operations, assurance, readiness, and cost"
        defaultOpen
      >
      <TopTierProductPanels
        gatewayStory={gatewayStory}
        developerQuickstart={developerQuickstart}
        regulatedOpsDemo={regulatedOpsDemo}
        policyStudio={policyStudio}
        identityGraph={identityGraph}
        auditVault={auditVault}
        moduleStatus={buyerModuleStatus}
        moduleErrors={buyerModuleErrors}
        onLoadGatewayStory={runGatewayStoryApi}
        onLoadDeveloperQuickstart={runDeveloperQuickstartApi}
        onLoadRegulatedOpsDemo={runRegulatedOpsDemoApi}
        onRunPolicyStudio={runPolicyStudioApi}
        onLoadIdentityGraph={runIdentityGraphApi}
        onLoadAuditVault={runAuditVaultApi}
      />
      <GatewayOnboardingPanels
        gatewayResult={gatewayResult}
        agentOnboardingResult={agentOnboardingResult}
        runGatewayApi={runGatewayApi}
        runAgentOnboardingApi={runAgentOnboardingApi}
      />
      <ReadinessIntegrationsPanels
        readinessResult={readinessResult}
        integrationsResult={integrationsResult}
        runReadinessApi={runReadinessApi}
        runIntegrationsApi={runIntegrationsApi}
      />
      <FinOpsPanel finopsResult={finopsResult} onLoad={runFinOpsApi} />
      </CollapsibleSection>

      <CollapsibleSection
        id="architect-console"
        title="5. Architect Console"
        subtitle="Connectors, MCP proxy, signed assurance, raw API testing, and reference architecture"
        defaultOpen={false}
      >
      <div className="control-plane-primary">
      <ConnectorCatalogPanel
        catalog={connectorCatalog}
        onLoad={runConnectorCatalogApi}
        isLoading={isLoadingCatalog}
      />
      <ConnectorRegistrationWizard
        httpConnectors={httpConnectors}
        lastTestResult={httpConnectorTestResult}
        lastRegisterResult={httpConnectorRegisterResult}
        isBusy={isHttpConnectorBusy}
        onLoad={runHttpConnectorsApi}
        onTest={runHttpConnectorTestApi}
        onRegister={runHttpConnectorRegisterApi}
        onDelete={runHttpConnectorDeleteApi}
      />
      <McpProxyPanel mcpResult={mcpResult} onSimulate={runMcpProxyApi} isLoading={isLoadingMcp} />
      <SignedAssurancePanel
        signingPosture={signingPosture}
        signedPacket={signedAuditPacket}
        verification={auditVerification}
        onLoadPosture={onLoadSigningPosture}
        onDownloadSigned={onDownloadSignedAudit}
        onVerify={onVerifySignedAudit}
        isLoading={isLoadingAssurance}
      />
      </div>

      <section className="observability-grid" aria-label="Observability signals">
        {observabilitySignals.map((signal) => {
const Icon = signal.icon;
return (
  <article className="obs-card" key={signal.label}>
    <Icon size={18} />
    <span>{signal.label}</span>
    <strong>{signal.value}</strong>
    <p>{signal.detail}</p>
  </article>
);
        })}
      </section>

      <section className="observability-layout">
        <section className="panel">
<div className="panel-heading compact">
  <div>
    <p className="eyebrow">Trace Timeline</p>
    <h2>What every agent run records</h2>
  </div>
  <Network size={18} />
</div>
<div className="trace-list">
  {traceTimeline.map((trace) => (
    <article className="trace-row" key={trace.step}>
      <span>{trace.step}</span>
      <div>
        <strong>{trace.span}</strong>
        <small>{trace.owner}</small>
        <p>{trace.signal}</p>
      </div>
    </article>
  ))}
</div>
        </section>

        <section className="panel">
<div className="panel-heading compact">
  <div>
    <p className="eyebrow">Tooling Strategy</p>
    <h2>Native control plane plus optional Langfuse/LangSmith adapters</h2>
  </div>
  <SlidersHorizontal size={18} />
</div>
<div className="adapter-list">
  {observabilityAdapters.map((adapter) => (
    <article className="adapter-card" key={adapter.name}>
      <span>{adapter.stance}</span>
      <strong>{adapter.name}</strong>
      <p>{adapter.fit}</p>
      <small>{adapter.tradeoff}</small>
    </article>
  ))}
</div>
        </section>
      </section>
      <ObservabilityExportPanel onRefreshStatus={onRefreshObservability} />

      <section className="kpi-grid" aria-label="Operating metrics">
        {kpis.map((item) => (
<div className="metric" key={item.label}>
  <span>{item.label}</span>
  <strong>{item.value}</strong>
  <small>{item.change}</small>
</div>
        ))}
      </section>

      <section className="layout-grid">
        <aside className="panel case-panel">
<div className="panel-heading">
  <div>
    <p className="eyebrow">Case Queue</p>
    <h2>Agent workflows</h2>
  </div>
  <Clock3 size={18} />
</div>

<div className="case-list">
  {caseRows.map((item) => {
    const meta = statusMeta[item.status];
    const isSelected = item.id === selectedCase.id;
    return (
      <button
        className={`case-row ${isSelected ? "selected" : ""}`}
        key={item.id}
        onClick={() => setSelectedCaseId(item.id)}
      >
        <span className={`status-dot ${meta.tone}`} />
        <span className="case-main">
          <strong>{item.title}</strong>
          <small>
            {item.id} · {item.workflow} · {item.amount}
          </small>
        </span>
        <span className={`status-pill ${meta.tone}`}>{meta.label}</span>
      </button>
    );
  })}
</div>
        </aside>

        <section className="main-column">
<div className="panel flow-panel">
  <div className="panel-heading">
    <div>
      <p className="eyebrow">Selected Case</p>
      <h2>{selectedCase.title}</h2>
    </div>
    <span className={`status-pill ${statusMeta[selectedCase.status].tone}`}>
      {statusMeta[selectedCase.status].label}
    </span>
  </div>

  <div className="architecture-strip">
    {systemLayers.map((layer, index) => (
      <div className="layer" key={layer.name}>
        <div className="layer-title">
          <Layers3 size={17} />
          <strong>{layer.name}</strong>
        </div>
        <p>{layer.description}</p>
        <div className="node-row">
          {layer.nodes.map((node) => (
            <span key={node}>{node}</span>
          ))}
        </div>
        {index < systemLayers.length - 1 && (
          <div className="flow-arrow" aria-hidden="true">
            <ArrowRight size={18} />
          </div>
        )}
      </div>
    ))}
  </div>

  <div className="agent-grid">
    {agents.map((agent) => {
      const Icon = agent.icon;
      const active = agent.key === selectedCase.activeAgent;
      return (
        <article className={`agent-card ${active ? "active" : ""}`} key={agent.key}>
          <div className="agent-icon">
            <Icon size={20} />
          </div>
          <div>
            <strong>{agent.name}</strong>
            <small>{agent.owner}</small>
          </div>
          <p>{agent.rule}</p>
          <span className={`agent-state ${agent.status}`}>{agent.status}</span>
        </article>
      );
    })}
  </div>
</div>

<div className="two-column">
  <section className="panel">
    <div className="panel-heading compact">
      <div>
        <p className="eyebrow">Shared Case Context</p>
        <h2>Governed memory</h2>
      </div>
      <LockKeyhole size={18} />
    </div>
    <div className="context-list">
      {sharedContext.map((item) => (
        <div className="context-item" key={item.label}>
          <span>{item.label}</span>
          <p>{item.value}</p>
        </div>
      ))}
    </div>
  </section>

  <section className="panel">
    <div className="panel-heading compact">
      <div>
        <p className="eyebrow">Evaluation Layer</p>
        <h2>Blocking gates</h2>
      </div>
      <Gauge size={18} />
    </div>
    <div className="eval-list">
      {evaluationMetrics.map((metric) => (
        <div className="eval-row" key={metric.label}>
          <div>
            <strong>{metric.label}</strong>
            <span>{metric.value}%</span>
          </div>
          <div className="bar">
            <span style={{ width: `${metric.value}%` }} />
          </div>
        </div>
      ))}
    </div>
  </section>
</div>

<div className="panel production-panel">
  <div className="panel-heading compact">
    <div>
      <p className="eyebrow">Production Controls</p>
      <h2>Enterprise readiness posture</h2>
    </div>
    <LockKeyhole size={18} />
  </div>
  <div className="control-grid">
    {productionControls.map((control) => {
      const Icon = control.icon;
      return (
        <article className="control-item" key={control.label}>
          <Icon size={18} />
          <div>
            <span>{control.label}</span>
            <strong>{control.value}</strong>
            <p>{control.detail}</p>
          </div>
        </article>
      );
    })}
  </div>
</div>
        </section>

        <aside className="right-column">
<section className="panel decision-panel">
  <div className="panel-heading">
    <div>
      <p className="eyebrow">Control-Plane Decision</p>
      <h2>{selectedCase.decision}</h2>
    </div>
    <Activity size={18} />
  </div>

  <div className="risk-meter">
    <div>
      <span>Risk Score</span>
      <strong>{selectedCase.risk}</strong>
    </div>
    <div className="risk-track">
      <span style={{ width: `${selectedCase.risk}%` }} />
    </div>
  </div>

  <div className="queue-grid">
    {operatingQueues.map((item) => {
      const Icon = item.icon;
      return (
        <div className="queue-item" key={item.label}>
          <Icon size={17} />
          <span>{item.label}</span>
          <strong>{item.value}</strong>
        </div>
      );
    })}
  </div>

  <div className="review-actions" aria-label="Reviewer actions">
    {reviewerActions.map((action) => (
      <button
        className={`review-action ${action.tone}`}
        key={action.label}
        onClick={() => applyReviewerAction(action.label)}
        title={action.description}
      >
        {action.label}
      </button>
    ))}
  </div>
</section>

<section className="panel event-panel">
  <div className="panel-heading compact">
    <div>
      <p className="eyebrow">Action Event Stream</p>
      <h2>Reviewer operations</h2>
    </div>
    <Activity size={18} />
  </div>
  <div className="event-list">
    {actionEvents.map((event, index) => (
      <div className="event-row" key={`${event}-${index}`}>
        <span>{event}</span>
        <small>{index === 0 ? "just now" : `${index + 1}m ago`}</small>
      </div>
    ))}
  </div>
</section>

<section className="panel data-panel">
  <div className="panel-heading compact">
    <div>
      <p className="eyebrow">Persistence Layer</p>
      <h2>Control-plane DB</h2>
    </div>
    <Database size={18} />
  </div>
  <div className="data-list">
    {dataContracts.map((contract) => (
      <div className="data-row" key={contract.table}>
        <div>
          <strong>{contract.table}</strong>
          <p>{contract.purpose}</p>
        </div>
        <span>{contract.count}</span>
      </div>
    ))}
  </div>
</section>

<section className="panel timeline-panel">
  <div className="panel-heading compact">
    <div>
      <p className="eyebrow">Audit Timeline</p>
      <h2>Evidence trail</h2>
    </div>
    <CheckCircle2 size={18} />
  </div>
  <div className="timeline">
    {governanceTimeline.map((event) => {
      const Icon = event.icon;
      return (
        <div className="timeline-item" key={event.label}>
          <span className="timeline-icon">
            <Icon size={16} />
          </span>
          <div>
            <strong>{event.label}</strong>
            <p>{event.detail}</p>
          </div>
        </div>
      );
    })}
  </div>
</section>
        </aside>
      </section>

      <section className="bottom-grid">
        <section className="panel">
<div className="panel-heading compact">
  <div>
    <p className="eyebrow">Agent Memory / Vector DB</p>
    <h2>Retrieved context</h2>
  </div>
  <Database size={18} />
</div>
<div className="memory-list">
  {memoryContracts.map((memory) => (
    <article className="memory-row" key={memory.source}>
      <div>
        <strong>{memory.namespace}</strong>
        <span>{memory.source}</span>
        <p>{memory.content}</p>
      </div>
      <small>{memory.score}</small>
    </article>
  ))}
</div>
        </section>

        <section className="panel">
<div className="panel-heading compact">
  <div>
    <p className="eyebrow">Data Plane</p>
    <h2>Backend dependencies</h2>
  </div>
  <Database size={18} />
</div>
<div className="data-plane-grid">
  {dataPlaneComponents.map((component) => {
    const Icon = component.icon;
    return (
      <article className="data-plane-card" key={component.name}>
        <Icon size={18} />
        <div>
          <strong>{component.name}</strong>
          <p>{component.role}</p>
          <span>{component.health}</span>
        </div>
      </article>
    );
  })}
</div>
        </section>
      </section>
      <DeveloperConsolePanel apiResult={apiResult} />
      </CollapsibleSection>
    </>
  );
}
