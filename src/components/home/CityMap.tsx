import { useEffect, useMemo, useRef, useState } from "react";
import { useInView, useReducedMotion } from "framer-motion";
import L from "leaflet";
import type { GeoJsonObject } from "geojson";
import {
  Crosshair,
  Minus,
  Plus,
  LocateFixed,
  Layers,
  Maximize2,
  Navigation,
  RefreshCw,
  MapPin,
} from "lucide-react";
import {
  citySummary,
  simulateCity,
  type City,
} from "../../data/cityIntelligence";
import {
  clusterCities,
  INDIA_BOUNDS,
  validPosition,
} from "../../data/mapViewport";
import indiaBoundary from "../../data/indiaBoundary.json";
import "leaflet/dist/leaflet.css";
import "../../styles/city-map.css";

function safeLabel(title: string, detail: string) {
  const element = document.createElement("div");
  const heading = document.createElement("strong");
  heading.textContent = title;
  const body = document.createElement("span");
  body.textContent = detail;
  element.append(heading, body);
  return element;
}
export default function CityMap({
  cities,
  selected,
  onSelect,
}: {
  cities: City[];
  selected: City;
  onSelect: (city: City) => void;
}) {
  const host = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const placesRef = useRef<L.LayerGroup | null>(null);
  const hotspotsRef = useRef<L.LayerGroup | null>(null);
  const tilesRef = useRef<L.TileLayer | null>(null);
  const focusRef = useRef<L.LayerGroup | null>(null);
  const latestSelect = useRef(onSelect);
  latestSelect.current = onSelect;
  const previousView = useRef<{ city: number; pointsKey: string } | null>(null);
  const reduced = useReducedMotion();
  const visible = useInView(host, { amount: 0.1 });
  const [zoom, setZoom] = useState(4);
  const [viewport, setViewport] = useState(0);
  const [style, setStyle] = useState<"tactical" | "street">("tactical");
  const [showHotspots, setShowHotspots] = useState(true);
  const [tileError, setTileError] = useState(false);
  const [detectionId, setDetectionId] = useState("");
  const [ready, setReady] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const pointsKey = useMemo(
    () => cities.map((city) => city.id).join(","),
    [cities],
  );
  const scenario = useMemo(() => simulateCity(selected), [selected]);
  const current =
    scenario.detections.find((d) => d.id === detectionId) ??
    scenario.detections[0];
  const animate = !reduced;
  const focusCity = () => {
    const map = mapRef.current;
    if (!map) return;
    const points = scenario.detections.map((d) =>
      L.latLng(d.latitude, d.longitude),
    );
    map.fitBounds(L.latLngBounds(points).pad(0.45), {
      padding: [50, 50],
      maxZoom: 13,
      animate,
    });
  };
  const fitResults = () => {
    const map = mapRef.current;
    if (!map || !cities.length) return;
    map.fitBounds(
      L.latLngBounds(cities.map((c) => [c.latitude, c.longitude])),
      { padding: [35, 35], maxZoom: 12, animate },
    );
  };
  useEffect(() => {
    if (!host.current) return;
    const map = L.map(host.current, {
      zoomControl: false,
      scrollWheelZoom: false,
      minZoom: 3,
      maxZoom: 18,
      zoomSnap: 0.5,
      zoomDelta: 1,
      attributionControl: true,
      zoomAnimation: !reduced,
      fadeAnimation: !reduced,
      markerZoomAnimation: !reduced,
      maxBounds: [
        [0, 58],
        [44, 106],
      ],
      maxBoundsViscosity: 0.8,
    });
    mapRef.current = map;
    map.attributionControl.setPrefix(false);
    map.attributionControl.addAttribution(
      'Outline: <a href="https://www.naturalearthdata.com/" target="_blank" rel="noreferrer">Natural Earth</a>',
    );
    L.geoJSON(indiaBoundary as GeoJsonObject, {
      interactive: false,
      style: {
        color: "#8295a5",
        weight: 1,
        opacity: 0.5,
        fillColor: "#657c8c",
        fillOpacity: 0.08,
      },
    }).addTo(map);
    L.control
      .scale({ position: "bottomleft", imperial: false, maxWidth: 90 })
      .addTo(map);
    placesRef.current = L.layerGroup().addTo(map);
    hotspotsRef.current = L.layerGroup().addTo(map);
    focusRef.current = L.layerGroup().addTo(map);
    map.fitBounds(INDIA_BOUNDS, { padding: [15, 15], animate: false });
    const update = () => {
      setZoom(map.getZoom());
      setViewport((value) => value + 1);
    };
    map.on("moveend zoomend", update);
    update();
    const resize = new ResizeObserver(() => map.invalidateSize({ pan: false }));
    resize.observe(host.current);
    setReady(true);
    return () => {
      resize.disconnect();
      map.off();
      map.remove();
      mapRef.current = null;
      placesRef.current = null;
      hotspotsRef.current = null;
      focusRef.current = null;
      tilesRef.current = null;
      previousView.current = null;
    };
    // The map instance persists; reactive layers and movement are handled below.
  }, []);
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready || !visible) return;
    const tiles = L.tileLayer(
      "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        maxZoom: 19,
        updateWhenIdle: true,
        keepBuffer: 1,
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors',
      },
    );
    tilesRef.current = tiles;
    tiles.on("tileerror", () => setTileError(true));
    tiles.on("tileload", () => setTileError(false));
    tiles.addTo(map);
    return () => {
      tiles.off();
      tiles.remove();
      tilesRef.current = null;
    };
  }, [ready, visible]);
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    if (previousView.current) {
      if (previousView.current.city !== selected.id) {
        setDetectionId("");
        focusCity();
      } else if (previousView.current.pointsKey !== pointsKey && cities.length)
        fitResults();
    }
    previousView.current = { city: selected.id, pointsKey };
  }, [ready, pointsKey, selected.id]);
  useEffect(() => {
    const map = mapRef.current;
    const layer = placesRef.current;
    if (!map || !layer) return;
    layer.clearLayers();
    const extent = map.getBounds().pad(0.1);
    const shown = cities.filter(
      (c) =>
        c.id !== selected.id &&
        validPosition(c.latitude, c.longitude) &&
        extent.contains([c.latitude, c.longitude]),
    );
    for (const group of clusterCities(shown, map.getZoom())) {
      if (group.members.length > 1) {
        const marker = L.marker([group.latitude, group.longitude], {
          icon: L.divIcon({
            className: "gis-cluster",
            html: `<span>${group.members.length}</span>`,
            iconSize: [34, 34],
            iconAnchor: [17, 17],
          }),
          title: `Zoom into ${group.members.length} representative places`,
          keyboard: true,
        });
        marker.on("click", () => {
          const bounds = L.latLngBounds(
            group.members.map((c) => [c.latitude, c.longitude]),
          );
          map.fitBounds(bounds, {
            padding: [50, 50],
            maxZoom: Math.min(18, map.getZoom() + 3),
            animate,
          });
        });
        marker.bindTooltip(`${group.members.length} places / click to expand`, {
          direction: "top",
          className: "gis-tooltip",
        });
        layer.addLayer(marker);
      } else {
        const city = group.members[0];
        const high = citySummary(city).risk >= 70;
        const marker = L.marker([city.latitude, city.longitude], {
          icon: L.divIcon({
            className: `gis-place ${high ? "is-high" : ""}`,
            html: "<span></span>",
            iconSize: [26, 26],
            iconAnchor: [13, 13],
          }),
          title: `Select ${city.name}, ${city.region}`,
          keyboard: true,
        });
        marker.bindTooltip(
          safeLabel(city.name, `${city.region} / simulated risk`),
          { direction: "top", className: "gis-tooltip" },
        );
        marker.on("click", () => {
          latestSelect.current(city);
        });
        layer.addLayer(marker);
      }
    }
  }, [ready, viewport, cities, selected.id, reduced]);
  useEffect(() => {
    const map = mapRef.current;
    const layer = focusRef.current;
    if (!map || !layer) return;
    layer.clearLayers();
    const marker = L.marker([selected.latitude, selected.longitude], {
      icon: L.divIcon({
        className: "gis-selected-marker",
        html: "<span></span>",
        iconSize: [34, 34],
        iconAnchor: [17, 17],
      }),
      zIndexOffset: 500,
      keyboard: true,
      title: `Inspect hotspots in ${selected.name}`,
    });
    marker.bindTooltip(
      safeLabel(selected.name, "Selected city / click for hotspots"),
      { direction: "top", className: "gis-tooltip", permanent: zoom < 10 },
    );
    marker.on("click", focusCity);
    layer.addLayer(marker);
  }, [ready, selected, zoom, reduced]);
  useEffect(() => {
    const map = mapRef.current;
    const layer = hotspotsRef.current;
    if (!map || !layer) return;
    layer.clearLayers();
    if (!showHotspots || zoom < 9) return;
    scenario.detections.forEach((spot, index) => {
      const active = spot.id === current.id;
      const marker = L.marker([spot.latitude, spot.longitude], {
        icon: L.divIcon({
          className: `gis-hotspot ${active ? "is-active" : ""}`,
          html: `<span>H${index + 1}</span>`,
          iconSize: [34, 34],
          iconAnchor: [17, 17],
        }),
        zIndexOffset: 800 + index,
        keyboard: true,
        title: `Inspect simulated hotspot H${index + 1}: ${spot.frp} MW`,
      });
      marker.bindTooltip(
        safeLabel(
          `H${index + 1} / ${spot.frp} MW`,
          "Simulated fire radiative power",
        ),
        { direction: "top", className: "gis-tooltip" },
      );
      marker.on("click", () => setDetectionId(spot.id));
      layer.addLayer(marker);
    });
  }, [ready, scenario, showHotspots, zoom, current.id]);
  useEffect(() => {
    mapRef.current?.invalidateSize({ pan: false });
  }, [expanded]);
  return (
    <div className={`gis-panel ${expanded ? "is-expanded" : ""}`}>
      <div className="gis-heading">
        <div>
          <span className="eyebrow">GEOSPATIAL WORKSPACE</span>
          <h3>India, in context.</h3>
        </div>
        <span className="gis-mode">
          <i /> DEMO OVERLAY
        </span>
      </div>
      <div className="gis-toolbar">
        <div className="gis-style-switch" aria-label="Basemap appearance">
          <button
            aria-pressed={style === "tactical"}
            onClick={() => setStyle("tactical")}
          >
            Tactical
          </button>
          <button
            aria-pressed={style === "street"}
            onClick={() => setStyle("street")}
          >
            Street
          </button>
        </div>
        <button
          className="gis-icon-button"
          title="Fit matching places"
          aria-label="Fit matching places"
          onClick={fitResults}
          disabled={!cities.length}
        >
          <Maximize2 size={16} />
        </button>
        <button
          className="gis-icon-button"
          title="Show all India"
          aria-label="Show all India"
          onClick={() =>
            mapRef.current?.fitBounds(INDIA_BOUNDS, {
              padding: [15, 15],
              animate,
            })
          }
        >
          <Navigation size={16} />
        </button>
        <button
          className="gis-icon-button"
          aria-label={expanded ? "Collapse map" : "Expand map"}
          aria-pressed={expanded}
          onClick={() => setExpanded(!expanded)}
        >
          <Layers size={16} />
        </button>
      </div>
      <div className={`gis-map-frame map-style-${style}`}>
        <div
          ref={host}
          className="gis-map"
          role="region"
          aria-label="Interactive India map. Drag to pan, use plus and minus or pinch to zoom. Select a city marker to inspect its simulated hotspots."
        />
        <div className="gis-zoom-controls">
          <button
            aria-label="Zoom in"
            disabled={zoom >= 18}
            onClick={() => mapRef.current?.zoomIn(1, { animate })}
          >
            <Plus size={18} />
          </button>
          <button
            aria-label="Zoom out"
            disabled={zoom <= 3}
            onClick={() => mapRef.current?.zoomOut(1, { animate })}
          >
            <Minus size={18} />
          </button>
          <button aria-label="Center on selected city" onClick={focusCity}>
            <LocateFixed size={17} />
          </button>
        </div>
        <span className="gis-map-caption">
          {zoom >= 9 ? "CITY DETAIL" : "NATIONAL OVERVIEW"} / Z{zoom.toFixed(1)}
        </span>
        {tileError && (
          <div className="gis-tile-notice" role="status">
            Street tiles unavailable. Outline and demo markers remain usable.
            <button
              onClick={() => {
                setTileError(false);
                tilesRef.current?.redraw();
              }}
              aria-label="Retry street tiles"
            >
              <RefreshCw size={13} />
            </button>
          </div>
        )}
      </div>
      <div className="gis-map-meta">
        <span>Drag to pan / + - or pinch to zoom</span>
        <label>
          <input
            type="checkbox"
            checked={showHotspots}
            onChange={(e) => setShowHotspots(e.target.checked)}
          />{" "}
          Demo hotspots
        </label>
      </div>
      <div className="gis-location">
        <MapPin size={19} />
        <div>
          <strong>{selected.name}</strong>
          <span>
            {selected.region} / {selected.latitude.toFixed(3)} N,{" "}
            {selected.longitude.toFixed(3)} E
          </span>
        </div>
        <button onClick={focusCity}>
          <Crosshair size={14} /> Inspect
        </button>
      </div>
      <div className="gis-detail">
        <div className="gis-detail-title">
          <span>SELECTED HOTSPOT</span>
          <span>SIMULATION</span>
        </div>
        <div className="gis-reading">
          <strong>
            {current.frp}
            <small>MW</small>
          </strong>
          <div>
            <span>Fire radiative power</span>
            <small>{current.confidence}% simulated confidence</small>
          </div>
        </div>
        <label className="gis-hotspot-select">
          Detection
          <select
            value={current.id}
            onChange={(e) => {
              setDetectionId(e.target.value);
              setShowHotspots(true);
              const hit = scenario.detections.find(
                (d) => d.id === e.target.value,
              );
              if (hit)
                mapRef.current?.setView(
                  [hit.latitude, hit.longitude],
                  Math.max(13, zoom),
                  { animate },
                );
            }}
          >
            {scenario.detections.map((d, i) => (
              <option key={d.id} value={d.id}>
                H{i + 1} / {d.frp} MW / Demo
              </option>
            ))}
          </select>
        </label>
        <p>
          {current.latitude.toFixed(4)} N / {current.longitude.toFixed(4)} E.
          Generated example; not an observed fire.
        </p>
      </div>
      <div className="gis-legend">
        <span>
          <i className="selected" />
          Selected city
        </span>
        <span>
          <i />
          Demo hotspot
        </span>
        <span>
          <i className="cluster" />
          Grouped places
        </span>
      </div>
      <p className="gis-footnote">
        Markers represent matching directory places; zoom in to separate groups.
        Street tiles need internet.{" "}
        <a
          href="https://www.openstreetmap.org/fixthemap"
          target="_blank"
          rel="noreferrer"
        >
          Report a map issue
        </a>
      </p>
    </div>
  );
}
