import { useEffect, useState } from "react";
import { ArrowUpRight, Flame, Menu, X } from "lucide-react";
import StatusBadge from "../common/StatusBadge";
const links = [
  ["Home", "home"],
  ["Platform", "platform"],
  ["Intelligence", "intelligence"],
  ["Technology", "technology"],
  ["Impact", "impact"],
  ["Team", "team"],
];
export default function Navbar() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [active, setActive] = useState("home");
  useEffect(() => {
    const update = () => {
      setScrolled(window.scrollY > 24);
      const current = links
        .filter(
          ([, id]) =>
            (document.getElementById(id)?.getBoundingClientRect().top ??
              Infinity) < 180,
        )
        .slice(-1)[0];
      setActive(current?.[1] ?? "home");
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
    return () => window.removeEventListener("scroll", update);
  }, []);
  return (
    <header className={`navbar ${scrolled ? "scrolled" : ""}`}>
      <div className="nav-inner">
        <a href="#home" className="brand" aria-label="AGNITE home">
          <Flame className="brand-mark" size={30} />
          <span>
            <strong>AGNITE</strong>
            <small>AI-Powered Thermal Intelligence</small>
          </span>
        </a>
        <nav
          id="main-navigation"
          aria-label="Main navigation"
          className={open ? "nav-links open" : "nav-links"}
          onKeyDown={(e) => {
            if (e.key === "Escape") {
              setOpen(false);
              document.getElementById("menu-toggle")?.focus();
            }
          }}
        >
          {links.map(([label, id]) => (
            <a
              key={id}
              href={`#${id}`}
              aria-current={active === id ? "location" : undefined}
              onClick={() => setOpen(false)}
            >
              {label}
            </a>
          ))}
        </nav>
        <div className="nav-actions">
          <StatusBadge />
          <a className="button small secondary" href="#/workspace">
            Launch Dashboard <ArrowUpRight size={14} />
          </a>
        </div>
        <button
          id="menu-toggle"
          className="menu-toggle"
          aria-label={open ? "Close navigation" : "Open navigation"}
          aria-expanded={open}
          aria-controls="main-navigation"
          onClick={() => setOpen(!open)}
        >
          {open ? <X /> : <Menu />}
        </button>
      </div>
    </header>
  );
}
