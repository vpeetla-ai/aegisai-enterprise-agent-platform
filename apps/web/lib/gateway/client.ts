import { API_BASE_URL } from "@/lib/api/client";

export type GatewayToolRequest = {
  tenant_id?: string;
  agent_id?: string;
  principal_id?: string;
  tool_name?: string;
  action_type?: string;
  target_system?: string;
  amount_usd?: number;
  data_classification?: string;
  reversible?: boolean;
  customer_impact?: boolean;
  grounding_score?: number;
  safety_score?: number;
  policy_compliance_score?: number;
};

export type GatewayToolResult = {
  gateway_decision: string;
  execution_token?: string | null;
  business_explanation?: string;
  enforcement_steps?: string[];
  [key: string]: unknown;
};

export class AegisGatewayClient {
  constructor(
    private readonly baseUrl: string = API_BASE_URL,
    private readonly authBearer?: string
  ) {}

  async requestTool(request: GatewayToolRequest): Promise<GatewayToolResult> {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (this.authBearer) {
      headers.Authorization = `Bearer ${this.authBearer}`;
    }
    const response = await fetch(`${this.baseUrl}/api/gateway/tool-request`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        tenant_id: "bank-demo",
        agent_id: "agent-refund",
        principal_id: "execution-broker",
        tool_name: "payments.issue_refund",
        action_type: "issue_refund",
        target_system: "payments",
        amount_usd: 2500,
        data_classification: "confidential",
        customer_impact: true,
        ...request
      })
    });
    if (!response.ok) {
      throw new Error(`Gateway request failed: ${response.status}`);
    }
    return (await response.json()) as GatewayToolResult;
  }
}
