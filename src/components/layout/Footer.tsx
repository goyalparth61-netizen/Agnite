import { Flame } from "lucide-react";
export default function Footer() {
  return (
    <footer className="footer container">
      <div className="footer-main">
        <div>
          <a className="brand" href="#home">
            <Flame className="brand-mark" size={30} />
            <span>
              <strong>AGNITE</strong>
              <small>AI-Powered Thermal Intelligence</small>
            </span>
          </a>
          <p>Built with purpose. By Team Timepass.</p>
        </div>
        <nav aria-label="Footer navigation">
          <a href="#intelligence">About</a>
          <a href="#impact">Mission</a>
          <a href="#technology">Technology</a>
          <a href="#team">Team</a>
          <a href="#contact">Contact</a>
          <a
            href={`${import.meta.env.BASE_URL}LICENSE`}
            target="_blank"
            rel="noreferrer"
          >
            License link
          </a>
        </nav>
      </div>
      <div className="team-contact">
        <span>TEAM TIMEPASS</span>
        <p>
          Smart India Hackathon 2026 / SIH26162
          <br />
          Use the Contact section above for project enquiries.
        </p>
      </div>
      <div className="footer-bottom">
        <span>Copyright 2026 AGNITE / MIT License</span>
        <span>SMART INDIA HACKATHON 2026 / SIH26162</span>
        <span>DESIGNED TO MAKE SIGNALS MATTER.</span>
      </div>
    </footer>
  );
}


