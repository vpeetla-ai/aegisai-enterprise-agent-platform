"use client";

import { useEffect, useState } from "react";
import { ApiHealthGate } from "@/components/control-plane/ApiHealthGate";
import { ReviewModeBanner } from "@/components/control-plane/ReviewModeBanner";
import { ArchitectLandingStrip } from "@/components/ArchitectLandingStrip";
import { GlassboxGovernance } from "@/components/GlassboxGovernance";
import { GovernanceModuleView } from "@/components/control-plane/GovernanceModuleView";
import type { DashboardModule } from "@/components/control-plane/GovernanceDashboard";
import { TopNavigation } from "@/components/navigation/TopNavigation";
import { useControlPlane } from "@/hooks/useControlPlane";

type WorkbenchView = "glassbox" | "product" | "architecture";

const MODULES: DashboardModule[] = [
  "dashboard",
  "monitor",
  "agents",
  "governance",
  "gateway",
  "llm-plane",
  "hitl",
  "finops",
  "incidents",
  "orchestrators",
  "onboard",
];

function parseDeepLink(): { view?: WorkbenchView; module?: DashboardModule } {
  if (typeof window === "undefined") return {};
  const params = new URLSearchParams(window.location.search);
  const viewRaw = params.get("view");
  const moduleRaw = params.get("module");
  const view =
    viewRaw === "glassbox" || viewRaw === "product" || viewRaw === "architecture"
      ? viewRaw
      : undefined;
  const module =
    moduleRaw && (MODULES as string[]).includes(moduleRaw)
      ? (moduleRaw as DashboardModule)
      : undefined;
  return { view, module };
}

export function ControlRoom() {
  const cp = useControlPlane();
  const [view, setView] = useState<WorkbenchView>("glassbox");

  useEffect(() => {
    const { view: deepView, module: deepModule } = parseDeepLink();
    if (deepView) setView(deepView);
    if (deepModule) {
      setView((v) => (deepView ? deepView : "product"));
      cp.selectModule(deepModule);
    }
    // Deep-link once on mount for VAP / portfolio HITL entry.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <main className="shell shell-clean">
      <TopNavigation
        activeModule={cp.activeModule}
        onSelectModule={cp.selectModule}
        apiHealthy={cp.apiHealth.isReady}
        onRecheckApi={() => void cp.apiHealth.check()}
      />

      <ReviewModeBanner
        productionStrict={cp.apiHealth.reviewMode.productionStrict}
        failClosedReady={cp.apiHealth.reviewMode.failClosedReady}
      />

      <div className="workbench-tabs-bar">
        <WorkbenchTab
          active={view === "glassbox"}
          onClick={() => setView("glassbox")}
          label="Glass-box"
          hint="Arch · pipeline · product"
        />
        <WorkbenchTab
          active={view === "product"}
          onClick={() => setView("product")}
          label="Operate"
          hint="Onboard → Gateway → Monitor"
        />
        <WorkbenchTab
          active={view === "architecture"}
          onClick={() => setView("architecture")}
          label="Architecture"
          hint="Stack · tradeoffs · live ops"
        />
      </div>

      <ApiHealthGate
        status={cp.apiHealth.status}
        detail={cp.apiHealth.detail}
        onRecheck={() => void cp.apiHealth.check()}
      >
        {view === "glassbox" ? (
          <GlassboxGovernance />
        ) : view === "architecture" ? (
          <ArchitectLandingStrip />
        ) : (
          <GovernanceModuleView
          activeModule={cp.activeModule}
          onBack={() => cp.setActiveModule("dashboard")}
          dashboardSummary={cp.dashboardSummary}
          isLoadingDashboard={cp.isLoadingDashboard}
          onRefreshDashboard={() => void cp.refreshDashboard()}
          onSelectModule={cp.selectModule}
          apiHealthy={cp.apiHealth.isReady}
          governanceMetrics={cp.governanceMetrics}
          onRefreshMetrics={() => void cp.refreshMetrics()}
          persistenceMode={cp.persistenceMode}
          finopsResult={cp.finopsResult}
          onRefreshFinops={() => void cp.refreshFinops()}
          agentRegistry={cp.agentRegistry}
          orchestratorRegistry={cp.orchestratorRegistry}
          contentRuns={cp.contentRuns}
          stockRuns={cp.stockRuns}
          websiteRuns={cp.websiteRuns}
          isLoadingOrchestrators={cp.isLoadingOrchestrators}
          onRefreshOrchestrators={() => void cp.refreshOrchestrators()}
          onRunContentPipeline={() => void cp.runContentPipeline()}
          onRunStockPipeline={() => void cp.runStockPipeline()}
          onRunWebsitePipeline={(req) => void cp.runWebsitePipeline(req)}
          onRefreshAgents={() => void cp.refreshAgents()}
          agentCloudPosture={cp.agentCloudPosture}
          agentCloudMonitor={cp.agentCloudMonitor}
          agentCloudGovern={cp.agentCloudGovern}
          agentCloudUndoable={cp.agentCloudUndoable}
          agentCloudUndoResult={cp.agentCloudUndoResult}
          isLoadingAgentCloud={cp.isLoadingAgentCloud}
          onLoadAgentCloud={() => void cp.loadAgentCloud()}
          onUndo={(id) => void cp.undoAgentAction(id)}
          incidentTimeline={cp.incidentTimeline}
          onRefreshIncidents={() => void cp.refreshIncidents()}
        />
        )}
      </ApiHealthGate>
    </main>
  );
}

function WorkbenchTab({
  active,
  onClick,
  label,
  hint,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
  hint: string;
}) {
  return (
    <button
      type="button"
      className={`workbench-tab${active ? " is-active" : ""}`}
      onClick={onClick}
    >
      <span className="workbench-tab-label">{label}</span>
      <span className="workbench-tab-hint">{hint}</span>
    </button>
  );
}
