# HTTP interface

This release provides server-rendered publication pages plus small JSON operational and identity endpoints. Django REST Framework is installed for future versioned APIs, but no `/api/v1/` resource API is published yet. Clients must not treat HTML views as a stable machine API.

All public production requests use HTTPS. `GET` and `HEAD` are the only safe methods unless a route explicitly says otherwise. Error responses can be HTML; operational endpoints return JSON as shown below.

## Operational endpoints

### `GET /health/`

Process liveness. It does not query dependencies.

```json
{"status": "ok"}
```

A `200` response means the Django process can serve requests.

### `GET /ready/`

Readiness checks PostgreSQL and the configured cache.

```json
{
  "status": "ready",
  "checks": {"database": "ok", "cache": "ok"}
}
```

Returns `200` when both checks pass and `503` otherwise. Failure values expose only an exception class, not connection strings or credentials.

### `GET /metrics/`

Prometheus text exposition. This endpoint is for Alloy only. Traefik's higher-priority route denies public clients even though the Django view itself is unauthenticated. Do not remove that edge restriction without adding equivalent application authorization.

## Identity endpoints

These routes are mounted below `/accounts/`.

| Method and path | Behavior |
|---|---|
| `GET /accounts/login/?next=/admin/` | Starts FusionAuth Authorization Code + PKCE login; an unsafe external `next` URL is ignored |
| `GET /accounts/callback/` | Validates state, exchanges the authorization code, retrieves UserInfo, and starts the Django session |
| `GET` or `POST /accounts/logout/` | Ends the Django session and redirects through FusionAuth logout when configured |
| `GET /accounts/status/` | Returns `{"authenticated": false, "user": null}` or the authenticated username |

The callback parameters and token exchange are protocol details, not a supported application API. Never log authorization codes, access tokens, session cookies, or client secrets.

## Publication routes

| Path | Query parameters | Result |
|---|---|---|
| `/publications/` | `q`, `category`, `keyword`, `series`, `type`, `page` | Public publication index, 12 results per page |
| `/publications/<slug>/` | none | Published article and rendered citations |
| `/people/` | none | Active contributor index |
| `/people/<slug>/` | none | Contributor profile and publications |
| `/sources/` | `q`, `type`, `year`, `page` | Active source index, 24 results per page |
| `/sources/<slug>/` | `format=csl-json` optional | Human-readable source page or CSL-JSON object |
| `/series/` | none | Active series index |
| `/series/<slug>/` | `page` | Series detail, 20 publications per page |
| `/search/` | `q`, `type`, `page` | Cross-content search; `type` is `all`, `publication`, `person`, or `source` |
| `/sitemap.xml` | none | Wagtail XML sitemap |

Only active/public/live records are returned by the selectors behind these routes. Invalid pages fall back to a valid paginator page. Unknown slugs return `404`.

### CSL-JSON response

`GET /sources/<slug>/?format=csl-json` is the one content-oriented JSON representation in this release. Its keys follow the Citation Style Language JSON shape and vary by source type. Consumers should tolerate absent optional fields. Example:

```json
{
  "id": "smith-1776",
  "type": "book",
  "title": "Example title",
  "issued": {"date-parts": [[1776]]}
}
```

## Caching, throttling, and versioning

Cloudflare may cache anonymous GET responses according to response headers, but must bypass cache for `/admin/`, `/django-admin/`, `/accounts/`, `/ready/`, and any request carrying a session cookie. The edge rate limiter is a coarse abuse control, not an API quota.

Any future machine API must be introduced under `/api/v1/`, document authentication and rate limits, use explicit serializers rather than model dumps, and ship compatibility tests before public use.

