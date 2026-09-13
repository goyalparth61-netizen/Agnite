import type { Intelligence } from "../../ai/intelligence";
export default function ExplainabilityPanel({ data }: { data: Intelligence }) {
  return (
    <section className="intel-card">
      <span className="eyebrow">WHY THIS CLASSIFICATION?</span>
      <h2>Evidence summary</h2>
      {data.report ? (
        <>
          <p>{data.report.summary}</p>
          <div className="intel-grid">
            {data.report.evidence.map((e) => (
              <div key={e.label}>
                <span className="evidence-chip">
                  {e.label}: {e.value}
                </span>
                <p>{e.detail}</p>
              </div>
            ))}
          </div>
          <h3>Relative model contributions</h3>
          {data.report.contributions.map((f, i) => (
            <div className="factor-row" key={`${f.feature}-${i}`}>
              <span>
                {f.direction === "supports" ? "+" : "−"} {f.feature}
              </span>
              <meter
                min={0}
                max={Math.max(
                  1,
                  ...data.report!.contributions.map((x) =>
                    Math.abs(x.contribution),
                  ),
                )}
                value={Math.abs(f.contribution)}
              />
              <small>
                {f.contribution.toFixed(2)} · input {f.value.toFixed(2)}
              </small>
            </div>
          ))}
          <p>
            Contributions explain this experimental classifier; they are not
            causal effects or calibrated confidence.
          </p>
        </>
      ) : (
        <p>
          Run site analysis to view classification evidence and factor
          importance.
        </p>
      )}
      <h3>Missing evidence</h3>
      {data.predictions[0]?.missingEvidence.map((m) => (
        <span className="evidence-chip" key={m}>
          {m}
        </span>
      ))}
      <p>
        Field verification and validated incident labels remain unavailable.
        Evidence confidence: {data.predictions[0]?.confidence ?? "Unavailable"}.
      </p>
    </section>
  );
}
