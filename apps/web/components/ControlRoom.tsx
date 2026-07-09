"use client";

import { useState } from "react";
import { ApiHealthGate } from "@/components/control-plane/ApiHealthGate";
import { ArchitectLandingStrip } from "@/components/ArchitectLandingStrip";
import { GovernanceModuleView } from "@/components/control-plane/GovernanceModuleView";
import { TopNavigation } from "@/components/navigation/TopNavigation";
import { useControlPlane } from "@/hooks/useControlPlane";

type WorkbenchView = "product" | "architecture";

export function ControlRoom() {
  const cp = useControlPlane();
  const [view, setView] = useState<WorkbenchView>("product");

  return (
    <main className="shell shell-clean">
      <TopNavigation
        activeModule={cp.activeModule}
        onSelectModule={cp.selectModule}
        apiHealthy={cp.apiHealth.isReady}
        onRecheckApi={() => void cp.apiHealth.check()}
      />

      <div className="workbench-tabs-bar" style={{ display: "flex", gap: "0.5rem", padding: "0 1.25rem", borderBottom: "1px solid var(--line, #d9e1ea)" }}>
        <WorkbenchTab active={view === "product"} onClick={() => setView("product")} label="Control plane" hint="Run governance workflows" />
        <WorkbenchTab active={view === "architecture"} onClick={() => setView("architecture")} label="Architecture & metrics" hint="Stack, tradeoffs, SLOs" />
      </div>

      <ApiHealthGate
        status={cp.apiHealth.status}
        detail={cp.apiHealth.detail}
        onRecheck={() => void cp.apiHealth.check()}
      >
        {view === "architecture" ? (
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
      onClick={onClick}
      style={{
        position: "relative",
        marginBottom: "-1px",
        padding: "0.65rem 1rem",
        border: active ? "1px solid var(--line, #d9e1ea)" : "1px solid transparent",
        borderBottom: active ? "1px solid var(--paper, #ffffff)" : "1px solid transparent",
        borderRadius: "8px 8px 0 0",
        background: active ? "var(--paper, #ffffff)" : "transparent",
        cursor: "pointer",
        textAlign: "left",
      }}
    >
      <span style={{ display: "block", fontSize: "0.85rem", fontWeight: 600, color: active ? "var(--ink, #142033)" : "var(--muted, #607086)" }}>{label}</span>
      <span style={{ display: "block", fontSize: "0.65rem", color: "var(--muted, #607086)" }}>{hint}</span>
      {active ? (
        <span style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 2, background: "var(--blue, #2563eb)" }} aria-hidden />
      ) : null}
    </button>
  );
}
