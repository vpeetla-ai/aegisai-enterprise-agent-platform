import { Activity } from "lucide-react";
import { API_BASE_URL } from "@/lib/api/client";
import type { PlatformActionKey } from "@/lib/api/types";

type ControlPlaneActionCenterProps = {
  platformActionStatus: Record<PlatformActionKey, string>;
  runPlatformPostureApi: () => void;
  runGatewayApi: () => void;
  runAgentOnboardingApi: () => void;
  runReadinessApi: (agentId?: string) => void;
  runIntegrationsApi: () => void;
};

function statusTone(status: string) {
  return status.includes("Backend unavailable") ? "error" : "";
}

export function ControlPlaneActionCenter({
  platformActionStatus,
  runPlatformPostureApi,
  runGatewayApi,
  runAgentOnboardingApi,
  runReadinessApi,
  runIntegrationsApi
}: ControlPlaneActionCenterProps) {
  return (
    <section className="panel control-action-center">
      <div className="panel-heading compact">
        <div>
          <p className="eyebrow">Control Plane Action Center</p>
          <h2>Operate the platform from the first screen</h2>
        </div>
        <Activity size={18} />
      </div>
      <div className="local-runtime-note">
        <strong>Local demo runtime required</strong>
        <p>
          These actions call FastAPI at {API_BASE_URL}. No AWS deployment or OpenAI key is required for the local demo;
          start the backend and the cards below will return live governance results.
        </p>
      </div>
      <div className="action-center-grid">
        <article className="action-card">
          <div>
            <span>Command</span>
            <strong>Executive posture</strong>
            <p>Shows agent inventory, high-risk autonomy, cost, incidents, freezes, and recommended actions.</p>
          </div>
          <button onClick={() => void runPlatformPostureApi()}>Show posture</button>
          <small className={statusTone(platformActionStatus.posture)}>{platformActionStatus.posture}</small>
        </article>
        <article className="action-card">
          <div>
            <span>Enforce</span>
            <strong>Test gateway</strong>
            <p>Simulates a side-effecting tool call before execution and proves the platform can pause or block it.</p>
          </div>
          <button onClick={() => void runGatewayApi()}>Test gateway</button>
          <small className={statusTone(platformActionStatus.gateway)}>{platformActionStatus.gateway}</small>
        </article>
        <article className="action-card">
          <div>
            <span>Onboard</span>
            <strong>Onboard agent</strong>
            <p>Scores a new Salesforce-style business agent against launch controls and missing governance gaps.</p>
          </div>
          <button onClick={() => void runAgentOnboardingApi()}>Score agent</button>
          <small className={statusTone(platformActionStatus.onboarding)}>{platformActionStatus.onboarding}</small>
        </article>
        <article className="action-card">
          <div>
            <span>Assure</span>
            <strong>Readiness score</strong>
            <p>Checks whether an existing registered agent has production controls before broader rollout.</p>
          </div>
          <button onClick={() => void runReadinessApi("agent-refund")}>Score readiness</button>
          <small className={statusTone(platformActionStatus.readiness)}>{platformActionStatus.readiness}</small>
        </article>
        <article className="action-card">
          <div>
            <span>Scale</span>
            <strong>Integrations</strong>
            <p>Explains how AegisAI governs LangGraph, OpenAI, Bedrock, Copilot Studio, Agentforce, and custom agents.</p>
          </div>
          <button onClick={() => void runIntegrationsApi()}>Show integrations</button>
          <small className={statusTone(platformActionStatus.integrations)}>{platformActionStatus.integrations}</small>
        </article>
      </div>
    </section>
  );
}
