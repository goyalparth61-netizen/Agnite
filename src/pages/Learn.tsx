import DocumentationSection from "../components/docs/DocumentationSection";
import AwarenessSection from "../components/awareness/AwarenessSection";
import SitePage from "../components/layout/SitePage";

export default function Learn() {
  return (
    <SitePage
      eyebrow="LEARN"
      title="DOCUMENTATION THAT IS EASY TO FOLLOW."
      description="See the data sources, architecture, AI/ML flow, risk methodology and fire-awareness material in one place. Active integrations and demo-only features are clearly separated."
      primaryHref="#/workspace?tab=assistant"
      primaryLabel="Ask AGNITE"
      secondaryHref="#/platform"
      secondaryLabel="Explore Platform"
    >
      <DocumentationSection />
      <AwarenessSection />
    </SitePage>
  );
}
