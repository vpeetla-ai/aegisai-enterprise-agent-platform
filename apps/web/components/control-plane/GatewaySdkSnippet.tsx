"use client";

import { useState } from "react";
import type { GatewaySdkPayload } from "@/lib/api/types";

type GatewaySdkSnippetProps = {
  sdk: GatewaySdkPayload | null;
};

export function GatewaySdkSnippet({ sdk }: GatewaySdkSnippetProps) {
  const [copied, setCopied] = useState(false);

  const snippet = `// Python — tenant: bank-demo, agent: agent-refund
import requests

decision = requests.post(
  "${sdk?.contract.request_endpoint ?? "http://localhost:8000/api/gateway/tool-request"}",
  json={
    "tenant_id": "bank-demo",
    "agent_id": "agent-refund",
    "principal_id": "platform-svc",
    "tool_name": "payments.issue_refund",
    "action_type": "issue_refund",
    "target_system": "payments",
    "amount_usd": 2500,
    "data_classification": "confidential",
    "reversible": True,
    "customer_impact": True,
    "grounding_score": 0.9,
    "safety_score": 0.95,
    "policy_compliance_score": 0.88,
  },
  headers={"X-AegisAI-Principal": "platform-svc"},
).json()

if decision.get("execution_token"):
    # Broker execute with X-AegisAI-Execution-Token header
    pass`;

  async function copy() {
    await navigator.clipboard.writeText(snippet);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  }

  if (!sdk) {
    return null;
  }

  return (
    <div className="sdk-snippet-panel">
      <div className="sdk-snippet-header">
        <span className="eyebrow">15-minute integration</span>
        <button type="button" className="btn-secondary" onClick={() => void copy()}>
          {copied ? "Copied" : "Copy snippet"}
        </button>
      </div>
      <p>{sdk.headline}</p>
      <pre className="code-sample">{snippet}</pre>
    </div>
  );
}
