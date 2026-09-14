# AGNITE API Reference

Base URL in local development: `http://127.0.0.1:8787`

In production, the same Node service serves the frontend and API.

## GET `/api/health`

Health check for the application service.

Example response:

```json
{
  "status": "ok",
  "service": "agnite",
  "firms": "public-nasa-downloads"
}
```

## GET `/api/firms`

Retrieves normalized NASA FIRMS thermal observations from fixed South Asia public feeds and filters them to the application India-region bounding box.

### Query parameters

| Parameter | Allowed values | Default |
| --- | --- | --- |
| `sensor` | `snpp`, `noaa20`, `modis` | `snpp` |
| `hours` | `24`, `48`, `168` | `24` |

Example:

```text
GET /api/firms?sensor=noaa20&hours=168
```

Returned metadata includes `fetchedAt`, `latestObservation`, `sourceUrl`, `sensor`, `windowHours`, `coverage`, `cached`, `stale` and optional `warning`.

Each normalized observation contains at minimum:

```json
{
  "id": "firms-...",
  "latitude": 21.1466,
  "longitude": 79.0889,
  "observedAt": "2026-09-13T06:30:00.000Z",
  "frp": 18.2,
  "source": "firms"
}
```

Brightness and confidence are included when present upstream.

### Behaviour

- requests use fixed NASA URLs; arbitrary upstream URLs are not accepted;
- responses are capped and validated;
- successful results are cached for ten minutes;
- upstream failure returns explicitly stale cached data if available;
- no synthetic rows are inserted into NASA responses.

## GET `/api/site-context`

Returns nearby mapped context from OpenStreetMap/Overpass.

Required query parameters:

```text
latitude=<number>&longitude=<number>
```

Coordinates must be within the configured India-region bounds. Results can include industrial, power, land-use and natural features within 5 km.

Important: mapped point/centre proximity does not prove that a hotspot lies inside a facility or that a facility is active.

## POST `/api/agnite/ask`

Server-side AGNITE AI endpoint. The server uses an OpenAI-compatible provider when configured; otherwise the frontend can continue in grounded local mode.

Provider configuration is documented in [server/AI-CONFIG.md](../server/AI-CONFIG.md).

Secrets must remain server-side.

## GET `/api/alerts/status`

Returns whether email delivery/contact delivery are configured, plus last alert-check state.

## POST `/api/alerts/subscribe`

Creates an unconfirmed email subscription for nearby NASA FIRMS detections.

Required values include:

- valid `email`;
- `consent: true`;
- India-region `latitude` and `longitude`;
- `radius` from 1–500 km;
- FRP threshold from 0–1,000,000 MW.

Monitoring starts only after email confirmation.

## POST `/api/alerts/confirm`

Confirms a pending subscription using the emailed token.

## POST `/api/alerts/unsubscribe`

Deletes the subscription and saved location associated with a valid management token.

## POST `/api/contact`

Sends a project enquiry to the configured contact inbox.

Requires email delivery configuration, a valid sender email and a message between 10 and 3,000 characters.

## Errors

API errors return JSON:

```json
{
  "error": "Human-readable message"
}
```

Unknown `/api/*` routes return `404`. Unsupported methods return `405`.

## Security and privacy notes

- provider keys are not sent to the browser;
- alert/contact request bodies are size-bounded;
- email subscriptions require explicit consent and confirmation;
- cross-origin email actions are checked against the configured public URL when an Origin header is present;
- the static server rejects traversal, dotfile and unsafe path patterns.
