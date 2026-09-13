import {
  ArrowUpRight,
  ArrowRight,
  Satellite,
  BrainCircuit,
  ShieldCheck,
} from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import IntelligenceVisual from "./IntelligenceVisual";
export default function Hero() {
  const reduced = useReducedMotion();
  return (
    <section id="home" className="hero container">
      <motion.div
        className="hero-copy"
        initial={reduced ? false : { opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        <span className="eyebrow">
          <span className="short-line" /> SMART INDIA HACKATHON 2026 / SIH26162
        </span>
        <h1>
          TURN THERMAL
          <br />
          ANOMALIES INTO
          <br />
          <span>
            ACTIONABLE
            <br />
            INTELLIGENCE.
          </span>
        </h1>
        <p>
          AGNITE combines satellite thermal observations, spatial context,
          historical behaviour and explainable AI to detect, classify and
          understand potential fire events and persistent thermal sources.
        </p>
        <div className="actions">
          <a className="button primary" href="#/workspace?tab=analysis">
            Explore Intelligence <ArrowUpRight size={17} />
          </a>
          <a className="button secondary" href="#/workspace">
            View GIS Platform <ArrowRight size={17} />
          </a>
        </div>
        <div className="trust-strip">
          <span>
            <Satellite /> Satellite Intelligence
          </span>
          <span>
            <BrainCircuit /> Explainable AI
          </span>
          <span>
            <ShieldCheck /> Risk Intelligence
          </span>
        </div>
      </motion.div>
      <motion.div
        initial={reduced ? false : { opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25, duration: 1 }}
      >
        <IntelligenceVisual />
      </motion.div>
      <div className="hero-caption">
        <span>SEE THE SIGNAL. UNDERSTAND THE CONTEXT.</span>
        <span>SCROLL TO EXPLORE</span>
      </div>
    </section>
  );
}
