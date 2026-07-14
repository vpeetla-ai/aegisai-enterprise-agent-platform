import {
  Eye,
  Home,
  Layers,
  Plug,
  Radio,
  Shield,
  Snowflake,
  UserCheck,
  UserPlus
} from "lucide-react";
import type { DashboardModule } from "@/components/control-plane/GovernanceDashboard";

type TopNavigationProps = {
  activeModule: DashboardModule;
  onSelectModule: (module: DashboardModule) => void;
  apiHealthy: boolean;
  onRecheckApi: () => void;
};

/** Product journey order — left → right teaches what AegisAI is. */
const NAV_ITEMS: Array<{
  module: DashboardModule;
  label: string;
  step?: string;
  hint: string;
  icon: typeof Home;
}> = [
  { module: "dashboard", label: "Home", hint: "What this product is", icon: Home },
  { module: "onboard", label: "Onboard", step: "1", hint: "Register an agent", icon: UserPlus },
  { module: "gateway", label: "AI Gateway", step: "2", hint: "Govern tool calls", icon: Plug },
  { module: "monitor", label: "Monitor", step: "3", hint: "See what ran", icon: Eye },
  { module: "hitl", label: "HITL queue", step: "4", hint: "Approve side effects", icon: UserCheck },
  { module: "governance", label: "Governance", step: "5", hint: "Policy & coverage", icon: Shield },
  { module: "incidents", label: "Incidents", hint: "Kill switch freeze", icon: Snowflake },
  { module: "orchestrators", label: "Orchestrators", step: "6", hint: "Pipelines", icon: Radio },
  { module: "llm-plane", label: "Model plane", hint: "LLM metrics (separate)", icon: Layers }
];

export function TopNavigation({
  activeModule,
  onSelectModule,
  apiHealthy,
  onRecheckApi
}: TopNavigationProps) {
  const isActive = (module: DashboardModule) => {
    if (activeModule === module) return true;
    if (module === "monitor" && activeModule === "agents") return true;
    return false;
  };

  const go = (module: DashboardModule) => {
    if (!apiHealthy && module !== "dashboard") return;
    onSelectModule(module);
  };

  return (
    <header className="topbar topbar-clean aegis-topbar">
      <div className="aegis-topbar-brand">
        <p className="eyebrow">AegisAI</p>
        <h1>Agent Governance Control Plane</h1>
        <p className="aegis-topbar-tagline">
          Stop risky agent tool calls before they hit production systems
        </p>
      </div>
      <nav className="aegis-top-nav" aria-label="Product journey">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.module);
          return (
            <button
              key={item.module}
              type="button"
              className={`aegis-nav-item${active ? " is-active" : ""}`}
              disabled={!apiHealthy && item.module !== "dashboard"}
              title={
                !apiHealthy && item.module !== "dashboard"
                  ? "Available when governance API is ready"
                  : item.hint
              }
              onClick={() => go(item.module)}
            >
              {item.step ? <span className="aegis-nav-step">{item.step}</span> : null}
              <Icon size={16} aria-hidden />
              <span className="aegis-nav-label">
                <strong>{item.label}</strong>
                <em>{item.hint}</em>
              </span>
            </button>
          );
        })}
        {!apiHealthy ? (
          <button type="button" className="aegis-btn-secondary" onClick={onRecheckApi}>
            Recheck API
          </button>
        ) : null}
      </nav>
    </header>
  );
}
