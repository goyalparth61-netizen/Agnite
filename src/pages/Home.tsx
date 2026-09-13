import { lazy, Suspense } from "react";

import Navbar from "../components/layout/Navbar";
import Footer from "../components/layout/Footer";

import Hero from "../components/home/Hero";
import SolarBackground from "../components/home/SolarBackground";
import IntelligencePipeline from "../components/home/IntelligencePipeline";
import ProblemSection from "../components/home/ProblemSection";
import SolutionSection from "../components/home/SolutionSection";
import IntelligenceFeatures from "../components/home/IntelligenceFeatures";
import DataSources from "../components/home/DataSources";
import ImpactSection from "../components/home/ImpactSection";
import TeamSection from "../components/home/TeamSection";
import FinalCTA from "../components/home/FinalCTA";

import {HomeRisk, HomeAlerts, Contact} from '../components/home/CompletionSections';
import DocumentationSection from '../components/docs/DocumentationSection';
import AwarenessSection from '../components/awareness/AwarenessSection';

const DashboardPreview = lazy(
  () => import("../components/home/DashboardPreview"),
);

export default function Home() {
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>

      <Navbar />

      <main id="main">
        <div className="solar-stage">
          <SolarBackground />
          <Hero />
        </div>

        <IntelligencePipeline />

        <ProblemSection />

        <SolutionSection />

        <IntelligenceFeatures />

        <Suspense
          fallback={
            <section
              id="platform"
              className="section container"
              aria-busy="true"
            >
              <p>Loading demo workspace…</p>
            </section>
          }
        >
          <DashboardPreview />
        </Suspense>

        <DataSources />
        <HomeRisk />
        <HomeAlerts />
        <DocumentationSection />
        <AwarenessSection />

        <ImpactSection />

        <TeamSection />

        <Contact />
        <FinalCTA />
      </main>

      <Footer />
    </>
  );
}
