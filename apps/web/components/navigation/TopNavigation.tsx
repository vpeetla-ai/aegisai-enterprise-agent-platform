import { Eye, LayoutDashboard, Layers, Plug, Radio, Shield, UserPlus } from "lucide-react";
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

  const go = (module: DashboardModule) => {
    if (!apiHealthy && module !== "dashboard") return;
    onSelectModule(module);
  };

  return (
    <header className="topbar topbar-clean aegis-topbar">
      <div>
        <p className="eyebrow">AegisAI</p>
        <h1>Agent Governance Control Plane</h1>
      </div>
      <div className="top-actions" aria-disabled={!apiHealthy || undefined}>
        <button type="button" className={navClass("dashboard")} onClick={() => go("dashboard")}>
          <LayoutDashboard size={18} />
          Dashboard
        </button>
        <button
          type="button"
          className={navClass("monitor")}
          disabled={!apiHealthy}
          title={!apiHealthy ? "Available when governance API is ready" : undefined}
          onClick={() => go("monitor")}
        >
          <Eye size={18} />
          Monitor
        </button>
        <button
          type="button"
          className={navClass("governance")}
          disabled={!apiHealthy}
          title={!apiHealthy ? "Available when governance API is ready" : undefined}
          onClick={() => go("governance")}
        >
          <Shield size={18} />
          Governance
        </button>
        <button
          type="button"
          className={navClass("gateway")}
          disabled={!apiHealthy}
          title={!apiHealthy ? "Available when governance API is ready" : undefined}
          onClick={() => go("gateway")}
        >
          <Plug size={18} />
          AI Gateway
        </button>
        <button
          type="button"
          className={navClass("llm-plane")}
          disabled={!apiHealthy}
          title={!apiHealthy ? "Available when governance API is ready" : undefined}
          onClick={() => go("llm-plane")}
        >
          <Layers size={18} />
          LLM Plane
        </button>
        <button
          type="button"
          className={activeModule === "orchestrators" ? "nav-active" : ""}
          disabled={!apiHealthy}
          title={!apiHealthy ? "Available when governance API is ready" : undefined}
          onClick={() => go("orchestrators")}
        >
          <Radio size={18} />
          Orchestrators
        </button>
        <button
          type="button"
          className={navClass("onboard")}
          disabled={!apiHealthy}
          title={!apiHealthy ? "Available when governance API is ready" : undefined}
          onClick={() => go("onboard")}
        >
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
