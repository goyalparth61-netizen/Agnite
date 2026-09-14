# Optional email and contact delivery

Set these server environment variables before `npm run dev` or `npm start`:

| Variable | Purpose |
| --- | --- |
| `AGNITE_EMAIL_API_KEY` | Resend API key (server only) |
| `AGNITE_EMAIL_FROM` | Sender on your verified Resend domain |
| `AGNITE_PUBLIC_URL` | App origin, such as `https://agnite.example`; for development use the browser's Vite origin |
| `AGNITE_CONTACT_EMAIL` | Team inbox for project enquiries (optional) |
| `AGNITE_ALERT_STORE` | Persistent JSON file; default `.agnite/alerts.json` |

Provider reference: https://resend.com/docs/api-reference/emails/send-email

Without configuration the forms show unavailable status and do not claim delivery. Keep all keys out of `VITE_` variables. A `.env` file is not loaded automatically by the Node server; set process environment variables using your host or shell. The LLM setup is independent; see `AI-CONFIG.md`.

Subscriptions require consent and an email confirmation link valid for 24 hours. The worker checks NASA NOAA-20 acquisitions from the last 24 hours every ten minutes while the server runs. It matches distance and FRP thresholds; it does not use heuristic risk as a calibrated probability. Demo/imported/manual observations never trigger email. Stale feeds are skipped. Delivery errors retry on the next check, with acquisition deduplication and provider idempotency keys. Each alert provides a stable unsubscribe link that deletes the saved email, location and delivery history. Email clients must support HTML; an on-page SVG alert image can also be downloaded.

Run **one server process** with a durable, private data directory. This file store is an MVP implementation; multiple replicas require a shared database and coordinated worker. Do not serve the store publicly. Protect its ACLs and backups because email, coordinates and unsubscribe tokens are stored there. Pending records are purged on the next store read after 24 hours; active subscriptions persist until removal. API counters limit requests per socket IP/address, with a maximum of 1,000 records. Configure edge rate limiting for a public deployment, particularly behind proxies. No provider credentials or recipient data are exposed by the status endpoint.

No actual emails are sent by `npm test`: all provider requests are mocked. Real sender/domain verification and delivery must be checked by the installation owner after configuration.

# Nearby mapped context

`GET /api/site-context?latitude=21&longitude=79` queries the public Overpass service for mapped industry, plants, works, kilns, chimneys, forest, residential land use, woodland, water and scrub within 5 km. Results are capped and cached for one hour; concurrent requests for the same point are combined. Provider failure leaves context unknown. Attribution: https://www.openstreetmap.org/copyright

Feature centres are approximate, especially for large polygons. They do not prove that a hotspot is inside a facility, that a plant is operating, or that a heat source is deliberate. The UI supplies evidence for review while verified classifier inputs remain explicit. Weather forecasts and complete historical archives are still not connected.
