import { HomeAlerts, HomeRisk } from "../components/home/CompletionSections";
import SitePage from "../components/layout/SitePage";

export default function Risk() {
  return (
    <SitePage
      eyebrow="RISK & ALERTS"
      title="UNDERSTAND RISK WITHOUT THE NOISE."
      description="Review AGNITE's 24-hour, 48-hour and 7-day screening windows, see the strongest contributing factors, and configure monitoring without treating estimates as guaranteed fire predictions."
      primaryHref="#/workspace?tab=risk"
      primaryLabel="Open Risk Workspace"
      secondaryHref="#/email-alerts"
      secondaryLabel="Email Alert Setup"
    >
      <HomeRisk />
      <HomeAlerts />
    </SitePage>
  );
}
