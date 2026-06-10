import { Gauge, Network } from "lucide-react";
import { safeArray } from "@/lib/api/safe";
import type { IntegrationsPayload, ReadinessPayload } from "@/lib/api/types";

type ReadinessIntegrationsPanelsProps = {
  readinessResult: ReadinessPayload | null;
  integrationsResult: IntegrationsPayload | null;
  runReadinessApi: (agentId?: string) => void;
  runIntegrationsApi: () => void;
};

export function ReadinessIntegrationsPanels({
  readinessResult,
  integrationsResult,
  runReadinessApi,
  runIntegrationsApi
}: ReadinessIntegrationsPanelsProps) {
  return (
    <section className="workspace-grid">
      <section className="panel">
        <div className="panel-heading compact">
          <div>
            <p className="eyebrow">Assure · Production Readiness Score</p>
            <h2>Which existing agents are ready, restricted, or unsafe?</h2>
          </div>
          <Gauge size={18} />
        </div>
        <div className="experience-actions inline-actions">
          <button onClick={() => void runReadinessApi("agent-refund")}>Refund agent</button>
          <button onClick={() => void runReadinessApi("agent-it-ops")}>IT ops agent</button>
        </div>
        {readinessResult ? (
          <>
            <div className="decision-preview simulator-result">
              <div>
                <span>Readiness</span>
                <strong>{readinessResult.readiness_score}/100</strong>
              </div>
              <p>{readinessResult.launch_decision}</p>
              <div className="simulator-explain">
                <span>Agent</span>
                <p>{readinessResult.name ?? readinessResult.agent_id}</p>
                <small>
                  Missing: {safeArray(readinessResult.missing_controls).join(" · ") || "none"}
                </small>
              </div>
            </div>
            <div className="agent-registry-list">
              {safeArray(readinessResult.controls).map((item) => (
                <article className="memory-row" key={item.control}>
                  <div>
                    <strong>{item.control}</strong>
                    <p>{item.why_it_matters}</p>
                  </div>
                  <small>{item.passed ? "pass" : "gap"}</small>
                </article>
              ))}
            </div>
          </>
        ) : (
          <div className="empty-results">
            <strong>Readiness score is ready to run.</strong>
            <p>Score a registered agent to show production approval, eval, observability, tool, and data controls.</p>
          </div>
        )}
      </section>

      <section className="panel">
        <div className="panel-heading compact">
          <div>
            <p className="eyebrow">Scale · Bring Your Own Agent</p>
            <h2>How does this govern agents built outside AegisAI?</h2>
          </div>
          <Network size={18} />
        </div>
        <div className="experience-actions inline-actions">
          <button onClick={() => void runIntegrationsApi()}>Show integration posture</button>
        </div>
        {integrationsResult ? (
          <>
            <div className="decision-preview simulator-result">
              <div>
                <span>Strategy</span>
                <strong>{integrationsResult.product_module}</strong>
              </div>
              <p>{integrationsResult.integration_strategy}</p>
            </div>
            <div className="agent-registry-list">
              {safeArray(integrationsResult.agent_frameworks).map((framework) => (
                <article className="memory-row" key={framework.name}>
                  <div>
                    <strong>{framework.name}</strong>
                    <span>{framework.mode}</span>
                    <p>{framework.value}</p>
                  </div>
                </article>
              ))}
            </div>
            <div className="milestone-strip">
              {safeArray(integrationsResult.enterprise_connectors).map((connector) => (
                <span key={connector}>{connector}</span>
              ))}
            </div>
          </>
        ) : (
          <div className="empty-results">
            <strong>Integration posture is ready to review.</strong>
            <p>Show how AegisAI governs LangGraph, OpenAI, Bedrock, Copilot Studio, Agentforce, and custom agents.</p>
          </div>
        )}
      </section>
    </section>
  );
}
