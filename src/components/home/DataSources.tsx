import { Database, ArrowUpRight } from "lucide-react";
import SectionHeader, { Reveal } from "../common/SectionHeader";
import { sources } from "../../data/homeData";
export default function DataSources() {
  return (
    <section className="section container data-section">
      <Reveal>
        <SectionHeader
          label="05 / MULTI-SOURCE BY DESIGN"
          title="A STRONGER FOUNDATION FOR EVERY INSIGHT."
          text="NASA FIRMS observations and OpenStreetMap basemaps are connected. Additional automatic context integrations remain planned."
        />
        <div className="data-grid">
          {sources.map(([name, contribution]) => (
            <article key={name}>
              <Database size={20} />
              <h3>{name}</h3>
              <p>{contribution}</p>
              <span>
                {["NASA FIRMS", "VIIRS", "MODIS"].includes(name) ? "LIVE OBSERVATIONS" : name === "OpenStreetMap" ? "BASEMAP CONNECTED" : "PLANNED INTEGRATION"} <ArrowUpRight size={12} />
              </span>
            </article>
          ))}
        </div>
      </Reveal>
    </section>
  );
}
