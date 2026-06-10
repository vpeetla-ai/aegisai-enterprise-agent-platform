"use client";

import type { ReactNode } from "react";

export type BuyerModuleLoadState = "idle" | "loading" | "ok" | "error";

type BuyerModuleCardProps = {
  title: string;
  eyebrow: string;
  icon: ReactNode;
  loadLabel?: string;
  loadState: BuyerModuleLoadState;
  errorMessage?: string;
  onLoad: () => void;
  children: ReactNode;
  emptyHint: string;
  wide?: boolean;
};

export function BuyerModuleCard({
  title,
  eyebrow,
  icon,
  loadLabel = "Refresh",
  loadState,
  errorMessage,
  onLoad,
  children,
  emptyHint,
  wide = false
}: BuyerModuleCardProps) {
  const showContent = loadState === "ok";

  return (
    <article
      className={`panel top-tier-card buyer-module-card${wide ? " wide" : ""}`}
    >
      <div className="panel-heading compact">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h2>{title}</h2>
        </div>
        {icon}
      </div>
      <button
        type="button"
        className="btn-secondary"
        onClick={() => void onLoad()}
        disabled={loadState === "loading"}
      >
        {loadState === "loading" ? "Loading…" : loadLabel}
      </button>
      {loadState === "error" ? (
        <p className="buyer-module-error" role="alert">
          {errorMessage ?? "API call failed. Expand Developer API console below for details."}
        </p>
      ) : null}
      {showContent ? children : loadState !== "error" ? <p className="empty-state">{emptyHint}</p> : null}
    </article>
  );
}
