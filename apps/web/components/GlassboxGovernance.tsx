"use client";

import { useMemo, useRef, useState } from "react";
import { ArchitectLandingStrip } from "@/components/ArchitectLandingStrip";
import { requestJson } from "@/lib/api/client";
import type { GatewayPayload } from "@/lib/api/types";

type PhaseTone = "idle" | "active" | "done" | "skipped";

const DEFAULT_STEPS = [
  "authorize_identity",
  "score_risk",
  "evaluate_policy",
  "decide_outcome",
];

function prettyStep(id: string): string {
  return id
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function decisionTone(decision: string | undefined): "allow" | "hitl" | "block" | "other" {
  const d = (decision || "").toLowerCase();
  if (d.includes("allow") || d === "approved") return "allow";
  if (d.includes("hitl") || d.includes("pending") || d.includes("review") || d.includes("approval")) {
    return "hitl";
  }
  if (d.includes("block") || d.includes("deny") || d.includes("reject")) return "block";
  return "other";
}

export function GlassboxGovernance() {
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GatewayPayload | null>(null);
  const [activeStep, setActiveStep] = useState<string | null>(null);
  const [doneSteps, setDoneSteps] = useState<Set<string>>(new Set());
  const timersRef = useRef<number[]>([]);

  const steps = useMemo(() => {
    if (result?.enforcement_steps?.length) return result.enforcement_steps;
    return DEFAULT_STEPS;
  }, [result]);

  async function runIntercept() {
    timersRef.current.forEach((t) => window.clearTimeout(t));
    timersRef.current = [];
    setIsRunning(true);
    setError(null);
    setResult(null);
    setActiveStep(null);
    setDoneSteps(new Set());

    const { payload, consolePayload, status } = await requestJson<GatewayPayload>(
      "/api/gateway/tool-request",
      {
        method: "POST",
        body: JSON.stringify({
          tenant_id: "bank-demo",
          agent_id: "agent-fe-builder",
          principal_id: "website-build-pipeline",
          tool_name: "deploy.vercel_release",
          action_type: "deploy_frontend",
          target_system: "vercel",
          amount_usd: 0,
          data_classification: "internal",
          reversible: true,
          customer_impact: false,
        }),
      },
    );

    setIsRunning(false);

    if (!payload) {
      setError(
        status
          ? `Gateway request failed (HTTP ${status}). API may be waking (~30s).`
          : consolePayload || "Gateway request failed — API may be waking (~30s).",
      );
      return;
    }

    setResult(payload);

    const phaseIds = payload.enforcement_steps?.length
      ? payload.enforcement_steps
      : DEFAULT_STEPS;

    setActiveStep(phaseIds[0] ?? null);
    const stepMs = 420;
    phaseIds.forEach((id, idx) => {
      timersRef.current.push(
        window.setTimeout(() => {
          setDoneSteps((prev) => {
            const next = new Set(prev);
            next.add(id);
            return next;
          });
          setActiveStep(phaseIds[idx + 1] ?? null);
        }, idx * stepMs),
      );
    });
  }

  const tone = decisionTone(result?.gateway_decision);

  return (
    <div className="gb-shell">
      <div className="gb-hero">
        <p className="gb-eyebrow">Governance · glass-box</p>
        <h2 className="gb-title">Watch policy before side effects</h2>
        <p className="gb-lede">
          Left: stack + live metrics. Center: replay <code>enforcement_steps</code> from{" "}
          <code>POST /api/gateway/tool-request</code> (post-response, not SSE). Right: run the
          governed intercept.
        </p>
      </div>

      <div className="gb-workbench">
        <aside className="gb-rail" aria-label="Architecture and metrics">
          <ArchitectLandingStrip />
        </aside>

        <section className="gb-center" aria-label="Gateway enforcement pipeline">
          <div className="gb-center-head">
            <h3>AI Gateway · enforcement replay</h3>
            <span className={`gb-badge${result ? " live" : ""}`}>
              {result ? "live steps" : "awaiting run"}
            </span>
          </div>

          <div className="gb-steps">
            {steps.map((step) => {
              let state: PhaseTone = "idle";
              if (doneSteps.has(step)) state = "done";
              else if (activeStep === step) state = "active";
              return (
                <div key={step} className={`gb-step gb-step-${state}`}>
                  <span className="gb-step-dot" aria-hidden />
                  {prettyStep(step)}
                </div>
              );
            })}
            {result ? (
              <div className={`gb-step gb-step-decision gb-decision-${tone}`}>
                <span className="gb-step-dot" aria-hidden />
                Decision: {result.gateway_decision}
              </div>
            ) : null}
          </div>

          <div className="gb-gate">
            {result ? (
              <>
                <strong>{prettyStep(activeStep || "complete")}</strong>
                <p>{result.business_explanation}</p>
              </>
            ) : (
              <p>
                Run a tool intercept to animate authorize → risk → policy → allow / HITL / block.
              </p>
            )}
          </div>

          {result?.policy_result ? (
            <div className="gb-policy">
              <div>
                <span>Risk</span>
                <strong>
                  {result.policy_result.risk_level} ({result.policy_result.risk_score})
                </strong>
              </div>
              <div>
                <span>Policy</span>
                <strong>{result.policy_result.policy_version}</strong>
              </div>
              <div>
                <span>Approval role</span>
                <strong>{result.policy_result.approval_role || "—"}</strong>
              </div>
            </div>
          ) : null}

          {result?.execution_token ? (
            <p className="gb-token">
              Execution token issued (truncated):{" "}
              <code>{result.execution_token.slice(0, 18)}…</code>
            </p>
          ) : null}
        </section>

        <aside className="gb-product" aria-label="Governed tool intercept">
          <h3>Governed tool call</h3>
          <p className="gb-guided">
            <strong>1.</strong> Agent requests <code>deploy.vercel_release</code> → <strong>2.</strong>{" "}
            Gateway evaluates → <strong>3.</strong> Allow, HITL, or block with audit.
          </p>

          <dl className="gb-facts">
            <div>
              <dt>Tenant</dt>
              <dd>bank-demo</dd>
            </div>
            <div>
              <dt>Agent</dt>
              <dd>agent-fe-builder</dd>
            </div>
            <div>
              <dt>Tool</dt>
              <dd>deploy.vercel_release</dd>
            </div>
            <div>
              <dt>Target</dt>
              <dd>vercel</dd>
            </div>
          </dl>

          <button
            type="button"
            className="gb-cta"
            onClick={() => void runIntercept()}
            disabled={isRunning}
          >
            {isRunning ? "Intercepting…" : "Run governed intercept"}
          </button>

          {error ? <p className="gb-error">{error}</p> : null}

          {result ? (
            <div className={`gb-result gb-result-${tone}`}>
              <div className="gb-result-title">{result.gateway_decision}</div>
              <p>{result.business_explanation}</p>
              {tone === "hitl" ? (
                <p className="gb-hint">
                  Open the <strong>HITL</strong> module in Operate to approve/reject the pending
                  task.
                </p>
              ) : null}
            </div>
          ) : null}
        </aside>
      </div>
    </div>
  );
}
