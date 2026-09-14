import DashboardPreview from "../components/home/DashboardPreview";
import ProblemSection from "../components/home/ProblemSection";
import SolutionSection from "../components/home/SolutionSection";
import DataSources from "../components/home/DataSources";
import SitePage from "../components/layout/SitePage";

export default function Platform() {
  return (
    <SitePage
      eyebrow="PLATFORM"
      title="SEE THE HOTSPOT. UNDERSTAND THE CONTEXT."
      description="Explore how AGNITE turns satellite thermal detections into a clear GIS workflow with source labels, hotspot details, historical context and evidence-first analysis."
      primaryHref="#/workspace"
      primaryLabel="Open Live Workspace"
      secondaryHref="#/intelligence"
      secondaryLabel="How Intelligence Works"
    >
      <ProblemSection />
      <SolutionSection />
      <DashboardPreview />
      <DataSources />
    </SitePage>
  );
}
