import { ArrowUpRight } from "lucide-react";
import SectionHeader, { Reveal } from "../common/SectionHeader";
export default function ImpactSection() {
  return (
    <section id="impact" className="section impact-section">
      <div className="container impact-layout">
        <Reveal>
          <SectionHeader
            label="06 / INTELLIGENCE WITH PURPOSE"
            title="CLARITY WHEN IT MATTERS MOST."
            text="Built to help analysts understand what is happening, why it matters and where to look next."
          />
          <div className="impact-note">
            <span>OUR MISSION</span>
            <p>Turn thermal observations into informed, explainable action.</p>
          </div>
        </Reveal>
        <Reveal className="impact-list">
          {[
            "Early situational awareness",
            "Industrial risk monitoring",
            "Persistent thermal source identification",
            "Historical anomaly investigation",
            "Explainable decision support",
            "Faster response prioritization",
          ].map((text, i) => (
            <div key={text}>
              <span>0{i + 1}</span>
              <h3>{text}</h3>
              <ArrowUpRight size={17} />
            </div>
          ))}
        </Reveal>
      </div>
    </section>
  );
}
