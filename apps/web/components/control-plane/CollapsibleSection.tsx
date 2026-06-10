"use client";

import { ChevronDown } from "lucide-react";
import { useState, type ReactNode } from "react";

type CollapsibleSectionProps = {
  id?: string;
  title: string;
  subtitle?: string;
  defaultOpen?: boolean;
  children: ReactNode;
  variant?: "default" | "developer";
};

export function CollapsibleSection({
  id,
  title,
  subtitle,
  defaultOpen = false,
  children,
  variant = "default"
}: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <section id={id} className={`collapsible-section collapsible-section-${variant}`}>
      <button
        type="button"
        className="collapsible-trigger"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <div>
          <h2>{title}</h2>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
        <ChevronDown size={20} className={open ? "chevron-open" : ""} />
      </button>
      {open ? <div className="collapsible-body">{children}</div> : null}
    </section>
  );
}
