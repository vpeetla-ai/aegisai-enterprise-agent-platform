"use client";

import { GitBranch, Network, ShieldCheck } from "lucide-react";
import type { McpProxyPayload } from "@/lib/api/types";

type McpProxyPanelProps = {
  mcpResult: McpProxyPayload | null;
  onSimulate: () => void;
  isLoading?: boolean;
};

export function McpProxyPanel({ mcpResult, onSimulate, isLoading }: McpProxyPanelProps) {
  return (
    <section className="product-panel mcp-proxy-panel" aria-label="MCP governance proxy">
      <header className="product-panel-header">
        <div>
          <p className="eyebrow">Integrate · MCP</p>
          <h2>MCP governance proxy</h2>
          <p className="product-panel-lead">
            Route Model Context Protocol tool calls through the same gateway as Salesforce,
            ServiceNow, or payments — policy, HITL, and audit before the MCP server runs.
          </p>
        </div>
        <button type="button" className="btn-primary" onClick={onSimulate} disabled={isLoading}>
          {isLoading ? "Simulating…" : "Simulate MCP tool call"}
        </button>
      </header>

      <div className="mcp-flow">
        <span>
          <Network size={16} /> agent
        </span>
        <span>→</span>
        <span>
          <ShieldCheck size={16} /> gateway
        </span>
        <span>→</span>
        <span>
          <GitBranch size={16} /> MCP server
        </span>
      </div>

      {!mcpResult ? (
        <div className="product-panel-empty">
          <p>Run a sample MCP invocation to see governance routing and execution token issuance.</p>
        </div>
      ) : (
        <div className="mcp-result">
          <div className="mcp-result-row">
            <span>Server / tool</span>
            <strong>
              {mcpResult.mcp_server} · {mcpResult.tool_name}
            </strong>
          </div>
          <div className="mcp-result-row">
            <span>Gateway decision</span>
            <strong className={`pill pill-${mcpResult.gateway_decision}`}>
              {mcpResult.gateway_decision}
            </strong>
          </div>
          <div className="mcp-result-row">
            <span>MCP status</span>
            <strong>{mcpResult.mcp_invocation_status}</strong>
          </div>
          <div className="mcp-result-row">
            <span>Canonical tool</span>
            <code>{mcpResult.canonical_tool_name}</code>
          </div>
          {mcpResult.execution_token ? (
            <div className="mcp-token">
              <span>Execution token issued</span>
              <code>{mcpResult.execution_token.slice(0, 48)}…</code>
            </div>
          ) : null}
          <p className="mcp-message">{mcpResult.message}</p>
        </div>
      )}
    </section>
  );
}
