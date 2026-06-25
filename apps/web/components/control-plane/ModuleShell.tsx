"use client";

import { ArrowLeft } from "lucide-react";
import type { ReactNode } from "react";

type ModuleShellProps = {
  title: string;
  subtitle?: string;
  onBack: () => void;
  children: ReactNode;
};

export function ModuleShell({ title, subtitle, onBack, children }: ModuleShellProps) {
  return (
    <section className="gov-module-shell">
      <button type="button" className="gov-module-back" onClick={onBack}>
        <ArrowLeft size={16} />
        Dashboard
      </button>
      <header className="gov-module-header">
        <h2>{title}</h2>
        {subtitle ? <p>{subtitle}</p> : null}
      </header>
      {children}
    </section>
  );
}
