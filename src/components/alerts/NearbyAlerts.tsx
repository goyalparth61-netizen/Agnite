import { useEffect, useMemo, useRef, useState } from "react";
import type { Observation } from "../../ai/thermalEngine";
import { acquisitionStatus, nearbyCandidates } from "../../ai/decisionSupport";
import { buildIntelligence, sourceLabel } from "../../ai/intelligence";
import { RiskLevelBadge } from "../risk/RiskOverview";
export default function NearbyAlerts({
  observations = [],
  stale = false,
  onInspect,
}: {
  observations?: Observation[];
  stale?: boolean;
  onInspect?: (row: Observation) => void;
}) {
  const [location, setLocation] = useState<{
    latitude: number;
    longitude: number;
  } | null>(null);
  const [status, setStatus] = useState(
    "Location is optional and stays in this page session.",
  );
  const [pending, setPending] = useState(false);
  const [radius, setRadius] = useState(25);
  const [threshold, setThreshold] = useState("MODERATE");
  const [saved, setSaved] = useState(false);
  const [maxAge, setMaxAge] = useState("all");
  const [now, setNow] = useState(() => Date.now());
  const request = useRef(0);
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 60000);
    return () => {
      clearInterval(timer);
      request.current++;
    };
  }, []);
  const candidates = useMemo(
    () =>
      location
        ? nearbyCandidates(
            observations,
            location,
            radius,
            maxAge === "all" ? null : Number(maxAge),
            now,
          ).map((candidate) => ({
            ...candidate,
            risk: buildIntelligence(
              candidate.row,
              observations,
              {
                landCover: "unknown",
                industrialDistanceKm: null,
                windKph: null,
              },
              null,
            ).predictions[0],
          }))
        : [],
    [location, observations, radius, maxAge, now],
  );
  function enable() {
    if (!navigator.geolocation) {
      setStatus("Geolocation is unavailable in this browser.");
      return;
    }
    setPending(true);
    const version = ++request.current;
    navigator.geolocation.getCurrentPosition(
      (p) => {
        if (version !== request.current) return;
        setLocation({
          latitude: p.coords.latitude,
          longitude: p.coords.longitude,
        });
        setStatus(
          `Location enabled · accuracy approximately ${Math.round(p.coords.accuracy)} m`,
        );
        setPending(false);
      },
      (e) => {
        if (version !== request.current) return;
        setStatus(
          e.code === 1
            ? "Location permission denied. You can still use the map and saved-site monitoring."
            : "Location could not be determined. Try again.",
        );
        setPending(false);
      },
      { timeout: 12000, maximumAge: 60000, enableHighAccuracy: false },
    );
  }
  return (
    <div className="intel-grid alerts-grid">
      <section className="intel-card">
        <span className="eyebrow">OPTIONAL LOCATION</span>
        <h2>Nearby thermal awareness.</h2>
        <p role="status">{status}</p>
        <button
          className="button secondary"
          disabled={pending}
          onClick={enable}
        >
          {pending ? "Locating…" : "Enable Nearby Alerts"}
        </button>
        <label className="alert-age-filter">
          Acquisition window
          <select value={maxAge} onChange={(e) => setMaxAge(e.target.value)}>
            <option value="all">All loaded acquisitions</option>
            <option value="24">Last 24 hours</option>
            <option value="48">Last 48 hours</option>
            <option value="168">Last 7 days</option>
          </select>
        </label>
        {location && (
          <>
            <button
              className="button secondary"
              onClick={() => {
                request.current++;
                setPending(false);
                setLocation(null);
                setStatus("Location cleared from this session.");
              }}
            >
              Clear location
            </button>
            <p>
              {location.latitude.toFixed(3)}, {location.longitude.toFixed(3)} ·{" "}
              {radius} km radius
            </p>
            {candidates.length ? (
              <div className="nearby-results">
                <p>
                  Up to 5 nearest coordinates, using the latest loaded
                  acquisition at each. Pixel locations can represent the same
                  site.
                </p>
                {candidates.map(({ row, distance, risk }) => (
                  <article
                    className="nearby-result"
                    key={`${row.source}:${row.id}`}
                  >
                    <RiskLevelBadge level={risk.level} />
                    <h3>
                      {distance.toFixed(1)} km away · {row.frp} MW
                    </h3>
                    <span className="evidence-chip">
                      {sourceLabel(row.source)}
                    </span>
                    <p>
                      {row.latitude.toFixed(4)}, {row.longitude.toFixed(4)}
                      <br />
                      {new Date(row.observedAt).toLocaleString()}
                      <br />
                      {acquisitionStatus(row.observedAt, now).label}
                    </p>
                    <p>
                      {risk.riskScore}/100 estimated index · confidence{" "}
                      {risk.confidence}.{" "}
                      {["LOW", "MODERATE", "HIGH", "CRITICAL"].indexOf(
                        risk.level,
                      ) >=
                      ["LOW", "MODERATE", "HIGH", "CRITICAL"].indexOf(threshold)
                        ? "Meets selected risk threshold."
                        : "Below selected risk threshold."}
                    </p>
                    <small>
                      Thermal detection within your radius. Estimate uses
                      unknown land cover, industry and wind.
                    </small>
                    {onInspect && (
                      <button
                        className="button secondary"
                        onClick={() => onInspect(row)}
                      >
                        Inspect this hotspot
                      </button>
                    )}
                  </article>
                ))}
              </div>
            ) : (
              <p>
                {observations.length
                  ? "No loaded detections match this radius and acquisition window. This does not establish safety."
                  : "No observations loaded here. Open the dashboard Alerts tab to compare NASA data."}
              </p>
            )}
          </>
        )}
        {stale && (
          <p>
            Feed is stale or unavailable. Displayed matches may be outdated.
          </p>
        )}
        <p>
          No background monitoring or automatic emergency alerts. Estimates
          reflect loaded satellite passes.
        </p>
      </section>
      <section className="intel-card">
        <span className="eyebrow">
          ALERT SETUP DEMO · BACKEND CONNECTION REQUIRED
        </span>
        <h2>Email preferences</h2>
        <form
          className="alert-form"
          onChange={() => setSaved(false)}
          onSubmit={(e) => {
            e.preventDefault();
            setSaved(true);
          }}
        >
          <label>
            Email
            <input required type="email" placeholder="you@example.com" />
          </label>
          <label>
            Risk threshold
            <select
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
            >
              {["LOW", "MODERATE", "HIGH", "CRITICAL"].map((l) => (
                <option key={l}>{l}</option>
              ))}
            </select>
          </label>
          <label>
            Radius (km)
            <input
              required
              type="number"
              min={1}
              max={500}
              value={radius}
              onChange={(e) => setRadius(Number(e.target.value))}
            />
          </label>
          <button className="button secondary" type="submit">
            Enable alerts · demo
          </button>
        </form>
        {saved && (
          <p role="status">
            Demo preferences validated for this session. No subscription created
            and no email sent.
          </p>
        )}
        <p>
          Email delivery, consent storage and scheduled checks require an alert
          backend.
        </p>
      </section>
    </div>
  );
}
