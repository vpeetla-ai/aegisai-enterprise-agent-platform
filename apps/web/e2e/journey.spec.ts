import { expect, test } from "@playwright/test";

const API = process.env.PLAYWRIGHT_API_URL || "http://127.0.0.1:8000";

test.describe("Control Room product journey", () => {
  test("API journey: gateway → HITL queue → approve", async ({ request }) => {
    const headers = {
      "Content-Type": "application/json",
      "X-AegisAI-Principal": "control-plane-admin",
      "X-AegisAI-Roles": "reviewer,admin",
      "X-AegisAI-Tenant": "bank-demo",
    };

    const health = await request.get(`${API}/health`);
    expect(health.ok()).toBeTruthy();
    const healthBody = await health.json();
    expect(healthBody.enforcement.pilot_profile).toBeTruthy();

    const gw = await request.post(`${API}/api/gateway/tool-request`, {
      headers,
      data: {
        tenant_id: "bank-demo",
        agent_id: "agent-fe-builder",
        principal_id: "e2e-journey",
        tool_name: "deploy.vercel_release",
        action_type: "deploy_frontend",
        target_system: "vercel",
        amount_usd: 0,
        data_classification: "internal",
        reversible: true,
        customer_impact: false,
      },
    });
    expect(gw.ok()).toBeTruthy();
    const gwBody = await gw.json();
    expect(gwBody.gateway_decision).toBe("approval_required");
    expect(gwBody.hitl_task?.proposal_id).toBeTruthy();

    const queue = await request.get(`${API}/api/hitl/queue?tenant_id=bank-demo&status=pending`);
    expect(queue.ok()).toBeTruthy();
    const queueBody = await queue.json();
    expect(queueBody.pending_count).toBeGreaterThan(0);

    const review = await request.post(`${API}/api/control-plane/reviewer-action`, {
      headers,
      data: {
        tenant_id: "bank-demo",
        case_id: gwBody.hitl_task.case_id,
        proposal_id: gwBody.hitl_task.proposal_id,
        reviewer_id: "control-plane-admin",
        action: "approve",
        reason: "Playwright journey approve",
      },
    });
    expect(review.ok()).toBeTruthy();
    const reviewBody = await review.json();
    expect(reviewBody.status).toBe("recorded");
    expect(reviewBody.execution_token).toBeTruthy();
  });

  test("UI shows journey nav including HITL queue", async ({ page }) => {
    test.skip(
      process.env.PLAYWRIGHT_SKIP_UI === "1",
      "UI server not required for API journey"
    );
    await page.goto("/");
    await expect(page.getByRole("navigation", { name: "Product journey" })).toBeVisible({
      timeout: 60_000,
    });
    await expect(page.getByRole("button", { name: /HITL queue/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /AI Gateway/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /LLM metrics/i })).toBeVisible();
    await expect(page.getByText("Optional", { exact: true }).first()).toBeVisible();
  });
});
