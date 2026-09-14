import ImpactSection from "../components/home/ImpactSection";
import TeamSection from "../components/home/TeamSection";
import { Contact } from "../components/home/CompletionSections";
import SitePage from "../components/layout/SitePage";

export default function About() {
  return (
    <SitePage
      eyebrow="ABOUT"
      title="THE TEAM BEHIND AGNITE."
      description="Meet Team Timepass, understand the mission behind the platform and find the project contact section without scrolling through the full product story."
      primaryHref="#/workspace"
      primaryLabel="Launch Dashboard"
      secondaryHref="#/learn"
      secondaryLabel="Read Documentation"
    >
      <ImpactSection />
      <TeamSection />
      <Contact />
    </SitePage>
  );
}
