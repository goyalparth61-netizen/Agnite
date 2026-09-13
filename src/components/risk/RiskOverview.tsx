import {
  ShieldCheck,
  ShieldAlert,
  TriangleAlert,
  OctagonAlert,
} from "lucide-react";
import { Reveal } from "../common/SectionHeader";
import type { Intelligence } from "../../ai/intelligence";
export const responses: Record<string, string> = {
  LOW: "Monitor and maintain routine awareness.",
  MODERATE: "Increase observation frequency and check additional passes.",
  HIGH: "Prioritize verification; request qualified review of nearby heat sources.",
  CRITICAL:
    "Escalate for field verification and emergency review by responsible authorities.",
};
export function RiskLevelBadge({ level }: { level: string }) {
  const Icon =
    {
      LOW: ShieldCheck,
      MODERATE: ShieldAlert,
      HIGH: TriangleAlert,
      CRITICAL: OctagonAlert,
    }[level] ?? ShieldAlert;
  return (
    <span className={`risk-badge risk-${level.toLowerCase()}`}>
      <Icon size={20} />
      {level}
    </span>
  );
}
export function SafetyPrecautions({ level = "LOW" }: { level?: string }) {
  return (
    <section className="intel-card">
      <span className="eyebrow">SAFETY PRECAUTIONS</span>
      <h3>{level} · Recommended response</h3>
      <p>{responses[level]}</p>
      <div className="intel-grid">
        <div>
          <h4>Industrial areas</h4>
          <p>
            Follow site safety procedures. Keep untrained personnel away from
            suspected hazards and report changes to the site safety team.
          </p>
        </div>
        <div>
          <h4>Forest areas</h4>
          <p>
            Follow local closures and official advisories. Keep clear of smoke
            and report suspected activity to responsible authorities.
          </p>
        </div>
        <div>
          <h4>Persistent heat</h4>
          <p>
            Compare repeated passes with the normal operating baseline. Request
            qualified review when the signal changes.
          </p>
        </div>
      </div>
      <small>
        Satellite estimates do not replace emergency instructions or on-site
        verification.
      </small>
    </section>
  );
}
export default function RiskOverview({ data }: { data?: Intelligence }) {
  return (
    <div className="risk-overview">
      <span className="eyebrow">RISK ESTIMATE / SIMULATION</span>
      <h2>From signal to response.</h2>
      {data?.selected ? (
        <>
          <p>
            Selected acquisition:{" "}
            {new Date(data.selected.observedAt).toLocaleString()}. Windows start
            at this acquisition. Classification:{" "}
            {data.report?.classification ?? "Run site analysis"}.
          </p>
          <span className="evidence-chip">Trend: {data.history.trend}</span>
          <div className="intel-grid">
            {data.predictions.map((p) => (
              <Reveal key={p.window}>
                <article className={`intel-card risk-${p.level.toLowerCase()}`}>
                  <span className="eyebrow">
                    NEXT{" "}
                    {
                      { "24h": "24 HOURS", "48h": "48 HOURS", "7d": "7 DAYS" }[
                        p.window
                      ]
                    }
                  </span>
                  <div
                    className="risk-meter"
                    role="meter"
                    aria-label={`${p.window} heuristic risk index`}
                    aria-valuenow={p.riskScore}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    style={{
                      background: `conic-gradient(var(--risk-color) ${p.riskScore * 3.6}deg, #27323e 0)`,
                    }}
                  >
                    <strong>
                      {p.riskScore}
                      <small>% of index scale</small>
                    </strong>
                  </div>
                  <RiskLevelBadge level={p.level} />
                  <p>Evidence confidence: {p.confidence}</p>
                  <details>
                    <summary>Contributing factors & uncertainty</summary>
                    {p.contributingFactors.map((f) => (
                      <p key={f.label}>
                        {f.points >= 0 ? "+" : ""}
                        {f.points} points · {f.label}
                      </p>
                    ))}
                    {p.missingEvidence.map((m) => (
                      <span className="evidence-chip" key={m}>
                        Missing: {m}
                      </span>
                    ))}
                  </details>
                  <p>{responses[p.level]}</p>
                </article>
              </Reveal>
            ))}
          </div>
          <p>
            Baseline: {data.history.baselineFrp?.toFixed(1) ?? "Unavailable"} MW
            → Current: {data.history.currentFrp?.toFixed(1)} MW · Deviation:{" "}
            {data.history.anomalyPercent?.toFixed(1) ?? "Unavailable"}%.
          </p>
          <p>{data.predictions[0]?.explanation}</p>
          <SafetyPrecautions level={data.predictions[0]?.level} />
        </>
      ) : (
        <>
          <p>
            Compare historical evidence and explore 24-hour, 48-hour and 7-day
            scenarios for a selected hotspot. Scores are heuristic indices, not
            probabilities of fire.
          </p>
          <div className="intel-grid risk-legend">
            {Object.entries(responses).map(([level, response]) => (
              <Reveal key={level}>
                <article className="intel-card">
                  <RiskLevelBadge level={level} />
                  <p>{response}</p>
                </article>
              </Reveal>
            ))}
          </div>
          <a className="button secondary" href="#/workspace?tab=risk">
            Explore selected-site risk →
          </a>
        </>
      )}
    </div>
  );
}
