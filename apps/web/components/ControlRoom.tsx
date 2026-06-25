"use client";

import { ApiHealthGate } from "@/components/control-plane/ApiHealthGate";
import { GovernanceModuleView } from "@/components/control-plane/GovernanceModuleView";
import { TopNavigation } from "@/components/navigation/TopNavigation";
import { useControlPlane } from "@/hooks/useControlPlane";

export function ControlRoom() {
  const cp = useControlPlane();

  return (
    <main className="shell shell-clean">
      <TopNavigation
        activeModule={cp.activeModule}
        onSelectModule={cp.selectModule}
        apiHealthy={cp.apiHealth.isReady}
        onRecheckApi={() => void cp.apiHealth.check()}
      />

      <ApiHealthGate
        status={cp.apiHealth.status}
        detail={cp.apiHealth.detail}
        onRecheck={() => void cp.apiHealth.check()}
      >
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
      </ApiHealthGate>
    </main>
  );
}
