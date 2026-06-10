"use client";

import { Cable, CheckCircle2, Plug, Shield } from "lucide-react";
import type { ConnectorCatalogPayload } from "@/lib/api/types";

type ConnectorCatalogPanelProps = {
  catalog: ConnectorCatalogPayload | null;
  onLoad: () => void;
  isLoading?: boolean;
};

export function ConnectorCatalogPanel({ catalog, onLoad, isLoading }: ConnectorCatalogPanelProps) {
  const connectors = Array.isArray(catalog?.connectors) ? catalog.connectors : [];

  return (
    <section className="product-panel connector-catalog-panel" aria-label="Enterprise connector catalog">
      <header className="product-panel-header">
        <div>
          <p className="eyebrow">Integrate · Universal execution</p>
          <h2>Enterprise connector catalog</h2>
          <p className="product-panel-lead">
            AegisAI is not a Stripe product. Govern any agent tool call, then execute through the
            connector that matches your stack — payments, CRM, ITSM, data, MCP, or custom HTTP.
          </p>
        </div>
        <button type="button" className="btn-primary" onClick={onLoad} disabled={isLoading}>
          {isLoading ? "Loading…" : "Refresh catalog"}
        </button>
      </header>

      {!catalog ? (
        <div className="product-panel-empty">
          <Plug size={28} />
          <p>Refresh the live connector registry from the control plane API.</p>
        </div>
      ) : (
        <>
          <div className="connector-stats">
            <article>
              <Cable size={18} />
              <span>Registered connectors</span>
              <strong>{catalog.total ?? connectors.length}</strong>
            </article>
            <article>
              <Shield size={18} />
              <span>Governance</span>
              <strong>Gateway + broker</strong>
            </article>
            <article>
              <CheckCircle2 size={18} />
              <span>Strategy</span>
              <strong className="connector-strategy">{catalog.strategy}</strong>
            </article>
          </div>
          <div className="connector-grid">
            {connectors.map((connector) => {
              const supportedTools = connector.supported_tools ?? [];
              return (
              <article
                className={`connector-card${connector.kind === "http" ? " connector-card-http" : ""}`}
                key={connector.connector_id}
              >
                <div className="connector-card-head">
                  <span className="connector-provider">{connector.provider}</span>
                  {connector.kind === "http" ? (
                    <span className="connector-kind-badge">HTTP · registered</span>
                  ) : null}
                  <code>{connector.connector_id}</code>
                </div>
                {connector.display_name ? (
                  <p className="connector-display-name">{connector.display_name}</p>
                ) : null}
                {connector.base_url_host ? (
                  <p className="connector-host">{connector.base_url_host}</p>
                ) : null}
                <ul>
                  {supportedTools.length > 0 ? (
                    supportedTools.map((tool) => <li key={tool}>{tool}</li>)
                  ) : (
                    <li>Any tool on target system (generic routing)</li>
                  )}
                </ul>
              </article>
              );
            })}
          </div>
        </>
      )}
    </section>
  );
}
