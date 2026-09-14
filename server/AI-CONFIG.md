# AGNITE AI Configuration

AGNITE AI supports two answering modes:

1. **Grounded local mode** — evidence-based answers generated from the selected hotspot, loaded history, analysis and risk/recurrence context.
2. **External provider mode** — optional server-side OpenAI-compatible chat-completions provider. The provider receives a bounded representation of selected evidence; secrets never go to the browser.

If no provider is configured, or the provider fails, AGNITE continues in local grounded mode.

## Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `AGNITE_LLM_API_KEY` | No | Server-only provider key |
| `AGNITE_LLM_BASE_URL` | No | API root; defaults to `https://api.openai.com/v1` |
| `AGNITE_LLM_MODEL` | No | Provider model identifier |
| `AGNITE_LLM_SITE_URL` | No | Optional provider metadata |
| `AGNITE_LLM_APP_NAME` | No | Optional application metadata |

Never use a `VITE_` prefix for secrets.

## Example: direct OpenAI-compatible endpoint

```env
AGNITE_LLM_API_KEY=...
AGNITE_LLM_BASE_URL=https://api.openai.com/v1
AGNITE_LLM_MODEL=gpt-4.1-mini
AGNITE_LLM_APP_NAME=AGNITE
```

## Example: OpenRouter

```env
AGNITE_LLM_API_KEY=...
AGNITE_LLM_BASE_URL=https://openrouter.ai/api/v1
AGNITE_LLM_MODEL=openai/gpt-4.1-mini
AGNITE_LLM_SITE_URL=https://your-public-app.example
AGNITE_LLM_APP_NAME=AGNITE
```

Use a model actually available to your provider account; the example identifier is not a guarantee of future provider availability.

## What is sent to the provider

When configured, a question can include a bounded evidence package containing:

- selected observation and coordinates;
- source/provenance label;
- selected-site history summary;
- recent observations (bounded);
- thermal classification and evidence when available;
- risk or historical-recurrence windows;
- mapped/supplied context;
- missing-evidence and limitation messages;
- relevant saved-report summaries.

Raw observation history is bounded before provider requests. The assistant is instructed to stay grounded in this supplied evidence and not invent incidents, causes or certainty.

## What is not sent

AGNITE does not need to send:

- server API keys;
- alert-management tokens;
- email subscription files;
- unrelated browser files;
- entire previous conversations when they are not required for the current grounded answer.

## Prediction language

AGNITE AI must preserve the active prediction mode:

### Heuristic fallback

When the recurrence artifact is untrained, future windows are a **RISK ESTIMATE / SIMULATION**. They are not fire probabilities or weather forecasts.

### Trained recurrence artifact

When a validated recurrence artifact is active, the score estimates another FIRMS thermal detection under the model's target definition. Even if a high-precision threshold reaches 99% on held-out recurrence labels, AGNITE AI must not translate that into “99% chance of fire.”

## Failure behaviour

Provider errors/timeouts must not expose secrets. The UI falls back to local grounded answers and identifies the answering mode.

## Deployment

Set provider variables in the server/hosting environment before `npm run dev` or `npm start`.

For Render or another host, configure them through the platform's secret/environment settings rather than committing a `.env` file.

See also:

- [API reference](../docs/API.md)
- [ML pipeline](../docs/ML_PIPELINE.md)
- [Data & limitations](../docs/DATA_AND_LIMITATIONS.md)
- [.env.example](../.env.example)
