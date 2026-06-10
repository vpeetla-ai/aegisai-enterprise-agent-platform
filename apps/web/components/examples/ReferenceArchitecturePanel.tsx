"use client";

import { Database, Layers3, ShieldAlert } from "lucide-react";
import {
  agents,
  businessRulePlaybook,
  executionBrokerSteps,
  experienceJourney,
  memoryContracts
} from "@/lib/controlPlaneData";

export function ReferenceArchitecturePanel() {
  return (
    <div className="reference-architecture">
      <section className="reference-section">
        <header>
          <Layers3 size={18} />
          <h3>Production path (6 steps)</h3>
        </header>
        <ol className="journey-timeline">
          {experienceJourney.map((item) => (
            <li key={item.step}>
              <span className="journey-step-num">{item.step}</span>
              <div>
                <small>{item.layer}</small>
                <strong>{item.title}</strong>
                <p>{item.question}</p>
                <em>{item.output}</em>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <div className="reference-two-col">
        <section className="reference-section">
          <header>
            <ShieldAlert size={18} />
            <h3>Business rules</h3>
          </header>
          <ul className="rule-list-compact">
            {businessRulePlaybook.map((rule) => (
              <li key={rule.name} className={`rule-tone-${rule.tone}`}>
                <strong>{rule.name}</strong>
                <span>{rule.decision}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="reference-section">
          <header>
            <Layers3 size={18} />
            <h3>Specialized agents</h3>
          </header>
          <ul className="agent-list-compact">
            {agents.map((agent) => {
              const Icon = agent.icon;
              return (
                <li key={agent.key}>
                  <Icon size={16} />
                  <div>
                    <strong>{agent.name}</strong>
                    <span>{agent.owner}</span>
                  </div>
                </li>
              );
            })}
          </ul>
        </section>
      </div>

      <section className="reference-section">
        <header>
          <Database size={18} />
          <h3>Hybrid retrieval memory</h3>
        </header>
        <ul className="memory-list-compact">
          {memoryContracts.map((memory) => (
            <li key={memory.source}>
              <strong>{memory.namespace}</strong>
              <span>{memory.score}</span>
              <p>{memory.content}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className="reference-section">
        <header>
          <h3>Execution broker steps</h3>
        </header>
        <div className="broker-steps">
          {executionBrokerSteps.map((step) => (
            <span key={step.label}>{step.label}</span>
          ))}
        </div>
      </section>
    </div>
  );
}
