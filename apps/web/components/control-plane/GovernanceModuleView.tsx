"use client";

import { AgentMonitorPanel } from "@/components/control-plane/AgentMonitorPanel";
import { FinOpsPanel } from "@/components/control-plane/FinOpsPanel";
import { GatewayPanel } from "@/components/control-plane/GatewayPanel";
import {
  GovernanceDashboard,
  type DashboardModule
} from "@/components/control-plane/GovernanceDashboard";
import { GovernanceControlPlanePanel } from "@/components/control-plane/GovernanceControlPlanePanel";
import { IncidentsModulePanel } from "@/components/control-plane/IncidentsModulePanel";
import { ModuleShell } from "@/components/control-plane/ModuleShell";
import { OrchestratorsPanel } from "@/components/control-plane/OrchestratorsPanel";
import { WebsiteBuildPanel } from "@/components/control-plane/WebsiteBuildPanel";
import { AgentOnboardingWizard } from "@/components/control-plane/AgentOnboardingWizard";
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

const MODULE_TITLES: Record<DashboardModule, string> = {
  dashboard: "Dashboard",
  monitor: "Agent Monitor",
  agents: "Agents",
  governance: "Governance",
  gateway: "AI Gateway",
  hitl: "HITL queue",
  finops: "FinOps",
  incidents: "Incidents",
  orchestrators: "Orchestrators",
  onboard: "Onboard agent"
};

type GovernanceModuleViewProps = {
  activeModule: DashboardModule;
  onBack: () => void;
  dashboardSummary: DashboardSummaryPayload | null;
  isLoadingDashboard: boolean;
  onRefreshDashboard: () => void;
  onSelectModule: (module: DashboardModule) => void;
  apiHealthy: boolean;
  governanceMetrics: GovernanceMetricsPayload | null;
  onRefreshMetrics: () => void;
  persistenceMode?: string;
  finopsResult: FinOpsDashboardPayload | null;
  onRefreshFinops: () => void;
  agentRegistry: AgentRegistryPayload | null;
  orchestratorRegistry: OrchestratorRegistryPayload | null;
  contentRuns: OrchestratorRunPayload | null;
  stockRuns: OrchestratorRunPayload | null;
  websiteRuns: OrchestratorRunPayload | null;
  isLoadingOrchestrators: boolean;
  onRefreshOrchestrators: () => void;
  onRunContentPipeline: () => void;
  onRunStockPipeline: () => void;
  onRunWebsitePipeline: (requirement?: string) => void;
  onRefreshAgents?: () => void;
  agentCloudPosture: AgentCloudPosturePayload | null;
  agentCloudMonitor: AgentCloudMonitorPayload | null;
  agentCloudGovern: AgentCloudGovernPayload | null;
  agentCloudUndoable: AgentCloudUndoablePayload | null;
  agentCloudUndoResult: AgentCloudUndoPayload | null;
  isLoadingAgentCloud: boolean;
  onLoadAgentCloud: () => void;
  onUndo: (executionId: string) => void;
  incidentTimeline: IncidentTimelinePayload | null;
};

export function GovernanceModuleView(props: GovernanceModuleViewProps) {
  const { activeModule, onBack } = props;

  if (activeModule === "dashboard") {
    return (
      <GovernanceDashboard
        summary={props.dashboardSummary}
        monitor={props.agentCloudMonitor}
        govern={props.agentCloudGovern}
        posture={props.agentCloudPosture}
        isLoading={props.isLoadingDashboard || props.isLoadingAgentCloud}
        onRefresh={() => {
          void props.onRefreshDashboard();
          void props.onLoadAgentCloud();
        }}
        onSelectModule={props.onSelectModule}
        apiHealthy={props.apiHealthy}
      />
    );
  }

  const title = MODULE_TITLES[activeModule];

  if (activeModule === "monitor" || activeModule === "agents") {
    return (
      <ModuleShell
        title={activeModule === "monitor" ? "Agent Monitor" : title}
        subtitle="Discover agents, trace identity → app → tool lineage, watch live activity"
        onBack={onBack}
      >
        <AgentMonitorPanel
          summary={props.dashboardSummary}
          monitor={props.agentCloudMonitor}
          govern={props.agentCloudGovern}
          isLoading={props.isLoadingAgentCloud}
          onRefresh={() => void props.onLoadAgentCloud()}
        />
      </ModuleShell>
    );
  }

  if (activeModule === "gateway") {
    return (
      <ModuleShell
        title={title}
        subtitle="Connect production agents · intercept tools · measure coverage"
        onBack={onBack}
      >
        <GatewayPanel
          apiHealthy={props.apiHealthy}
          metrics={props.governanceMetrics}
          onRefreshMetrics={props.onRefreshMetrics}
          isLoading={props.isLoadingAgentCloud}
        />
      </ModuleShell>
    );
  }

  if (activeModule === "orchestrators") {
    const lastWebRun = props.websiteRuns?.runs?.[0] as
      | { run_id: string; status: string; hitl_pending?: boolean; review_deploy?: object }
      | undefined;
    return (
      <ModuleShell title={title} onBack={onBack}>
        <WebsiteBuildPanel
          isLoading={props.isLoadingOrchestrators}
          onSubmit={props.onRunWebsitePipeline}
          lastRun={lastWebRun ?? null}
        />
        <OrchestratorsPanel
          registry={props.orchestratorRegistry}
          contentRuns={props.contentRuns}
          stockRuns={props.stockRuns}
          websiteRuns={props.websiteRuns}
          isLoading={props.isLoadingOrchestrators}
          onRefresh={props.onRefreshOrchestrators}
          onRunContent={props.onRunContentPipeline}
          onRunStock={props.onRunStockPipeline}
          onRunWebsite={props.onRunWebsitePipeline}
        />
      </ModuleShell>
    );
  }

  if (activeModule === "onboard") {
    return (
      <ModuleShell
        title={title}
        subtitle="Register production agents and promote through shadow → approved"
        onBack={onBack}
      >
        <AgentOnboardingWizard onComplete={() => void props.onRefreshAgents?.()} />
      </ModuleShell>
    );
  }

  if (activeModule === "governance") {
    return (
      <ModuleShell
        title={title}
        subtitle="Guild-style control plane — policies, permissions, observability, audit"
        onBack={onBack}
      >
        <GovernanceControlPlanePanel
          metrics={props.governanceMetrics}
          monitor={props.agentCloudMonitor}
          govern={props.agentCloudGovern}
          undoable={props.agentCloudUndoable}
          isLoading={props.isLoadingAgentCloud}
          onRefresh={() => {
            void props.onLoadAgentCloud();
            void props.onRefreshMetrics();
          }}
          onUndo={props.onUndo}
        />
      </ModuleShell>
    );
  }

  if (activeModule === "finops") {
    return (
      <ModuleShell title={title} subtitle="Token cost and fleet spend" onBack={onBack}>
        <FinOpsPanel finopsResult={props.finopsResult} onLoad={props.onRefreshFinops} />
      </ModuleShell>
    );
  }

  if (activeModule === "hitl" || activeModule === "incidents") {
    return (
      <ModuleShell
        title={title}
        subtitle={activeModule === "hitl" ? "Approval queue and reviewer path" : "Freeze and remediate"}
        onBack={onBack}
      >
        <IncidentsModulePanel incident={props.incidentTimeline} />
      </ModuleShell>
    );
  }

  return null;
}
