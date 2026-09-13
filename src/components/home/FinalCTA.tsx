import { ArrowUpRight, ArrowRight } from "lucide-react";
import { Reveal } from "../common/SectionHeader";
export default function FinalCTA() {
  return (
    <section className="final-cta container">
      <Reveal>
        <span className="eyebrow">
          AGNITE / AI-POWERED THERMAL INTELLIGENCE
        </span>
        <h2>
          FROM DETECTION
          <br />
          <span>TO DECISION.</span>
        </h2>
        <p>
          Connect the signal, the context and the evidence.
          <br />
          Make thermal intelligence actionable.
        </p>
        <div className="actions">
          <a className="button primary" href="#/workspace">
            Launch Intelligence Platform <ArrowUpRight size={17} />
          </a>
          <a className="button secondary" href="#/workspace">
            Explore GIS <ArrowRight size={17} />
          </a>
        </div>
        <small>NASA FIRMS CONNECTED / BUILT FOR SIH 2026</small>
      </Reveal>
    </section>
  );
}
