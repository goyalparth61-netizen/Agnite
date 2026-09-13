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
    "Connected feed pathway",
    "Public near-real-time downloads through the existing server. NASA DATA appears only after successful retrieval.",
  ],
  [
    "OpenStreetMap",
    "Map tiles",
    "Street-map context; tiles require network access. Not a land-cover classifier.",
  ],
  [
    "Historical records",
    "Loaded / local",
    "Earlier loaded detections and saved browser reports within 5 km. No complete historical archive connected.",
  ],
  [
    "Land cover / industrial context",
    "User supplied",
    "Unknown unless entered by the user; demo context is simulated.",
  ],
  [
    "Weather / wind",
    "User supplied / pending",
    "Manual wind input supported. No automatic weather forecast integration.",
  ],
];
const details: Record<string, string> = {
  Overview:
    "AGNITE combines satellite thermal detections, loaded history and explainable experimental analysis. A detection is not a confirmed fire.",
  "AI / ML Pipeline":
    "Validate coordinates and acquisition times → group nearby passes → derive FRP, baseline and persistence features → synthetic-trained classifier with insufficient-evidence abstention → heuristic risk windows. No field-validated accuracy claim.",
  "AGNITE AI":
    "Grounded local mode answers from selected evidence. An optional server-configured external provider receives selected context when you ask a question. Response badges identify the answering mode.",
  "Risk Methodology":
    "Risk is a 0–100 heuristic index, not event probability. FRP, baseline deviation, recurrence, trend and supplied context contribute points. Future windows assume trend continuation from acquisition; missing evidence lowers confidence.",
  Alerts:
    "Optional browser location is requested only after a click. Saved-site monitoring checks loaded NASA observations. Email setup is a frontend demo, with no delivery service.",
  "APIs / Integrations":
    "GET /api/firms retrieves NASA data. POST /api/agnite/ask supports a configured AI provider with local fallback. CSV import and JSON/CSV export work locally. Provider keys belong on the server.",
  "Agents / Services":
    "Current services: feed retrieval/cache, observation validation, local classification and assistant request handling. No autonomous dispatch, emergency response or background email agents are connected.",
  "Upcoming Features":
    "Pending: historical archive ingestion, verified land-cover and industrial datasets, weather forecasts, field validation, alert delivery and calibrated prediction models.",
};
export function ArchitectureFlow() {
  return (
    <ol className="architecture-flow">
      {[
        "User",
        "Interactive India Map",
        "NASA FIRMS / Other Data",
        "Hotspot Processing",
        "Historical Intelligence",
        "Classification",
        "Risk Engine",
        "Future Risk",
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
        Source → processing → intelligence → output. Inspect what is connected
        and what remains experimental.
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
                  Conceptual system flow. Alerts include local monitoring and
                  demo email setup; future risk is an unvalidated estimate.
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
