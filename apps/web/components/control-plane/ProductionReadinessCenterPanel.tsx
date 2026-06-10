import {
  Boxes,
  Cloud,
  GitPullRequestArrow,
  KeyRound,
  PackageCheck,
  RadioTower,
  ScrollText,
  ShieldAlert
} from "lucide-react";
import type { ReactNode } from "react";
import type {
  AgentLifecyclePayload,
  DeploymentPosturePayload,
  FlagshipDemoPayload,
  GatewaySdkPayload,
  IncidentTimelinePayload,
  PermissionMatrixPayload,
  PolicyReplayPayload,
  ReleaseGatePayload
} from "@/lib/api/types";

type ProductionReadinessCenterPanelProps = {
  sdk: GatewaySdkPayload | null;
  replay: PolicyReplayPayload | null;
  lifecycle: AgentLifecyclePayload | null;
  matrix: PermissionMatrixPayload | null;
  releaseGate: ReleaseGatePayload | null;
  incident: IncidentTimelinePayload | null;
  deployment: DeploymentPosturePayload | null;
  demo: FlagshipDemoPayload | null;
  onLoadSdk: () => void;
  onRunReplay: () => void;
  onLoadLifecycle: () => void;
  onLoadMatrix: () => void;
  onRunReleaseGate: () => void;
  onLoadIncident: () => void;
  onLoadDeployment: () => void;
  onLoadDemo: () => void;
};

