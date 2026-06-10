"use client";

import { CollapsibleSection } from "@/components/control-plane/CollapsibleSection";

type DeveloperConsolePanelProps = {
  apiResult: string;
};

export function DeveloperConsolePanel({ apiResult }: DeveloperConsolePanelProps) {
  return (
    <CollapsibleSection
      title="Developer API console"
      subtitle="Raw JSON responses for engineering validation — hidden during buyer demos."
      variant="developer"
    >
      <pre className="api-console-output">{apiResult}</pre>
    </CollapsibleSection>
  );
}
