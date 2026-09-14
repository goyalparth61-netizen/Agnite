import { motion, useReducedMotion } from "framer-motion";
import {
  MapPinned,
  Satellite,
  History,
  Factory,
  BrainCircuit,
  BellRing,
} from "lucide-react";

const steps = [
  {
    icon: MapPinned,
    title: "1. Select a hotspot",
    text: "Open the India map and click a NASA FIRMS thermal detection. AGNITE anchors everything to that exact satellite acquisition.",
    output: "Input: location + acquisition time",
  },
  {
    icon: Satellite,
    title: "2. Check the thermal signal",
    text: "Read FRP, brightness, confidence, sensor and timestamp. The system first verifies that the loaded observation is valid and traceable.",
    output: "Checks: FRP · brightness · confidence",
  },
  {
    icon: History,
    title: "3. Compare with history",
    text: "Look at earlier detections near the same place, recent 24h / 7d / 30d recurrence, thermal baseline, trend and persistence.",
    output: "Checks: past vs present behaviour",
  },
  {
    icon: Factory,
    title: "4. Add location context",
    text: "Compare the hotspot with nearby industrial features, land-cover context and other mapped evidence instead of judging heat alone.",
    output: "Checks: industrial + natural context",
  },
  {
    icon: BrainCircuit,
    title: "5. Classify & estimate recurrence",
    text: "AGNITE classifies the thermal anomaly and runs the trained recurrence model for 24h, 48h and 7-day windows with conservative confidence gates.",
    output: "Output: class + recurrence outlook",
  },
  {
    icon: BellRing,
    title: "6. Explain & act",
    text: "AGNITE AI explains why, shows missing evidence, gives precautions and lets the user save reports or monitor a location for future detections.",
    output: "Output: explanation + action",
  },
] as const;

export default function IntelligencePipeline() {
  const reduced = useReducedMotion();
  return (
    <section id="how-agnite-checks" className="section container how-agnite" aria-labelledby="how-agnite-title">
      <div className="how-agnite-head">
        <span className="eyebrow"><span className="short-line" /> HOW AGNITE CHECKS A LOCATION</span>
        <h2 id="how-agnite-title">One hotspot. Six clear checks.</h2>
        <p>
          You do not need to understand the backend to use AGNITE. Follow this flow from left to right:
          select a hotspot, verify the signal, compare history, add context, classify/predict, then explain and act.
        </p>
      </div>

      <div className="how-agnite-grid">
        {steps.map(({ icon: Icon, title, text, output }, i) => (
          <motion.article
            className="how-step"
            key={title}
            initial={reduced ? false : { opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ delay: i * 0.07 }}
          >
            <div className="how-step-icon"><Icon size={20} /></div>
            <h3>{title}</h3>
            <p>{text}</p>
            <small>{output}</small>
          </motion.article>
        ))}
      </div>

      <div className="how-agnite-note">
        <strong>Important:</strong> NASA FIRMS detects thermal anomalies. AGNITE's recurrence model estimates repeat satellite thermal detections — it does not claim that every hotspot is a confirmed fire.
        <a href="#/workspace?tab=feed">Open live workflow →</a>
      </div>
    </section>
  );
}
