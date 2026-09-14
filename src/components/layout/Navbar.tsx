import { useEffect, useState } from "react";
import { ArrowUpRight, Flame, Menu, X } from "lucide-react";
import StatusBadge from "../common/StatusBadge";

const links = [
  ["Home", "#/"],
  ["Platform", "#/platform"],
  ["Intelligence", "#/intelligence"],
  ["Risk & Alerts", "#/risk"],
  ["Learn", "#/learn"],
  ["About", "#/about"],
] as const;

function currentRoute(hash: string) {
  if (hash.startsWith("#/platform")) return "#/platform";
  if (hash.startsWith("#/intelligence")) return "#/intelligence";
  if (hash.startsWith("#/risk") || hash.startsWith("#/email-alerts")) return "#/risk";
  if (hash.startsWith("#/learn")) return "#/learn";
  if (hash.startsWith("#/about")) return "#/about";
  return "#/";
}

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [active, setActive] = useState(() => currentRoute(window.location.hash));

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    const onHash = () => {
      setActive(currentRoute(window.location.hash));
      setOpen(false);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("hashchange", onHash);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("hashchange", onHash);
    };
  }, []);

  return (
    <header className={`navbar ${scrolled ? "scrolled" : ""}`}>
      <div className="nav-inner">
        <a href="#/" className="brand" aria-label="AGNITE home">
          <Flame className="brand-mark" size={30} />
          <span>
            <strong>AGNITE</strong>
            <small>AI-Powered Thermal Intelligence</small>
          </span>
        </a>

        <nav id="main-navigation" aria-label="Main navigation" className={open ? "nav-links open" : "nav-links"}>
          {links.map(([label, href]) => (
            <a key={href} href={href} aria-current={active === href ? "page" : undefined} onClick={() => setOpen(false)}>
              {label}
            </a>
          ))}
        </nav>

        <div className="nav-actions">
          <StatusBadge />
          <a className="button small secondary" href="#/workspace">
            Dashboard <ArrowUpRight size={14} />
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
