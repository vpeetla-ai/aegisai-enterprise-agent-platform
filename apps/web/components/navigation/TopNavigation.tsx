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

type NavItem = {
  module: DashboardModule;
  label: string;
  step?: string;
  hint: string;
  icon: typeof Home;
  satellite?: boolean;
};

/** Numbered path = govern agent tools. Satellites = ops extras, not the core product. */
const CORE_NAV: NavItem[] = [
  { module: "dashboard", label: "Home", hint: "What this product is", icon: Home },
  { module: "onboard", label: "Onboard", step: "1", hint: "Register an agent", icon: UserPlus },
  { module: "gateway", label: "AI Gateway", step: "2", hint: "Govern tool calls", icon: Plug },
  { module: "monitor", label: "Monitor", step: "3", hint: "See what ran", icon: Eye },
  { module: "hitl", label: "HITL queue", step: "4", hint: "Approve side effects", icon: UserCheck },
  { module: "governance", label: "Governance", step: "5", hint: "Policy & coverage", icon: Shield },
  { module: "orchestrators", label: "Orchestrators", step: "6", hint: "Pipelines", icon: Radio }
];

const SATELLITE_NAV: NavItem[] = [
  { module: "incidents", label: "Incidents", hint: "Kill switch freeze", icon: Snowflake, satellite: true },
  {
    module: "llm-plane",
    label: "LLM metrics",
    hint: "Cost & cache only",
    icon: Layers,
    satellite: true
  }
];

function NavButton({
  item,
  active,
  disabled,
  onClick
}: {
  item: NavItem;
  active: boolean;
  disabled: boolean;
  onClick: () => void;
}) {
  const Icon = item.icon;
  return (
    <button
      type="button"
      className={`aegis-nav-item${active ? " is-active" : ""}${item.satellite ? " is-satellite" : ""}`}
      disabled={disabled}
      title={disabled ? "Available when governance API is ready" : item.hint}
      onClick={onClick}
    >
      {item.step ? <span className="aegis-nav-step">{item.step}</span> : null}
      <Icon size={16} aria-hidden />
      <span className="aegis-nav-label">
        <strong>{item.label}</strong>
        <em>{item.hint}</em>
      </span>
    </button>
  );
}

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
          Govern agent tools before they hit production — AI Gateway is the product
        </p>
      </div>
      <nav className="aegis-top-nav" aria-label="Product journey">
        <div className="aegis-nav-cluster" aria-label="Tool governance">
          {CORE_NAV.map((item) => (
            <NavButton
              key={item.module}
              item={item}
              active={isActive(item.module)}
              disabled={!apiHealthy && item.module !== "dashboard"}
              onClick={() => go(item.module)}
            />
          ))}
        </div>
        <div className="aegis-nav-satellite-wrap" aria-label="Optional ops">
          <span className="aegis-nav-group-label">Optional</span>
          {SATELLITE_NAV.map((item) => (
            <NavButton
              key={item.module}
              item={item}
              active={isActive(item.module)}
              disabled={!apiHealthy}
              onClick={() => go(item.module)}
            />
          ))}
        </div>
        {!apiHealthy ? (
          <button type="button" className="aegis-btn-secondary" onClick={onRecheckApi}>
            Recheck API
          </button>
        ) : null}
      </nav>
    </header>
  );
}
