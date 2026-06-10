"use client";

import { useState } from "react";
import {
  HttpConnectorRegistrationPanel,
  type HttpConnectorFormState
} from "@/components/control-plane/HttpConnectorRegistrationPanel";
import type {
  HttpConnectorListPayload,
  HttpConnectorRegisterPayload,
  HttpConnectorTestPayload
} from "@/lib/api/types";

const wizardSteps = ["Configure endpoint", "Test connection", "Register & govern"];

type ConnectorRegistrationWizardProps = {
  httpConnectors: HttpConnectorListPayload | null;
  lastTestResult: HttpConnectorTestPayload | null;
  lastRegisterResult: HttpConnectorRegisterPayload | null;
  isBusy: boolean;
  onLoad: () => void;
  onTest: (form: HttpConnectorFormState) => void;
  onRegister: (form: HttpConnectorFormState) => void;
  onDelete: (connectorId: string) => void;
};

export function ConnectorRegistrationWizard(props: ConnectorRegistrationWizardProps) {
  const [step, setStep] = useState(0);

  return (
    <section className="connector-wizard product-panel">
      <p className="eyebrow">Integrate · BYOA wizard</p>
      <h2>Register your HTTP connector in three steps</h2>
      <ol className="wizard-steps">
        {wizardSteps.map((label, index) => (
          <li key={label} className={index === step ? "wizard-step-active" : ""}>
            <button type="button" onClick={() => setStep(index)}>
              {index + 1}. {label}
            </button>
          </li>
        ))}
      </ol>
      {step === 0 ? (
        <p className="wizard-hint">Enter your API base URL and tool names, then test and register.</p>
      ) : null}
      {step === 1 && props.lastTestResult ? (
        <p className={`wizard-hint ${props.lastTestResult.success ? "wizard-ok" : "wizard-fail"}`}>
          Test: {props.lastTestResult.message} ({props.lastTestResult.latency_ms}ms)
        </p>
      ) : null}
      {step === 2 && props.lastRegisterResult ? (
        <p className="wizard-hint wizard-ok">
          Registered {props.lastRegisterResult.connector?.connector_id} — visible in catalog.
        </p>
      ) : null}
      <HttpConnectorRegistrationPanel
        {...props}
        onTest={(form) => {
          props.onTest(form);
          setStep(1);
        }}
        onRegister={(form) => {
          props.onRegister(form);
          setStep(2);
        }}
      />
    </section>
  );
}
