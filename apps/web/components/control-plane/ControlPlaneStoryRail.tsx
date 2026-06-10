import {
  Activity,
  CheckCircle2,
  ClipboardCheck,
  Compass,
  ShieldCheck
} from "lucide-react";

const storySteps = [
  {
    href: "#command-center",
    label: "Command",
    title: "Know the risk posture",
    proof: "Coverage, spend, incidents, freezes"
  },
  {
    href: "#buyer-demo",
    label: "Prove",
    title: "Run the governed workflow",
    proof: "Gateway, HITL, broker, signed audit"
  },
  {
    href: "#readiness-center",
    label: "Harden",
    title: "Make agents production-ready",
    proof: "Adopt, govern, release, operate, prove"
  },
  {
    href: "#governance-modules",
    label: "Explain",
    title: "Show buyer-facing controls",
    proof: "Policy, identity, assurance, FinOps"
  },
  {
    href: "#architect-console",
    label: "Integrate",
    title: "Wire real enterprise systems",
    proof: "Connectors, MCP, audit signing, APIs"
  }
];

export function ControlPlaneStoryRail() {
  return (
    <nav className="story-rail" aria-label="Control plane product story">
      <div className="story-rail-heading">
        <Compass size={18} />
        <div>
          <p className="eyebrow">UX Storyline</p>
          <strong>Follow the buyer proof path</strong>
        </div>
      </div>
      <ol>
        {storySteps.map((step, index) => (
          <li key={step.href}>
            <a href={step.href}>
              <span>{index + 1}</span>
              <div>
                <small>{step.label}</small>
                <strong>{step.title}</strong>
                <p>{step.proof}</p>
              </div>
            </a>
          </li>
        ))}
      </ol>
    </nav>
  );
}

export function BuyerProofBrief() {
  return (
    <section className="buyer-proof-brief" aria-label="Buyer proof brief">
      <article>
        <ShieldCheck size={18} />
        <div>
          <span>Problem</span>
          <strong>Agent sprawl is turning into uncontrolled tool authority.</strong>
          <p>Enterprises need runtime enforcement before autonomous agents touch refunds, CRM, data, or production operations.</p>
        </div>
      </article>
      <article>
        <Activity size={18} />
        <div>
          <span>Product thesis</span>
          <strong>AegisAI is the control plane above every agent framework.</strong>
          <p>It governs identity, policy, evaluations, HITL, execution tokens, audit packets, and cost from one operating layer.</p>
        </div>
      </article>
      <article>
        <ClipboardCheck size={18} />
        <div>
          <span>Demo promise</span>
          <strong>Every CTA should prove a buyer-critical control.</strong>
          <p>Run the demo, inspect readiness, open governance modules, then show how architects connect real systems.</p>
        </div>
      </article>
      <article>
        <CheckCircle2 size={18} />
        <div>
          <span>Success signal</span>
          <strong>The platform blocks unsafe autonomy without slowing safe work.</strong>
          <p>The signed evidence trail makes the decision explainable to security, compliance, finance, and operations.</p>
        </div>
      </article>
    </section>
  );
}
