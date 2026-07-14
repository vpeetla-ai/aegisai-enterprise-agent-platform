"use client";

import { CheckCircle2, CircleAlert, Plug, RefreshCw, Shield, UserCheck, XCircle } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { requestJson } from "@/lib/api/client";
import { isGovernanceMetricsPayload } from "@/lib/api/safe";
import type { GatewayPayload, GovernanceMetricsPayload } from "@/lib/api/types";

type GatewayStory = {
  headline?: string;
  buyer_promise?: string;
  flow?: Array<{ step: string; control: string }>;
  supported_runtimes?: string[];
};

type GatewayPanelProps = {
  apiHealthy: boolean;
  metrics: GovernanceMetricsPayload | null;
  onRefreshMetrics: () => void;
  isLoading: boolean;
  onOpenOnboard?: () => void;
  onOpenMonitor?: () => void;
  onOpenHitl?: () => void;
};

const FLOW_STEPS = [
  {
    n: "1",
    title: "Agent wants a tool",
    detail: "e.g. deploy to Vercel, refund a customer, push code"
  },
  {
    n: "2",
    title: "Gateway intercepts",
    detail: "Checks identity, policy, kill switch, and risk"
  },
  {
    n: "3",
    title: "Decide",
    detail: "Allow · ask a human · or block — with an audit trail"
  },
  {
    n: "4",
    title: "Execute only if allowed",
    detail: "Side effect runs with a short-lived execution token"
  }
];

function decisionCopy(decision: string | undefined): {
  tone: "allow" | "hitl" | "block" | "other";
  title: string;
  body: string;
} {
  const d = (decision || "").toLowerCase();
  if (d.includes("allow") || d === "approved") {
    return {
      tone: "allow",
      title: "Allowed",
      body: "Policy passed. The agent may proceed with a short-lived execution token."
    };
  }
  if (d.includes("hitl") || d.includes("pending") || d.includes("review") || d.includes("approval")) {
    return {
      tone: "hitl",
      title: "Needs a human",
      body: "Risk is high enough that a reviewer must approve before anything runs."
    };
  }
  if (d.includes("block") || d.includes("deny") || d.includes("reject")) {
    return {
      tone: "block",
      title: "Blocked",
      body: "Policy denied this tool call. Nothing executed — evidence is in the audit log."
    };
  }
  return {
    tone: "other",
    title: decision || "Decision recorded",
    body: "The gateway returned a decision. Check the explanation below."
  };
}

