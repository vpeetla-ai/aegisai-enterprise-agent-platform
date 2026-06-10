"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/api/client";

type ApiHealthBannerProps = {
  onRecheck?: () => void;
};

export function ApiHealthBanner({ onRecheck }: ApiHealthBannerProps) {
  const [status, setStatus] = useState<"checking" | "ok" | "stale" | "down">("checking");
  const [detail, setDetail] = useState("");

  async function check() {
    setStatus("checking");
    try {
      const health = await fetch(`${API_BASE_URL}/health`);
      if (!health.ok) {
        setStatus("down");
        setDetail(`Health returned ${health.status}. Start API: ./scripts/start-api.sh`);
        return;
      }
      const canary = await fetch(`${API_BASE_URL}/api/platform/developer-quickstart`);
      if (canary.status === 404) {
        setStatus("stale");
        setDetail(
          "API is running but missing buyer-module routes (404 on developer-quickstart). " +
            "Stop the old process and run: ./scripts/start-api.sh from repo root."
        );
        return;
      }
      if (!canary.ok) {
        setStatus("down");
        setDetail(`Buyer modules unavailable (${canary.status}). Check ${API_BASE_URL}/docs`);
        return;
      }
      setStatus("ok");
      setDetail(`Connected to ${API_BASE_URL}`);
    } catch {
      setStatus("down");
      setDetail(`Cannot reach ${API_BASE_URL}. Run ./scripts/start-api.sh then refresh.`);
    }
  }

  useEffect(() => {
    void check();
  }, []);

  useEffect(() => {
    if (onRecheck) {
      void check();
    }
  }, [onRecheck]);

  if (status === "ok") {
    return null;
  }

  return (
    <div className={`api-health-banner api-health-${status}`} role="status">
      <strong>
        {status === "checking"
          ? "Checking API…"
          : status === "stale"
            ? "Stale API process detected"
            : "API not reachable"}
      </strong>
      <p>{detail}</p>
      <button type="button" className="btn-secondary" onClick={() => void check()}>
        Recheck API
      </button>
    </div>
  );
}
