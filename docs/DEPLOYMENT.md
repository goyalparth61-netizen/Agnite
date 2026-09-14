# Deployment Guide

## Recommended production model

AGNITE is designed to run as a single Node.js service that serves both:

- the compiled Vite frontend from `dist/`;
- the `/api/*` backend routes.

This keeps deployment simple and avoids browser CORS issues for the built-in API.

## Local production test

```sh
npm ci
npm test
npm run build
npm start
```

Default URL:

```text
http://127.0.0.1:8787
```

Open the workspace at:

```text
http://127.0.0.1:8787/#/workspace
```

## Environment variables

Copy `.env.example` as a reference. Do not commit real secrets.

Core runtime:

| Variable | Purpose |
| --- | --- |
| `HOST` | Bind address. Production usually uses `0.0.0.0`. |
| `PORT` | HTTP port. Hosting providers may inject this automatically. |

Optional AGNITE AI:

| Variable | Purpose |
| --- | --- |
| `AGNITE_LLM_API_KEY` | Server-only provider key |
| `AGNITE_LLM_BASE_URL` | OpenAI-compatible API base URL |
| `AGNITE_LLM_MODEL` | Provider model identifier |
| `AGNITE_LLM_SITE_URL` | Optional provider metadata |
| `AGNITE_LLM_APP_NAME` | Optional provider metadata |

Optional email/contact:

| Variable | Purpose |
| --- | --- |
| `AGNITE_EMAIL_API_KEY` | Resend API key |
| `AGNITE_EMAIL_FROM` | Verified sender address |
| `AGNITE_PUBLIC_URL` | Public application origin |
| `AGNITE_CONTACT_EMAIL` | Team enquiry destination |
| `AGNITE_ALERT_STORE` | Persistent alert subscription file |

Optional historical-model preparation:

| Variable | Purpose |
| --- | --- |
| `NASA_FIRMS_MAP_KEY` | Used by the offline historical-data downloader; not required for the live public NRT feed |

## Render

The repository includes `render.yaml`.

Current service configuration:

- Node runtime;
- `npm ci && npm run build` build command;
- `npm start` start command;
- `/api/health` health check;
- persistent disk mounted at `/var/data` for alert subscription state.

### Render setup

1. Connect the GitHub repository to Render.
2. Create a Blueprint from `render.yaml` or create a Web Service using the same commands.
3. Add optional secrets in the Render dashboard; never put them in the repository.
4. Set `AGNITE_PUBLIC_URL` to the final HTTPS origin if email subscriptions are enabled.
5. Deploy.
6. Confirm `/api/health` returns `status: ok`.
7. Open `/#/workspace` and test a NASA feed request.

## Pre-deployment checklist

```sh
npm ci
npm test
npm run build
```

Then verify:

- homepage loads;
- `/#/workspace` opens;
- `GET /api/health` succeeds;
- NASA feed either loads or reports an explicit upstream error;
- map tiles and site context are reachable;
- demo scenario works without NASA availability;
- AGNITE AI clearly shows local/provider mode;
- secrets are absent from browser bundles and Git history;
- email alerts are disabled unless all required delivery variables are configured.

## Rollback

For a failed release:

1. identify the last CI-passing commit;
2. redeploy that commit from the hosting provider or revert the breaking commit;
3. avoid editing production secrets during code rollback unless the failure is configuration-specific;
4. re-run the smoke-test checklist.

## Data persistence

The live NASA cache is in memory and resets on restart.

Email subscription state uses `AGNITE_ALERT_STORE`. On Render, the included configuration points this file at the persistent disk. Without persistent storage, subscriptions can be lost when the service restarts.

## Security notes

- use HTTPS in production;
- keep all keys server-side;
- do not create `VITE_*` variables for secrets;
- rotate any key that is accidentally committed or exposed;
- keep `AGNITE_PUBLIC_URL` aligned with the production origin when email actions are enabled.
