import { Activity, Play, Presentation, ShieldAlert, UserRound, Wrench } from "lucide-react";
import type { PlatformActionKey } from "@/lib/api/types";

export type UiMode = "buyer" | "platform";

type TopNavigationProps = {
  activeView: "examples" | "control-plane";
  uiMode: UiMode;
  setUiMode: (mode: UiMode) => void;
  openView: (view: "examples" | "control-plane") => void;
  runBuyerDemo: () => void;
  isRunningPlatformDemo: boolean;
  apiHealthy: boolean;
  onRecheckApi: () => void;
  platformActionStatus: Record<PlatformActionKey, string>;
  runPlatformPostureApi: () => void;
  runGatewayApi: () => void;
};

export function TopNavigation({
  activeView,
  uiMode,
  setUiMode,
  openView,
  runBuyerDemo,
  isRunningPlatformDemo,
  apiHealthy,
  onRecheckApi,
  platformActionStatus,
  runPlatformPostureApi,
  runGatewayApi
}: TopNavigationProps) {
  const postureBusy = platformActionStatus.posture.toLowerCase().includes("loading");
  const gatewayBusy = platformActionStatus.gateway.toLowerCase().includes("checking");

  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">AegisAI Platform</p>
        <h1>AegisAI Agent Governance Control Plane</h1>
        <p className="topbar-mode-copy">
          {uiMode === "buyer"
            ? "Buyer mode: outcomes, controlled action, and signed evidence."
            : "Platform mode: architecture, integrations, and operator controls."}
        </p>
      </div>
      <div className="top-actions" aria-label="Primary navigation">
        <button
          type="button"
          className={activeView === "control-plane" && uiMode === "buyer" ? "primary-action" : ""}
          onClick={() => {
            setUiMode("buyer");
            openView("control-plane");
          }}
          title="Buyer-facing governed workflow demo"
        >
          <Presentation size={18} />
          Buyer Demo
        </button>
        <button
          type="button"
          className={activeView === "control-plane" && uiMode === "platform" ? "nav-active" : ""}
          onClick={() => {
            setUiMode("platform");
            openView("control-plane");
          }}
          title="Platform operator and architect console"
        >
          <Wrench size={18} />
          Platform Console
        </button>
        <button
          type="button"
          className={activeView === "examples" ? "nav-active" : ""}
          onClick={() => openView("examples")}
          title="Reference workloads that prove the control plane"
        >
          <ShieldAlert size={18} />
          Proof Workloads
        </button>
        <span className="top-action-divider" aria-hidden="true" />
        <button
          type="button"
          className="top-action-command"
          onClick={runBuyerDemo}
          disabled={isRunningPlatformDemo || !apiHealthy}
          title="Run gateway, HITL, broker execution, and signed audit"
        >
          <Play size={18} />
          {isRunningPlatformDemo ? "Running…" : apiHealthy ? "Run Workflow" : "API offline"}
        </button>
        {!apiHealthy ? (
          <button
            type="button"
            className="top-action-command"
            onClick={onRecheckApi}
            title="Recheck backend connection before running buyer workflow"
          >
            Recheck API
          </button>
        ) : null}
        <button
          type="button"
          className="top-action-command top-action-with-status"
          onClick={() => void runPlatformPostureApi()}
          disabled={postureBusy}
          title="Refresh board-level risk, cost, incident, and autonomy posture"
        >
          <span>
            <Activity size={18} />
            Show Posture
          </span>
          <small>{platformActionStatus.posture}</small>
        </button>
        <button
          type="button"
          className="top-action-command top-action-with-status"
          onClick={() => void runGatewayApi()}
          disabled={gatewayBusy}
          title="Simulate a governed side-effecting tool call"
        >
          <span>
            <UserRound size={18} />
            Test Gateway
          </span>
          <small>{platformActionStatus.gateway}</small>
        </button>
      </div>
    </header>
  );
}
