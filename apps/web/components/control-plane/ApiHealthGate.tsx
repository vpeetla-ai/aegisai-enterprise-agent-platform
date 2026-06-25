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
  return (
    <>
      {status === "checking" ? (
        <div className="api-health-banner api-health-banner-checking" role="status">
          <span className="api-health-dot" aria-hidden />
          Connecting to governance API…
        </div>
      ) : null}

      {status === "stale" || status === "down" ? (
        <div className="api-health-banner api-health-banner-fail" role="alert">
          <div>
            <strong>API offline</strong>
            <p>{detail}</p>
          </div>
          <button type="button" className="btn-secondary" onClick={() => void onRecheck()}>
            Recheck API
          </button>
        </div>
      ) : null}

      {children}
    </>
  );
}
