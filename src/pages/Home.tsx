import { lazy, Suspense } from "react";
import { ArrowUpRight, BookOpen, BrainCircuit, Map, ShieldAlert } from "lucide-react";
import Navbar from "../components/layout/Navbar";
import Footer from "../components/layout/Footer";
import Hero from "../components/home/Hero";
import SolarBackground from "../components/home/SolarBackground";
import IntelligencePipeline from "../components/home/IntelligencePipeline";
import FinalCTA from "../components/home/FinalCTA";

const DashboardPreview = lazy(() => import("../components/home/DashboardPreview"));

const paths = [
  { icon: Map, title: "Explore the platform", text: "Open the India thermal map and inspect satellite detections.", href: "#/platform" },
  { icon: BrainCircuit, title: "Understand intelligence", text: "See classification, history, explainability and AGNITE AI.", href: "#/intelligence" },
  { icon: ShieldAlert, title: "Check risk & alerts", text: "Review 24h, 48h and 7-day screening windows and monitoring.", href: "#/risk" },
  { icon: BookOpen, title: "Read documentation", text: "Learn the architecture, data sources, limitations and awareness material.", href: "#/learn" },
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
            <span className="eyebrow"><span className="short-line" /> START HERE</span>
            <h2 id="quick-start-title">Choose what you want to do.</h2>
            <p>AGNITE is now split into focused pages so you can reach the right tool without scrolling through everything.</p>
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
