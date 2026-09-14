import { lazy, Suspense } from "react";
import { ArrowUpRight, BrainCircuit, Map, MessageSquare, ShieldAlert } from "lucide-react";
import Navbar from "../components/layout/Navbar";
import Footer from "../components/layout/Footer";
import Hero from "../components/home/Hero";
import SolarBackground from "../components/home/SolarBackground";
import IntelligencePipeline from "../components/home/IntelligencePipeline";
import FinalCTA from "../components/home/FinalCTA";

const DashboardPreview = lazy(() => import("../components/home/DashboardPreview"));

const paths = [
  { icon: Map, title: "1. Open the live map", text: "Load NASA FIRMS detections for India and select the hotspot you want to investigate.", href: "#/workspace?tab=feed" },
  { icon: BrainCircuit, title: "2. Analyze the hotspot", text: "Check thermal history, context, classification, evidence and what information is still missing.", href: "#/workspace?tab=analysis" },
  { icon: ShieldAlert, title: "3. Review future recurrence", text: "See the 24h, 48h and 7-day thermal-recurrence model output and its confidence gate.", href: "#/workspace?tab=risk" },
  { icon: MessageSquare, title: "4. Ask AGNITE AI", text: "Ask why it was classified that way, what happened before and what action should be considered next.", href: "#/workspace?tab=assistant" },
];

export default function Home() {
  return (
    <>
      <a className="skip-link" href="#main">Skip to content</a>
      <Navbar />
      <main id="main">
        <div className="solar-stage">
          <SolarBackground />
          <Hero />
        </div>

        <section className="section container quick-start" aria-labelledby="quick-start-title">
          <div className="quick-start-head">
            <span className="eyebrow"><span className="short-line" /> USE AGNITE IN 60 SECONDS</span>
            <h2 id="quick-start-title">Start here — this is the actual user flow.</h2>
            <p>You do not have to jump between every page. Use these four steps for the complete demo: map → analysis → recurrence risk → AGNITE AI.</p>
          </div>
          <div className="quick-start-grid">
            {paths.map(({ icon: Icon, title, text, href }) => (
              <a className="quick-start-card" href={href} key={href}>
                <Icon size={22} />
                <div><h3>{title}</h3><p>{text}</p></div>
                <ArrowUpRight size={18} />
              </a>
            ))}
          </div>
        </section>

        <IntelligencePipeline />

        <Suspense fallback={<section className="section container" aria-busy="true"><p>Loading platform preview…</p></section>}>
          <DashboardPreview />
        </Suspense>

        <FinalCTA />
      </main>
      <Footer />
    </>
  );
}
