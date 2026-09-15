# Dependency ownership: core first, optional integrations separately

The supported target is Python 3.14.7 on Debian 13, Django 6.0.8 and Wagtail 7.4.3.
This states the chosen baseline, not a claim that every pinned third-party package
has been installed and tested. Wagtail's 7.4 compatibility table lists Django 6.0
and Python 3.14; the complete lock still has to resolve on the build host.

## Installation boundaries

| Profile | Purpose and status |
|---|---|
| `requirements/core.in` | Active direct runtime dependencies; the approved framework rollback is here |
| `requirements/production.in` | Includes core only; generates the hashed production lock |
| `requirements/development.in` | Includes core plus test/audit tools; constrained by production.lock |
| `requirements/lock-tools.in` | Pinned pip-tools resolver; not installed in the application |
| `requirements/optional/editor-extensions.in` | Original exact third-party editor pins, kept as candidates only |
| `requirements/optional/integrations.in` | Original unused integration/direct pins, kept as candidates only |

The current site uses its own mounted-secret/environment reader, custom metrics,
file-backed Celery Beat, local media storage, and human-reviewed citation text.
The optional django-environ, django-prometheus, django-celery-beat, R2 storage,
and citeproc pins do not imply that those integrations are activated.

Django REST Framework and django-filter may be installed transitively by Wagtail.
Their earlier direct version constraints are now optional candidate constraints,
not independent overrides of Wagtail's supported dependency graph. `httpx` is
preserved as a candidate because the current application/ops code does not import it.

All original requested exact package pins are retained across core and candidate
files, except the two explicitly superseded Django/Wagtail versions. The original
full profile remains unchanged under `source-import/` for provenance.

## Lock behavior

Python locks are compiled inside the pinned Debian builder with pip-tools 7.6.1.
The resolver records its installed tooling versions in `resolver-tools.json`.
Old Python lock outputs are not used as constraints during this framework change.
The development profile is constrained by the newly resolved production lock.

Before publishing candidates, the helper installs the hashed production lock in a
clean builder environment using binary wheels only, runs pip check and native
imports, and verifies the selected Django/Wagtail/Python baseline. Missing wheels
or conflicting requirements stop the process. A failure leaves prior reviewed
lockfiles unchanged. Resolver containers receive staged inputs, not your project
secrets or old writable lockfiles.

A matching existing npm lock is preserved. `--refresh-frontend` is an explicit,
separate choice; it is not required just because Python moved to Debian. Final
builds run npm ci, TypeScript/build checks and frontend unit tests.

Input and output hashes are checked before deployment. Metadata is a consistency
check, not a digital signature or security audit. Review and commit generated
non-secret locks and metadata. Do not commit runtime/ or secrets/.

## Qualifying an optional package

Do not install the entire candidate list at once. Work in a branch and a separate
test environment. Inspect that package's supported Wagtail/Django/Python versions,
choose exactly one candidate, and constrain its resolution by the reviewed
production.lock. For example, an experimental input would include:

```text
-c ../production.lock
-r ../production.in
wagtailmedia==0.18.1
```

Compile it in the same pinned Debian builder, install it with hashes in an isolated
environment, and run pip check. Then add the package's documented settings/hooks
and test its editor forms, StreamField integration, draft preview, revisions,
publishing, accessibility and permission boundaries. A resolver success alone
is not approval to enable an editor plugin. Promote the package to core only after
those tests pass and a security scan is acceptable.

The supplied code has no universal automatic plugin-activation flag. Packages
have different integration requirements; toggling every one through an environment
variable would hide those differences rather than solve them.

## References

- https://docs.wagtail.org/en/stable-7.4.x/releases/upgrading.html
- https://docs.wagtail.org/en/stable-7.4.x/releases/7.4.3.html
- https://docs.djangoproject.com/en/6.0/releases/6.0.8/
- https://pip-tools.readthedocs.io/en/stable/
- https://hub.docker.com/hardened-images/catalog/dhi/python/guides

These describe upstream behavior, not successful execution of this repository.
