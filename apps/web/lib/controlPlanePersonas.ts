export type BuyerPersona = "finops" | "security" | "compliance";

export const buyerPersonas: Array<{
  id: BuyerPersona;
  label: string;
  headline: string;
  connectorFocus: string;
  proofLine: string;
}> = [
  {
    id: "finops",
    label: "FinOps",
    headline: "Govern money-moving agent actions before they hit production.",
    connectorFocus: "payments · refunds · credits",
    proofLine: "High-value refund requires approval, broker execution, and signed audit."
  },
  {
    id: "security",
    label: "Security",
    headline: "See blast radius and freeze unsafe agent tool paths.",
    connectorFocus: "identity graph · kill switch · gateway",
    proofLine: "No side-effecting tool executes without policy, identity, and token."
  },
  {
    id: "compliance",
    label: "Compliance",
    headline: "Archive tamper-evident evidence for every agent decision.",
    connectorFocus: "signed audit · assurance vault · policy replay",
    proofLine: "Observability shows traces — we provide packets your GRC team can archive."
  }
];

export function personaById(id: BuyerPersona) {
  return buyerPersonas.find((p) => p.id === id) ?? buyerPersonas[0];
}
