"use client";

type ReviewModeBannerProps = {
  productionStrict: boolean | null;
  failClosedReady?: boolean | null;
};

/**
 * Sticky Demo vs Strict strip — S2 honesty (Top-1% plan).
 * Reads PRODUCTION_STRICT from /health enforcement; never paints demo as production.
 */
export function ReviewModeBanner({ productionStrict, failClosedReady }: ReviewModeBannerProps) {
  if (productionStrict === null) {
    return (
      <div className="review-mode-banner review-mode-banner-pending" role="status">
        <strong>Checking review mode…</strong>
        <span>Reading <code>PRODUCTION_STRICT</code> from governance API health.</span>
      </div>
    );
  }

  if (productionStrict) {
    return (
      <div className="review-mode-banner review-mode-banner-strict" role="status">
        <strong>Strict review mode</strong>
        <span>
          <code>PRODUCTION_STRICT</code> is on
          {failClosedReady ? " · pilot fail-closed profile ready" : " · complete pilot profile for full fail-closed"}.
          Prefer this path for Principal panels.
        </span>
      </div>
    );
  }

  return (
    <div className="review-mode-banner review-mode-banner-demo" role="status">
      <strong>Demo review mode</strong>
      <span>
        Live default allows demo seed / fail-open paths. For Principal panels, set{" "}
        <code>PRODUCTION_STRICT=1</code> (and pilot auth/token flags) — see README Honesty section.
      </span>
    </div>
  );
}
