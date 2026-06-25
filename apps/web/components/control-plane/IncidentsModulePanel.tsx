"use client";

import { safeArray } from "@/lib/api/safe";
import type { IncidentTimelinePayload } from "@/lib/api/types";

type IncidentsModulePanelProps = {
  incident: IncidentTimelinePayload | null;
};

export function IncidentsModulePanel({ incident }: IncidentsModulePanelProps) {
  const events = safeArray(incident?.events);
  return (
    <div className="gov-module-panel">
      <p className="gov-module-lead">{incident?.headline ?? "Freeze, investigate, remediate, unfreeze."}</p>
      <ul className="gov-incident-list">
        {events.map((event, index) => (
          <li key={`${event.event}-${index}`}>
            <span>{event.time}</span>
            <strong>{event.event}</strong>
            <p>{event.detail}</p>
          </li>
        ))}
      </ul>
      {incident?.operating_procedure ? (
        <ol className="gov-procedure">
          {safeArray(incident.operating_procedure).map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      ) : null}
    </div>
  );
}
