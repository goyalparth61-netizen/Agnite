# Contributing to AGNITE

Thank you for contributing to AGNITE.

## Development setup

Requirements:

- Node.js 22+;
- npm;
- Python only for optional data/ML maintenance scripts.

```sh
git clone https://github.com/goyalparth61-netizen/Agnite.git
cd Agnite
npm ci
npm run dev
```

Before opening a pull request:

```sh
npm test
npm run build
```

## Branching

Use focused branches, for example:

```text
feature/historical-timeline
fix/firms-parser
ml/recurrence-validation
docs/api-reference
```

Keep unrelated work in separate branches/PRs.

## Commit style

Use short conventional-style messages where practical:

```text
feat: add district hotspot filters
fix: preserve selected site on refresh
ml: validate recurrence threshold
docs: clarify FIRMS provenance
test: cover stale feed behaviour
```

## Pull-request expectations

A good PR explains:

- what changed;
- why the change is needed;
- how it was tested;
- any new environment variables;
- any data/model assumption introduced;
- screenshots for visible UI changes;
- limitations or follow-up work.

## Data and model changes

For ML/data changes, include:

- data source and license/provenance;
- target definition;
- feature definition;
- split methodology;
- evaluation size;
- relevant metrics;
- reproducibility instructions;
- failure cases and limitations.

Never relabel a synthetic metric as real-world performance.

If a model uses a selective threshold, report both the metric on selected cases and the coverage/recall trade-off.

## API changes

When changing an API contract:

1. update the server implementation;
2. update affected frontend types/consumers;
3. add or update deterministic tests;
4. update `docs/API.md` and any configuration docs.

## UI changes

Preserve:

- keyboard accessibility;
- reduced-motion support where applicable;
- source labels;
- explicit loading/error/stale states;
- demo-vs-live separation;
- mobile readability.

## Security

Do not commit:

- API keys;
- `.env` files containing secrets;
- email lists or alert subscription stores;
- private datasets without redistribution rights.

See [SECURITY.md](SECURITY.md).

## Documentation

Any feature that changes behaviour visible to users or operators should update the relevant documentation in `docs/`.

## Review checklist

Before requesting review, confirm:

- [ ] `npm test` passes
- [ ] `npm run build` passes
- [ ] no secrets are committed
- [ ] source/provenance wording is accurate
- [ ] model/risk claims are scoped correctly
- [ ] failure states remain explicit
- [ ] docs are updated
