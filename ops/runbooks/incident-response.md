# Incident response runbook

This runbook covers security, availability, integrity, and privacy incidents. Favor evidence-backed containment over speculative broad changes.

## Severity

| Severity | Examples | Initial response target |
|---|---|---|
| SEV-1 | Public outage, active compromise, confirmed destructive data loss, credentials used by an attacker | 15 minutes |
| SEV-2 | Major feature or editor authentication unavailable, database/queue degradation, likely sensitive-data exposure | 30 minutes |
| SEV-3 | Partial degradation, isolated failed job, warning alert with customer impact risk | Four business hours |

Any responder can declare a higher severity. Lowering severity requires incident commander approval and recorded evidence.

## First 15 minutes

1. Acknowledge the alert and create one incident channel/record.
2. Assign incident commander, operations lead, communications lead, and scribe. One person may hold multiple roles for a small event, but the commander should not perform every technical action.
3. State the user-visible symptom, first known time, affected tier, and current hypothesis separately. Do not present a hypothesis as fact.
4. Freeze deployments and unrelated configuration changes.
5. Inspect Cloudflare, blackbox probes, Prometheus alerts, Grafana, Loki, and the three host service states. Correlate with the last deployment and backup.
6. Select a reversible containment action and record the operator, time, command/change, and observed result.

## Evidence collection

Capture to an incident-specific, access-controlled directory. Avoid copying full production databases or secrets.

```bash
date --utc
docker compose --env-file /etc/liberty/compose.env -f /opt/liberty/deploy/SERVER/compose.yaml ps
docker inspect CONTAINER_ID
sudo journalctl --since '2 hours ago' --output=short-iso
```

Export relevant Grafana panels and narrow Loki queries by time, host, container, request ID, and deployment delivery. Record Cloudflare security/audit event identifiers. Hash exported evidence, preserve original timestamps, and restrict access. Never paste cookies, authorization headers, OIDC codes, passwords, environment dumps, or age identities into chat/tickets.

## Triage by symptom

### Public site unavailable

Trace in order: Cloudflare DNS/tunnel status, cloudflared, Traefik, replica health, `/health/`, `/ready/`, PostgreSQL, and cache. A liveness success with readiness failure points downstream. Keep one known-good replica in service while replacing the other.

### Elevated HTTP errors or latency

Break down Traefik status/latency by router and service, then correlate Django request IDs with database connections/long transactions, Redis memory/rejections, CPU, memory, disk, and container restarts. Rate-limit abusive traffic at Cloudflare before scaling internal capacity.

### Authentication failure

Check the public FusionAuth probe, private `liberty02.internal:9011` origin, PostgreSQL health, callback URL, issuer/client configuration, and recent key/secret rotation. Do not bypass OIDC by enabling shared local credentials. Preserve at least one offline recovery superuser procedure.

### Queue backlog or duplicate work

Pause producers where possible, inspect worker health and broker memory/AOF status, then identify task names and idempotency keys. Celery delivery is at-least-once. Do not purge queues or replay tasks until the domain impact is understood and approved.

### Suspected compromise

Restrict the affected host at network boundaries, preserve volatile evidence, revoke exposed external tokens, and engage the security owner. A compromised Traefik or Alloy container with Docker socket access is a host compromise. Rebuild from known-good media. For suspected data access, preserve database, Cloudflare, FusionAuth, and object-storage audit evidence and follow applicable notification requirements.

## Communication

Publish an initial internal update for SEV-1/2 with confirmed impact, start time, current containment, and next update time. Public updates must avoid attacker-helpful detail, personal data, and unsupported restoration estimates. Use one source of truth; the communications lead keeps status pages and stakeholders consistent.

## Recovery and closure

Prefer the narrowest recovery: roll back code, replace one unhealthy replica, rotate one scoped credential, or rebuild one stateless host. Database restore is reserved for confirmed data loss/corruption and follows the disaster recovery runbook.

Before resolving, verify public health and readiness, representative anonymous/editor workflows, task processing, alert delivery, fresh backup success, and at least 30 minutes of stable metrics for SEV-1/2. Record any residual data-loss or delayed-work window.

Create a blameless post-incident review within five business days. It must include a UTC timeline, root and contributing causes, customer/data impact, why controls did or did not work, and corrective actions with owners and due dates. Test the corrective controls; closing a ticket without verification is not remediation.
