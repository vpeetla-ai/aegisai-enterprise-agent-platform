"use client";

import { buyerPersonas, type BuyerPersona } from "@/lib/controlPlanePersonas";

type PersonaChipsProps = {
  selected: BuyerPersona;
  onSelect: (persona: BuyerPersona) => void;
};

export function PersonaChips({ selected, onSelect }: PersonaChipsProps) {
  return (
    <div className="persona-chips" role="tablist" aria-label="Buyer persona">
      {buyerPersonas.map((persona) => (
        <button
          key={persona.id}
          type="button"
          role="tab"
          aria-selected={selected === persona.id}
          className={selected === persona.id ? "persona-chip persona-chip-active" : "persona-chip"}
          onClick={() => onSelect(persona.id)}
        >
          {persona.label}
        </button>
      ))}
    </div>
  );
}
