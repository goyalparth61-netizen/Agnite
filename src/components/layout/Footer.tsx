export default function Footer() {
  return (
    <footer className="footer container">
      <div className="footer-main">
        <div>
          <a className="brand" href="#/" aria-label="AGNITE home">
            <span className="brand-logo-shell" aria-hidden="true">
              <img
                src={`${import.meta.env.BASE_URL}brand/agnite-logo.png`}
                alt=""
                width={52}
                height={52}
                loading="lazy"
                decoding="async"
                className="brand-logo"
              />
            </span>
            <span>
              <strong>AGNITE</strong>
              <small>AI-Powered Thermal Intelligence</small>
            </span>
          </a>
          <p>From satellite thermal signal to explainable action.</p>
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

      <div className="footer-team-signoff" aria-label="Project team">
        <span>BUILT BY</span>
        <strong>TEAM TIMEPASS</strong>
        <small>QUANTUM UNIVERSITY · SMART INDIA HACKATHON 2026</small>
      </div>
    </footer>
  );
}
