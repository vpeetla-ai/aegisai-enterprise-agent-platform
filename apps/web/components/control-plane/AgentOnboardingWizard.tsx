"use client";

import { useState } from "react";
import { CheckCircle2, ChevronRight, UserPlus } from "lucide-react";
import { requestJson } from "@/lib/api/client";

const DEV_HEADERS = {
  "X-AegisAI-Principal": "control-plane-admin",
  "X-AegisAI-Tenant": "bank-demo",
  "X-AegisAI-Roles": "admin,reviewer"
};

const STATUSES = ["shadow", "pilot", "approved"] as const;
const RISK_TIERS = ["low", "medium", "high", "critical"] as const;
const TOOL_OPTIONS = [
  "rag.search_policy_memory",
  "deploy.vercel_release",
  "deploy.render_release",
  "github.push_files",
  "design.analyze_figma"
];
const DATA_CLASSES = ["public", "internal", "confidential", "restricted"];

type WizardStep = "identity" | "tools" | "review" | "done";

export function AgentOnboardingWizard({ onComplete }: { onComplete?: () => void }) {
  const [step, setStep] = useState<WizardStep>("identity");
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [form, setForm] = useState({
    agent_id: "",
    name: "",
    owner: "",
    business_domain: "",
    risk_tier: "medium" as (typeof RISK_TIERS)[number],
    autonomy_level: 2,
    status: "shadow" as (typeof STATUSES)[number],
    model_provider: "gemini",
    allowed_tools: ["rag.search_policy_memory"] as string[],
    data_classes: ["internal"] as string[]
  });

  const toggle = (key: "allowed_tools" | "data_classes", value: string) => {
    setForm((current) => {
      const set = new Set(current[key]);
      if (set.has(value)) set.delete(value);
      else set.add(value);
      return { ...current, [key]: [...set] };
    });
  };

  const register = async (promoteTo?: (typeof STATUSES)[number]) => {
    setIsSaving(true);
    setError(null);
    const payload = { ...form, status: promoteTo ?? form.status };
    const { payload: result } = await requestJson<{ status?: string; agent?: { agent_id: string } }>(
      "/api/agent-registry/lifecycle",
      {
        method: "POST",
        headers: DEV_HEADERS,
        body: JSON.stringify(payload)
      }
    );
    if (!result?.agent) {
      setError("Registration failed — is the API running?");
      setIsSaving(false);
      return;
    }
    if (promoteTo && promoteTo !== form.status) {
      await requestJson(`/api/agent-registry/lifecycle/${form.agent_id}/status`, {
        method: "PATCH",
        headers: DEV_HEADERS,
        body: JSON.stringify({ status: promoteTo })
      });
    }
    setIsSaving(false);
    setStep("done");
    onComplete?.();
  };

  return (
    <section className="aegis-card aegis-onboard-wizard" aria-label="Agent onboarding wizard">
      <header>
        <UserPlus size={22} />
        <div>
          <h3>Onboard a production agent</h3>
          <p className="aegis-page-lead">
            Register → assign tools & data classes → start in shadow → promote when ready.
          </p>
        </div>
      </header>

      <ol className="aegis-wizard-steps">
        {(["identity", "tools", "review", "done"] as WizardStep[]).map((id, index) => (
          <li key={id} className={step === id ? "active" : step === "done" || index < ["identity", "tools", "review", "done"].indexOf(step) ? "done" : ""}>
            {id}
          </li>
        ))}
      </ol>

      {step === "identity" ? (
        <div className="aegis-wizard-grid">
          <label>
            Agent ID
            <input
              value={form.agent_id}
              onChange={(e) => setForm({ ...form, agent_id: e.target.value })}
              placeholder="agent-my-service"
            />
          </label>
          <label>
            Display name
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </label>
          <label>
            Owner team
            <input value={form.owner} onChange={(e) => setForm({ ...form, owner: e.target.value })} />
          </label>
          <label>
            Business domain
            <input
              value={form.business_domain}
              onChange={(e) => setForm({ ...form, business_domain: e.target.value })}
            />
          </label>
          <label>
            Risk tier
            <select
              value={form.risk_tier}
              onChange={(e) =>
                setForm({ ...form, risk_tier: e.target.value as (typeof RISK_TIERS)[number] })
              }
            >
              {RISK_TIERS.map((tier) => (
                <option key={tier} value={tier}>
                  {tier}
                </option>
              ))}
            </select>
          </label>
          <label>
            Autonomy level (1–4)
            <input
              type="number"
              min={1}
              max={4}
              value={form.autonomy_level}
              onChange={(e) => setForm({ ...form, autonomy_level: Number(e.target.value) })}
            />
          </label>
          <button type="button" className="aegis-btn-primary" onClick={() => setStep("tools")}>
            Next <ChevronRight size={16} />
          </button>
        </div>
      ) : null}

      {step === "tools" ? (
        <div className="aegis-wizard-tools">
          <fieldset>
            <legend>Allowed tools (gateway-enforced)</legend>
            {TOOL_OPTIONS.map((tool) => (
              <label key={tool} className="aegis-check">
                <input
                  type="checkbox"
                  checked={form.allowed_tools.includes(tool)}
                  onChange={() => toggle("allowed_tools", tool)}
                />
                {tool}
              </label>
            ))}
          </fieldset>
          <fieldset>
            <legend>Data classification scope</legend>
            {DATA_CLASSES.map((dc) => (
              <label key={dc} className="aegis-check">
                <input
                  type="checkbox"
                  checked={form.data_classes.includes(dc)}
                  onChange={() => toggle("data_classes", dc)}
                />
                {dc}
              </label>
            ))}
          </fieldset>
          <div className="aegis-wizard-nav">
            <button type="button" className="aegis-btn-ghost" onClick={() => setStep("identity")}>
              Back
            </button>
            <button type="button" className="aegis-btn-primary" onClick={() => setStep("review")}>
              Review <ChevronRight size={16} />
            </button>
          </div>
        </div>
      ) : null}

      {step === "review" ? (
        <div className="aegis-wizard-review">
          <pre>{JSON.stringify(form, null, 2)}</pre>
          <p>Start in <strong>shadow</strong> (observe only), then promote to pilot or approved.</p>
          {error ? <p className="aegis-wizard-error">{error}</p> : null}
          <div className="aegis-wizard-nav">
            <button type="button" className="aegis-btn-ghost" onClick={() => setStep("tools")}>
              Back
            </button>
            <button
              type="button"
              className="aegis-btn-secondary"
              disabled={isSaving}
              onClick={() => void register("shadow")}
            >
              Register as shadow
            </button>
            <button
              type="button"
              className="aegis-btn-primary"
              disabled={isSaving}
              onClick={() => void register("approved")}
            >
              Register & approve
            </button>
          </div>
        </div>
      ) : null}

      {step === "done" ? (
        <div className="aegis-wizard-done">
          <CheckCircle2 size={32} />
          <p>
            Agent <code>{form.agent_id}</code> registered. Route tool calls through{" "}
            <code>POST /api/gateway/tool-request</code> on Render.
          </p>
        </div>
      ) : null}
    </section>
  );
}
