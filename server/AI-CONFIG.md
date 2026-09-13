AGNITE AI uses a server-side fetch provider with a chat-completions-compatible API.

- `AGNITE_LLM_API_KEY`: optional server-only key. Without it, the frontend answers locally.
- `AGNITE_LLM_BASE_URL`: optional API root, defaults to `https://api.openai.com/v1`.
- `AGNITE_LLM_MODEL`: optional model identifier, defaults to `gpt-4.1-mini`.

Set variables in the server process environment before `npm run dev` or `npm start`. Never use a `VITE_` prefix for secrets. No credentials are stored in the browser. Provider errors and timeouts return local mode without exposing upstream errors or secrets. No credentials are needed for the existing public NASA feed.

When configured, asking a question sends selected observations, supplied context, computed history/risk and relevant saved-report summaries to the provider. Raw observation history is limited to the most recent 100 rows; summaries cover all included rows. Chat is bounded to 40 messages and reset on selection/data/context changes. Previous conversational messages are not sent to the provider.

Risk scores are unvalidated heuristic simulations anchored to the selected acquisition. They sum the displayed factors and clamp to 0–100. Historical baselines exclude later observations and separate simulated data. Missing satellite passes, verified incidents and weather forecasts are unavailable. Confidence denotes input coverage, not accuracy. External answers are instructed to ground claims in evidence; they are not independently fact-validated.
