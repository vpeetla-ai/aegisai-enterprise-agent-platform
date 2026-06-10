"use client";

import { CollapsibleSection } from "@/components/control-plane/CollapsibleSection";
import { DeveloperConsolePanel } from "@/components/control-plane/DeveloperConsolePanel";
import { ExamplesHero } from "@/components/examples/ExamplesHero";
import { ProofModulesPanel } from "@/components/examples/ProofModulesPanel";
import { ReferenceArchitecturePanel } from "@/components/examples/ReferenceArchitecturePanel";
import { RunResultsPanel } from "@/components/examples/RunResultsPanel";
import { ScenarioPicker } from "@/components/examples/ScenarioPicker";
import { WorkflowLabPanel } from "@/components/examples/WorkflowLabPanel";
import { marketProblemCoverage, startupProductModules } from "@/lib/controlPlaneData";
import type {
  AgentRegistryPayload,
  AuditPacketPayload,
  ExecutionPayload,
  GoldenEvalPayload,
  IdentityPosturePayload,
  KillSwitchPayload,
  PolicySimulationPayload,
  UseCaseRun
} from "@/lib/api/types";
import { requestTemplates } from "@/lib/controlPlaneData";

type ReferenceExamplesViewProps = {
  requestText: string;
  setRequestText: (value: string) => void;
  selectedTemplateIndex: number;
  selectedTemplate: (typeof requestTemplates)[number];
  chooseTemplate: (index: number) => void;
  runAgentApi: () => void;
  runAllUseCases: () => void;
  isRunningUseCases: boolean;
  runRagApi: () => void;
  runGovernedExecutionApi: () => void;
  runAgentRegistryApi: () => void;
  agentRegistryResult: AgentRegistryPayload | null;
  runPolicySimulatorApi: (index?: number) => void;
  policySimulationResult: PolicySimulationPayload | null;
  runAuditPacketApi: () => void;
  callApi: <T = unknown>(path: string, init?: RequestInit) => Promise<T | null>;
  caseIdForTemplate: (index: number) => string;
  auditPacketResult: AuditPacketPayload | null;
  runIdentityPostureApi: () => void;
  identityPostureResult: IdentityPosturePayload | null;
  runKillSwitchApi: () => void;
  runKillSwitchPostureApi: () => void;
  killSwitchResult: KillSwitchPayload | null;
  runGoldenEvalApi: () => void;
  goldenEvalResult: GoldenEvalPayload | null;
  runUseCase: (index: number) => void;
  executionResult: ExecutionPayload | null;
  runHistory: UseCaseRun[];
  selectedRun: UseCaseRun | undefined;
  setSelectedRunId: (id: string) => void;
  apiResult: string;
  openControlPlane: () => void;
};

export function ReferenceExamplesView({
  requestText,
  setRequestText,
  selectedTemplateIndex,
  selectedTemplate,
  chooseTemplate,
  runAgentApi,
  runAllUseCases,
  isRunningUseCases,
  runRagApi,
  runGovernedExecutionApi,
  runAgentRegistryApi,
  agentRegistryResult,
  runPolicySimulatorApi,
  policySimulationResult,
  runAuditPacketApi,
  callApi,
  caseIdForTemplate,
  auditPacketResult,
  runIdentityPostureApi,
  identityPostureResult,
  runKillSwitchApi,
  runKillSwitchPostureApi,
  killSwitchResult,
  runGoldenEvalApi,
  goldenEvalResult,
  runUseCase,
  executionResult,
  runHistory,
  selectedRun,
  setSelectedRunId,
  apiResult,
  openControlPlane
}: ReferenceExamplesViewProps) {
  return (
    <div className="examples-page">
      <ExamplesHero
        isRunningUseCases={isRunningUseCases}
        onRunScenario={() => void runUseCase(selectedTemplateIndex)}
        onRunAll={() => void runAllUseCases()}
        onCheckEvidence={() => void runRagApi()}
        onBackToControlPlane={openControlPlane}
      />

      <section className="examples-value-strip" aria-label="What these scenarios prove">
        {marketProblemCoverage.slice(0, 3).map((item) => (
          <article key={item.problem}>
            <span>{item.problem}</span>
            <strong>{item.capability}</strong>
            <p>{item.proof}</p>
          </article>
        ))}
      </section>

      <ScenarioPicker
        selectedIndex={selectedTemplateIndex}
        onSelect={chooseTemplate}
        onRun={(index) => void runUseCase(index)}
      />

      <WorkflowLabPanel
        requestText={requestText}
        setRequestText={setRequestText}
        selectedTemplate={selectedTemplate}
        onRunAgents={() => void runAgentApi()}
        onApproveExecute={() => void runGovernedExecutionApi()}
        executionResult={executionResult}
      />

      <RunResultsPanel
        runHistory={runHistory}
        selectedRun={selectedRun}
        setSelectedRunId={setSelectedRunId}
      />

      <CollapsibleSection
        title="Platform modules (API smoke tests)"
        subtitle="Registry, policy simulator, audit, identity, kill switch, golden evals"
        defaultOpen={false}
      >
        <ProofModulesPanel
          runAgentRegistryApi={runAgentRegistryApi}
          agentRegistryResult={agentRegistryResult}
          runPolicySimulatorApi={runPolicySimulatorApi}
          policySimulationResult={policySimulationResult}
          runAuditPacketApi={runAuditPacketApi}
          auditPacketResult={auditPacketResult}
          onCheckPdf={() =>
            void callApi(`/api/audit-packets/bank-demo/${caseIdForTemplate(selectedTemplateIndex)}.pdf`)
          }
          runIdentityPostureApi={runIdentityPostureApi}
          identityPostureResult={identityPostureResult}
          runKillSwitchApi={runKillSwitchApi}
          runKillSwitchPostureApi={runKillSwitchPostureApi}
          killSwitchResult={killSwitchResult}
          runGoldenEvalApi={runGoldenEvalApi}
          goldenEvalResult={goldenEvalResult}
        />
      </CollapsibleSection>

      <CollapsibleSection
        title="Architecture reference"
        subtitle="Journey, business rules, agents, retrieval memory, broker steps"
        defaultOpen={false}
      >
        <ReferenceArchitecturePanel />
      </CollapsibleSection>

      <CollapsibleSection
        title="Product modules map"
        subtitle="How proof workloads map to Discover · Govern · Execute · Assure"
        defaultOpen={false}
      >
        <div className="examples-module-map">
          {startupProductModules.map((module) => (
            <article key={module.label}>
              <span>{module.label}</span>
              <strong>{module.headline}</strong>
              <p>{module.detail}</p>
            </article>
          ))}
        </div>
      </CollapsibleSection>

      <DeveloperConsolePanel apiResult={apiResult} />
    </div>
  );
}
