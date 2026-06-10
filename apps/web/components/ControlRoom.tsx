"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ApiHealthGate } from "@/components/control-plane/ApiHealthGate";
import { BuyerModeView } from "@/components/control-plane/BuyerModeView";
import { ControlPlaneOperationsView } from "@/components/control-plane/ControlPlaneOperationsView";
import type { HttpConnectorFormState } from "@/components/control-plane/HttpConnectorRegistrationPanel";
import type { GuidedDemoStep } from "@/components/control-plane/GuidedBuyerDemo";
import { ReferenceExamplesView } from "@/components/examples/ReferenceExamplesView";
import { TopNavigation, type UiMode } from "@/components/navigation/TopNavigation";
import { useToast } from "@/context/ToastContext";
import { useApiHealth } from "@/hooks/useApiHealth";
import { API_BASE_URL, requestJson } from "@/lib/api/client";
import type { BuyerPersona } from "@/lib/controlPlanePersonas";
import type { BuyerModuleStatusMap } from "@/components/control-plane/TopTierProductPanels";
import {
  isAuditVaultPayload,
  isDeveloperQuickstartPayload,
  isGatewayStoryPayload,
  isGovernanceMetricsPayload,
  isIdentityGraphPayload,
  isPolicyStudioPayload,
  isRegulatedOpsDemoPayload
} from "@/lib/api/safe";
import type {
  AgentLifecyclePayload,
  AgentOnboardingPayload,
  AgentRegistryPayload,
  AgentRunPayload,
  AuditVaultPayload,
  AuditPacketPayload,
  ExecutionPayload,
  ConnectorCatalogPayload,
  DeveloperQuickstartPayload,
  DeploymentPosturePayload,
  FlagshipDemoPayload,
  HttpConnectorListPayload,
  HttpConnectorRegisterPayload,
  HttpConnectorTestPayload,
  AuditVerificationPayload,
  FinOpsDashboardPayload,
  GatewayPayload,
  GatewaySdkPayload,
  GatewayStoryPayload,
  McpProxyPayload,
  SignedAuditPayload,
  GoldenEvalPayload,
  IdentityGraphPayload,
  IdentityPosturePayload,
  IncidentTimelinePayload,
  IntegrationsPayload,
  KillSwitchPayload,
  MutableCase,
  PermissionMatrixPayload,
  PlatformActionKey,
  PlatformPosturePayload,
  PolicyReplayPayload,
  PolicySimulationPayload,
  PolicyStudioPayload,
  ReadinessPayload,
  ReleaseGatePayload,
  RegulatedOpsDemoPayload,
  GovernanceMetricsPayload,
  UseCaseRun
} from "@/lib/api/types";
import { cases, policySimulatorScenarios, requestTemplates } from "@/lib/controlPlaneData";
import type { CaseStatus } from "@/lib/controlPlaneData";

const initialGuidedSteps: GuidedDemoStep[] = [
  { id: "metrics", label: "Gateway coverage", detail: "Refresh north-star KPI", status: "pending" },
  { id: "catalog", label: "Connector catalog", detail: "Prove horizontal platform", status: "pending" },
  { id: "gateway", label: "Governance gateway", detail: "Policy + execution token", status: "pending" },
  { id: "hitl", label: "Human approval", detail: "Reviewer issues bound token", status: "pending" },
  { id: "execute", label: "Broker execution", detail: "Side effect only with token", status: "pending" },
  { id: "audit", label: "Signed audit", detail: "Verify tamper-evident packet", status: "pending" }
];

const SENSITIVE_TOKEN_PATTERN = /([A-Za-z0-9_-]{16,})/g;

function redactForExternalShare(value: string): string {
  return value
    .replace(/(execution[_-]?token|authorization|cookie)\s*[:=]\s*[^\s,]+/gi, "$1=[REDACTED]")
    .replace(/\b(case|proposal|request)-?[A-Za-z0-9:_-]*\b/gi, "[ID_REDACTED]")
    .replace(SENSITIVE_TOKEN_PATTERN, (match) => (match.length >= 24 ? "[TOKEN_REDACTED]" : match));
}
const orderedBuyerDemoSteps: GuidedDemoStep["id"][] = [
  "metrics",
  "catalog",
  "gateway",
  "hitl",
  "execute",
  "audit"
];

