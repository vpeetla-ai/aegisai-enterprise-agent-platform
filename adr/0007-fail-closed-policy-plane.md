# ADR-0007 — Fail-closed policy plane under PRODUCTION_STRICT

**Status:** Accepted  
**Date:** 2026-08-08  
**Repos:** aegisai-enterprise-agent-platform

## Context

Demo mode may evaluate policy with the builtin `PolicyEngine` when the OPA CLI
or Rego pack is unavailable. That is correct for local demos, but a Principal
governance brand cannot silently allow irreversible tools when the policy plane
is down.

## Decision

Under `PRODUCTION_STRICT=true`:

- Irreversible tools, customer-impact tools, and high/critical risk actions
  **deny** with `policy_version=policy_unavailable` when OPA is missing or
  `opa eval` errors.
- `/health` exposes `policy_plane` posture (`opa` | `builtin` | `unavailable`).
- Demo (`PRODUCTION_STRICT` unset/false) keeps builtin fallback.

## Consequences

- Pilot Strict profile requires the OPA CLI + `platform/policy/aegisai.rego`.
- Unit tests monkeypatch `OpaPolicyEngine.available` — no OPA install required
  for CI.
- LinkedIn / README claims must say “hard-block under Strict,” not “OPA always on.”
