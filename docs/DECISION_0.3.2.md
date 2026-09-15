# Decision: Debian Python and a core-first dependency baseline

Scope: revise the supplied 0.3.1 source archive, not a live host or database.

- Keep Python 3.14.7; use Debian 13 for both the DHI development and runtime images.
- Pin Django 6.0.8 and Wagtail 7.4.3 as explicitly requested after the failed newer-version trials.
- Retain the Wagtail-rendered publication, all three React tools, branding, content snapshots,
  native page models, and their existing migration files.
- Install only the active application dependencies by default. Preserve unused integrations
  and editor-extension pins as qualification candidates, not an automatic installation.
- Preserve all non-Python container image source references and service topology.
- Regenerate Python locks on the Debian target. Preserve unchanged npm locks and unrelated
  image digests when explicitly refreshing the Python pair in an existing checkout.
- Add fail-closed lock checks, builder/runtime ABI checks, a native import smoke test,
  and read-only migration-history checks before the normal migration step.

This does not certify a Wagtail 8 database downgrade. Use a new project and fresh volumes,
then a reviewed data migration or a compatible restored backup if content must be moved.
No production deployment, database downgrade, credential rotation, or DNS change is authorized
by generating this bundle.