export function ProductionReadinessCenterPanel({
  sdk,
  replay,
  lifecycle,
  matrix,
  releaseGate,
  incident,
  deployment,
  demo,
  onLoadSdk,
  onRunReplay,
  onLoadLifecycle,
  onLoadMatrix,
  onRunReleaseGate,
  onLoadIncident,
  onLoadDeployment,
  onLoadDemo
}: ProductionReadinessCenterPanelProps) {
  return (
    <section className="panel readiness-center">
      <div className="panel-heading compact">
        <div>
          <p className="eyebrow">Production Readiness Center</p>
          <h2>Adopt, govern, release, operate, and prove enterprise agent control</h2>
        </div>
        <ShieldAlert size={18} />
      </div>

      <div className="readiness-journey">
        <ReadinessStage label="Adopt" detail="Plug in any agent and bring it under lifecycle control.">
          <MaturityCard
            icon={<PackageCheck size={18} />}
            title="Integrate Any Agent"
            action="Show SDK contracts"
            onClick={onLoadSdk}
            summary={sdk?.headline ?? "Make AegisAI installable from LangGraph, OpenAI Agents, MCP, and custom runtimes."}
          >
            {sdk ? (
              <div className="mini-list">
                {sdk.packages.map((item) => (
                  <div key={item.name}>
                    <strong>{item.name}</strong>
                    <span>{item.runtime} · {item.status}</span>
                    <code>{item.install}</code>
                  </div>
                ))}
              </div>
            ) : null}
          </MaturityCard>
          <MaturityCard
            icon={<Boxes size={18} />}
            title="Control Agent Sprawl"
            action="Review lifecycle"
            onClick={onLoadLifecycle}
            summary={lifecycle?.headline ?? "Register, approve, revoke, and deprecate agents as governed assets."}
          >
            {lifecycle ? (
              <div className="maturity-tags">
                {lifecycle.allowed_statuses.map((status) => <span key={status}>{status}</span>)}
              </div>
            ) : null}
          </MaturityCard>
        </ReadinessStage>

        <ReadinessStage label="Govern" detail="See policy impact and tool blast radius before production harm.">
          <MaturityCard
            icon={<ScrollText size={18} />}
            title="Preview Policy Impact"
            action="Run replay"
            onClick={onRunReplay}
            summary={replay?.recommendation ?? "Preview how new policies would affect the last 30 days of agent actions."}
          >
            {replay ? (
              <div className="metric-grid compact-metrics">
                <div><span>Cases</span><strong>{replay.cases_replayed}</strong></div>
                <div><span>Changed</span><strong>{replay.changed_decisions}</strong></div>
                <div><span>Review delta</span><strong>{replay.review_load_delta_percent}%</strong></div>
              </div>
            ) : null}
          </MaturityCard>
          <MaturityCard
            icon={<KeyRound size={18} />}
            title="See Tool Blast Radius"
            action="Show matrix"
            onClick={onLoadMatrix}
            summary={matrix?.headline ?? "Show agent-to-tool authority across read, request, execute, approval, and block."}
          >
            {matrix ? (
              <div className="matrix-preview">
                <strong>{matrix.rows.length} agents</strong>
                <span>{matrix.columns.length} governed tools</span>
              </div>
            ) : null}
          </MaturityCard>
        </ReadinessStage>

        <ReadinessStage label="Release" detail="Promote agent changes only after gates pass.">
          <MaturityCard
            icon={<GitPullRequestArrow size={18} />}
            title="Approve Agent Releases"
            action="Run gate"
            onClick={onRunReleaseGate}
            summary={releaseGate?.headline ?? "Promote prompt, model, retrieval, and tool changes only after gates pass."}
          >
            {releaseGate ? (
              <div className="release-gate">
                <span className={`pill pill-${releaseGate.decision}`}>{releaseGate.decision}</span>
                <strong>{releaseGate.release_version}</strong>
                <p>{releaseGate.readiness_score}/100 readiness</p>
              </div>
            ) : null}
          </MaturityCard>
        </ReadinessStage>

        <ReadinessStage label="Operate" detail="Respond to incidents and deploy with a credible production posture.">
          <MaturityCard
            icon={<RadioTower size={18} />}
            title="Freeze Unsafe Agents"
            action="Review timeline"
            onClick={onLoadIncident}
            summary={incident?.headline ?? "Freeze, investigate, remediate, and unfreeze agent runtime scope."}
          >
            {incident ? (
              <div className="mini-list">
                {incident.events.slice(0, 3).map((event) => (
                  <div key={`${event.event}-${event.time}`}>
                    <strong>{event.event}</strong>
                    <span>{event.time}</span>
                  </div>
                ))}
              </div>
            ) : null}
          </MaturityCard>
          <MaturityCard
            icon={<Cloud size={18} />}
            title="Deploy With Confidence"
            action="Compare deployment"
            onClick={onLoadDeployment}
            summary={deployment?.production_line ?? "Separate local demo, low-cost cloud, and AWS enterprise deployment tracks."}
          >
            {deployment ? (
              <div className="maturity-tags">
                {deployment.tracks.map((track) => <span key={track.name}>{track.name}</span>)}
              </div>
            ) : null}
          </MaturityCard>
        </ReadinessStage>

        <ReadinessStage label="Prove" detail="Show the full buyer story from request to audit and ROI.">
          <MaturityCard
            icon={<ShieldAlert size={18} />}
            title="Prove End-to-End Governance"
            action="Open demo proof"
            onClick={onLoadDemo}
            summary={demo?.talk_track ?? "One flawless buyer demo from customer request to signed audit and ROI."}
          >
            {demo ? (
              <div className="matrix-preview">
                <strong>{demo.steps.length} steps</strong>
                <span>{demo.success_criteria.length} success criteria</span>
              </div>
            ) : null}
          </MaturityCard>
        </ReadinessStage>
      </div>
    </section>
  );
}

type ReadinessStageProps = {
  label: string;
  detail: string;
  children: ReactNode;
};

function ReadinessStage({ label, detail, children }: ReadinessStageProps) {
  return (
    <section className="readiness-stage">
      <header>
        <span>{label}</span>
        <p>{detail}</p>
      </header>
      <div className="readiness-stage-cards">{children}</div>
    </section>
  );
}

type MaturityCardProps = {
  icon: ReactNode;
  title: string;
  action: string;
  summary: string;
  onClick: () => void;
  children?: ReactNode;
};

function MaturityCard({ icon, title, action, summary, onClick, children }: MaturityCardProps) {
  return (
    <article className="maturity-card">
      <div className="maturity-card-header">
        <span>{icon}</span>
        <strong>{title}</strong>
      </div>
      <p>{summary}</p>
      <button className="btn-secondary" onClick={onClick}>{action}</button>
      {children}
    </article>
  );
}
