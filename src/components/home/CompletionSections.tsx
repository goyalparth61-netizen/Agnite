import RiskOverview from "../risk/RiskOverview";
import NearbyAlerts from "../alerts/NearbyAlerts";
import PersistentHeatComparison from "../intelligence/PersistentHeatComparison";
import ContactForm from './ContactForm';
export function HomeRisk() {
  return (
    <section id="risk" className="section container">
      <RiskOverview />
      <PersistentHeatComparison />
    </section>
  );
}
export function HomeAlerts() {
  return (
    <section id="alerts" className="section container">
      <span className="eyebrow">ALERTS</span>
      <NearbyAlerts />
      <a className="button secondary" href="#/workspace?tab=monitoring">
        Open alerts with loaded NASA observations →
      </a>
    </section>
  );
}
export function Contact() {
  return (
    <section id="contact" className="section container">
      <div className="intel-card">
        <span className="eyebrow">CONTACT · SIH26162</span>
        <h2>AGNITE</h2>
        <p>
          Team Timepass · Quantum University
          <br />
          Smart India Hackathon 2026
        </p>
        <ContactForm />
      </div>
    </section>
  );
}
