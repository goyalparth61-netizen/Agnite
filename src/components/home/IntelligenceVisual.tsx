import { useEffect, useId, useMemo, useRef, useState } from "react";
import {
  ArrowRight,
  BrainCircuit,
  Pause,
  Play,
  Radio,
  Satellite,
  ShieldCheck,
  Search,
  Plus,
  Minus,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  X,
} from "lucide-react";
import { useInView, useReducedMotion } from "framer-motion";
import {
  simulateCity,
  type City,
  type DirectoryResult,
} from "../../data/cityIntelligence";
import {
  loadDirectory,
  loadMap,
  searchDirectory,
} from "../../data/directoryClient";
import {
  limitView,
  NATIONAL_VIEW,
  projectPlace,
  viewForCluster,
  zoomView,
  type HeroMapResult,
  type MapView,
  type PlaceCluster,
} from "../../data/heroMapData";
import { INDIA_PATH } from "../../data/indiaGeometry";
import "../../styles/intelligence-visual.css";
const steps = [
  { icon: Satellite, title: "Satellite", detail: "Observe" },
  { icon: Radio, title: "Signal", detail: "Detect" },
  { icon: BrainCircuit, title: "AI context", detail: "Understand" },
  { icon: ShieldCheck, title: "Risk", detail: "Prioritize" },
];
const compact = new Intl.NumberFormat("en", {
  notation: "compact",
  maximumFractionDigits: 1,
});
export default function IntelligenceVisual() {
  const card = useRef<HTMLElement>(null);
  const inView = useInView(card);
  const reduced = useReducedMotion();
  const id = useId().replace(/:/g, "");
  const [paused, setPaused] = useState(false);
  const [hidden, setHidden] = useState(false);
  const [view, setView] = useState<MapView>(NATIONAL_VIEW);
  const [mapData, setMapData] = useState<HeroMapResult | null>(null);
  const [selected, setSelected] = useState<City | null>(null);
  const [directory, setDirectory] = useState<DirectoryResult | null>(null);
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searching, setSearching] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const drag = useRef<{
    x: number;
    y: number;
    view: MapView;
    pointer: number;
  } | null>(null);
  const moved = useRef(false);
  const [dragging, setDragging] = useState(false);
  const stopped = paused || !!reduced || hidden || !inView;
  const scale = view.width / 600;
  const spot = useMemo(
    () => (selected ? simulateCity(selected) : null),
    [selected],
  );
  useEffect(() => {
    const update = () => setHidden(document.hidden);
    update();
    document.addEventListener("visibilitychange", update);
    return () => document.removeEventListener("visibilitychange", update);
  }, []);
  useEffect(() => {
    let active = true;
    setError("");
    loadDirectory()
      .then((data) => {
        if (active) {
          setDirectory(data);
          setSelected((previous) => previous ?? data.cities[0]);
        }
      })
      .catch((reason) => {
        if (active)
          setError(
            reason instanceof Error ? reason.message : "Directory unavailable.",
          );
      });
    return () => {
      active = false;
    };
  }, [retry]);
  useEffect(() => {
    let active = true;
    setLoading(true);
    const timer = setTimeout(() => {
      loadMap(view)
        .then((data) => {
          if (active) {
            setMapData(data);
            setLoading(false);
            setError("");
          }
        })
        .catch((reason) => {
          if (active) {
            setLoading(false);
            setError(
              reason instanceof Error ? reason.message : "Map unavailable.",
            );
          }
        });
    }, 120);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [view, retry]);
  useEffect(() => {
    if (!searchOpen) return;
    let active = true;
    setSearching(true);
    const timer = setTimeout(() => {
      searchDirectory(query, "", page)
        .then((data) => {
          if (active) {
            setDirectory(data);
            setSearching(false);
          }
        })
        .catch((reason) => {
          if (active) {
            setSearching(false);
            setError(
              reason instanceof Error ? reason.message : "Search unavailable.",
            );
          }
        });
    }, 180);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [query, page, searchOpen, retry]);
  function chooseCity(city: City) {
    setSelected(city);
    setSearchOpen(false);
    const point = projectPlace(city.latitude, city.longitude);
    setView(zoomView(NATIONAL_VIEW, 28, point));
  }
  function chooseGroup(group: PlaceCluster) {
    if (moved.current) return;
    if (group.count === 1) {
      chooseCity(group.city);
      return;
    }
    const next = viewForCluster(group);
    if (view.width <= 1.21 || next.width >= view.width * 0.98) {
      setQuery(group.city.name);
      setPage(0);
      setSearchOpen(true);
      setSelected(group.city);
    } else setView(next);
  }
  const selectedPoint = selected
    ? projectPlace(selected.latitude, selected.longitude)
    : null;
  const markerVisible =
    selectedPoint &&
    selectedPoint.x >= view.x &&
    selectedPoint.x <= view.x + view.width &&
    selectedPoint.y >= view.y &&
    selectedPoint.y <= view.y + view.height;
  return (
    <section
      ref={card}
      className={`iv-card${stopped ? " iv-is-paused" : ""}`}
      aria-label="India city intelligence map"
    >
      <header className="iv-header">
        <div className="iv-header-title">
          <span className="iv-instrument-icon">
            <Satellite size={17} />
          </span>
          <div>
            <strong>India. Every place in view.</strong>
            <span>SEARCH / ZOOM / EXPLORE</span>
          </div>
        </div>
        <span className="iv-demo">DEMO</span>
      </header>
      <div className="iv-search-area">
        <div className="iv-search">
          <Search size={15} aria-hidden="true" />
          <input
            type="search"
            aria-label="Search all Indian cities, towns and villages"
            placeholder="Search any city, town or village..."
            value={query}
            onFocus={() => setSearchOpen(true)}
            onChange={(event) => {
              setQuery(event.target.value);
              setPage(0);
              setSearchOpen(true);
            }}
            onKeyDown={(event) => {
              if (event.key === "Escape") setSearchOpen(false);
            }}
            aria-expanded={searchOpen}
            aria-controls="hero-city-results"
          />
          <button
            type="button"
            aria-label={searchOpen ? "Close city results" : "Show city results"}
            onClick={() => setSearchOpen(!searchOpen)}
          >
            {searchOpen ? <X size={14} /> : <Search size={14} />}
          </button>
        </div>
        {searchOpen && (
          <div
            id="hero-city-results"
            className="iv-search-results"
            aria-label="City search results"
            aria-busy={searching}
          >
            <div className="iv-search-status" role="status">
              {searching
                ? "Searching directory..."
                : `${directory?.matching.toLocaleString("en-IN") ?? 0} matching places`}
            </div>
            {directory?.cities.map((city) => (
              <button key={city.id} onClick={() => chooseCity(city)}>
                <strong>{city.name}</strong>
                <span>{city.region}</span>
                <ArrowRight size={12} />
              </button>
            ))}
            {!searching && directory?.matching === 0 && (
              <p>No match found. Try another spelling or region.</p>
            )}
            <div className="iv-search-pages">
              <button
                aria-label="Previous city results"
                disabled={page === 0 || searching}
                onClick={() => setPage(page - 1)}
              >
                <ChevronLeft size={15} />
              </button>
              <span>
                Page {page + 1} /{" "}
                {Math.max(
                  1,
                  Math.ceil((directory?.matching ?? 0) / 8),
                ).toLocaleString("en-IN")}
              </span>
              <button
                aria-label="Next city results"
                disabled={
                  searching || (page + 1) * 8 >= (directory?.matching ?? 0)
                }
                onClick={() => setPage(page + 1)}
              >
                <ChevronRight size={15} />
              </button>
            </div>
          </div>
        )}
      </div>
      <div className="iv-map-surface">
        <div className="iv-atmosphere" aria-hidden="true" />
        <div className="iv-map-caption">
          <span className="iv-layer-key" />
          INDIA DIRECTORY{" "}
          <span>
            {mapData ? mapData.total.toLocaleString("en-IN") : "LOADING"}
          </span>
        </div>
        <button
          className="iv-motion-control"
          onClick={() => setPaused(!paused)}
          disabled={!!reduced}
          aria-label={
            reduced
              ? "Map animation disabled by reduced motion preference"
              : paused
                ? "Play map animation"
                : "Pause map animation"
          }
        >
          {stopped ? <Play size={13} /> : <Pause size={13} />}
        </button>
        <div className={`iv-map-canvas${dragging ? " iv-is-dragging" : ""}`}>
          <svg
            className="iv-geography"
            viewBox={`${view.x} ${view.y} ${view.width} ${view.height}`}
            role="group"
            aria-label="Interactive India city map. Select a numbered group to zoom, or drag to pan."
            onPointerDown={(event) => {
              if (event.button !== 0) return;
              moved.current = false;
              drag.current = {
                x: event.clientX,
                y: event.clientY,
                view,
                pointer: event.pointerId,
              };
            }}
            onPointerMove={(event) => {
              const start = drag.current;
              if (!start || start.pointer !== event.pointerId) return;
              const dx = event.clientX - start.x;
              const dy = event.clientY - start.y;
              if (Math.abs(dx) + Math.abs(dy) < 5) return;
              moved.current = true;
              setDragging(true);
              event.currentTarget.setPointerCapture(event.pointerId);
              const rect = event.currentTarget.getBoundingClientRect();
              setView(
                limitView({
                  ...start.view,
                  x: start.view.x - (dx / rect.width) * start.view.width,
                  y: start.view.y - (dy / rect.height) * start.view.height,
                }),
              );
            }}
            onPointerUp={(event) => {
              if (event.currentTarget.hasPointerCapture(event.pointerId))
                event.currentTarget.releasePointerCapture(event.pointerId);
              drag.current = null;
              setDragging(false);
            }}
            onPointerCancel={() => {
              drag.current = null;
              setDragging(false);
            }}
            onPointerLeave={() => {
              if (!dragging) drag.current = null;
            }}
          >
            <defs>
              <linearGradient id={`${id}-land`} x1="0" y1="0" x2="1" y2="1">
                <stop stopColor="#334653" />
                <stop offset="1" stopColor="#202d37" />
              </linearGradient>
              <linearGradient id={`${id}-scan`}>
                <stop stopColor="#92b9df" stopOpacity="0" />
                <stop offset="1" stopColor="#b2d3ed" stopOpacity=".25" />
              </linearGradient>
              <pattern
                id={`${id}-grid`}
                width="20"
                height="20"
                patternUnits="userSpaceOnUse"
              >
                <path
                  d="M20 0H0V20"
                  fill="none"
                  stroke="#92b9df"
                  strokeOpacity=".12"
                  strokeWidth=".6"
                />
              </pattern>
              <clipPath id={`${id}-country`}>
                <path d={INDIA_PATH} />
              </clipPath>
            </defs>
            <path
              d={INDIA_PATH}
              fill={`url(#${id}-land)`}
              stroke="#708694"
              strokeWidth={1.2 * scale}
            />
            <path d={INDIA_PATH} fill={`url(#${id}-grid)`} />
            <g clipPath={`url(#${id}-country)`}>
              <g className="iv-scan-beam">
                <rect
                  x="-95"
                  y="0"
                  width="95"
                  height="620"
                  fill={`url(#${id}-scan)`}
                />
                <path
                  d="M0 0V620"
                  stroke="#badcf5"
                  strokeOpacity=".7"
                  strokeWidth={1.5 * scale}
                />
              </g>
            </g>
            {view.width > 250 && (
              <>
                <text
                  x="75"
                  y="450"
                  className="iv-sea-label"
                  transform="rotate(-12 75 450)"
                >
                  ARABIAN SEA
                </text>
                <text
                  x="397"
                  y="435"
                  className="iv-sea-label"
                  transform="rotate(12 397 435)"
                >
                  BAY OF BENGAL
                </text>
              </>
            )}
            {mapData?.clusters.map((group) => (
              <g
                key={group.key}
                className={`iv-cluster${group.count === 1 ? " iv-single-city" : ""}`}
                role="button"
                tabIndex={0}
                aria-label={
                  group.count === 1
                    ? `Select ${group.city.name}, ${group.city.region}`
                    : `Zoom into ${group.count.toLocaleString("en-IN")} places near ${group.city.name}`
                }
                onClick={() => chooseGroup(group)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    moved.current = false;
                    chooseGroup(group);
                  }
                }}
              >
                <title>
                  {group.count.toLocaleString("en-IN")} places /{" "}
                  {group.city.name}, {group.city.region}
                </title>
                <circle
                  cx={group.x}
                  cy={group.y}
                  r={22 * scale}
                  fill="transparent"
                  stroke="none"
                />
                <circle
                  cx={group.x}
                  cy={group.y}
                  r={(group.count === 1 ? 5 : 14) * scale}
                  strokeWidth={scale}
                />
                {group.count > 1 && (
                  <text
                    x={group.x}
                    y={group.y}
                    dy={0}
                    textAnchor="middle"
                    style={{ fontSize: 11 * scale }}
                  >
                    {compact.format(group.count)}
                  </text>
                )}
                {group.count === 1 && (
                  <text
                    className="iv-city-label"
                    x={group.x + 9 * scale}
                    y={group.y + 3 * scale}
                    style={{ fontSize: 11 * scale }}
                  >
                    {group.city.name}
                  </text>
                )}
              </g>
            ))}
            {markerVisible && selectedPoint && selected && (
              <g className="iv-current-location" pointerEvents="none">
                <circle
                  cx={selectedPoint.x}
                  cy={selectedPoint.y}
                  r={9 * scale}
                  fill="#e6b477"
                  fillOpacity=".15"
                  stroke="#f6c68a"
                  strokeWidth={1.6 * scale}
                />
                <circle
                  cx={selectedPoint.x}
                  cy={selectedPoint.y}
                  r={3 * scale}
                  fill="#ffe0b5"
                />
                <text
                  x={selectedPoint.x}
                  y={selectedPoint.y - 15 * scale}
                  textAnchor="middle"
                  style={{ fontSize: 13 * scale }}
                >
                  {selected.name}
                </text>
              </g>
            )}
          </svg>
          <div className="iv-zoom-tools">
            <button
              aria-label="Zoom in on city map"
              disabled={view.width <= 1.2}
              onClick={() => setView((current) => zoomView(current, 2))}
            >
              <Plus size={15} />
            </button>
            <span>{(600 / view.width).toFixed(0)}x</span>
            <button
              aria-label="Zoom out on city map"
              disabled={view.width >= 600}
              onClick={() => setView((current) => zoomView(current, 0.5))}
            >
              <Minus size={15} />
            </button>
            <button
              aria-label="Reset India city map"
              onClick={() => setView(NATIONAL_VIEW)}
            >
              <RotateCcw size={14} />
            </button>
          </div>
        </div>
        <div className="iv-map-footer">
          <span>
            <i />
            {stopped ? "ANIMATION PAUSED" : "SIMULATED SATELLITE SWEEP"}
          </span>
          <span>
            {loading
              ? "UPDATING..."
              : `${(mapData?.visible ?? 0).toLocaleString("en-IN")} PLACES IN VIEW`}
          </span>
        </div>
        <p className="iv-map-help">
          Select a group to zoom. Drag to pan. Search to find any listed place.
        </p>
        {error && (
          <div className="iv-map-error" role="alert">
            {error}
            <button onClick={() => setRetry(retry + 1)}>Retry</button>
          </div>
        )}
      </div>
      <div className="iv-observation iv-readout" aria-live="polite">
        <div className="iv-observation-copy">
          <span className="iv-kicker">SELECTED PLACE / THERMAL SIMULATION</span>
          <strong>
            {selected
              ? `${selected.name}, ${selected.region}`
              : "Choose a place on the map"}
          </strong>
          <span className="iv-observation-type">
            {spot?.type ?? "Geographic directory loading..."}
            <span className="iv-observation-coordinates">
              {selected
                ? `${selected.latitude.toFixed(3)} N / ${selected.longitude.toFixed(3)} E`
                : "Cities, towns and villages across India"}
            </span>
          </span>
        </div>
        {spot && (
          <div className={`iv-risk ${spot.risk >= 70 ? "iv-risk-high" : ""}`}>
            <span>DEMO RISK</span>
            <strong>
              {spot.risk}
              <small>/100</small>
            </strong>
            <div className="iv-risk-track">
              <span style={{ width: `${spot.risk}%` }} />
            </div>
          </div>
        )}
      </div>
      <ol className="iv-pipeline" aria-label="Satellite to risk workflow">
        {steps.map(({ icon: Icon, title, detail }, index) => (
          <li key={title}>
            <Icon size={16} />
            <div>
              <strong>{title}</strong>
              <span>{detail}</span>
            </div>
            {index < 3 && (
              <ArrowRight className="iv-pipeline-arrow" size={11} />
            )}
          </li>
        ))}
      </ol>
      <p className="iv-disclaimer">
        Groups count every directory record in view.{" "}
        <a href="https://www.geonames.org/" target="_blank" rel="noreferrer">
          GeoNames / CC BY 4.0
        </a>
        . Includes towns and villages; source coverage is not exhaustive.
        Thermal values are simulated.
      </p>
    </section>
  );
}
