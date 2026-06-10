"use client";

import { CheckCircle2, Circle } from "lucide-react";
import type { GuidedDemoStep } from "@/components/control-plane/GuidedBuyerDemo";

const checklistItems = [
  { id: "gateway", label: "100% side-effecting calls through gateway (pilot env)" },
  { id: "hitl", label: "High-risk actions require named approver" },
  { id: "token", label: "Broker execution only with scoped token" },
  { id: "audit", label: "Signed audit packet verifies for sample case" },
  { id: "postgres", label: "Postgres as system of record (production profile)" }
] as const;

type DesignPartnerChecklistProps = {
  guidedSteps: GuidedDemoStep[];
  persistenceMode?: string;
};

export function DesignPartnerChecklist({
  guidedSteps,
  persistenceMode
}: DesignPartnerChecklistProps) {
  const done = new Set(guidedSteps.filter((s) => s.status === "done").map((s) => s.id));

  function isChecked(id: string) {
    if (id === "gateway") return done.has("gateway") && done.has("execute");
    if (id === "hitl") return done.has("hitl");
    if (id === "token") return done.has("execute");
    if (id === "audit") return done.has("audit");
    if (id === "postgres") return persistenceMode === "postgres";
    return false;
  }

  return (
    <section className="design-partner-checklist" aria-label="Design partner success criteria">
      <p className="eyebrow">90-day pilot success</p>
      <h3>Design partner checklist</h3>
      <ul>
        {checklistItems.map((item) => {
          const checked = isChecked(item.id);
          const Icon = checked ? CheckCircle2 : Circle;
          return (
            <li key={item.id} className={checked ? "checklist-done" : ""}>
              <Icon size={18} />
              <span>{item.label}</span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
