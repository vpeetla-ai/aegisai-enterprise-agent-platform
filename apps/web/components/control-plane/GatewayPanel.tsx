"use client";

import { CheckCircle2, Plug, RefreshCw, Shield, Zap } from "lucide-react";
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

type GatewayQuickstart = {
  steps?: string[];
  python?: string;
  typescript?: string;
};

type GatewayPanelProps = {
  apiHealthy: boolean;
  metrics: GovernanceMetricsPayload | null;
  onRefreshMetrics: () => void;
  isLoading: boolean;
};

export function GatewayPanel({
  apiHealthy,
  metrics,
  onRefreshMetrics,
  isLoading
}: GatewayPanelProps) {
  const [story, setStory] = useState<GatewayStory | null>(null);
  const [quickstart, setQuickstart] = useState<GatewayQuickstart | null>(null);
  const [testResult, setTestResult] = useState<GatewayPayload | null>(null);
  const [isTesting, setIsTesting] = useState(false);
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

  const loadGatewayMeta = useCallback(async () => {
    const [storyRes, qsRes] = await Promise.all([
      requestJson<GatewayStory>("/api/platform/gateway-story"),
      requestJson<GatewayQuickstart>("/api/platform/developer-quickstart")
    ]);
    if (storyRes.payload) setStory(storyRes.payload);
    if (qsRes.payload) setQuickstart(qsRes.payload);
  }, []);

  useEffect(() => {
    void checkConnection();
    void loadGatewayMeta();
  }, [checkConnection, loadGatewayMeta]);

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

  return (
    <section className="aegis-page aegis-gateway" aria-label="AI Gateway">
      <header className="aegis-page-header">
        <div>
          <p className="aegis-kicker">AI Gateway</p>
          <h2>{story?.headline ?? "Runtime gateway for every agent tool call"}</h2>
          <p className="aegis-page-lead">
            {story?.buyer_promise ??
              "Intercept side-effecting calls, enforce policy, issue execution tokens, and audit evidence."}
          </p>
        </div>
        <button
          type="button"
          className="aegis-btn-ghost"
          onClick={() => {
            void checkConnection();
            void onRefreshMetrics();
            void loadGatewayMeta();
          }}
          disabled={isLoading}
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </header>

      <div className="aegis-gateway-status-row">
        <article
          className={`aegis-card aegis-gateway-connection status-${connectionStatus}`}
        >
          <Plug size={22} />
          <div>
            <strong>Gateway connection</strong>
            <span>
              {connectionStatus === "connected"
                ? "API + metrics reachable"
                : connectionStatus === "checking"
                  ? "Checking…"
                  : "Offline — start ./scripts/dev.sh"}
            </span>
          </div>
          {connectionStatus === "connected" ? (
            <CheckCircle2 size={20} className="aegis-gateway-ok" />
          ) : null}
        </article>

        <article className="aegis-card aegis-gateway-metric">
          <Shield size={22} />
          <div>
            <strong>{coverage}%</strong>
            <span>Gateway coverage / {target}% target</span>
          </div>
          <div className="aegis-progress">
            <div
              className="aegis-progress-fill"
              style={{ width: `${Math.min(100, (coverage / target) * 100)}%` }}
            />
          </div>
        </article>

        <article className="aegis-card aegis-gateway-metric">
          <Zap size={22} />
          <div>
            <strong>{metrics?.gateway_tool_calls ?? "—"}</strong>
            <span>Tool calls intercepted</span>
          </div>
        </article>

        <article className="aegis-card aegis-gateway-metric">
          <Zap size={22} />
          <div>
            <strong>{metrics?.executions_with_token ?? "—"}</strong>
            <span>Token-bound executions</span>
          </div>
        </article>
      </div>

      <div className="aegis-gateway-grid">
        <article className="aegis-card">
          <h3>Gateway flow</h3>
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
          <div className="aegis-integration-grid">
            {(story?.supported_runtimes ?? ["LangGraph", "MCP", "Custom Python/TS"]).map(
              (runtime) => (
                <span key={runtime} className="aegis-integration-tile">
                  {runtime}
                </span>
              )
            )}
          </div>
        </article>

        <article className="aegis-card">
          <h3>Test live intercept</h3>
          <p className="aegis-page-lead">
            Simulates a governed deploy tool call from the Website Build FE agent through the
            gateway.
          </p>
          <button
            type="button"
            className="aegis-btn-primary"
            onClick={() => void runTestIntercept()}
            disabled={!apiHealthy || isTesting}
          >
            {isTesting ? "Intercepting…" : "POST /api/gateway/tool-request"}
          </button>
          {testResult ? (
            <div className="aegis-gateway-test-result">
              <span className={`aegis-status-pill ${testResult.gateway_decision}`}>
                {testResult.gateway_decision}
              </span>
              {testResult.execution_token ? (
                <code>Token issued (redacted in UI)</code>
              ) : (
                <span>{testResult.business_explanation ?? "Routed to HITL or blocked by policy"}</span>
              )}
            </div>
          ) : null}
        </article>
      </div>

      <div className="aegis-gateway-grid">
        <article className="aegis-card">
          <h3>Python SDK</h3>
          <pre className="aegis-code-block">
            {quickstart?.python ??
              `from aegisai_gateway import GatewayClient, GatewayToolRequest

client = GatewayClient("http://localhost:8000")
result = client.request_tool(GatewayToolRequest(...))
if result.allowed:
    client.execute_with_token(execution_token=result.execution_token, ...)`}
          </pre>
        </article>
        <article className="aegis-card">
          <h3>TypeScript SDK</h3>
          <pre className="aegis-code-block">
            {quickstart?.typescript ??
              `import { AegisGatewayClient } from "@/lib/gateway/client";

const decision = await client.toolRequest({ agentId, toolName });
if (decision.gatewayDecision === "allow") await execute(decision.executionToken);`}
          </pre>
        </article>
      </div>

      {quickstart?.steps ? (
        <article className="aegis-card">
          <h3>Onboard a production agent</h3>
          <ol className="aegis-gateway-onboard">
            {quickstart.steps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </article>
      ) : null}
    </section>
  );
}
