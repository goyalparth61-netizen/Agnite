import { GraduationCap, Users } from "lucide-react";
import SectionHeader, { Reveal } from "../common/SectionHeader";
import { teamMembers, teamMeta } from "../../data/teamData";

export default function TeamSection() {
  return (
    <section id="team" className="section container team-section">
      <Reveal>
        <SectionHeader
          label="07 / TEAM TIMEPASS"
          title="THE PEOPLE BEHIND AGNITE."
          text="A multidisciplinary student team from Quantum University building thermal intelligence for faster, explainable and data-driven decisions."
        />

        <div className="team-command-card">
          <div className="team-command-copy">
            <span className="team-kicker">
              <Users size={15} />
              {teamMeta.name.toUpperCase()}
            </span>

            <h3>{teamMeta.project}</h3>

            <p>
              AI-Powered Thermal Intelligence for {teamMeta.event}.
              Our team combines AI/ML, computer science and application
              development to build a system that connects historical thermal
              behaviour, present observations and explainable risk intelligence.
            </p>
          </div>

          <div className="team-university">
            <GraduationCap size={25} />

            <div>
              <span>INSTITUTION</span>
              <strong>{teamMeta.university}</strong>
              <small>{teamMeta.problemStatement}</small>
            </div>
          </div>
        </div>

        <div className="team-grid">
          {teamMembers.map((member, index) => (
            <article className="team-member-card" key={member.name}>
              <div className="team-member-index">
                {String(index + 1).padStart(2, "0")}
              </div>

              <div className="team-avatar" aria-hidden="true">
                {member.name
                  .split(" ")
                  .map((part) => part[0])
                  .slice(0, 2)
                  .join("")}
              </div>

              <div className="team-member-copy">
                <h3>{member.name}</h3>
                <span>{member.program}</span>
                <small>Quantum University</small>
              </div>
            </article>
          ))}
        </div>
      </Reveal>
    </section>
  );
}
