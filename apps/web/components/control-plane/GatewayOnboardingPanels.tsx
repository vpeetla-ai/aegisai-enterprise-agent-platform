import { CheckCircle2, ShieldAlert } from "lucide-react";
import { safeArray } from "@/lib/api/safe";
import type { AgentOnboardingPayload, GatewayPayload } from "@/lib/api/types";

type GatewayOnboardingPanelsProps = {
  gatewayResult: GatewayPayload | null;
  agentOnboardingResult: AgentOnboardingPayload | null;
  runGatewayApi: () => void;
  runAgentOnboardingApi: () => void;
};

export function GatewayOnboardingPanels({
  gatewayResult,
  agentOnboardingResult,
  runGatewayApi,
  runAgentOnboardingApi
}: GatewayOnboardingPanelsProps) {
  return (
    <section className="workspace-grid">
      <section className="panel">
        <div className="panel-heading compact">
          <div>
            <p className="eyebrow">Enforce · Governance Gateway</p>
            <h2>Can any agent call a tool directly?</h2>
          </div>
          <ShieldAlert size={18} />
        </div>
        <div className="experience-actions inline-actions">
          <button onClick={() => void runGatewayApi()}>Simulate tool call</button>
        </div>
        {gatewayResult ? (
          <div className="decision-preview simulator-result">
            <div>
              <span>Gateway decision</span>
              <strong>{gatewayResult.gateway_decision}</strong>
            </div>
            <p>{gatewayResult.tool_name}</p>
            <div className="simulator-explain">
              <span>Business explanation</span>
              <p>{gatewayResult.business_explanation}</p>
              <small>{safeArray(gatewayResult.enforcement_steps).join(" · ")}</small>
            </div>
          </div>
        ) : (
          <div className="empty-results">
            <strong>Gateway simulation is ready.</strong>
            <p>Run a high-value refund tool call and watch the control plane pause it for approval before execution.</p>
          </div>
        )}
      </section>

      <section className="panel">
        <div className="panel-heading compact">
          <div>
            <p className="eyebrow">Onboard · Agent Launch Control</p>
            <h2>Should a new business agent be allowed into production?</h2>
          </div>
          <CheckCircle2 size={18} />
        </div>
        <div className="experience-actions inline-actions">
          <button onClick={() => void runAgentOnboardingApi()}>Score new agent</button>
        </div>
        {agentOnboardingResult ? (
          <>
            <div className="decision-preview simulator-result">
              <div>
                <span>Launch decision</span>
                <strong>{agentOnboardingResult.launch_decision}</strong>
              </div>
              <p>{agentOnboardingResult.readiness_score}/100</p>
              <div className="simulator-explain">
                <span>Required approver</span>
                <p>{agentOnboardingResult.required_approver}</p>
                <small>
                  Missing: {safeArray(agentOnboardingResult.missing_controls).join(" · ") || "none"}
                </small>
              </div>
            </div>
            <div className="agent-registry-list">
              {safeArray(agentOnboardingResult.control_checklist).map((item) => (
                <article className="memory-row" key={item.control}>
                  <div>
                    <strong>{item.control}</strong>
                    <p>{item.why_it_matters}</p>
                  </div>
                  <small>{item.passed ? "pass" : "missing"}</small>
                </article>
              ))}
            </div>
          </>
        ) : (
          <div className="empty-results">
            <strong>Agent onboarding score is ready.</strong>
            <p>Score a sample Salesforce agent to show launch readiness, missing controls, and required approval.</p>
          </div>
        )}
      </section>
    </section>
  );
}
