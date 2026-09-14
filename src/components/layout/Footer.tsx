import { Flame } from "lucide-react";
export default function Footer() {
  return (
    <footer className="footer container">
      <div className="footer-main">
        <div>
          <a className="brand" href="#/">
            <Flame className="brand-mark" size={30} />
            <span>
              <strong>AGNITE</strong>
              <small>AI-Powered Thermal Intelligence</small>
            </span>
          </a>
          <p>Built with purpose. By Team Timepass.</p>
        </div>
        <nav aria-label="Footer navigation">
          <a href="#/platform">Platform</a>
          <a href="#/intelligence">Intelligence</a>
          <a href="#/risk">Risk & Alerts</a>
          <a href="#/learn">Learn</a>
          <a href="#/about">About</a>
          <a href="#/workspace">Dashboard</a>
          <a href={`${import.meta.env.BASE_URL}LICENSE`} target="_blank" rel="noreferrer">License</a>
        </nav>
      </div>
      <div className="team-contact">
        <span>TEAM TIMEPASS</span>
        <p>Smart India Hackathon 2026 / SIH26162<br/>Quantum University</p>
      </div>
      <div className="footer-bottom">
        <span>Copyright 2026 AGNITE / MIT License</span>
        <span>SMART INDIA HACKATHON 2026 / SIH26162</span>
        <span>DESIGNED TO MAKE SIGNALS MATTER.</span>
      </div>
    </footer>
  );
}
