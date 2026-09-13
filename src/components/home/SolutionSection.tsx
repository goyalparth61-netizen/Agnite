import { ArrowRight, Cpu, Database, Layers, ScanEye } from "lucide-react";
import SectionHeader, { Reveal } from "../common/SectionHeader";
export default function SolutionSection() {
  return (
    <section id="technology" className="section technology-section">
      <div className="container">
        <Reveal>
          <SectionHeader
            label="02 / THE INTELLIGENCE ARCHITECTURE"
            title="EVERY SIGNAL. MORE CONTEXT."
            text="A proposed intelligence architecture that connects observation to an explainable decision."
          />
          <div className="architecture">
            <div className="architecture-column">
              <span className="eyebrow">
                <Database size={14} /> OBSERVE + ENRICH
              </span>
              <div className="source-node">
                NASA FIRMS / VIIRS / MODIS{" "}
                <small>Thermal Hotspot Detection</small>
              </div>
              <div className="context-sources">
                <span>OpenStreetMap industrial context</span>
                <span>Land Cover</span>
                <span>Satellite Context</span>
                <span>Historical Hotspot Records</span>
              </div>
            </div>
            <ArrowRight className="architecture-arrow" />
            <div className="fusion-node">
              <Layers size={25} />
              <span>SPATIAL + TEMPORAL</span>
              <h3>Feature fusion</h3>
              <p>Location. Recurrence. Change.</p>
              <div className="fusion-line" />
              <Cpu size={25} />
              <h3>AI Classification</h3>
              <small>Four anomaly classes</small>
            </div>
            <ArrowRight className="architecture-arrow" />
            <div className="architecture-column output-column">
              <span className="eyebrow">
                <ScanEye size={14} /> UNDERSTAND + ACT
              </span>
              <div>
                01 <strong>Risk Assessment</strong>
              </div>
              <div>
                02 <strong>Explainable AI</strong>
              </div>
              <div>
                03 <strong>Decision Support</strong>
              </div>
            </div>
          </div>
          <p className="footnote">
            DESIGN PREVIEW / Data connections and model inference are planned;
            this prototype uses simulated examples.
          </p>
        </Reveal>
      </div>
    </section>
  );
}
