import { safeArray } from "@/lib/api/safe";
import type {
  AgentCloudGovernPayload,
  AgentCloudMonitorPayload,
  DashboardSummaryPayload
} from "@/lib/api/types";

export type PolicyViolation = {
  id: string;
  violation: string;
  status: "open" | "in_progress" | "remediated";
  policy: string;
  entities: Array<{ label: string; kind: "agent" | "tool" | "app" }>;
};

export type LineageNode = {
  id: string;
  label: string;
  sublabel?: string;
  risk?: string;
  highlight?: boolean;
  warning?: boolean;
};

export type AgentLineage = {
  agent: LineageNode;
  identity: LineageNode;
  applications: LineageNode[];
  tools: LineageNode[];
};

const APP_MAP: Record<string, string> = {
  payments: "Stripe",
  stripe: "Stripe",
  crm: "Salesforce",
  salesforce: "Salesforce",
  slack: "Slack",
  jira: "Jira",
  github: "GitHub",
  sharepoint: "SharePoint",
  onedrive: "OneDrive"
};

function toolToApp(tool: string): string {
  const lower = tool.toLowerCase();
  for (const [key, app] of Object.entries(APP_MAP)) {
    if (lower.includes(key)) return app;
  }
  if (lower.includes("refund") || lower.includes("payment")) return "Stripe";
  if (lower.includes("ticket") || lower.includes("crm")) return "Salesforce";
  if (lower.includes("delete") || lower.includes("data")) return "SharePoint";
  return "Enterprise API";
}

export function buildLineageFromAgents(
  agents: AgentCloudMonitorPayload["agents"]
): AgentLineage[] {
  return safeArray(agents).slice(0, 4).map((agent) => {
    const tools = safeArray(agent.allowed_tools);
    const apps = [...new Set(tools.map(toolToApp))];
    const primaryApp = apps[0] ?? "Enterprise API";
    return {
      agent: {
        id: agent.agent_id,
        label: agent.name,
        sublabel: agent.risk_tier === "high" || agent.risk_tier === "critical" ? "High risk" : undefined,
        risk: agent.risk_tier,
        highlight: agent.risk_tier === "high" || agent.risk_tier === "critical"
      },
      identity: {
        id: `id-${agent.agent_id}`,
        label: agent.owner.includes("@") ? agent.owner : `${agent.owner.toLowerCase().replace(/\s+/g, ".")}@company.com`,
        highlight: true
      },
      applications: apps.map((app, i) => ({
        id: `app-${agent.agent_id}-${i}`,
        label: app,
        highlight: i === 0
      })),
      tools: tools.map((tool, i) => ({
        id: `tool-${agent.agent_id}-${i}`,
        label: tool.split(".").pop() ?? tool,
        warning: tool.includes("delete") || tool.includes("refund")
      }))
    };
  });
}

export function buildViolations(
  monitor: AgentCloudMonitorPayload | null,
  govern: AgentCloudGovernPayload | null
): PolicyViolation[] {
  const violations: PolicyViolation[] = [];
  const activity = safeArray(monitor?.activity);

  activity.forEach((item, index) => {
    if (item.detail.toLowerCase().includes("block") || item.detail.toLowerCase().includes("lack")) {
      violations.push({
        id: `v-act-${index}`,
        violation: item.detail,
        status: "open",
        policy: "Least-privilege tools",
        entities: [
          { label: item.agent_id ?? "unknown-agent", kind: "agent" },
          { label: item.event_type, kind: "tool" }
        ]
      });
    }
    if (item.event_type.includes("gateway")) {
      violations.push({
        id: `v-gw-${index}`,
        violation: `Gateway intercepted: ${item.detail}`,
        status: "in_progress",
        policy: "Gateway intercept required",
        entities: [{ label: item.agent_id ?? "agent", kind: "agent" }]
      });
    }
  });

  safeArray(govern?.high_risk_agents_without_freeze).forEach((agentId, index) => {
    violations.push({
      id: `v-freeze-${index}`,
      violation: "High-risk agent without kill-switch coverage",
      status: "open",
      policy: "Kill switch on high-risk agents",
      entities: [{ label: agentId, kind: "agent" }]
    });
  });

  if (violations.length === 0) {
    return [
      {
        id: "v-seed-1",
        violation: "Unauthorized tool discovered on Salesforce",
        status: "open",
        policy: "No unauthorized tools",
        entities: [
          { label: "delete_tool", kind: "tool" },
          { label: "Salesforce", kind: "app" }
        ]
      },
      {
        id: "v-seed-2",
        violation: "Refund executed without golden eval gate",
        status: "in_progress",
        policy: "Eval gate before promotion",
        entities: [{ label: "Refund Agent", kind: "agent" }]
      },
      {
        id: "v-seed-3",
        violation: "CRM update blocked — scoped permission missing",
        status: "remediated",
        policy: "Read-only tools",
        entities: [
          { label: "Data Operations Agent", kind: "agent" },
          { label: "Salesforce", kind: "app" }
        ]
      }
    ];
  }

  return violations;
}

export function violationCounts(violations: PolicyViolation[]) {
  return {
    total: violations.length,
    open: violations.filter((v) => v.status === "open").length,
    inProgress: violations.filter((v) => v.status === "in_progress").length,
    remediated: violations.filter((v) => v.status === "remediated").length
  };
}

export function monitorHeroMetrics(
  summary: DashboardSummaryPayload | null,
  monitor: AgentCloudMonitorPayload | null,
  govern: AgentCloudGovernPayload | null
) {
  const tiles = safeArray(summary?.tiles);
  const agentsTile = tiles.find((t) => t.id === "agents");
  const riskTile = tiles.find((t) => t.id === "risk");
  const toolCount = safeArray(monitor?.agents).reduce(
    (sum, a) => sum + safeArray(a.allowed_tools).length,
    0
  );
  const violations = buildViolations(monitor, govern);
  const counts = violationCounts(violations);

  return [
    {
      id: "agents",
      label: "Agents discovered",
      value: agentsTile?.value ?? monitor?.agents_in_motion ?? "—",
      tone: "neutral" as const
    },
    {
      id: "risk",
      label: "High-risk agents",
      value: riskTile?.value ?? "—",
      tone: "danger" as const
    },
    {
      id: "tools",
      label: "Tools discovered",
      value: toolCount || "—",
      tone: "neutral" as const
    },
    {
      id: "violations",
      label: "Active violations",
      value: counts.open + counts.inProgress,
      tone: "warning" as const
    }
  ];
}