export function ControlRoom() {
  const { pushToast } = useToast();
  const apiHealth = useApiHealth();
  const [uiMode, setUiMode] = useState<UiMode>("buyer");
  const [buyerPersona, setBuyerPersona] = useState<BuyerPersona>("finops");
  const buyerBootstrapDone = useRef(false);
  const [activeView, setActiveView] = useState<"examples" | "control-plane">("control-plane");
  const [selectedTemplateIndex, setSelectedTemplateIndex] = useState(0);
  const selectedTemplate = requestTemplates[selectedTemplateIndex];
  const [requestText, setRequestText] = useState<string>(selectedTemplate.text);
  const [runHistory, setRunHistory] = useState<UseCaseRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [isRunningUseCases, setIsRunningUseCases] = useState(false);
  const [caseRows, setCaseRows] = useState<MutableCase[]>(cases.map((item) => ({ ...item })));
  const [selectedCaseId, setSelectedCaseId] = useState<string>(cases[0].id);
  const [actionEvents, setActionEvents] = useState([
    "case.orchestrated",
    "proposal.created",
    "evaluation.completed",
    "risk.scored",
    "policy.routed"
  ]);
  const [apiResult, setApiResult] = useState("API console ready. Start FastAPI on :8000, then run a test.");
  const [executionResult, setExecutionResult] = useState<ExecutionPayload | null>(null);
  const [agentRegistryResult, setAgentRegistryResult] = useState<AgentRegistryPayload | null>(null);
  const [policySimulationResult, setPolicySimulationResult] = useState<PolicySimulationPayload | null>(null);
  const [auditPacketResult, setAuditPacketResult] = useState<AuditPacketPayload | null>(null);
  const [identityPostureResult, setIdentityPostureResult] = useState<IdentityPosturePayload | null>(null);
  const [killSwitchResult, setKillSwitchResult] = useState<KillSwitchPayload | null>(null);
  const [goldenEvalResult, setGoldenEvalResult] = useState<GoldenEvalPayload | null>(null);
  const [platformPostureResult, setPlatformPostureResult] = useState<PlatformPosturePayload | null>(null);
  const [gatewayStory, setGatewayStory] = useState<GatewayStoryPayload | null>(null);
  const [developerQuickstart, setDeveloperQuickstart] = useState<DeveloperQuickstartPayload | null>(null);
  const [regulatedOpsDemo, setRegulatedOpsDemo] = useState<RegulatedOpsDemoPayload | null>(null);
  const [policyStudio, setPolicyStudio] = useState<PolicyStudioPayload | null>(null);
  const [identityGraph, setIdentityGraph] = useState<IdentityGraphPayload | null>(null);
  const [auditVault, setAuditVault] = useState<AuditVaultPayload | null>(null);
  const [gatewaySdk, setGatewaySdk] = useState<GatewaySdkPayload | null>(null);
  const [policyReplay, setPolicyReplay] = useState<PolicyReplayPayload | null>(null);
  const [agentLifecycle, setAgentLifecycle] = useState<AgentLifecyclePayload | null>(null);
  const [permissionMatrix, setPermissionMatrix] = useState<PermissionMatrixPayload | null>(null);
  const [releaseGate, setReleaseGate] = useState<ReleaseGatePayload | null>(null);
  const [incidentTimeline, setIncidentTimeline] = useState<IncidentTimelinePayload | null>(null);
  const [deploymentPosture, setDeploymentPosture] = useState<DeploymentPosturePayload | null>(null);
  const [flagshipDemo, setFlagshipDemo] = useState<FlagshipDemoPayload | null>(null);
  const [agentOnboardingResult, setAgentOnboardingResult] = useState<AgentOnboardingPayload | null>(null);
  const [gatewayResult, setGatewayResult] = useState<GatewayPayload | null>(null);
  const [readinessResult, setReadinessResult] = useState<ReadinessPayload | null>(null);
  const [integrationsResult, setIntegrationsResult] = useState<IntegrationsPayload | null>(null);
  const [finopsResult, setFinopsResult] = useState<FinOpsDashboardPayload | null>(null);
  const [connectorCatalog, setConnectorCatalog] = useState<ConnectorCatalogPayload | null>(null);
  const [httpConnectors, setHttpConnectors] = useState<HttpConnectorListPayload | null>(null);
  const [httpConnectorTestResult, setHttpConnectorTestResult] =
    useState<HttpConnectorTestPayload | null>(null);
  const [httpConnectorRegisterResult, setHttpConnectorRegisterResult] =
    useState<HttpConnectorRegisterPayload | null>(null);
  const [mcpResult, setMcpResult] = useState<McpProxyPayload | null>(null);
  const [isLoadingCatalog, setIsLoadingCatalog] = useState(false);
  const [isHttpConnectorBusy, setIsHttpConnectorBusy] = useState(false);
  const [isLoadingMcp, setIsLoadingMcp] = useState(false);
  const [signingPosture, setSigningPosture] = useState<Record<string, unknown> | null>(null);
  const [signedAuditPacket, setSignedAuditPacket] = useState<SignedAuditPayload | null>(null);
  const [auditVerification, setAuditVerification] = useState<AuditVerificationPayload | null>(null);
  const [isLoadingAssurance, setIsLoadingAssurance] = useState(false);
  const [isRunningPlatformDemo, setIsRunningPlatformDemo] = useState(false);
  const [buyerDemoState, setBuyerDemoState] = useState<
    "idle" | "preparing" | "running" | "evidence_ready" | "failed"
  >("idle");
  const [demoTimeline, setDemoTimeline] = useState<string[]>([]);
  const [governanceMetrics, setGovernanceMetrics] = useState<GovernanceMetricsPayload | null>(null);
  const [isLoadingMetrics, setIsLoadingMetrics] = useState(false);
  const [persistenceMode, setPersistenceMode] = useState<string>("sqlite");
  const [guidedDemoSteps, setGuidedDemoSteps] = useState<GuidedDemoStep[]>(initialGuidedSteps);
  const [lastExecutionToken, setLastExecutionToken] = useState<string | null>(null);
  const executionTokenRef = useRef<string | null>(null);
  const [buyerModuleStatus, setBuyerModuleStatus] = useState<BuyerModuleStatusMap>({
    gatewayStory: "idle",
    quickstart: "idle",
    regulatedOps: "idle",
    policyStudio: "idle",
    identityGraph: "idle",
    auditVault: "idle"
  });
  const [buyerModuleErrors, setBuyerModuleErrors] = useState<
    Partial<Record<keyof BuyerModuleStatusMap, string>>
  >({});
  const [platformActionStatus, setPlatformActionStatus] = useState<Record<PlatformActionKey, string>>({
    posture: "Ready to refresh",
    gateway: "Gateway test ready",
    onboarding: "Onboarding score ready",
    readiness: "Readiness score ready",
    integrations: "Integration posture ready"
  });
  const selectedCase = useMemo(
    () => caseRows.find((item) => item.id === selectedCaseId) ?? caseRows[0],
    [caseRows, selectedCaseId]
  );
  const selectedRun = useMemo(
    () => runHistory.find((item) => item.id === selectedRunId) ?? runHistory[0],
    [runHistory, selectedRunId]
  );

  function applyReviewerAction(actionLabel: string) {
    const nextState: Record<string, { status: CaseStatus; decision: string; activeAgent: string }> = {
      Approve: {
        status: "approved",
        decision: "Approved: execution token issued",
        activeAgent: "control"
      },
      Reject: {
        status: "rejected",
        decision: "Rejected: returned to orchestrator",
        activeAgent: "planner"
      },
      "Request Info": {
        status: "info-requested",
        decision: "More evidence requested",
        activeAgent: "evidence"
      },
      Escalate: {
        status: "escalated",
        decision: "Escalated to compliance approver",
        activeAgent: "compliance"
      }
    };
    const update = nextState[actionLabel];
    if (!update) {
      return;
    }
    setCaseRows((current) =>
      current.map((item) => (item.id === selectedCase.id ? { ...item, ...update } : item))
    );
    setActionEvents((current) => [
      `reviewer.${actionLabel.toLowerCase().replace(" ", "_")}`,
      `audit.appended:${selectedCase.id}`,
      ...current.slice(0, 6)
    ]);
  }

  async function callApi<T = unknown>(path: string, init?: RequestInit): Promise<T | null> {
    setApiResult(`Calling ${path} ...`);
    const { payload, consolePayload } = await requestJson<T>(path, init);
    setApiResult(consolePayload);
    return payload;
  }

  async function callApiDetailed<T = unknown>(path: string, init?: RequestInit) {
    setApiResult(`Calling ${path} ...`);
    const result = await requestJson<T>(path, init);
    setApiResult(result.consolePayload);
    return result;
  }

  function setPlatformStatus(action: PlatformActionKey, status: string) {
    setPlatformActionStatus((current) => ({ ...current, [action]: status }));
  }

  function backendErrorStatus() {
    return `Backend unavailable. Start FastAPI at ${API_BASE_URL}.`;
  }

  function buyerModuleFailureMessage(path: string, status?: number) {
    const statusHint = status === 404
      ? " Route not found — stop the old API and run ./scripts/start-api.sh from the repo root."
      : "";
    return `Failed ${path} (${status ?? "no response"}).${statusHint} API base: ${API_BASE_URL}`;
  }

  async function loadBuyerModule<T>(
    key: keyof BuyerModuleStatusMap,
    path: string,
    validate: (value: unknown) => boolean,
    apply: (value: T) => void,
    init?: RequestInit
  ) {
    setBuyerModuleStatus((current) => ({ ...current, [key]: "loading" }));
    setBuyerModuleErrors((current) => {
      const next = { ...current };
      delete next[key];
      return next;
    });
    const result = await callApiDetailed<T>(path, init);
    if (result.payload && validate(result.payload)) {
      apply(result.payload);
      setBuyerModuleStatus((current) => ({ ...current, [key]: "ok" }));
      return;
    }
    setBuyerModuleStatus((current) => ({ ...current, [key]: "error" }));
    setBuyerModuleErrors((current) => ({
      ...current,
      [key]: buyerModuleFailureMessage(path, result.status ?? undefined)
    }));
  }

  function buildAgentRequest(index: number, text = requestText) {
    const template = requestTemplates[index];
    return {
      request_id: `case-ui-${index + 1}`,
      tenant_id: "bank-demo",
      user_id: "portfolio-user",
      text,
      amount_usd: template.amountUsd,
      data_classification: template.classification,
      customer_impact: true
    };
  }

  function caseIdForTemplate(index: number) {
    return `case-ui-${index + 1}`;
  }

  function proposalIdForTemplate(index: number) {
    const template = requestTemplates[index];
    if (template.text.toLowerCase().includes("deletion")) {
      return `${caseIdForTemplate(index)}:data-operation`;
    }
    return `${caseIdForTemplate(index)}:refund`;
  }

  async function runAgentApi() {
    const payload = await callApi<AgentRunPayload>("/api/agents/run", {
      method: "POST",
      body: JSON.stringify(buildAgentRequest(selectedTemplateIndex))
    });
    if (payload) {
      const run: UseCaseRun = {
        id: `${selectedTemplate.label}-${Date.now()}`,
        label: selectedTemplate.label,
        status: "complete",
        requestText,
        payload
      };
      setRunHistory((current) => [run, ...current.filter((item) => item.label !== run.label)]);
      setSelectedRunId(run.id);
    }
  }

  function chooseTemplate(index: number) {
    setSelectedTemplateIndex(index);
    setRequestText(requestTemplates[index].text);
  }

  async function runRagApi() {
    await callApi("/api/rag/search", {
      method: "POST",
      body: JSON.stringify({
        tenant_id: "bank-demo",
        namespace: "refund_policy",
        query: requestText
      })
    });
  }

  async function runUseCase(index: number) {
    const template = requestTemplates[index];
    const id = `${template.label}-${Date.now()}`;
    const running: UseCaseRun = {
      id,
      label: template.label,
      status: "running",
      requestText: template.text
    };
    setRunHistory((current) => [running, ...current.filter((item) => item.label !== template.label)]);
    setSelectedRunId(id);
    const payload = await callApi<AgentRunPayload>("/api/agents/run", {
      method: "POST",
      body: JSON.stringify(buildAgentRequest(index, template.text))
    });
    setRunHistory((current) =>
      current.map((item) =>
        item.id === id
          ? payload
            ? { ...item, status: "complete", payload }
            : { ...item, status: "error", error: "API call failed. Confirm FastAPI is running on :8000." }
          : item
      )
    );
  }

  async function runAllUseCases() {
    setIsRunningUseCases(true);
    for (let index = 0; index < requestTemplates.length; index += 1) {
      await runUseCase(index);
    }
    setIsRunningUseCases(false);
  }

  function openView(view: "examples" | "control-plane") {
    setActiveView(view);
  }

  function focusPlatformCommandCenter() {
    window.setTimeout(() => {
      document.getElementById("command-center")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 80);
  }

  function runWorkflowFromTopNavigation() {
    setUiMode("buyer");
    setActiveView("control-plane");
    void (async () => {
      const ready = await apiHealth.check();
      if (!ready) {
        pushToast("API is unavailable — reconnect backend before running demo", "error");
        return;
      }
      await runBuyerDemo();
    })();
  }

  function runPostureFromTopNavigation() {
    setUiMode("platform");
    setActiveView("control-plane");
    focusPlatformCommandCenter();
    void runPlatformPostureApi();
  }

  function runGatewayFromTopNavigation() {
    setUiMode("platform");
    setActiveView("control-plane");
    focusPlatformCommandCenter();
    void runGatewayApi();
  }

  function runReviewerApi() {
    const caseId = caseIdForTemplate(selectedTemplateIndex);
    const proposalId = proposalIdForTemplate(selectedTemplateIndex);
    void callApi("/api/control-plane/reviewer-action", {
      method: "POST",
      body: JSON.stringify({
        tenant_id: "bank-demo",
        case_id: caseId,
        proposal_id: proposalId,
        reviewer_id: "approver-7",
        action: "approve",
        reason: "Approved from enterprise test UI."
      })
    });
  }

  async function runGovernedExecutionApi() {
    const caseId = caseIdForTemplate(selectedTemplateIndex);
    const proposalId = proposalIdForTemplate(selectedTemplateIndex);
    await callApi<AgentRunPayload>("/api/agents/run", {
      method: "POST",
      body: JSON.stringify(buildAgentRequest(selectedTemplateIndex))
    });
    const review = await callApi<{ execution_token?: string | null }>(
      "/api/control-plane/reviewer-action",
      {
        method: "POST",
        body: JSON.stringify({
          tenant_id: "bank-demo",
          case_id: caseId,
          proposal_id: proposalId,
          reviewer_id: "approver-7",
          action: "approve",
          reason: "Approved from enterprise test UI before broker execution."
        })
      }
    );
    const token = review?.execution_token ?? gatewayResult?.execution_token ?? null;
    const execution = await callApi<ExecutionPayload>("/api/execution/execute", {
      method: "POST",
      headers: token ? { "X-AegisAI-Execution-Token": token } : undefined,
      body: JSON.stringify({
        tenant_id: "bank-demo",
        case_id: caseId,
        proposal_id: proposalId,
        actor_id: "execution-broker"
      })
    });
    if (execution) {
      setExecutionResult(execution);
      setActionEvents((current) => [
        `execution.${execution.status}:${proposalId}`,
        `audit.appended:${caseId}`,
        ...current.slice(0, 6)
      ]);
    }
  }

  async function runAgentRegistryApi() {
    const registry = await callApi<AgentRegistryPayload>("/api/agent-registry");
    if (registry) {
      setAgentRegistryResult(registry);
    }
  }

  async function runPolicySimulatorApi(index = 0) {
    const scenario = policySimulatorScenarios[index];
    const simulation = await callApi<PolicySimulationPayload>("/api/policy/simulate", {
      method: "POST",
      body: JSON.stringify({
        tenant_id: "bank-demo",
        action_type: scenario.actionType,
        target_system: scenario.targetSystem,
        amount_usd: scenario.amountUsd,
        data_classification: scenario.dataClassification,
        reversible: scenario.reversible,
        customer_impact: scenario.customerImpact,
        model_confidence: 0.86,
        grounding_score: 0.9,
        safety_score: 0.95,
        policy_compliance_score: 0.88
      })
    });
    if (simulation) {
      setPolicySimulationResult(simulation);
    }
  }

  async function runAuditPacketApi() {
    await callApi<AgentRunPayload>("/api/agents/run", {
      method: "POST",
      body: JSON.stringify(buildAgentRequest(selectedTemplateIndex))
    });
    const caseId = caseIdForTemplate(selectedTemplateIndex);
    const packet = await callApi<AuditPacketPayload>(`/api/audit-packets/bank-demo/${caseId}.json`);
    if (packet) {
      setAuditPacketResult(packet);
    }
  }

  async function runIdentityPostureApi() {
    const posture = await callApi<IdentityPosturePayload>("/api/identity/posture");
    if (posture) {
      setIdentityPostureResult(posture);
    }
  }

  async function runKillSwitchApi() {
    const result = await callApi<KillSwitchPayload>("/api/kill-switches", {
      method: "POST",
      body: JSON.stringify({
        scope_type: "tool",
        scope_value: "payments.issue_refund",
        reason: "Payment connector anomaly detected by AgentOps.",
        created_by: "security-admin"
      })
    });
    if (result) {
      setKillSwitchResult(result);
    }
  }

  async function runKillSwitchPostureApi() {
    const result = await callApi<KillSwitchPayload>("/api/kill-switches");
    if (result) {
      setKillSwitchResult(result);
    }
  }

  async function runGoldenEvalApi() {
    const result = await callApi<GoldenEvalPayload>("/api/evaluations/golden/run", {
      method: "POST"
    });
    if (result) {
      setGoldenEvalResult(result);
    }
  }

  async function runFinOpsApi() {
    const result = await callApi<FinOpsDashboardPayload>("/api/finops/dashboard");
    if (result) {
      setFinopsResult(result);
      setApiResult(JSON.stringify(result, null, 2));
    }
  }

  function buildHttpConnectorBody(form: HttpConnectorFormState) {
    return {
      display_name: form.displayName,
      base_url: form.baseUrl,
      target_system: form.targetSystem,
      tool_names: form.toolNames
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      health_path: form.healthPath,
      execute_path: form.executePath,
      auth_mode: form.authMode,
      demo_mode: form.demoMode
    };
  }

  function setGuidedStep(id: GuidedDemoStep["id"], status: GuidedDemoStep["status"]) {
    setGuidedDemoSteps((current) =>
      current.map((step) => (step.id === id ? { ...step, status } : step))
    );
  }

  function logDemo(message: string) {
    const timestamp = new Date().toLocaleTimeString();
    setDemoTimeline((current) => [`${timestamp} · ${message}`, ...current].slice(0, 20));
  }

  async function runGovernanceMetricsApi() {
    setIsLoadingMetrics(true);
    const result = await callApi<GovernanceMetricsPayload>("/api/governance/metrics?tenant_id=bank-demo");
    setIsLoadingMetrics(false);
    if (result && isGovernanceMetricsPayload(result)) {
      setGovernanceMetrics(result);
      return result;
    }
    return null;
  }

  async function runHealthPostureApi() {
    const result = await callApi<{
      persistence?: { mode?: string };
      enforcement?: { recommended_persistence?: string };
    }>("/health");
    if (result?.persistence?.mode) {
      setPersistenceMode(String(result.persistence.mode));
    }
  }

  async function runConnectorCatalogApi() {
    setIsLoadingCatalog(true);
    const result = await callApi<ConnectorCatalogPayload>("/api/connectors/catalog");
    setIsLoadingCatalog(false);
    if (result) {
      setConnectorCatalog(result);
      setApiResult(JSON.stringify(result, null, 2));
      return result;
    }
    return null;
  }

  async function runHttpConnectorsApi() {
    setIsHttpConnectorBusy(true);
    const result = await callApi<HttpConnectorListPayload>("/api/connectors/http");
    setIsHttpConnectorBusy(false);
    if (result) {
      setHttpConnectors(result);
      return result;
    }
    return null;
  }

  async function runHttpConnectorTestApi(form: HttpConnectorFormState) {
    setIsHttpConnectorBusy(true);
    const result = await callApi<HttpConnectorTestPayload>("/api/connectors/http/test", {
      method: "POST",
      body: JSON.stringify(buildHttpConnectorBody(form))
    });
    setIsHttpConnectorBusy(false);
    if (result) {
      setHttpConnectorTestResult(result);
      setApiResult(JSON.stringify(result, null, 2));
    }
  }

  async function runHttpConnectorRegisterApi(form: HttpConnectorFormState) {
    setIsHttpConnectorBusy(true);
    const result = await callApi<HttpConnectorRegisterPayload>("/api/connectors/http", {
      method: "POST",
      body: JSON.stringify(buildHttpConnectorBody(form))
    });
    setIsHttpConnectorBusy(false);
    if (result) {
      setHttpConnectorRegisterResult(result);
      setApiResult(JSON.stringify(result, null, 2));
      await runHttpConnectorsApi();
      await runConnectorCatalogApi();
    }
  }

  async function runHttpConnectorDeleteApi(connectorId: string) {
    setIsHttpConnectorBusy(true);
    const result = await callApi<{ status: string }>(`/api/connectors/http/${connectorId}`, {
      method: "DELETE"
    });
    setIsHttpConnectorBusy(false);
    if (result) {
      await runHttpConnectorsApi();
      await runConnectorCatalogApi();
    }
  }

  async function runSigningPostureApi() {
    const result = await callApi<Record<string, unknown>>("/api/audit-signing/posture");
    if (result) {
      setSigningPosture(result);
    }
  }

  async function runDownloadSignedAuditApi() {
    setIsLoadingAssurance(true);
    const caseId = selectedCaseId;
    const result = await callApi<SignedAuditPayload>(
      `/api/audit-packets/bank-demo/${caseId}/signed.json`
    );
    setIsLoadingAssurance(false);
    if (result) {
      setSignedAuditPacket(result);
      setAuditPacketResult(result as unknown as AuditPacketPayload);
      setApiResult(JSON.stringify(result, null, 2));
      return result;
    }
    return null;
  }

  async function runVerifySignedAuditApi() {
    if (!signedAuditPacket) {
      return;
    }
    setIsLoadingAssurance(true);
    const result = await callApi<{ verification: AuditVerificationPayload }>(
      "/api/audit-packets/verify",
      {
        method: "POST",
        body: JSON.stringify({ signed_packet: signedAuditPacket })
      }
    );
    setIsLoadingAssurance(false);
    if (result?.verification) {
      setAuditVerification(result.verification);
      setApiResult(JSON.stringify(result, null, 2));
      return result.verification;
    }
    return null;
  }

  async function runMcpProxyApi() {
    setIsLoadingMcp(true);
    const result = await callApi<McpProxyPayload>("/api/mcp/tool-call", {
      method: "POST",
      body: JSON.stringify({
        mcp_server: "github",
        tool_name: "create_issue",
        action_type: "create_issue",
        target_system: "mcp",
        arguments: { repo: "aegisai", title: "Governed MCP invocation" }
      })
    });
    setIsLoadingMcp(false);
    if (result) {
      setMcpResult(result);
      setApiResult(JSON.stringify(result, null, 2));
      pushToast("MCP tool call governed through gateway", "success");
    } else {
      pushToast("MCP proxy call failed — check API on :8000", "error");
    }
  }

  async function runPlatformPostureApi() {
    setPlatformStatus("posture", "Loading executive posture...");
    const result = await callApi<PlatformPosturePayload>("/api/platform/posture");
    if (result) {
      setPlatformPostureResult(result);
      setPlatformStatus("posture", `${result.posture_score}/100 governance score`);
      pushToast(`Executive posture refreshed: ${result.posture_score}/100`, "success");
    } else {
      setPlatformStatus("posture", backendErrorStatus());
      pushToast("Posture action failed — check FastAPI on :8000", "error");
    }
  }

  async function runGatewayStoryApi() {
    await loadBuyerModule(
      "gatewayStory",
      "/api/platform/gateway-story",
      isGatewayStoryPayload,
      setGatewayStory
    );
  }

  async function runDeveloperQuickstartApi() {
    await loadBuyerModule(
      "quickstart",
      "/api/platform/developer-quickstart",
      isDeveloperQuickstartPayload,
      setDeveloperQuickstart
    );
  }

  async function runRegulatedOpsDemoApi() {
    await loadBuyerModule(
      "regulatedOps",
      "/api/product/regulatory-customer-ops-demo",
      isRegulatedOpsDemoPayload,
      setRegulatedOpsDemo
    );
  }

  function gatewayToolRequestBody() {
    return {
      tenant_id: "bank-demo",
      agent_id: "agent-refund",
      principal_id: "execution-broker",
      tool_name: "payments.issue_refund",
      action_type: "issue_refund",
      target_system: "payments",
      amount_usd: 2500,
      data_classification: "confidential",
      reversible: true,
      customer_impact: true,
      grounding_score: 0.9,
      safety_score: 0.95,
      policy_compliance_score: 0.88
    };
  }

  async function runPolicyStudioApi() {
    await loadBuyerModule(
      "policyStudio",
      "/api/policy/studio/dry-run",
      isPolicyStudioPayload,
      setPolicyStudio,
      {
        method: "POST",
        body: JSON.stringify(gatewayToolRequestBody())
      }
    );
  }

  async function runIdentityGraphApi() {
    await loadBuyerModule(
      "identityGraph",
      "/api/identity/graph",
      isIdentityGraphPayload,
      setIdentityGraph
    );
  }

  async function runAuditVaultApi() {
    await loadBuyerModule(
      "auditVault",
      "/api/audit-vault/posture",
      isAuditVaultPayload,
      setAuditVault
    );
  }

  async function runGatewaySdkApi() {
    const result = await callApi<GatewaySdkPayload>("/api/platform/gateway-sdks");
    if (result) {
      setGatewaySdk(result);
      return result;
    }
    return null;
  }

  async function runPolicyReplayApi() {
    const result = await callApi<PolicyReplayPayload>("/api/policy/replay", {
      method: "POST",
      body: JSON.stringify(gatewayToolRequestBody())
    });
    if (result) {
      setPolicyReplay(result);
      return result;
    }
    return null;
  }

  async function runAgentLifecycleApi() {
    const result = await callApi<AgentLifecyclePayload>("/api/agent-registry/lifecycle");
    if (result) {
      setAgentLifecycle(result);
    }
  }

  async function runPermissionMatrixApi() {
    const result = await callApi<PermissionMatrixPayload>("/api/identity/permission-matrix");
    if (result) {
      setPermissionMatrix(result);
      return result;
    }
    return null;
  }

  async function runReleaseGateApi() {
    const result = await callApi<ReleaseGatePayload>("/api/release-gates/promote", {
      method: "POST",
      body: JSON.stringify({
        agent_id: "agent-refund",
        release_version: "refund-agent-2026.05.26",
        requested_by: "ai-platform-lead"
      })
    });
    if (result) {
      setReleaseGate(result);
    }
  }

  async function runIncidentTimelineApi() {
    const result = await callApi<IncidentTimelinePayload>("/api/incidents/timeline");
    if (result) {
      setIncidentTimeline(result);
    }
  }

  async function runDeploymentPostureApi() {
    const result = await callApi<DeploymentPosturePayload>("/api/platform/deployment-posture");
    if (result) {
      setDeploymentPosture(result);
    }
  }

  async function runFlagshipDemoApi() {
    const result = await callApi<FlagshipDemoPayload>("/api/demo/flagship-flow");
    if (result) {
      setFlagshipDemo(result);
      return result;
    }
    return null;
  }

  async function preloadBuyerModules() {
    await Promise.all([
      runGatewayStoryApi(),
      runDeveloperQuickstartApi(),
      runRegulatedOpsDemoApi(),
      runPolicyStudioApi(),
      runIdentityGraphApi(),
      runAuditVaultApi(),
      runGatewaySdkApi(),
      runPolicyReplayApi(),
      runAgentLifecycleApi(),
      runPermissionMatrixApi(),
      runReleaseGateApi(),
      runIncidentTimelineApi(),
      runDeploymentPostureApi(),
      runFlagshipDemoApi()
    ]);
  }

  async function runAgentOnboardingApi() {
    setPlatformStatus("onboarding", "Scoring new agent controls...");
    const result = await callApi<AgentOnboardingPayload>("/api/platform/onboard-agent", {
      method: "POST",
      body: JSON.stringify({
        agent_id: "agent-salesforce-case-assistant",
        name: "Salesforce Case Assistant",
        owner: "Customer Operations",
        business_domain: "Customer Support",
        risk_tier: "high",
        autonomy_level: 3,
        tools: ["crm.update_case", "rag.search_policy_memory"],
        data_classes: ["internal", "confidential"],
        eval_suite_attached: true,
        policy_attached: true,
        observability_enabled: true,
        kill_switch_enabled: false
      })
    });
    if (result) {
      setAgentOnboardingResult(result);
      setPlatformStatus("onboarding", `${result.launch_decision} · ${result.readiness_score}/100`);
    } else {
      setPlatformStatus("onboarding", backendErrorStatus());
    }
  }

  async function runGatewayApi() {
    setPlatformStatus("gateway", "Checking policy, identity, eval, and HITL gates...");
    const result = await callApi<GatewayPayload>("/api/gateway/tool-request", {
      method: "POST",
      body: JSON.stringify(gatewayToolRequestBody())
    });
    if (result) {
      setGatewayResult(result);
      setPlatformStatus("gateway", `${result.gateway_decision} · ${result.tool_name}`);
      pushToast(`Gateway tested: ${result.gateway_decision}`, "success");
      return result;
    } else {
      setPlatformStatus("gateway", backendErrorStatus());
      pushToast("Gateway action failed — check FastAPI on :8000", "error");
    }
    return null;
  }

  async function runReadinessApi(agentId = "agent-refund") {
    setPlatformStatus("readiness", `Scoring ${agentId}...`);
    const result = await callApi<ReadinessPayload>(`/api/platform/readiness/${agentId}`);
    if (result) {
      setReadinessResult(result);
      setPlatformStatus("readiness", `${result.launch_decision} · ${result.readiness_score}/100`);
    } else {
      setPlatformStatus("readiness", backendErrorStatus());
    }
  }

  async function runIntegrationsApi() {
    setPlatformStatus("integrations", "Loading integration posture...");
    const result = await callApi<IntegrationsPayload>("/api/platform/integrations");
    if (result) {
      setIntegrationsResult(result);
      setPlatformStatus("integrations", `${result.agent_frameworks.length} agent frameworks`);
    } else {
      setPlatformStatus("integrations", backendErrorStatus());
    }
  }

  function downloadAuditPdf() {
    const caseId = caseIdForTemplate(selectedTemplateIndex);
    window.open(`${API_BASE_URL}/api/audit-packets/bank-demo/${caseId}.pdf`, "_blank");
    pushToast("Opening audit PDF in new tab", "success");
  }

  async function runBuyerDemoStep(stepId: GuidedDemoStep["id"]) {
    setGuidedStep(stepId, "active");
    logDemo(`Started ${stepId}`);
    try {
      if (stepId === "metrics") {
        const [metrics, flagship, sdk] = await Promise.all([
          runGovernanceMetricsApi(),
          runFlagshipDemoApi(),
          runGatewaySdkApi()
        ]);
        if (!metrics || !flagship || !sdk) {
          throw new Error("Failed to refresh buyer proof context");
        }
      }

      if (stepId === "catalog") {
        const [catalog, connectors] = await Promise.all([
          runConnectorCatalogApi(),
          runHttpConnectorsApi()
        ]);
        if (!catalog || !connectors) {
          throw new Error("Failed to load connector inventory");
        }
      }

      if (stepId === "gateway") {
        const [gateway, replay, matrix] = await Promise.all([
          runGatewayApi(),
          runPolicyReplayApi(),
          runPermissionMatrixApi()
        ]);
        if (!gateway || !replay || !matrix) {
          throw new Error("Failed to prove gateway decision path");
        }
      }

      if (stepId === "hitl") {
        await runAgentApi();
        const caseId = caseIdForTemplate(selectedTemplateIndex);
        const proposalId = proposalIdForTemplate(selectedTemplateIndex);
        const review = await callApi<{ execution_token?: string | null }>(
          "/api/control-plane/reviewer-action",
          {
            method: "POST",
            body: JSON.stringify({
              tenant_id: "bank-demo",
              case_id: caseId,
              proposal_id: proposalId,
              reviewer_id: "approver-7",
              action: "approve",
              reason: "Buyer demo — approval issues execution token."
            })
          }
        );
        const approvalToken = review?.execution_token ?? null;
        setLastExecutionToken(approvalToken);
        executionTokenRef.current = approvalToken;
        if (!approvalToken) {
          throw new Error("No execution token from HITL approval");
        }
      }

      if (stepId === "execute") {
        const caseId = caseIdForTemplate(selectedTemplateIndex);
        const proposalId = proposalIdForTemplate(selectedTemplateIndex);
        const token = executionTokenRef.current ?? gatewayResult?.execution_token ?? lastExecutionToken;
        const execution = await callApi<ExecutionPayload>("/api/execution/execute", {
          method: "POST",
          headers: token ? { "X-AegisAI-Execution-Token": token } : undefined,
          body: JSON.stringify({
            tenant_id: "bank-demo",
            case_id: caseId,
            proposal_id: proposalId,
            actor_id: "execution-broker"
          })
        });
        if (!execution) {
          throw new Error("Execution broker call failed");
        }
        setExecutionResult(execution);
        await runGovernanceMetricsApi();
      }

      if (stepId === "audit") {
        const signed = await runDownloadSignedAuditApi();
        const verification = await runVerifySignedAuditApi();
        if (!signed || !verification) {
          throw new Error("Signed audit verification failed");
        }
        await runPlatformPostureApi();
        await runReleaseGateApi();
        await runIncidentTimelineApi();
        await runDeploymentPostureApi();
      }

      setGuidedStep(stepId, "done");
      logDemo(`Completed ${stepId}`);
      return true;
    } catch (error) {
      setGuidedStep(stepId, "error");
      const message = error instanceof Error ? error.message : `Step ${stepId} failed`;
      pushToast(message, "error");
      logDemo(`Failed ${stepId}: ${message}`);
      return false;
    }
  }

  async function runBuyerDemo() {
    setIsRunningPlatformDemo(true);
    setBuyerDemoState("preparing");
    setDemoTimeline([]);
    logDemo("Buyer demo initialized");
    setGuidedDemoSteps(initialGuidedSteps.map((step, index) => ({
      ...step,
      status: index === 0 ? "active" : "pending"
    })));
    setBuyerDemoState("running");

    for (const stepId of orderedBuyerDemoSteps) {
      const ok = await runBuyerDemoStep(stepId);
      if (!ok) {
        setBuyerDemoState("failed");
        setIsRunningPlatformDemo(false);
        logDemo(`Workflow stopped at ${stepId}`);
        return;
      }
    }

    setBuyerDemoState("evidence_ready");
    setIsRunningPlatformDemo(false);
    logDemo("Workflow completed with signed evidence");
    pushToast("Buyer demo completed — gateway, HITL, execution, and audit verified", "success");
  }

  async function retryBuyerDemoStep(stepId: GuidedDemoStep["id"]) {
    if (isRunningPlatformDemo) {
      return;
    }
    setIsRunningPlatformDemo(true);
    setBuyerDemoState("running");
    logDemo(`Retry initiated from ${stepId}`);
    const startIndex = orderedBuyerDemoSteps.indexOf(stepId);
    let ok = true;
    for (let index = startIndex; index < orderedBuyerDemoSteps.length; index += 1) {
      const next = orderedBuyerDemoSteps[index];
      ok = await runBuyerDemoStep(next);
      if (!ok) {
        break;
      }
    }
    setIsRunningPlatformDemo(false);
    setBuyerDemoState(ok ? "evidence_ready" : "failed");
    if (ok) {
      logDemo("Retry sequence finished successfully");
      pushToast("Recovered workflow and completed remaining steps", "success");
    }
  }

  function copyBuyerDemoReport() {
    const redactedTimeline = demoTimeline.map((entry) => redactForExternalShare(entry));
    const lines = [
      "AegisAI Buyer Demo Incident Report (Redacted)",
      `State: ${buyerDemoState}`,
      "",
      "Step Status",
      ...guidedDemoSteps.map((step) => `- ${step.label}: ${step.status}`),
      "",
      "Timeline",
      ...(redactedTimeline.length > 0
        ? redactedTimeline.map((entry) => `- ${entry}`)
        : ["- No events recorded"]),
      "",
      "Redaction: enabled by default for external sharing"
    ];
    const report = lines.join("\n");
    navigator.clipboard
      .writeText(report)
      .then(() => {
        pushToast("Incident report copied to clipboard", "success");
      })
      .catch(() => {
        pushToast("Clipboard copy failed", "error");
      });
  }

  function copyBuyerDemoJsonReport() {
    const redactedTimeline = demoTimeline.map((entry) => redactForExternalShare(entry));
    const report = {
      report_type: "aegisai_buyer_demo_incident",
      redacted: true,
      state: buyerDemoState,
      generated_at: new Date().toISOString(),
      steps: guidedDemoSteps.map((step) => ({
        id: step.id,
        label: step.label,
        detail: step.detail,
        status: step.status
      })),
      timeline: redactedTimeline
    };
    navigator.clipboard
      .writeText(JSON.stringify(report, null, 2))
      .then(() => {
        pushToast("JSON incident report copied", "success");
      })
      .catch(() => {
        pushToast("Clipboard copy failed", "error");
      });
  }

  function downloadBuyerDemoJsonReport() {
    const redactedTimeline = demoTimeline.map((entry) => redactForExternalShare(entry));
    const report = {
      report_type: "aegisai_buyer_demo_incident",
      redacted: true,
      state: buyerDemoState,
      generated_at: new Date().toISOString(),
      steps: guidedDemoSteps.map((step) => ({
        id: step.id,
        label: step.label,
        detail: step.detail,
        status: step.status
      })),
      timeline: redactedTimeline
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    anchor.href = url;
    anchor.download = `aegisai-demo-incident-${timestamp}.json`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
    pushToast("JSON incident report downloaded", "success");
  }

  useEffect(() => {
    if (activeView !== "control-plane" || uiMode !== "buyer" || !apiHealth.isReady) {
      return;
    }
    if (buyerBootstrapDone.current) {
      return;
    }
    buyerBootstrapDone.current = true;
    void (async () => {
      await Promise.all([
        runGovernanceMetricsApi(),
        runFlagshipDemoApi(),
        runRegulatedOpsDemoApi(),
        runPolicyStudioApi(),
        runIdentityGraphApi(),
        runPolicyReplayApi(),
        runConnectorCatalogApi(),
        runFinOpsApi(),
        runGatewaySdkApi()
      ]);
      await runBuyerDemo();
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- bootstrap buyer demo once when API is healthy
  }, [activeView, uiMode, apiHealth.isReady]);

  useEffect(() => {
    if (activeView === "control-plane" && uiMode === "platform" && connectorCatalog === null && !isLoadingCatalog) {
      void runConnectorCatalogApi();
      void runHttpConnectorsApi();
      void runGovernanceMetricsApi();
      void runHealthPostureApi();
    }
    if (activeView === "control-plane" && uiMode === "platform" && signingPosture === null) {
      void runSigningPostureApi();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- hydrate platform modules only on mode/view transition
  }, [activeView, uiMode]);

  return (
    <main className="shell">
      <TopNavigation
        activeView={activeView}
        uiMode={uiMode}
        setUiMode={setUiMode}
        openView={openView}
        runBuyerDemo={runWorkflowFromTopNavigation}
        isRunningPlatformDemo={isRunningPlatformDemo}
        apiHealthy={apiHealth.isReady}
        onRecheckApi={() => void apiHealth.check()}
        platformActionStatus={platformActionStatus}
        runPlatformPostureApi={runPostureFromTopNavigation}
        runGatewayApi={runGatewayFromTopNavigation}
      />

      {activeView === "examples" ? (
        <ReferenceExamplesView
          requestText={requestText}
          setRequestText={setRequestText}
          selectedTemplateIndex={selectedTemplateIndex}
          selectedTemplate={selectedTemplate}
          chooseTemplate={chooseTemplate}
          runAgentApi={runAgentApi}
          runAllUseCases={runAllUseCases}
          isRunningUseCases={isRunningUseCases}
          runRagApi={runRagApi}
          runGovernedExecutionApi={runGovernedExecutionApi}
          runAgentRegistryApi={runAgentRegistryApi}
          agentRegistryResult={agentRegistryResult}
          runPolicySimulatorApi={runPolicySimulatorApi}
          policySimulationResult={policySimulationResult}
          runAuditPacketApi={runAuditPacketApi}
          callApi={callApi}
          caseIdForTemplate={caseIdForTemplate}
          auditPacketResult={auditPacketResult}
          runIdentityPostureApi={runIdentityPostureApi}
          identityPostureResult={identityPostureResult}
          runKillSwitchApi={runKillSwitchApi}
          runKillSwitchPostureApi={runKillSwitchPostureApi}
          killSwitchResult={killSwitchResult}
          runGoldenEvalApi={runGoldenEvalApi}
          goldenEvalResult={goldenEvalResult}
          runUseCase={runUseCase}
          executionResult={executionResult}
          runHistory={runHistory}
          selectedRun={selectedRun}
          setSelectedRunId={setSelectedRunId}
          apiResult={apiResult}
          openControlPlane={() => {
            setUiMode("buyer");
            openView("control-plane");
          }}
        />
      ) : uiMode === "buyer" ? (
        <ApiHealthGate
          status={apiHealth.status}
          detail={apiHealth.detail}
          onRecheck={() => void apiHealth.check()}
        >
          <BuyerModeView
            persona={buyerPersona}
            setPersona={setBuyerPersona}
            persistenceMode={persistenceMode}
            governanceMetrics={governanceMetrics}
            isLoadingMetrics={isLoadingMetrics}
            runGovernanceMetricsApi={runGovernanceMetricsApi}
            flagshipDemo={flagshipDemo}
            guidedDemoSteps={guidedDemoSteps}
            demoTimeline={demoTimeline}
            buyerDemoState={buyerDemoState}
            isRunningPlatformDemo={isRunningPlatformDemo}
            runBuyerDemo={runBuyerDemo}
            retryBuyerDemoStep={retryBuyerDemoStep}
            copyBuyerDemoReport={copyBuyerDemoReport}
            copyBuyerDemoJsonReport={copyBuyerDemoJsonReport}
            downloadBuyerDemoJsonReport={downloadBuyerDemoJsonReport}
            gatewayResult={gatewayResult}
            executionResult={executionResult}
            auditVerification={auditVerification}
            regulatedOpsDemo={regulatedOpsDemo}
            policyStudio={policyStudio}
            policyReplay={policyReplay}
            identityGraph={identityGraph}
            connectorCatalog={connectorCatalog}
            isLoadingCatalog={isLoadingCatalog}
            runConnectorCatalogApi={runConnectorCatalogApi}
            finopsResult={finopsResult}
            gatewaySdk={gatewaySdk}
            mcpResult={mcpResult}
            runMcpProxyApi={runMcpProxyApi}
            isLoadingMcp={isLoadingMcp}
            onDownloadAuditPdf={downloadAuditPdf}
            openProofWorkloads={() => openView("examples")}
          />
        </ApiHealthGate>
      ) : (
        <ControlPlaneOperationsView
          surfaceMode="platform"
          isRunningPlatformDemo={isRunningPlatformDemo}
          governanceMetrics={governanceMetrics}
          runGovernanceMetricsApi={runGovernanceMetricsApi}
          isLoadingMetrics={isLoadingMetrics}
          persistenceMode={persistenceMode}
          guidedDemoSteps={guidedDemoSteps}
          demoTimeline={demoTimeline}
          buyerDemoState={buyerDemoState}
          runBuyerDemo={runBuyerDemo}
          retryBuyerDemoStep={retryBuyerDemoStep}
          copyBuyerDemoReport={copyBuyerDemoReport}
          copyBuyerDemoJsonReport={copyBuyerDemoJsonReport}
          downloadBuyerDemoJsonReport={downloadBuyerDemoJsonReport}
          platformActionStatus={platformActionStatus}
          platformPostureResult={platformPostureResult}
          gatewayStory={gatewayStory}
          developerQuickstart={developerQuickstart}
          regulatedOpsDemo={regulatedOpsDemo}
          policyStudio={policyStudio}
          identityGraph={identityGraph}
          auditVault={auditVault}
          gatewaySdk={gatewaySdk}
          policyReplay={policyReplay}
          agentLifecycle={agentLifecycle}
          permissionMatrix={permissionMatrix}
          releaseGate={releaseGate}
          incidentTimeline={incidentTimeline}
          deploymentPosture={deploymentPosture}
          flagshipDemo={flagshipDemo}
          gatewayResult={gatewayResult}
          agentOnboardingResult={agentOnboardingResult}
          readinessResult={readinessResult}
          integrationsResult={integrationsResult}
          finopsResult={finopsResult}
          runFinOpsApi={runFinOpsApi}
          connectorCatalog={connectorCatalog}
          runConnectorCatalogApi={runConnectorCatalogApi}
          isLoadingCatalog={isLoadingCatalog}
          httpConnectors={httpConnectors}
          httpConnectorTestResult={httpConnectorTestResult}
          httpConnectorRegisterResult={httpConnectorRegisterResult}
          isHttpConnectorBusy={isHttpConnectorBusy}
          runHttpConnectorsApi={runHttpConnectorsApi}
          runHttpConnectorTestApi={runHttpConnectorTestApi}
          runHttpConnectorRegisterApi={runHttpConnectorRegisterApi}
          runHttpConnectorDeleteApi={runHttpConnectorDeleteApi}
          mcpResult={mcpResult}
          runMcpProxyApi={runMcpProxyApi}
          isLoadingMcp={isLoadingMcp}
          signingPosture={signingPosture}
          signedAuditPacket={signedAuditPacket}
          auditVerification={auditVerification}
          onLoadSigningPosture={runSigningPostureApi}
          onDownloadSignedAudit={runDownloadSignedAuditApi}
          onVerifySignedAudit={runVerifySignedAuditApi}
          isLoadingAssurance={isLoadingAssurance}
          caseRows={caseRows}
          selectedCase={selectedCase}
          selectedCaseId={selectedCaseId}
          actionEvents={actionEvents}
          apiResult={apiResult}
          openView={openView}
          runPlatformPostureApi={runPlatformPostureApi}
          runGatewayStoryApi={runGatewayStoryApi}
          runDeveloperQuickstartApi={runDeveloperQuickstartApi}
          runRegulatedOpsDemoApi={runRegulatedOpsDemoApi}
          runPolicyStudioApi={runPolicyStudioApi}
          runIdentityGraphApi={runIdentityGraphApi}
          runAuditVaultApi={runAuditVaultApi}
          runGatewaySdkApi={runGatewaySdkApi}
          runPolicyReplayApi={runPolicyReplayApi}
          runAgentLifecycleApi={runAgentLifecycleApi}
          runPermissionMatrixApi={runPermissionMatrixApi}
          runReleaseGateApi={runReleaseGateApi}
          runIncidentTimelineApi={runIncidentTimelineApi}
          runDeploymentPostureApi={runDeploymentPostureApi}
          runFlagshipDemoApi={runFlagshipDemoApi}
          buyerModuleStatus={buyerModuleStatus}
          buyerModuleErrors={buyerModuleErrors}
          runGatewayApi={runGatewayApi}
          runAgentOnboardingApi={runAgentOnboardingApi}
          runReadinessApi={runReadinessApi}
          runIntegrationsApi={runIntegrationsApi}
          onRefreshObservability={runHealthPostureApi}
          runGovernedExecutionApi={runGovernedExecutionApi}
          callApi={callApi}
          runAgentApi={runAgentApi}
          runRagApi={runRagApi}
          runReviewerApi={runReviewerApi}
          setSelectedCaseId={setSelectedCaseId}
          applyReviewerAction={applyReviewerAction}
        />
      )}
    </main>
  );
}
