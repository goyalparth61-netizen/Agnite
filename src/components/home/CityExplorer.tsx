import {
  Search,
  MapPin,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
} from "lucide-react";
import { citySummary, type City } from "../../data/cityIntelligence";
const PAGE_SIZE = 8;
export default function CityExplorer({
  result,
  selected,
  onSelect,
  query,
  region,
  onQuery,
  onRegion,
  onPage,
  busy,
}: {
  result: import("../../data/cityIntelligence").DirectoryResult;
  selected: City;
  onSelect: (city: City) => void;
  query: string;
  region: string;
  onQuery: (value: string) => void;
  onRegion: (value: string) => void;
  onPage: (page: number) => void;
  busy: boolean;
}) {
  const { cities, regions, matching, page: currentPage, total } = result;
  const pages = Math.max(1, Math.ceil(matching / PAGE_SIZE));
  const reset = () => {
    onQuery("");
    onRegion("");
    onPage(0);
  };
  return (
    <div className="city-explorer">
      <div className="explorer-heading">
        <div>
          <span className="eyebrow">NATIONWIDE DIRECTORY</span>
          <h3>Find your city.</h3>
        </div>
        <span className="coverage-pill">
          {total.toLocaleString("en-IN")} places
        </span>
      </div>
      <div className="city-filters">
        <label className="city-search">
          <Search size={16} />
          <span className="sr-only">
            Search Indian cities, towns or villages
          </span>
          <input
            type="search"
            placeholder="Search city, town or village..."
            value={query}
            onChange={(e) => {
              onQuery(e.target.value);
              onPage(0);
            }}
          />
        </label>
        <label>
          <span className="sr-only">Filter by state or union territory</span>
          <select
            aria-label="State or union territory"
            value={region}
            onChange={(e) => {
              onRegion(e.target.value);
              onPage(0);
            }}
          >
            <option value="">All states & territories</option>
            {regions.map((r) => (
              <option key={r}>{r}</option>
            ))}
          </select>
        </label>
      </div>
      <div className="directory-count">
        <span aria-live="polite">
          {matching.toLocaleString("en-IN")} matching places
          {busy ? " / searching..." : ""}
        </span>
        <button onClick={reset}>
          <RotateCcw size={11} /> Reset filters
        </button>
      </div>
      <div
        className="city-results"
        aria-busy={busy}
        aria-label="Matching places"
      >
        {cities.map((city) => {
          const summary = citySummary(city);
          return (
            <button
              key={city.id}
              className="city-result"
              aria-pressed={city.id === selected.id}
              onClick={() => onSelect(city)}
            >
              <MapPin size={15} />
              <span>
                <strong>{city.name}</strong>
                <small>{city.region}</small>
              </span>
              <span
                className={`city-risk ${summary.risk >= 70 ? "high" : summary.risk >= 40 ? "moderate" : "low"}`}
              >
                <strong>{summary.count} demo hotspots</strong>
                <small>{summary.risk}/100 simulated risk</small>
              </span>
            </button>
          );
        })}
        {!matching && (
          <div className="empty-cities">
            <Search size={24} />
            <h4>No matching places</h4>
            <p>
              Try another spelling or remove the state filter. The source may
              not include every settlement.
            </p>
            <button className="button secondary" onClick={reset}>
              Show all places
            </button>
          </div>
        )}
      </div>
      {matching > 0 && (
        <div className="city-pagination">
          <button
            aria-label="Previous city results"
            disabled={currentPage === 0}
            onClick={() => onPage(currentPage - 1)}
          >
            <ChevronLeft size={16} />
          </button>
          <span>
            Page {currentPage + 1} of {pages.toLocaleString("en-IN")}
          </span>
          <button
            aria-label="Next city results"
            disabled={currentPage >= pages - 1}
            onClick={() => onPage(currentPage + 1)}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}
      <p className="directory-source">
        City names and coordinates:{" "}
        <a href="https://www.geonames.org/" target="_blank" rel="noreferrer">
          GeoNames
        </a>{" "}
        /{" "}
        <a
          href="https://creativecommons.org/licenses/by/4.0/"
          target="_blank"
          rel="noreferrer"
        >
          CC BY 4.0
        </a>
        . Includes towns and villages; not an exhaustive official city register.
        Thermal data is simulated.
      </p>
    </div>
  );
}
