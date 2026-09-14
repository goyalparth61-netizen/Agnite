import { Reveal } from "../common/SectionHeader";
export const documentationLinks = [
  "Overview",
  "Data Sources",
  "System Architecture",
  "AI / ML Pipeline",
  "AGNITE AI",
  "Risk Methodology",
  "Alerts",
  "APIs / Integrations",
  "Agents / Services",
  "Upcoming Features",
];
export const docId = (s: string) =>
  "docs-" + s.toLowerCase().replace(/[^a-z0-9]+/g, "-");
const sources = [
  [
    "NASA FIRMS / VIIRS / MODIS",
    "Connected",
    "Public near-real-time downloads power the live map. A separate offline training script can ingest historical FIRMS CSV exports for recurrence-model development.",
  ],
  [
    "OpenStreetMap / Overpass",
    "Connected",
    "Map tiles plus a 5 km lookup for industrial and geographic features. AGNITE can suggest land cover and nearest industrial distance, but mapped centre distances do not prove site containment or operating status.",
  ],
  [
    "Historical records",
    "Training pathway ready",
    "Loaded observations and saved reports provide local history. scripts/download-firms-history.py and scripts/train-firms-recurrence-model.py provide the reproducible path for a larger historical NASA FIRMS model artifact.",
  ],
  [
    "Weather / wind",
    "Manual / pending automation",
    "Wind can be supplied as analysis context. No automatic weather forecast is treated as verified evidence yet.",
  ],
];
const details: Record<string, string> = {
  Overview:
    "AGNITE combines satellite thermal detections, mapped context, historical behaviour, explainable classification, future thermal-recurrence/risk windows and a grounded assistant. A satellite hotspot is evidence, not a confirmed incident or cause.",
  "AI / ML Pipeline":
    "Classification: validate observations → build spatial/thermal/temporal features → multinomial classifier → conservative abstention on ambiguous cases. The bundled synthetic experiment reaches about 99% precision only on the selected high-confidence synthetic subset, not 99% real-world accuracy. Future modelling: historical NASA FIRMS CSV → temporal feature engineering → chronological holdout → 24h/48h/7d thermal-recurrence logistic models → precision-targeted decision thresholds. A real-data artifact is activated only after training and validation.",
  "AGNITE AI":
    "AGNITE AI is grounded in the selected hotspot, history, classification, risk windows, mapped context and missing evidence. An optional server-configured OpenAI-compatible provider enables conversational answers; the local evidence-grounded fallback remains available when the provider is unconfigured or unavailable.",
  "Risk Methodology":
    "Until a trained historical recurrence artifact exists, AGNITE displays a transparent 0–100 heuristic simulation based on FRP, baseline deviation, recurrence, trend, classification and supplied context. After real-data training, the same 24h/48h/7d view switches to a historical thermal-recurrence model. A 99% precision target is reported only if achieved on chronological held-out data; it is never assumed in advance and is not the probability that a confirmed fire will occur.",
  Alerts:
    "Location access is optional and requested only after user action. In-app monitoring compares nearby loaded thermal detections, can generate an alert image, and supports saved sites. Server email subscriptions require explicit consent/confirmation and provider configuration; they are decision-support alerts, not emergency dispatch.",
  "APIs / Integrations":
    "GET /api/firms retrieves NASA thermal observations. GET /api/site-context loads mapped OpenStreetMap evidence. POST /api/agnite/ask supports AGNITE AI with local fallback. /api/alerts/* handles confirmed alert subscriptions and POST /api/contact handles enquiries when configured. Provider secrets stay server-side.",
  "Agents / Services":
    "Services include NASA feed retrieval/cache, validation, mapped-context lookup, local classification, historical intelligence, future-risk/recurrence inference, AGNITE AI request handling, report/export tools and an optional confirmed-email worker. No autonomous emergency response is connected.",
  "Upcoming Features":
    "Highest-value next validation work: train the recurrence artifact on multi-year FIRMS history, test later unseen time periods and geographically held-out regions, add verified industrial/land-cover sources, weather forecasts, field incident labels and calibration/drift monitoring.",
};
export function ArchitectureFlow() {
  return (
    <ol className="architecture-flow">
      {[
        "User",
        "Interactive India Map",
        "NASA FIRMS + Mapped Context",
        "Hotspot Processing",
        "Historical Intelligence",
        "Classification + Abstention",
        "Risk / Recurrence Engine",
        "24h / 48h / 7d",
        "AGNITE AI",
        "Alerts / Reports / Safety Guidance",
      ].map((s, i) => (
        <li key={s}>
          <small>{String(i + 1).padStart(2, "0")}</small>
          <strong>{s}</strong>
          {i < 9 && <span aria-hidden="true">→</span>}
        </li>
      ))}
    </ol>
  );
}
export default function DocumentationSection() {
  return (
    <section id="documentation" className="section container">
      <span className="eyebrow">DOCUMENTATION</span>
      <h2>Every signal has a source.</h2>
      <p>
        Source → processing → intelligence → output. Inspect what is connected,
        what is validated and what is still experimental.
      </p>
      {documentationLinks.map((title) => (
        <Reveal key={title}>
          <article id={docId(title)} className="intel-card doc-article">
            <h3>{title}</h3>
            {title === "Data Sources" ? (
              <div className="intel-grid">
                {sources.map(([name, status, text]) => (
                  <div key={name}>
                    <h4>{name}</h4>
                    <span className="evidence-chip">{status}</span>
                    <p>{text}</p>
                  </div>
                ))}
              </div>
            ) : title === "System Architecture" ? (
              <>
                <ArchitectureFlow />
                <p>
                  The live application uses NASA FIRMS and mapped context. A
                  trained recurrence artifact can replace the heuristic future
                  window fallback after real historical validation.
                </p>
              </>
            ) : (
              <p>{details[title]}</p>
            )}
          </article>
        </Reveal>
      ))}
    </section>
  );
}
