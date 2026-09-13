import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useInView, useReducedMotion } from "framer-motion";
import { ArrowUpRight, Crosshair, BrainCircuit } from "lucide-react";
import SectionHeader, { Reveal } from "../common/SectionHeader";
import StatusBadge from "../common/StatusBadge";
import AnimatedNumber from "../common/AnimatedNumber";
import { loadDirectory, searchDirectory } from "../../data/directoryClient";
import CityExplorer from "./CityExplorer";
const CityMap = lazy(() => import("./CityMap"));
import {
  simulateCity,
  type City,
  type DirectoryResult,
} from "../../data/cityIntelligence";
export default function DashboardPreview() {
  const root = useRef<HTMLElement>(null);
  const near = useInView(root, { once: true, margin: "600px" });
  const [result, setResult] = useState<DirectoryResult | null>(null);
  const [selected, setSelected] = useState<City | null>(null);
  const [query, setQuery] = useState("");
  const [region, setRegion] = useState("");
  const [page, setPage] = useState(0);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [window, setWindow] = useState(0);
  const reduced = useReducedMotion();
  useEffect(() => {
    if (!near) return;
    let active = true;
    setError("");
    setBusy(true);
    const timer = setTimeout(
      () => {
        const task =
          query || region || page
            ? searchDirectory(query, region, page)
            : loadDirectory();
        task
          .then((data) => {
            if (!active) return;
            setResult(data);
            setSelected((previous) => previous ?? data.cities[0]);
            setBusy(false);
          })
          .catch((error) => {
            if (active) {
              setError(
                error instanceof Error
                  ? error.message
                  : "City directory unavailable.",
              );
              setBusy(false);
            }
          });
      },
      query ? 180 : 0,
    );
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [near, attempt, query, region, page]);
  const spot = useMemo(
    () => (selected ? simulateCity(selected) : null),
    [selected],
  );
  if (!result || !selected || !spot)
    return (
      <section id="platform" ref={root} className="section container">
        <SectionHeader
          label="04 / INDIA INTELLIGENCE"
          title="EVERY CITY. A CLOSER LOOK."
        />
        <div className="directory-loading" role="status">
          <Crosshair size={28} />
          <h3>
            {error ? "Directory unavailable" : "Preparing the India directory"}
          </h3>
          <p>
            {error ||
              "Loading city names and coordinates. Search will run in the background to keep the workspace responsive."}
          </p>
          {error && (
            <button
              className="button secondary"
              onClick={() => setAttempt(attempt + 1)}
            >
              Retry directory
            </button>
          )}
        </div>
      </section>
    );
  const summary = result.summary;
  const trend = spot.history.map((value, i) => ({
    day: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i],
    current: value,
    baseline: 22 + (i % 3) * 3,
  }));
  const risk = Math.min(99, spot.risk + [0, 4, 8][window]);
  return (
    <section id="platform" ref={root} className="section container">
      <Reveal>
        <div className="section-top">
          <SectionHeader
            label="04 / THE COMMAND CENTER"
            title="EVERY CITY. A CLOSER LOOK."
          />
          <span className="preview-hint">
            Explore the demo <ArrowUpRight size={18} />
          </span>
        </div>
        <div className="dashboard">
          <div className="dashboard-header">
            <div>
              <Crosshair size={18} />
              <strong>
                AGNITE <span>/ Intelligence workspace</span>
              </strong>
            </div>
            <StatusBadge />
          </div>
          <div className="demo-notice">
            GEOGRAPHY: GEONAMES / THERMAL DATA: SIMULATION. Search Indian
            cities, towns and villages. Hotspots, classifications, confidence
            and risk are generated examples, not observed events.
          </div>
          <div className="metrics">
            {[
              ["Demo Hotspots", summary.count, ""],
              ["Industrial Fire Scenarios", summary.industrial, ""],
              ["Persistent Heat Scenarios", summary.persistent, ""],
              ["Natural Fire Scenarios", summary.natural, ""],
              ["High Risk Demo Places", summary.high, ""],
              ["Demo Confidence", summary.confidence, "%"],
            ].map(([label, value, suffix]) => (
              <div key={label}>
                <span>{label}</span>
                <strong>
                  <AnimatedNumber
                    value={Number(value)}
                    suffix={String(suffix)}
                  />
                </strong>
                <small>FILTERED / SIMULATION</small>
              </div>
            ))}
          </div>
          <div className="directory-scope" aria-live="polite">
            Metrics cover {result.matching.toLocaleString("en-IN")} matching
            places. {busy && "Updating search..."}{" "}
            {error && <span role="alert">{error}</span>}
          </div>
          <div className="city-workspace">
            <CityExplorer
              result={result}
              selected={selected}
              onSelect={setSelected}
              query={query}
              region={region}
              onQuery={(value) => {
                setQuery(value);
                setPage(0);
              }}
              onRegion={(value) => {
                setRegion(value);
                setPage(0);
              }}
              onPage={setPage}
              busy={busy}
            />
            <Suspense
              fallback={
                <div className="directory-loading" role="status">
                  Loading interactive map...
                </div>
              }
            >
              <CityMap
                cities={result.points}
                selected={selected}
                onSelect={setSelected}
              />
            </Suspense>
          </div>
          <div className="dashboard-body city-analysis-body">
            <div className="analysis-panel" aria-live="polite">
              <div className="panel-title">
                LOCATION INTELLIGENCE <span>SIMULATION</span>
              </div>
              <h3>{spot.name}</h3>
              <div className="city-facts">
                <span>GEONAMES / LOCATION DATA</span>
                <p>
                  {selected.latitude.toFixed(4)} N /{" "}
                  {selected.longitude.toFixed(4)} E
                </p>
                <p>
                  Source population:{" "}
                  {selected.population > 0
                    ? selected.population.toLocaleString("en-IN")
                    : "Not available"}{" "}
                  <small>(source record; not a current estimate)</small>
                </p>
                <a
                  href={`https://www.geonames.org/${selected.id}/`}
                  target="_blank"
                  rel="noreferrer"
                >
                  View geographic source
                </a>
              </div>
              <p className="selected-scope">
                Analysis stays on the selected place until you choose another
                result.
              </p>
              <div className="classification">
                <span>{spot.type}</span>
                <strong>
                  {spot.confidence}%<small>CONFIDENCE</small>
                </strong>
              </div>
              <div className="risk-heading">
                <span>Future risk window</span>
                <StatusBadge>SIMULATION</StatusBadge>
              </div>
              <div className="risk-tabs" aria-label="Risk window">
                {["Next 24 hours", "Next 48 hours", "Next 7 days"].map(
                  (label, i) => (
                    <button
                      key={label}
                      aria-pressed={window === i}
                      onClick={() => setWindow(i)}
                    >
                      {label}
                    </button>
                  ),
                )}
              </div>
              <div className="risk-score">
                <strong>
                  {risk}
                  <small>/100</small>
                </strong>
                <span>
                  {risk >= 70 ? "HIGH" : risk >= 40 ? "MODERATE" : "LOW"} RISK
                  INDEX
                </span>
              </div>
              <div className="risk-bar">
                <i style={{ width: `${risk}%` }} />
              </div>
              <div className="ai-explanation">
                <span className="eyebrow">
                  <BrainCircuit size={15} /> AGNITE AI / EXPLANATION
                </span>
                <p>{spot.evidence}</p>
                <div className="factor-tags">
                  {spot.factors.map((f) => (
                    <span key={f}>{f}</span>
                  ))}
                </div>
                <div className="recommendation">
                  <strong>RECOMMENDED ACTION</strong>
                  <p>{spot.action}</p>
                </div>
              </div>
            </div>
            <div className="chart-panel">
              <div className="panel-title">
                <span>HISTORICAL TIMELINE / THERMAL TREND</span>
                <span>
                  <i className="legend-line" /> Current anomaly{" "}
                  <i className="legend-line baseline" /> Historical baseline
                </span>
              </div>
              <div
                className="trend-chart"
                role="img"
                aria-label={`Simulated daily thermal index for ${spot.name}: ${spot.history.join(", ")}. Historical baseline between 22 and 28.`}
              >
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart
                    data={trend}
                    margin={{ top: 15, right: 10, left: -25, bottom: 0 }}
                  >
                    <defs>
                      <linearGradient
                        id="trend-fill"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="0%"
                          stopColor="#e6b477"
                          stopOpacity={0.22}
                        />
                        <stop
                          offset="100%"
                          stopColor="#e6b477"
                          stopOpacity={0}
                        />
                      </linearGradient>
                    </defs>
                    <CartesianGrid vertical={false} stroke="#35404b" />
                    <XAxis
                      dataKey="day"
                      stroke="#b2bdc7"
                      tickLine={false}
                      axisLine={false}
                      fontSize={11}
                    />
                    <YAxis
                      domain={[0, 100]}
                      stroke="#b2bdc7"
                      tickLine={false}
                      axisLine={false}
                      fontSize={10}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "#202832",
                        border: "1px solid #46515d",
                        borderRadius: 6,
                      }}
                      labelStyle={{ color: "#f1f6f8" }}
                    />
                    <Area
                      name="Historical baseline"
                      type="monotone"
                      dataKey="baseline"
                      fill="transparent"
                      stroke="#92b9df"
                      strokeDasharray="4 4"
                      isAnimationActive={!reduced}
                    />
                    <Area
                      name="Current anomaly"
                      type="monotone"
                      dataKey="current"
                      fill="url(#trend-fill)"
                      stroke="#e6b477"
                      strokeWidth={2}
                      isAnimationActive={!reduced}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
          <div className="dashboard-bottom">
            <span>GEONAMES SNAPSHOT / {result.downloaded} / SIH26162</span>
            <span>Designed for human-led decisions.</span>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
