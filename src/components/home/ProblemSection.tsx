import {
  Factory,
  Flame,
  Trees,
  ScanLine,
  Plus,
  Equal,
  Activity,
  MapPin,
  History,
  ScanEye,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import SectionHeader, { Reveal } from "../common/SectionHeader";
export default function ProblemSection() {
  return (
    <section id="intelligence" className="section container">
      <Reveal>
        <div className="section-top">
          <SectionHeader
            label="01 / BEYOND DETECTION"
            title="A HOTSPOT IS NOT ALWAYS A FIRE."
          />
          <p className="section-aside">
            The same thermal signature can tell very different stories. Context
            makes the difference.
          </p>
        </div>
        <div className="anomaly-grid">
          {(
            [
              [
                Flame,
                "Industrial Fire",
                "An unexpected thermal event.",
                "fire",
              ],
              [
                Factory,
                "Persistent Industrial Heat",
                "A recurring operational signature.",
                "heat",
              ],
              [
                Trees,
                "Forest / Natural Fire",
                "A thermal event in natural cover.",
                "forest",
              ],
              [
                ScanLine,
                "Other Thermal Anomaly",
                "A signal that needs a closer look.",
                "other",
              ],
            ] as [LucideIcon, string, string, string][]
          ).map(([Icon, title, text, tone]) => (
            <article className={`anomaly-card ${tone}`} key={title}>
              <div className="thermal-thumbnail">
                <div className="thermal-patch" />
                <Icon size={27} />
                <span>THERMAL SIGNATURE</span>
              </div>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
          ))}
        </div>
        <div className="context-equation">
          <span>
            <Activity />
            Satellite Thermal Signal
          </span>
          <Plus />
          <span>
            <MapPin />
            Location Context
          </span>
          <Plus />
          <span>
            <History />
            Historical Behaviour
          </span>
          <Equal />
          <span className="equation-result">
            <ScanEye />
            Better Classification
          </span>
        </div>
      </Reveal>
    </section>
  );
}
