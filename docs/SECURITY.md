# Security model, exceptions, and release review

## Public and editor trust boundaries

No production service publishes a host port. Public traffic uses the dashboard-managed Cloudflare Tunnel and private Traefik origin. Set the Cloudflare editor Access policy before routing the editor hostname. Django requires a valid signed Access JWT with the configured issuer, audience, expiration and issued-at claims, then still requires normal Wagtail authentication and permissions. Plain identity headers are not accepted as authentication.

Traefik explicitly sets the HTTPS forwarding indication on known-host routes because that entry point is reachable only through the private Tunnel network. Do not expose port 8080 publicly, attach untrusted containers to the edge network, or reuse the production forwarding policy for an arbitrary public reverse proxy. The Docker host and its administrators remain trusted. Docker socket access or root can defeat container-level trust boundaries.

There is no state-changing public widget API. Same-origin public reads need no CORS wildcard. Django retains CSRF validation on editor/session operations. Direct public-host requests cannot reach the editor URLconf or metrics endpoint. Admin route names also exist in the default resolver for management-command URL reversal; the host middleware, not missing route names, is the public-host security boundary. Public HTML uses a restrictive CSP; Wagtail editor pages are not given the public CSP because editor assets/preview have different needs.

The archive's Traefik rate limit is an aggregate per-request-host limit, not a trusted per-person identity limit. This avoids trusting caller-supplied forwarded IP headers but can throttle all readers together. Measure it and add an appropriate Cloudflare rate-limit policy when operational requirements justify one.

## Secrets and role separation

Compose secrets here are local file-backed mounts, not an encrypted secrets manager. Secret file contents are never placed in Compose environment strings. The enclosing host secret directory is 0700; individual files are 0444 so different non-root container UIDs can read their explicitly mounted files. Protect host backups, administrators, file labeling, and Docker access accordingly. Only permitted services receive each file.

PostgreSQL uses distinct bootstrap-admin, application-owner, and monitoring accounts. The application cannot create roles/databases and is not a superuser. The exporter uses pg_monitor. Initialization creates roles only on an empty data directory. Editing a secret file does not rotate an existing PostgreSQL role password. Rotate the database role and its mounted secret together using a reviewed administrative procedure, then restart the affected services.

Redis's default user is off. App and exporter users have separate credentials and hashed ACL entries. The health user is unauthenticated but restricted to PING only, with no data access. The exporter receives a JSON password map keyed by its Redis URI. Redis logical databases are not a security boundary; application cache and broker share an app credential and fault/resource domain. No Redis port is published. noeviction protects broker keys from eviction but makes memory exhaustion visible as errors. Monitor usage and separate broker/cache deployments when scale requires it.

The email password is separate and blank until configured. JWT public keys are fetched over HTTPS from the configured Access team domain. Application egress is required for this lookup and optional SMTP; the database has no internet egress network.

## Explicit host-level exceptions

| Component | Exception | Risk and control |
|---|---|---|
| cAdvisor | Privileged, rootful Linux sensor with read-only host filesystem/sysfs/Docker-data mounts | Broad host visibility and privilege. Restrict monitoring access; validate on the exact host. Omit/disable this service until reviewed on rootless, Desktop, or restricted hosts. |
| Node Exporter | Host PID namespace and read-only host root/proc/sys | Exposes sensitive host metrics. Not a tenant-isolated application component. Network collectors that would report the container namespace are disabled. |
| Docker socket proxy | Root user and mounted Docker socket; only GET/HEAD allowlisted discovery/log/stats paths | A read-only socket mount alone does not make the Docker API read-only. HAProxy filters methods/paths. Reads can still expose container metadata and logs; no untrusted clients may reach docker_api. |
| volume-init | One-shot root process with CHOWN/FOWNER/DAC_OVERRIDE | Writes ownership only on named application/monitoring volumes. No network or host filesystem mount. |
| PostgreSQL | Fixed non-root image UID/GID 70:70 with owned writable data and socket mounts | The image qualifier verifies that contract. SQL initialization uses the local bootstrap administrator; application traffic uses non-superuser credentials. |

Do not disable host SELinux globally. `compose.selinux.yaml` narrowly disables labeling separation on the three host sensors where shared host interfaces demand it. Review this exception on Fedora. Separately label project bind/secret files for container access according to the host policy, for example a persistent semanage file-context rule restricted to this project's config/secret paths. Bind mounts marked `:z` share a label within this trusted project; do not relabel `/`, `/sys`, or Docker's entire data directory. Rootless Docker and Docker Desktop require a different host-monitoring design and are not claimed supported by this bundle.

## Documented Django check exceptions

Owner: publication operator. Review deadline: 13 December 2026.

- `security.W005`: includeSubDomains is not imposed on all existing/future domain services without the owner's decision. HSTS is enabled for the served host.
- `security.W021`: preload enrollment is intentionally not asserted by generated configuration.
- `security.W019`: same-origin framing is retained for Wagtail preview rather than DENY. The public CSP also limits frame ancestors to self.

Only these three checks are silenced. All other deployment warnings fail the release command. Reassess the exceptions rather than copying the silence list to another project.

## Content and media limitations

Rich text is rendered using Wagtail's content renderer. React text is not inserted via dangerouslySetInnerHTML. Embedded JSON uses Django's escaping helper. Widget links reject active schemes and protocol-relative URLs. Missing source references block form validation and are visibly flagged by defensive rendering.

Uploaded documents use Wagtail's permission-aware serve view. Only registered images/renditions and selected safe image extensions can be served by the application image route; originals require an authenticated Wagtail administrator. **Existing rendition URLs are public even when an image was generated for a draft or restricted article. Do not upload confidential imagery to this public asset system.** A confidential-media authorization layer is outside scope. Current local-volume media storage is not an R2 migration.

Cloudflare Access does not replace least-privilege Wagtail group/workflow configuration, image collection permissions, account lifecycle management, MFA, recovery codes, or password-reset email setup. The default Reviewer group can change pages; adjust that role to your actual editorial policy before assigning it.

## Required security evidence

Run secret history and working-tree scans, image vulnerability scans, Python/npm dependency audits, deployment checks, editor denial/acceptance tests, CSRF tests, private/draft publication tests, and backup restore drills. Review cAdvisor/socket exceptions and dependency scan findings explicitly. No successful scan, penetration test, or compliance certification is asserted by this source bundle.

## Imported content and identity boundary

Imported layout IDs and fragment keys are allowlisted; text is escaped and links are validated again at render time. Original source code is retained for provenance, not executed in a Next.js runtime. Do not replace these boundaries with raw HTML editing to bypass validation.

Optional Keycloak has separate secrets/database/edge networks and requires its own administrator, MFA, recovery and federation review. It does not remove the existing Access gate. The complete requested third-party package profile is unverified; scan the resolved packages even when their editor hooks are not activated. Alertmanager is internal and has no configured outbound notification receiver.
