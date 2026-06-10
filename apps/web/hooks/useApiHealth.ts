"use client";

import { useCallback, useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/api/client";

export type ApiHealthStatus = "checking" | "ok" | "stale" | "down";

export function useApiHealth() {
  const [status, setStatus] = useState<ApiHealthStatus>("checking");
  const [detail, setDetail] = useState("");

  const check = useCallback(async () => {
    setStatus("checking");
    try {
      const health = await fetch(`${API_BASE_URL}/health`);
      if (!health.ok) {
        setStatus("down");
        setDetail(`Health returned ${health.status}. Run: AEGISAI_FORCE_RESTART=1 ./scripts/start-api.sh`);
        return false;
      }
      const canary = await fetch(`${API_BASE_URL}/api/platform/developer-quickstart`);
      if (canary.status === 404) {
        setStatus("stale");
        setDetail(
          "Stale API on port 8000 (buyer routes missing). Run: AEGISAI_FORCE_RESTART=1 ./scripts/start-api.sh"
        );
        return false;
      }
      if (!canary.ok) {
        setStatus("down");
        setDetail(`Buyer modules unavailable (${canary.status}). See ${API_BASE_URL}/docs`);
        return false;
      }
      setStatus("ok");
      setDetail(`Connected · ${API_BASE_URL}`);
      return true;
    } catch {
      setStatus("down");
      setDetail(`Cannot reach ${API_BASE_URL}. Run ./scripts/start-api.sh`);
      return false;
    }
  }, []);

  useEffect(() => {
    void check();
  }, [check]);

  return { status, detail, check, isReady: status === "ok" };
}
