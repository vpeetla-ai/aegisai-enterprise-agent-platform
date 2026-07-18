"use client";

import { useCallback, useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/api/client";

export type ApiHealthStatus = "checking" | "ok" | "stale" | "down";

export type ReviewModePosture = {
  productionStrict: boolean | null;
  failClosedReady: boolean | null;
};

export function useApiHealth() {
  const [status, setStatus] = useState<ApiHealthStatus>("checking");
  const [detail, setDetail] = useState("");
  const [reviewMode, setReviewMode] = useState<ReviewModePosture>({
    productionStrict: null,
    failClosedReady: null,
  });

  const check = useCallback(async () => {
    setStatus("checking");
    try {
      const health = await fetch(`${API_BASE_URL}/health`);
      if (!health.ok) {
        setStatus("down");
        setDetail(`Health returned ${health.status}. Run: AEGISAI_FORCE_RESTART=1 ./scripts/start-api.sh`);
        setReviewMode({ productionStrict: null, failClosedReady: null });
        return false;
      }
      try {
        const body = (await health.json()) as {
          enforcement?: {
            production_strict?: boolean;
            pilot_profile?: { fail_closed_ready?: boolean };
          };
        };
        setReviewMode({
          productionStrict: Boolean(body.enforcement?.production_strict),
          failClosedReady: Boolean(body.enforcement?.pilot_profile?.fail_closed_ready),
        });
      } catch {
        setReviewMode({ productionStrict: null, failClosedReady: null });
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
      setDetail("Connected · API proxied via Next.js");
      return true;
    } catch {
      setStatus("down");
      setDetail("Cannot reach API. Run ./scripts/start-api.sh then ./scripts/start-web.sh");
      setReviewMode({ productionStrict: null, failClosedReady: null });
      return false;
    }
  }, []);

  useEffect(() => {
    void check();
  }, [check]);

  return { status, detail, check, isReady: status === "ok", reviewMode };
}
