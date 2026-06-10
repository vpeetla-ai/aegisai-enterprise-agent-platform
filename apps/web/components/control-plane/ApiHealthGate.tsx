"use client";

import type { ReactNode } from "react";
import type { ApiHealthStatus } from "@/hooks/useApiHealth";

type ApiHealthGateProps = {
  status: ApiHealthStatus;
  detail: string;
  onRecheck: () => void;
  children: ReactNode;
};

export function ApiHealthGate({ status, detail, onRecheck, children }: ApiHealthGateProps) {
  if (status === "checking") {
    return (
      <div className="api-health-blocker" role="status">
        <div className="skeleton-block skeleton-hero" />
        <div className="skeleton-block skeleton-panel" />
        <p>Connecting to governance API…</p>
      </div>
    );
  }

  if (status !== "ok") {
    return (
      <div className="api-health-blocker api-health-blocker-fail" role="alert">
        <h2>Connect your governance API to continue</h2>
        <p>{detail}</p>
        <pre className="code-sample">AEGISAI_FORCE_RESTART=1 ./scripts/start-api.sh</pre>
        <button type="button" className="btn-primary" onClick={() => void onRecheck()}>
          Recheck connection
        </button>
      </div>
    );
  }

  return <>{children}</>;
}
