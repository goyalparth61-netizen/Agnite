# Security Policy

## Supported branch

The actively maintained branch is `main`.

## Reporting a vulnerability

Do not open a public issue containing secrets, exploit details or personally identifiable data.

For a security-sensitive problem, contact the repository maintainers privately through the GitHub repository owner/collaborator channels before public disclosure.

Please include:

- affected component/path;
- reproduction steps;
- impact;
- whether credentials or user data are involved;
- suggested mitigation if known.

## Secrets

AGNITE expects provider credentials only through server-side environment variables.

Never commit:

- `AGNITE_LLM_API_KEY`;
- `AGNITE_EMAIL_API_KEY`;
- NASA FIRMS MAP_KEY values;
- email subscription stores;
- local `.env` files containing secrets.

If a secret is exposed, rotate/revoke it immediately and remove it from active configuration. Git history cleanup may also be required.

## Trust boundaries

### Browser

The browser receives application data and user-visible analysis. It must not receive provider secrets.

### Node server

The server handles upstream NASA/Overpass requests, optional AI-provider calls and optional email delivery.

### External data

NASA FIRMS and OpenStreetMap/Overpass are external sources. Their content is treated as untrusted input and validated/bounded before use.

### Imported CSV

User-supplied files are parsed locally by the application and should be treated as unverified data.

## Existing safeguards

The repository includes safeguards such as:

- fixed NASA upstream URLs;
- query allowlists;
- bounded body/response sizes;
- request timeouts;
- strict CSV/date/number validation;
- duplicate handling;
- path traversal and dotfile protections in static serving;
- no-store headers for API JSON;
- explicit email consent and confirmation;
- request-rate limits for contact/subscription actions;
- server-side-only provider keys;
- deterministic CI tests.

## Deployment recommendations

- deploy behind HTTPS;
- keep dependencies current;
- use a hosting secret manager/environment settings;
- restrict access to provider dashboards;
- persist alert data only on intended storage;
- configure `AGNITE_PUBLIC_URL` to the canonical production origin;
- monitor CI and deployment logs for unexpected failures;
- never enable operational alerting until the installation has been tested end to end.

## Model and safety integrity

Misrepresenting model confidence can create a safety risk. AGNITE therefore treats model-performance claims as part of the security/safety boundary.

Do not remove or bypass:

- data provenance labels;
- insufficient-evidence abstention;
- stale-data warnings;
- simulation/heuristic labels;
- statements distinguishing thermal detections from confirmed fires.
