export default function PersistentHeatComparison() {
  return (
    <section className="intel-card">
      <span className="eyebrow">PERSISTENT HEAT ≠ CONFIRMED FIRE</span>
      <h2>Read the pattern, not just the pixel.</h2>
      <div className="intel-grid">
        {[
          [
            "Normal industrial heat",
            "▁▂▂▁▂▂",
            "Expected operational heat within a verified site baseline. Industrial land use alone is not proof.",
          ],
          [
            "Persistent industrial thermal source",
            "▃▃▄▃▃▄",
            "Repeated detections over distinct passes with a stable baseline suggest a persistent source; missing passes limit certainty.",
          ],
          [
            "Abnormal industrial fire — candidate",
            "▂▂▃▄▆█",
            "A sudden FRP jump and strong baseline deviation warrant verification. A confirmed industrial fire requires incident evidence.",
          ],
        ].map(([title, signal, text]) => (
          <article key={title}>
            <div className="thermal-spark" aria-hidden="true">
              {signal}
            </div>
            <h3>{title}</h3>
            <p>{text}</p>
          </article>
        ))}
      </div>
      <small>
        Conceptual comparison · not measured data. Compare recurrence,
        persistence, industrial context and baseline deviation together.
      </small>
    </section>
  );
}
