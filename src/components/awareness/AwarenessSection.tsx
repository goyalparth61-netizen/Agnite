import { Reveal } from "../common/SectionHeader";
const cards = [
  [
    "A thermal pixel is a clue",
    "Satellite monitoring",
    "High thermal energy can come from vegetation, industry or other sources. It does not identify the cause on its own.",
    "Compare acquisition time, multiple passes and site context before interpreting a detection.",
  ],
  [
    "Repeated heat has a history",
    "Thermal awareness",
    "A recurring signal may indicate a persistent source rather than a new incident.",
    "A stable baseline and industrial context help distinguish routine thermal activity; a sudden deviation requires verification.",
  ],
  [
    "Respond to evidence",
    "Safety awareness",
    "Satellite estimates supplement official guidance and qualified field verification.",
    "Follow responsible local authorities, respect closures and avoid approaching suspected hazards.",
  ],
];
export default function AwarenessSection() {
  return (
    <section id="awareness" className="section container">
      <span className="eyebrow">EDUCATIONAL CONTENT · NO LIVE NEWS FEED</span>
      <h2>Understand heat. Stay aware.</h2>
      <div className="intel-card safety-resource"><span className="eyebrow">OFFICIAL LEARNING RESOURCES</span><h3>Fire precautions & awareness videos</h3><p>Explore the NDMA SACHET library for Fire, Forest Fire and Chemical Emergencies guidance, with multilingual resources and a video section.</p><a className="button secondary" href="https://sachet.ndma.gov.in/DosDont" target="_blank" rel="noreferrer">Watch precaution videos & read guidance ↗</a><a className="button secondary" href="https://sachet.ndma.gov.in/" target="_blank" rel="noreferrer">View official disaster alerts ↗</a><p>External official resources; AGNITE does not republish these as a live news feed.</p></div>
      <div className="intel-grid">
        {cards.map(([title, category, summary, more]) => (
          <Reveal key={title}>
            <article className="intel-card">
              <span className="eyebrow">{category}</span>
              <p>
                <time dateTime="2026-09-13">13 September 2026</time> ·
                Educational edition
              </p>
              <h3>{title}</h3>
              <p>{summary}</p>
              <details>
                <summary>Read more</summary>
                <p>{more}</p>
              </details>
            </article>
          </Reveal>
        ))}
      </div>
      <a
        className="button secondary"
        href="https://firms.modaps.eosdis.nasa.gov/"
        target="_blank"
        rel="noreferrer"
      >
        Resource: NASA FIRMS →
      </a>
    </section>
  );
}
