"use client";

import { safeArray } from "@/lib/api/safe";
import type { IdentityGraphPayload } from "@/lib/api/types";

type IdentityGraphVizProps = {
  graph: IdentityGraphPayload | null;
};

export function IdentityGraphViz({ graph }: IdentityGraphVizProps) {
  const nodes = safeArray(graph?.nodes).slice(0, 12);
  const edges = safeArray(graph?.edges).slice(0, 10);

  if (!graph) {
    return <p className="empty-state">Identity graph loads with buyer demo.</p>;
  }

  return (
    <div className="identity-graph-viz">
      <div className="graph-stats">
        <span>{graph.blast_radius.privileged_principals} privileged principals</span>
        <span>{graph.blast_radius.side_effecting_tools} side-effecting tools</span>
      </div>
      <div className="identity-graph-grid">
        {nodes.map((node) => (
          <div key={node.id} className={`graph-node graph-node-${node.kind}`}>
            <strong>{node.label}</strong>
            <small>{node.kind} · {node.risk}</small>
          </div>
        ))}
      </div>
      <div className="edge-list">
        {edges.map((edge) => (
          <small key={`${edge.from}-${edge.to}`}>
            {edge.from.replace(/^.*:/, "")} → {edge.relationship} → {edge.to.replace(/^.*:/, "")}
          </small>
        ))}
      </div>
    </div>
  );
}
