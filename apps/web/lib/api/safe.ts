/** FastAPI error bodies and other non-domain JSON should not hydrate UI state. */
export function isFastApiErrorBody(value: unknown): boolean {
  if (!value || typeof value !== "object") {
    return false;
  }
  const record = value as Record<string, unknown>;
  if ("detail" in record && Object.keys(record).length <= 2) {
    return true;
  }
  return "error" in record && typeof record.error === "object";
}

export function safeArray<T>(value: T[] | undefined | null): T[] {
  return Array.isArray(value) ? value : [];
}

export function safeNumber(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

export function isGovernanceMetricsPayload(value: unknown): value is {
  gateway_coverage_pct: number;
  headline?: string;
  board_metrics?: unknown;
  recommended_actions?: unknown;
} {
  return (
    !!value &&
    typeof value === "object" &&
    typeof (value as { gateway_coverage_pct?: unknown }).gateway_coverage_pct === "number"
  );
}

export function isDeveloperQuickstartPayload(value: unknown): value is {
  steps: unknown;
  typescript: string;
} {
  return (
    !!value &&
    typeof value === "object" &&
    Array.isArray((value as { steps?: unknown }).steps) &&
    typeof (value as { typescript?: unknown }).typescript === "string"
  );
}

export function isRegulatedOpsDemoPayload(value: unknown): value is {
  story: string;
  governed_steps: unknown;
} {
  return (
    !!value &&
    typeof value === "object" &&
    typeof (value as { story?: unknown }).story === "string" &&
    Array.isArray((value as { governed_steps?: unknown }).governed_steps)
  );
}

export function isPolicyStudioPayload(value: unknown): value is {
  dry_run_decision: string;
  blast_radius: { estimated_monthly_intercepts: number };
} {
  const record = value as { dry_run_decision?: unknown; blast_radius?: unknown };
  return (
    !!value &&
    typeof value === "object" &&
    typeof record.dry_run_decision === "string" &&
    !!record.blast_radius &&
    typeof record.blast_radius === "object" &&
    typeof (record.blast_radius as { estimated_monthly_intercepts?: unknown })
      .estimated_monthly_intercepts === "number"
  );
}

export function isIdentityGraphPayload(value: unknown): value is {
  nodes: unknown;
  edges: unknown;
  blast_radius: { privileged_principals: number };
} {
  const record = value as { nodes?: unknown; edges?: unknown; blast_radius?: unknown };
  return (
    !!value &&
    typeof value === "object" &&
    Array.isArray(record.nodes) &&
    Array.isArray(record.edges) &&
    !!record.blast_radius &&
    typeof record.blast_radius === "object"
  );
}

export function isGatewayStoryPayload(value: unknown): value is {
  headline: string;
  flow: unknown;
} {
  return (
    !!value &&
    typeof value === "object" &&
    typeof (value as { headline?: unknown }).headline === "string" &&
    Array.isArray((value as { flow?: unknown }).flow)
  );
}

export function isAuditVaultPayload(value: unknown): value is {
  retention_policy: string;
  evidence_types: unknown;
} {
  return (
    !!value &&
    typeof value === "object" &&
    typeof (value as { retention_policy?: unknown }).retention_policy === "string" &&
    Array.isArray((value as { evidence_types?: unknown }).evidence_types)
  );
}
