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
        <div className="hero-brand-lockup">
          <span className="hero-logo-shell" aria-hidden="true">
            <img
              src={`${import.meta.env.BASE_URL}brand/agnite-logo.png`}
              alt=""
              width={92}
              height={92}
              className="hero-logo"
            />
          </span>
          <div>
            <strong>AGNITE</strong>
            <small>AI-Powered Thermal Intelligence for India</small>
          </div>
        </div>

        <span className="eyebrow">
          <span className="short-line" /> SMART INDIA HACKATHON 2026 / SIH26162
        </span>
        <h1>
          SEE THE HOTSPOT.
          <br />
          UNDERSTAND <span>WHY.</span>
          <br />
          KNOW WHAT TO DO NEXT.
        </h1>
        <p>
          Pick a thermal hotspot on the India map. AGNITE checks its NASA FIRMS signal,
          recent history, nearby context and recurrence pattern, then shows a classification,
          24h / 48h / 7-day thermal-recurrence outlook, missing evidence and an explainable AI summary.
        </p>
        <div className="actions">
          <a className="button primary" href="#/workspace?tab=feed">
            Start with Live Map <ArrowUpRight size={17} />
          </a>
          <a className="button secondary" href="#how-agnite-checks">
            See How It Checks <ArrowRight size={17} />
          </a>
        </div>
        <div className="trust-strip">
          <span><Satellite /> NASA FIRMS observations</span>
          <span><BrainCircuit /> Explainable AGNITE AI</span>
          <span><ShieldCheck /> Evidence-first risk screening</span>
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
        <span>PAST → PRESENT → UNDERSTAND → PREDICT → EXPLAIN → ACT</span>
        <span>THERMAL RECURRENCE ≠ CONFIRMED FIRE</span>
      </div>
    </section>
  );
}
