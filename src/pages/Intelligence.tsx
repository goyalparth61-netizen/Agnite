import IntelligencePipeline from "../components/home/IntelligencePipeline";
import IntelligenceFeatures from "../components/home/IntelligenceFeatures";
import SitePage from "../components/layout/SitePage";

export default function Intelligence() {
  return (
    <SitePage
      eyebrow="INTELLIGENCE"
      title="PAST, PRESENT, RISK — EXPLAINED."
      description="AGNITE combines thermal strength, spatial context and historical behaviour to classify hotspots, identify persistent heat patterns and explain why a risk score was produced."
      primaryHref="#/workspace?tab=analysis"
      primaryLabel="Analyze a Hotspot"
      secondaryHref="#/risk"
      secondaryLabel="View Risk & Alerts"
    >
      <IntelligencePipeline />
      <IntelligenceFeatures />
    </SitePage>
  );
}
