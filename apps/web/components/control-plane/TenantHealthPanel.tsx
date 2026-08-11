"use client";

import { useCallback, useEffect, useState } from "react";
import { ModuleShell } from "@/components/control-plane/ModuleShell";

type HealthPayload = {
  tenant_id?: string;
  usage?: {
    missions_per_week?: number;
    error_rate_pct?: number;
    hitl_reject_rate_pct?: number;
    budget_burn_pct?: number;
    warm_sla_breaches?: number;
  };
  onboarding?: {
    checklist?: { id: string; complete: boolean }[];
    ttfv_seconds?: number | null;
    completed_steps?: number;
    total_steps?: number;
  };
  latest_alert?: { reasons?: string[] } | null;
  honesty?: string;
};

const API_BASE = process.env.NEXT_PUBLIC_AEGISAI_API_URL || "";

export function TenantHealthPanel({ onBack }: { onBack: () => void }) {
  const [tenantId, setTenantId] = useState("acme");
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/tenants/${encodeURIComponent(tenantId)}/health`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setHealth(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load tenant health");
      setHealth(null);
    } finally {
      setLoading(false);
    }
  }, [tenantId]);

  useEffect(() => {
    void load();
  }, [load]);

  const completeStep = async (step: string) => {
    await fetch(`${API_BASE}/api/tenants/${encodeURIComponent(tenantId)}/onboarding/complete-step`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-AegisAI-Principal": "control-plane-admin",
        "X-AegisAI-Roles": "admin"
      },
      body: JSON.stringify({ step })
    });
    await load();
  };

  return (
    <ModuleShell title="Tenant health" onBack={onBack}>
      <p className="mb-4 max-w-2xl text-sm text-zinc-600">
        Embed ops for one customer — usage, HITL rejects, budget burn, onboarding TTFV. Not a CS SaaS.
      </p>
      <div className="mb-6 flex flex-wrap items-end gap-3">
        <label className="text-sm text-zinc-700">
          Tenant
          <input
            className="mt-1 block rounded border border-zinc-300 px-3 py-2 font-mono text-sm"
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
          />
        </label>
        <button
          type="button"
          onClick={() => void load()}
          className="rounded bg-zinc-900 px-4 py-2 text-sm font-semibold text-white"
        >
          Refresh
        </button>
      </div>
      {loading && <p className="text-sm text-zinc-500">Loading…</p>}
      {error && <p className="text-sm text-red-700">{error}</p>}
      {health?.usage && (
        <dl className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {(
            [
              ["Missions / week", health.usage.missions_per_week],
              ["Error rate %", health.usage.error_rate_pct],
              ["HITL reject %", health.usage.hitl_reject_rate_pct],
              ["Budget burn %", health.usage.budget_burn_pct],
              ["Warm SLA breaches", health.usage.warm_sla_breaches]
            ] as const
          ).map(([label, value]) => (
            <div key={label} className="border-b border-zinc-200 pb-3">
              <dt className="text-xs uppercase tracking-wide text-zinc-500">{label}</dt>
              <dd className="mt-1 font-mono text-xl text-zinc-900">{value ?? "—"}</dd>
            </div>
          ))}
        </dl>
      )}
      {health?.onboarding && (
        <section className="mb-8">
          <h3 className="mb-2 text-sm font-semibold text-zinc-900">Onboarding checklist</h3>
          <p className="mb-3 text-xs text-zinc-500">
            TTFV: {health.onboarding.ttfv_seconds ?? "pending"} ·{" "}
            {health.onboarding.completed_steps}/{health.onboarding.total_steps} steps
          </p>
          <ul className="space-y-2">
            {(health.onboarding.checklist || []).map((item) => (
              <li key={item.id} className="flex items-center justify-between text-sm">
                <span className="font-mono text-zinc-700">{item.id}</span>
                {item.complete ? (
                  <span className="text-teal-800">done</span>
                ) : (
                  <button
                    type="button"
                    className="text-[#0f5c56] underline"
                    onClick={() => void completeStep(item.id)}
                  >
                    Complete
                  </button>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
      {health?.latest_alert && (
        <p className="text-sm text-amber-800">
          Alert: {(health.latest_alert.reasons || []).join(", ")}
        </p>
      )}
      {health?.honesty && <p className="mt-6 text-xs text-zinc-500">{health.honesty}</p>}
    </ModuleShell>
  );
}
