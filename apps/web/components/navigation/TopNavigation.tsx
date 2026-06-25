import { Eye, LayoutDashboard, Plug, Radio, Shield, UserPlus } from "lucide-react";
import type { DashboardModule } from "@/components/control-plane/GovernanceDashboard";

type TopNavigationProps = {
  activeModule: DashboardModule;
  onSelectModule: (module: DashboardModule) => void;
  apiHealthy: boolean;
  onRecheckApi: () => void;
};

export function TopNavigation({
  activeModule,
  onSelectModule,
  apiHealthy,
  onRecheckApi
}: TopNavigationProps) {
  const navClass = (module: DashboardModule) => {
    if (activeModule === module) return "primary-action";
    if (module === "monitor" && activeModule === "agents") return "primary-action";
    return activeModule === module ? "nav-active" : "";
  };

  return (
    <header className="topbar topbar-clean aegis-topbar">
      <div>
        <p className="eyebrow">AegisAI</p>
        <h1>Agent Governance Control Plane</h1>
      </div>
      <div className="top-actions">
        <button type="button" className={navClass("dashboard")} onClick={() => onSelectModule("dashboard")}>
          <LayoutDashboard size={18} />
          Dashboard
        </button>
        <button type="button" className={navClass("monitor")} onClick={() => onSelectModule("monitor")}>
          <Eye size={18} />
          Monitor
        </button>
        <button type="button" className={navClass("governance")} onClick={() => onSelectModule("governance")}>
          <Shield size={18} />
          Governance
        </button>
        <button type="button" className={navClass("gateway")} onClick={() => onSelectModule("gateway")}>
          <Plug size={18} />
          AI Gateway
        </button>
        <button
          type="button"
          className={activeModule === "orchestrators" ? "nav-active" : ""}
          onClick={() => onSelectModule("orchestrators")}
        >
          <Radio size={18} />
          Orchestrators
        </button>
        <button type="button" className={navClass("onboard")} onClick={() => onSelectModule("onboard")}>
          <UserPlus size={18} />
          Onboard
        </button>
        {!apiHealthy ? (
          <button type="button" className="btn-secondary" onClick={onRecheckApi}>
            Recheck API
          </button>
        ) : null}
      </div>
    </header>
  );
}
