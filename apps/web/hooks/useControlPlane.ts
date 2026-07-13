"use client";

import { useCallback, useEffect, useState } from "react";
import { useToast } from "@/context/ToastContext";
import { useApiHealth } from "@/hooks/useApiHealth";
import type { DashboardModule } from "@/components/control-plane/GovernanceDashboard";
import { API_BASE_URL, requestJson } from "@/lib/api/client";
import { isGovernanceMetricsPayload } from "@/lib/api/safe";
import type {
  AgentCloudGovernPayload,
  AgentCloudMonitorPayload,
  AgentCloudPosturePayload,
  AgentCloudUndoPayload,
  AgentCloudUndoablePayload,
  AgentRegistryPayload,
  DashboardSummaryPayload,
  FinOpsDashboardPayload,
  GovernanceMetricsPayload,
  IncidentTimelinePayload,
  OrchestratorRegistryPayload,
  OrchestratorRunPayload
} from "@/lib/api/types";

export function useControlPlane() {
  const { pushToast } = useToast();
  const apiHealth = useApiHealth();
  const [activeModule, setActiveModule] = useState<DashboardModule>("dashboard");
  const [dashboardSummary, setDashboardSummary] = useState<DashboardSummaryPayload | null>(null);
  const [isLoadingDashboard, setIsLoadingDashboard] = useState(false);
  const [governanceMetrics, setGovernanceMetrics] = useState<GovernanceMetricsPayload | null>(null);
  const [finopsResult, setFinopsResult] = useState<FinOpsDashboardPayload | null>(null);
  const [agentRegistry, setAgentRegistry] = useState<AgentRegistryPayload | null>(null);
  const [orchestratorRegistry, setOrchestratorRegistry] = useState<OrchestratorRegistryPayload | null>(null);
  const [contentRuns, setContentRuns] = useState<OrchestratorRunPayload | null>(null);
  const [stockRuns, setStockRuns] = useState<OrchestratorRunPayload | null>(null);
  const [websiteRuns, setWebsiteRuns] = useState<OrchestratorRunPayload | null>(null);
  const [isLoadingOrchestrators, setIsLoadingOrchestrators] = useState(false);
  const [agentCloudPosture, setAgentCloudPosture] = useState<AgentCloudPosturePayload | null>(null);
  const [agentCloudMonitor, setAgentCloudMonitor] = useState<AgentCloudMonitorPayload | null>(null);
  const [agentCloudGovern, setAgentCloudGovern] = useState<AgentCloudGovernPayload | null>(null);
  const [agentCloudUndoable, setAgentCloudUndoable] = useState<AgentCloudUndoablePayload | null>(null);
  const [agentCloudUndoResult, setAgentCloudUndoResult] = useState<AgentCloudUndoPayload | null>(null);
  const [isLoadingAgentCloud, setIsLoadingAgentCloud] = useState(false);
  const [incidentTimeline, setIncidentTimeline] = useState<IncidentTimelinePayload | null>(null);
  const [persistenceMode, setPersistenceMode] = useState("sqlite");

  const callApi = useCallback(async <T,>(path: string, init?: RequestInit): Promise<T | null> => {
    const { payload } = await requestJson<T>(path, init);
    return payload;
  }, []);

  const refreshDashboard = useCallback(async () => {
    setIsLoadingDashboard(true);
    const result = await callApi<DashboardSummaryPayload>("/api/dashboard/summary");
    setIsLoadingDashboard(false);
    if (result) setDashboardSummary(result);
    return result;
  }, [callApi]);

  const refreshMetrics = useCallback(async () => {
    const result = await callApi<GovernanceMetricsPayload>("/api/governance/metrics?tenant_id=bank-demo");
    if (result && isGovernanceMetricsPayload(result)) setGovernanceMetrics(result);
    return result;
  }, [callApi]);

  const refreshFinops = useCallback(async () => {
    const result = await callApi<FinOpsDashboardPayload>("/api/finops/dashboard");
    if (result) setFinopsResult(result);
    return result;
  }, [callApi]);

  const refreshAgents = useCallback(async () => {
    const result = await callApi<AgentRegistryPayload>("/api/agent-registry");
    if (result) setAgentRegistry(result);
    return result;
  }, [callApi]);

  const loadAgentCloud = useCallback(async () => {
    setIsLoadingAgentCloud(true);
    const [posture, monitor, govern, undoable] = await Promise.all([
      callApi<AgentCloudPosturePayload>("/api/agent-cloud/posture"),
      callApi<AgentCloudMonitorPayload>("/api/agent-cloud/monitor"),
      callApi<AgentCloudGovernPayload>("/api/agent-cloud/govern"),
      callApi<AgentCloudUndoablePayload>("/api/agent-cloud/undoable")
    ]);
    setIsLoadingAgentCloud(false);
    if (posture) setAgentCloudPosture(posture);
    if (monitor) setAgentCloudMonitor(monitor);
    if (govern) setAgentCloudGovern(govern);
    if (undoable) setAgentCloudUndoable(undoable);
  }, [callApi]);

  const refreshOrchestrators = useCallback(async () => {
    setIsLoadingOrchestrators(true);
    const [registry, content, stock, website] = await Promise.all([
      callApi<OrchestratorRegistryPayload>("/api/orchestrators"),
      callApi<OrchestratorRunPayload>("/api/orchestrators/ai-content/runs"),
      callApi<OrchestratorRunPayload>("/api/orchestrators/stock-research/runs"),
      callApi<OrchestratorRunPayload>("/api/orchestrators/website-build/runs")
    ]);
    setIsLoadingOrchestrators(false);
    if (registry) setOrchestratorRegistry(registry);
    if (content) setContentRuns(content);
    if (stock) setStockRuns(stock);
    if (website) setWebsiteRuns(website);
  }, [callApi]);

  const refreshIncidents = useCallback(async () => {
    const result = await callApi<IncidentTimelinePayload>("/api/incidents/timeline");
    if (result) setIncidentTimeline(result);
    return result;
  }, [callApi]);

  const undoAgentAction = useCallback(
    async (executionId: string) => {
      setIsLoadingAgentCloud(true);
      const result = await callApi<AgentCloudUndoPayload>("/api/agent-cloud/undo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tenant_id: "bank-demo",
          execution_id: executionId,
          reason: "Undo from control plane"
        })
      });
      setIsLoadingAgentCloud(false);
      if (result) {
        setAgentCloudUndoResult(result);
        pushToast(result.status === "rolled_back" ? "Action rolled back" : result.message, "info");
        await loadAgentCloud();
      }
    },
    [callApi, loadAgentCloud, pushToast]
  );

  const runContentPipeline = useCallback(async () => {
    setIsLoadingOrchestrators(true);
    await callApi("/api/orchestrators/ai-content/run", { method: "POST" });
    setIsLoadingOrchestrators(false);
    pushToast("AI Content Pipeline completed", "success");
    await refreshOrchestrators();
  }, [callApi, pushToast, refreshOrchestrators]);

  const runStockPipeline = useCallback(async () => {
    setIsLoadingOrchestrators(true);
    await callApi("/api/orchestrators/stock-research/run", { method: "POST" });
    setIsLoadingOrchestrators(false);
    pushToast("Stock briefing generated", "success");
    await refreshOrchestrators();
  }, [callApi, pushToast, refreshOrchestrators]);

  const runWebsitePipeline = useCallback(
    async (requirement?: string) => {
      setIsLoadingOrchestrators(true);
      const query = requirement ? `?requirement=${encodeURIComponent(requirement)}` : "";
      await callApi(`/api/orchestrators/website-build/run${query}`, { method: "POST" });
      setIsLoadingOrchestrators(false);
      pushToast("Website Build Pipeline completed", "success");
      await refreshOrchestrators();
      await refreshAgents();
    },
    [callApi, pushToast, refreshAgents, refreshOrchestrators]
  );

  const loadModule = useCallback(
    async (module: DashboardModule) => {
      if (
        module === "dashboard" ||
        module === "monitor" ||
        module === "agents" ||
        module === "governance"
      ) {
        await loadAgentCloud();
      }
      if (module === "gateway" || module === "governance") await refreshMetrics();
      if (module === "finops") await refreshFinops();
      if (module === "incidents" || module === "hitl") await refreshIncidents();
      if (module === "orchestrators") {
        await refreshOrchestrators();
        await refreshAgents();
      }
      if (module === "onboard" || module === "gateway" || module === "llm-plane") await refreshAgents();
    },
    [loadAgentCloud, refreshAgents, refreshFinops, refreshIncidents, refreshMetrics, refreshOrchestrators]
  );

  const selectModule = useCallback(
    (module: DashboardModule) => {
      setActiveModule(module);
      void loadModule(module);
    },
    [loadModule]
  );

  useEffect(() => {
    if (!apiHealth.isReady) return;
    void (async () => {
      const health = await callApi<{ persistence?: { mode?: string } }>("/health");
      if (health?.persistence?.mode) setPersistenceMode(health.persistence.mode);
      await refreshDashboard();
      await refreshOrchestrators();
      await loadAgentCloud();
      await refreshMetrics();
      await refreshAgents();
    })();
  }, [apiHealth.isReady, callApi, loadAgentCloud, refreshAgents, refreshDashboard, refreshMetrics, refreshOrchestrators]);

  return {
    apiHealth,
    activeModule,
    selectModule,
    setActiveModule,
    dashboardSummary,
    isLoadingDashboard,
    refreshDashboard,
    governanceMetrics,
    refreshMetrics,
    finopsResult,
    refreshFinops,
    agentRegistry,
    refreshAgents,
    orchestratorRegistry,
    contentRuns,
    stockRuns,
    websiteRuns,
    isLoadingOrchestrators,
    refreshOrchestrators,
    runContentPipeline,
    runStockPipeline,
    runWebsitePipeline,
    agentCloudPosture,
    agentCloudMonitor,
    agentCloudGovern,
    agentCloudUndoable,
    agentCloudUndoResult,
    isLoadingAgentCloud,
    loadAgentCloud,
    undoAgentAction,
    incidentTimeline,
    refreshIncidents,
    persistenceMode,
    apiBaseUrl: API_BASE_URL
  };
}
