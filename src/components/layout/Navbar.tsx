import { useEffect, useState } from "react";
import { ArrowUpRight, Flame, Menu, X } from "lucide-react";
import StatusBadge from "../common/StatusBadge";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { documentationLinks, docId } from "../docs/DocumentationSection";
const links = [
  ["Home", "home"],
  ["Platform", "platform"],
  ["Intelligence", "intelligence"],
  ["Risk", "risk"],
  ["Alerts", "alerts"],
  ["Awareness", "awareness"],
  ["Team", "team"],
  ["Contact", "contact"],
];
export default function Navbar() {
  const [open, setOpen] = useState(false);
  const [docsOpen, setDocsOpen] = useState(false);
  const reduced = useReducedMotion();
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
              setDocsOpen(false);
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
          <div
            className="docs-dropdown"
            onBlur={(e) => {
              if (!e.currentTarget.contains(e.relatedTarget as Node | null))
                setDocsOpen(false);
            }}
          >
            <button
              id="docs-toggle"
              aria-expanded={docsOpen}
              aria-controls="docs-menu"
              onClick={() => setDocsOpen(!docsOpen)}
              onKeyDown={(e) => {
                if (e.key === "Escape") {
                  e.stopPropagation();
                  setDocsOpen(false);
                  e.currentTarget.focus();
                }
              }}
            >
              Documentation <span aria-hidden="true">⌄</span>
            </button>
            <AnimatePresence>
              {docsOpen && (
                <motion.div
                  id="docs-menu"
                  className="docs-menu"
                  initial={reduced ? false : { opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: reduced ? 0 : 0.15 }}
                  onKeyDown={(e) => {
                    if (e.key === "Escape") {
                      e.stopPropagation();
                      setDocsOpen(false);
                      document.getElementById("docs-toggle")?.focus();
                    }
                  }}
                >
                  {documentationLinks.map((title) => (
                    <a
                      key={title}
                      href={`#${docId(title)}`}
                      onClick={() => {
                        setOpen(false);
                        setDocsOpen(false);
                      }}
                    >
                      {title}
                    </a>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
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
