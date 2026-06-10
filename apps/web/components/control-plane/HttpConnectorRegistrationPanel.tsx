"use client";

import { useState } from "react";
import { Globe, Link2, PlugZap, Trash2 } from "lucide-react";
import type {
  HttpConnectorListPayload,
  HttpConnectorRegisterPayload,
  HttpConnectorTestPayload
} from "@/lib/api/types";

export type HttpConnectorFormState = {
  displayName: string;
  baseUrl: string;
  targetSystem: string;
  toolNames: string;
  healthPath: string;
  executePath: string;
  authMode: "none" | "bearer" | "api_key";
  demoMode: boolean;
};

const defaultForm: HttpConnectorFormState = {
  displayName: "",
  baseUrl: "https://api.your-company.com",
  targetSystem: "custom",
  toolNames: "custom.execute_action",
  healthPath: "/health",
  executePath: "/execute",
  authMode: "none",
  demoMode: true
};

type HttpConnectorRegistrationPanelProps = {
  httpConnectors: HttpConnectorListPayload | null;
  lastTestResult: HttpConnectorTestPayload | null;
  lastRegisterResult: HttpConnectorRegisterPayload | null;
  isBusy: boolean;
  onLoad: () => void;
  onTest: (form: HttpConnectorFormState) => void;
  onRegister: (form: HttpConnectorFormState) => void;
  onDelete: (connectorId: string) => void;
};

export function HttpConnectorRegistrationPanel({
  httpConnectors,
  lastTestResult,
  lastRegisterResult,
  isBusy,
  onLoad,
  onTest,
  onRegister,
  onDelete
}: HttpConnectorRegistrationPanelProps) {
  const [form, setForm] = useState<HttpConnectorFormState>(defaultForm);
  const registeredConnectors = Array.isArray(httpConnectors?.connectors)
    ? httpConnectors.connectors
    : [];

  function updateField<K extends keyof HttpConnectorFormState>(
    key: K,
    value: HttpConnectorFormState[K]
  ) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  return (
    <section className="product-panel http-connector-panel" aria-label="Register HTTP connector">
      <header className="product-panel-header">
        <div>
          <p className="eyebrow">Integrate · BYOA</p>
          <h2>Register custom HTTP connector</h2>
          <p className="product-panel-lead">
            Plug in your billing API, internal workflow service, or webhook — same gateway and
            broker, your endpoint. Use demo mode for live pitches without calling production.
          </p>
        </div>
        <button type="button" className="btn-secondary" onClick={onLoad} disabled={isBusy}>
          {isBusy ? "Working…" : "Refresh registered"}
        </button>
      </header>

      <div className="http-connector-layout">
        <form
          className="http-connector-form"
          onSubmit={(event) => {
            event.preventDefault();
            onRegister(form);
          }}
        >
          <label>
            Display name
            <input
              required
              value={form.displayName}
              onChange={(event) => updateField("displayName", event.target.value)}
              placeholder="Acme billing API"
            />
          </label>
          <label>
            Base URL
            <input
              required
              type="url"
              value={form.baseUrl}
              onChange={(event) => updateField("baseUrl", event.target.value)}
              placeholder="https://api.acme.com"
            />
          </label>
          <label>
            Target system key
            <input
              required
              value={form.targetSystem}
              onChange={(event) => updateField("targetSystem", event.target.value)}
              placeholder="acme_billing"
            />
          </label>
          <label>
            Tool names (comma-separated)
            <input
              value={form.toolNames}
              onChange={(event) => updateField("toolNames", event.target.value)}
              placeholder="acme_billing.issue_credit"
            />
          </label>
          <div className="http-connector-form-row">
            <label>
              Health path
              <input
                value={form.healthPath}
                onChange={(event) => updateField("healthPath", event.target.value)}
              />
            </label>
            <label>
              Execute path
              <input
                value={form.executePath}
                onChange={(event) => updateField("executePath", event.target.value)}
              />
            </label>
          </div>
          <label>
            Auth mode
            <select
              value={form.authMode}
              onChange={(event) =>
                updateField("authMode", event.target.value as HttpConnectorFormState["authMode"])
              }
            >
              <option value="none">None</option>
              <option value="bearer">Bearer token</option>
              <option value="api_key">API key header</option>
            </select>
          </label>
          <label className="http-connector-checkbox">
            <input
              type="checkbox"
              checked={form.demoMode}
              onChange={(event) => updateField("demoMode", event.target.checked)}
            />
            Demo mode (skip live HTTP on execute — recommended for Bay Area / Zoom demos)
          </label>
          <div className="http-connector-actions">
            <button
              type="button"
              className="btn-secondary"
              disabled={isBusy}
              onClick={() => onTest(form)}
            >
              <PlugZap size={16} />
              Test connection
            </button>
            <button type="submit" className="btn-primary" disabled={isBusy}>
              <Link2 size={16} />
              Register connector
            </button>
          </div>
        </form>

        <aside className="http-connector-aside">
          {lastTestResult ? (
            <article
              className={
                lastTestResult.success ? "http-connector-result success" : "http-connector-result error"
              }
            >
              <strong>Connection test</strong>
              <p>{lastTestResult.message}</p>
              <span>
                {lastTestResult.status_code ?? "—"} · {lastTestResult.latency_ms}ms
              </span>
              <code>{lastTestResult.url}</code>
            </article>
          ) : null}
          {lastRegisterResult?.connector ? (
            <article className="http-connector-result success">
              <strong>Registered</strong>
              <p>{lastRegisterResult.connector.display_name}</p>
              <code>{lastRegisterResult.connector.connector_id}</code>
            </article>
          ) : null}
          {registeredConnectors.length > 0 ? (
            <ul className="http-connector-list">
              {registeredConnectors.map((connector) => (
                <li key={connector.connector_id}>
                  <div>
                    <Globe size={16} />
                    <div>
                      <strong>{connector.display_name}</strong>
                      <span>{connector.target_system}</span>
                      <code>{connector.base_url}</code>
                    </div>
                  </div>
                  <button
                    type="button"
                    className="btn-icon"
                    aria-label={`Delete ${connector.connector_id}`}
                    onClick={() => onDelete(connector.connector_id)}
                    disabled={isBusy}
                  >
                    <Trash2 size={16} />
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="http-connector-empty">No custom HTTP connectors yet. Register one for your demo stack.</p>
          )}
        </aside>
      </div>
    </section>
  );
}