export function GatewayPanel({
  apiHealthy,
  metrics,
  onRefreshMetrics,
  isLoading,
  onOpenOnboard,
  onOpenMonitor,
  onOpenHitl
}: GatewayPanelProps) {
  const [story, setStory] = useState<GatewayStory | null>(null);
  const [testResult, setTestResult] = useState<GatewayPayload | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [showDev, setShowDev] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<"checking" | "connected" | "offline">(
    "checking"
  );

  const checkConnection = useCallback(async () => {
    setConnectionStatus("checking");
    const health = await fetch("/health");
    const metricsRes = await requestJson<GovernanceMetricsPayload>(
      "/api/governance/metrics?tenant_id=bank-demo"
    );
    if (health.ok && metricsRes.payload && isGovernanceMetricsPayload(metricsRes.payload)) {
      setConnectionStatus("connected");
    } else {
      setConnectionStatus("offline");
    }
  }, []);

  useEffect(() => {
    void checkConnection();
    void (async () => {
      const storyRes = await requestJson<GatewayStory>("/api/platform/gateway-story");
      if (storyRes.payload) setStory(storyRes.payload);
    })();
  }, [checkConnection]);

  const runTestIntercept = async () => {
    setIsTesting(true);
    const { payload } = await requestJson<GatewayPayload>("/api/gateway/tool-request", {
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
        customer_impact: false
      })
    });
    setTestResult(payload);
    setIsTesting(false);
    void onRefreshMetrics();
  };

  const coverage = metrics?.gateway_coverage_pct ?? 0;
  const target = metrics?.pilot_target_pct ?? 100;
  const verdict = decisionCopy(testResult?.gateway_decision);

  return (
    <section className="aegis-page aegis-gateway" aria-label="AI Gateway">
      <header className="aegis-page-header">
        <div>
          <p className="aegis-kicker">Step 2 · Core product</p>
          <h2>AI Gateway — the seatbelt for agent tools</h2>
          <p className="aegis-page-lead">
            Agents can call dangerous tools (deploy, refund, email, git push). The{" "}
            <strong>AI Gateway</strong> stops those calls, checks policy, and only then allows
            execution. That is the product — not a chat box.
          </p>
        </div>
        <button
          type="button"
          className="aegis-btn-ghost"
          onClick={() => {
            void checkConnection();
            void onRefreshMetrics();
          }}
          disabled={isLoading}
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </header>

      <aside className="aegis-callout aegis-callout-info" role="note">
        <Shield size={18} />
        <div>
          <strong>Not the same as “LLM metrics”</strong>
          <p>
            <em>AI Gateway</em> = tool side effects (deploy / notify / refund) — the core product.{" "}
            <em>LLM metrics</em> = optional cost &amp; cache dashboard for the shared model plane.
            Different jobs on purpose (ADR-028).
          </p>
        </div>
      </aside>

      <ol className="aegis-journey-strip" aria-label="How the gateway works">
        {FLOW_STEPS.map((step) => (
          <li key={step.n}>
            <span className="aegis-journey-n">{step.n}</span>
            <strong>{step.title}</strong>
            <span>{step.detail}</span>
          </li>
        ))}
      </ol>

      <div className="aegis-gateway-proof-grid">
        <article className="aegis-card aegis-try-card">
          <p className="aegis-kicker">Try it yourself</p>
          <h3>Simulate a real tool call</h3>
          <p>
            Click once. We send a sample <code>deploy.vercel_release</code> request through the live
            gateway. You will see <strong>Allow</strong>, <strong>Needs a human</strong>, or{" "}
            <strong>Blocked</strong> — in plain language.
          </p>
          <button
            type="button"
            className="aegis-btn-primary aegis-btn-lg"
            onClick={() => void runTestIntercept()}
            disabled={!apiHealthy || isTesting}
          >
            <Plug size={18} />
            {isTesting ? "Running intercept…" : "Run sample tool intercept"}
          </button>
          {!apiHealthy ? (
            <p className="aegis-empty">API offline — use Recheck API in the header.</p>
          ) : null}

          {testResult ? (
            <div className={`aegis-verdict aegis-verdict-${verdict.tone}`} role="status">
              {verdict.tone === "allow" ? <CheckCircle2 size={28} /> : null}
              {verdict.tone === "hitl" ? <UserCheck size={28} /> : null}
              {verdict.tone === "block" ? <XCircle size={28} /> : null}
              {verdict.tone === "other" ? <CircleAlert size={28} /> : null}
              <div>
                <strong>{verdict.title}</strong>
                <p>{verdict.body}</p>
                {testResult.business_explanation ? (
                  <p className="aegis-verdict-detail">{testResult.business_explanation}</p>
                ) : null}
                <button
                  type="button"
                  className="aegis-link-btn"
                  onClick={() =>
                    verdict.tone === "hitl" ? onOpenHitl?.() : onOpenMonitor?.()
                  }
                >
                  {verdict.tone === "hitl"
                    ? "Open HITL queue to approve →"
                    : "See related activity in Monitor →"}
                </button>
              </div>
            </div>
          ) : (
            <div className="aegis-try-placeholder">
              Result appears here after you run the intercept.
            </div>
          )}
        </article>

        <div className="aegis-gateway-side-stack">
          <article
            className={`aegis-card aegis-gateway-connection status-${connectionStatus}`}
          >
            <Plug size={20} />
            <div>
              <strong>Gateway status</strong>
              <span>
                {connectionStatus === "connected"
                  ? "Live — ready to intercept"
                  : connectionStatus === "checking"
                    ? "Checking…"
                    : "Offline"}
              </span>
            </div>
            {connectionStatus === "connected" ? (
              <CheckCircle2 size={18} className="aegis-gateway-ok" />
            ) : null}
          </article>

          <article className="aegis-card aegis-gateway-metric">
            <strong>{coverage}%</strong>
            <span>Tool calls going through the gateway (target {target}%)</span>
            <div className="aegis-progress">
              <div
                className="aegis-progress-fill"
                style={{ width: `${Math.min(100, (coverage / Math.max(target, 1)) * 100)}%` }}
              />
            </div>
          </article>

          <article className="aegis-card aegis-gateway-metric">
            <strong>{metrics?.gateway_tool_calls ?? "—"}</strong>
            <span>Intercepts recorded</span>
          </article>

          <article className="aegis-card aegis-next-steps">
            <p className="aegis-kicker">What to do next</p>
            <ol>
              <li>
                <button type="button" className="aegis-link-btn" onClick={() => onOpenOnboard?.()}>
                  Onboard an agent
                </button>{" "}
                if you have not registered one yet
              </li>
              <li>Run the sample intercept above</li>
              <li>
                <button type="button" className="aegis-link-btn" onClick={() => onOpenHitl?.()}>
                  Open HITL queue
                </button>{" "}
                if the verdict needs a human
              </li>
              <li>
                <button type="button" className="aegis-link-btn" onClick={() => onOpenMonitor?.()}>
                  Open Monitor
                </button>{" "}
                to see the audit trail
              </li>
            </ol>
          </article>
        </div>
      </div>

      <article className="aegis-card">
        <div className="aegis-card-header">
          <h3>What the gateway checks</h3>
          <span>From platform story</span>
        </div>
        <ol className="aegis-gateway-flow">
          {(
            story?.flow ?? [
              { step: "Agent requests tool", control: "Normalize identity + tool scope" },
              { step: "Gateway intercepts", control: "Policy + kill switch + risk score" },
              { step: "HITL or auto-decision", control: "Issue execution token or block" },
              { step: "Broker executes", control: "Idempotent side effect + audit" }
            ]
          ).map((item) => (
            <li key={item.step}>
              <strong>{item.step}</strong>
              <span>{item.control}</span>
            </li>
          ))}
        </ol>
      </article>

      <details className="aegis-dev-details" open={showDev} onToggle={(e) => setShowDev((e.target as HTMLDetailsElement).open)}>
        <summary>For developers — SDK snippets</summary>
        <div className="aegis-gateway-grid">
          <article className="aegis-card">
            <h3>Python</h3>
            <pre className="aegis-code-block">{`from aegisai_gateway import GatewayClient, GatewayToolRequest

client = GatewayClient("https://your-aegisai-api")
result = client.request_tool(GatewayToolRequest(...))
if result.allowed:
    client.execute_with_token(execution_token=result.execution_token, ...)`}</pre>
          </article>
          <article className="aegis-card">
            <h3>TypeScript</h3>
            <pre className="aegis-code-block">{`const decision = await client.toolRequest({ agentId, toolName });
if (decision.gatewayDecision === "allow") {
  await execute(decision.executionToken);
}`}</pre>
          </article>
        </div>
      </details>
    </section>
  );
}
