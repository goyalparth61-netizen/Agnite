import {
  Map,
  ScanLine,
  History,
  Repeat2,
  BrainCircuit,
  ShieldCheck,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import SectionHeader, { Reveal } from "../common/SectionHeader";
export default function IntelligenceFeatures() {
  return (
    <section className="section container">
      <Reveal>
        <SectionHeader
          label="03 / BUILT TO UNDERSTAND"
          title="INTELLIGENCE, IN EVERY DIMENSION."
          text="From a single thermal observation to the patterns and evidence behind it."
        />
        <div className="features-grid">
          {(
            [
              [
                Map,
                "GIS Intelligence",
                "India-focused hotspot monitoring with location and land-use context.",
                "01 / SPATIAL AWARENESS",
                "India / region / location",
              ],
              [
                ScanLine,
                "Thermal Classification",
                "Industrial Fire / Persistent Industrial Heat / Forest / Natural Fire / Other Anomaly",
                "02 / SIGNAL UNDERSTANDING",
                "One signal. Four possible stories.",
              ],
              [
                History,
                "Historical Intelligence",
                "Compare historical baseline versus current anomaly to identify meaningful change.",
                "03 / TEMPORAL CONTEXT",
                "Historical Baseline / Current Anomaly",
              ],
              [
                Repeat2,
                "Persistent Heat Analysis",
                "Repeated detections over time help distinguish routine activity from emerging events.",
                "04 / PATTERN RECOGNITION",
                "MON / TUE / WED / THU / FRI / SAT / SUN",
              ],
              [
                BrainCircuit,
                "Explainable AI",
                "Classification, confidence, evidence, contributing factors and a recommended action.",
                "05 / EVIDENCE FIRST",
                "Observe / explain / verify",
              ],
              [
                ShieldCheck,
                "Future Risk Window",
                "Explore illustrative risk across the next 24 hours, 48 hours and 7 days.",
                "06 / SIMULATION",
                "24 HOURS / 48 HOURS / 7 DAYS",
              ],
            ] as [LucideIcon, string, string, string, string][]
          ).map(([Icon, title, text, label, detail]) => (
            <article className="feature-card" key={title}>
              <div className="feature-top">
                <Icon size={23} />
                <span>{label}</span>
              </div>
              <h3>{title}</h3>
              <p>{text}</p>
              <div className="feature-detail">{detail}</div>
            </article>
          ))}
        </div>
      </Reveal>
    </section>
  );
}
