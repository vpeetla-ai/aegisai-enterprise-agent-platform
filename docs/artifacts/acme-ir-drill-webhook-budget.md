# Failed webhook / budget breach — golden IR drill (ADR-032)

## Drill goal

Prove single-tenant blast radius: Slack webhook forced failure lands in DLQ and replays;
tenant budget breach freezes **acme** only.

## Steps

1. Set `SLACK_FORCE_FAIL=true` (or webhook `force_fail=true` with valid HMAC).
2. Ingest interaction → delivery status `dlq`.
3. `GET /api/webhooks/dlq?tenant_id=acme` shows the row.
4. Clear force flag; `POST /api/webhooks/{id}/replay` → `replayed`.
5. Seed FinOps `PUT /v1/budget/tenant/acme` with low budget; record usage until `breached`.
6. `GET /api/tenants/acme/budget/preflight` → `breached=true`; kill-switch activates for tenant `acme`.
7. Pull `GET /api/incidents/acme/case-drill-webhook/playbook` for post-mortem + customer comms.

## Artifact receipt

- Playbook JSON includes `post_mortem_markdown` and `customer_comms_markdown`.
- Evidence pack signature present under `evidence_pack.signature`.
- Limitations: in-memory DLQ on Free/Demo processes; Postgres-backed DLQ is Phase-2 enterprise.
