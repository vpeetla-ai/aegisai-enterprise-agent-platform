"use client";

import type { PolicyReplayPayload, PolicyStudioPayload } from "@/lib/api/types";

type PolicyReplayDiffProps = {
  studio: PolicyStudioPayload | null;
  replay: PolicyReplayPayload | null;
};

export function PolicyReplayDiff({ studio, replay }: PolicyReplayDiffProps) {
  if (!studio && !replay) {
    return <p className="empty-state">Policy preview loads with buyer demo.</p>;
  }

  return (
    <div className="policy-replay-diff">
      {studio ? (
        <div className="diff-card">
          <span className="eyebrow">Dry-run decision</span>
          <strong className={`pill pill-${studio.dry_run_decision}`}>{studio.dry_run_decision}</strong>
          <p>{studio.draft_rule}</p>
          <div className="diff-stats">
            <article>
              <span>Monthly intercepts</span>
              <strong>{studio.blast_radius.estimated_monthly_intercepts}</strong>
            </article>
            <article>
              <span>Review load +</span>
              <strong>{studio.blast_radius.expected_review_increase_percent}%</strong>
            </article>
          </div>
        </div>
      ) : null}
      {replay ? (
        <div className="diff-card">
          <span className="eyebrow">Historical replay</span>
          <strong>{replay.changed_decisions} decisions changed</strong>
          <p>
            {replay.cases_replayed} cases · {replay.review_load_delta_percent}% review load delta
          </p>
          <ul className="replay-case-list">
            {replay.cases.slice(0, 4).map((item) => (
              <li key={item.case_id} className={item.changed ? "replay-changed" : ""}>
                <code>{item.case_id}</code>
                <span>
                  {item.historical_decision} → {item.new_decision}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
