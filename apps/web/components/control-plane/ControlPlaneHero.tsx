"use client";

import { Play, Shield } from "lucide-react";

type ControlPlaneHeroProps = {
  isRunningPlatformDemo: boolean;
  runBuyerDemo: () => void;
  openExamples: () => void;
};

export function ControlPlaneHero({
  isRunningPlatformDemo,
  runBuyerDemo,
  openExamples
}: ControlPlaneHeroProps) {
  return (
    <section className="control-plane-hero">
      <div className="control-plane-hero-copy">
        <p className="eyebrow">Agent Governance Control Plane</p>
        <h1>The operating system for governing enterprise AI agents.</h1>
        <p>
          Bring every agent, tool, policy, approval, execution, audit packet, and cost signal into
          one control plane before autonomous workflows touch production systems.
        </p>
        <ul className="control-plane-hero-bullets">
          <li>
            <Shield size={16} />
            Runtime enforcement, not observability-only traces
          </li>
          <li>Agent identity, tool authority, policy replay, HITL, and kill switches</li>
          <li>Signed evidence packets for security, compliance, finance, and operations</li>
        </ul>
      </div>
      <div className="control-plane-hero-actions">
        <button type="button" className="btn-primary btn-lg" onClick={runBuyerDemo} disabled={isRunningPlatformDemo}>
          <Play size={18} />
          {isRunningPlatformDemo ? "Running buyer demo…" : "Run governed workflow"}
        </button>
        <button type="button" className="btn-secondary" onClick={openExamples}>
          Open reference workloads
        </button>
      </div>
    </section>
  );
}
