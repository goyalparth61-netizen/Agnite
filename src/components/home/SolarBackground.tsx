import { useEffect, useId, useRef, useState } from "react";
import { Pause, Play, Sun } from "lucide-react";
import { useInView, useReducedMotion } from "framer-motion";
import "../../styles/solar-background.css";

/** Decorative solar atmosphere; no network assets or per-frame React updates. */
export default function SolarBackground() {
  const id = useId().replace(/:/g, "");
  const reduced = useReducedMotion();
  const artwork = useRef<HTMLDivElement>(null);
  const inView = useInView(artwork);
  const [paused, setPaused] = useState(false);
  const [tabHidden, setTabHidden] = useState(false);
  useEffect(() => {
    const update = () => setTabHidden(document.hidden);
    update();
    document.addEventListener("visibilitychange", update);
    return () => document.removeEventListener("visibilitychange", update);
  }, []);
  const still = paused || !!reduced || tabHidden || !inView;
  return (
    <>
      <div
        ref={artwork}
        className={`solar-background${still ? " solar-still" : ""}`}
        aria-hidden="true"
      >
        <div className="solar-starfield" />
        <div className="solar-body">
          <svg className="solar-art" viewBox="0 0 800 800" focusable="false">
            <defs>
              <radialGradient id={`${id}-halo`}>
                <stop offset="36%" stopColor="#9a481e" stopOpacity="0" />
                <stop offset="57%" stopColor="#d47a30" stopOpacity=".23" />
                <stop offset="65%" stopColor="#b4672e" stopOpacity=".1" />
                <stop offset="100%" stopColor="#dc953b" stopOpacity="0" />
              </radialGradient>
              <radialGradient id={`${id}-surface`} cx="65%" cy="27%" r="78%">
                <stop offset="0" stopColor="#f4c984" />
                <stop offset="35%" stopColor="#cf7638" />
                <stop offset="72%" stopColor="#713623" />
                <stop offset="100%" stopColor="#211f21" />
              </radialGradient>
              <radialGradient id={`${id}-shade`} cx="32%" cy="61%" r="71%">
                <stop offset="8%" stopColor="#11151a" stopOpacity=".94" />
                <stop offset="55%" stopColor="#15161b" stopOpacity=".76" />
                <stop offset="88%" stopColor="#1b1c21" stopOpacity=".16" />
                <stop offset="100%" stopColor="#12151a" stopOpacity="0" />
              </radialGradient>
              <linearGradient id={`${id}-limb`} x1="0" y1="1" x2="1" y2="0">
                <stop offset="0" stopColor="#b26336" stopOpacity=".05" />
                <stop offset="50%" stopColor="#db8644" stopOpacity=".32" />
                <stop offset="100%" stopColor="#ffdfa8" stopOpacity=".9" />
              </linearGradient>
              <filter
                id={`${id}-plasma`}
                x="0"
                y="0"
                width="100%"
                height="100%"
              >
                <feTurbulence
                  type="fractalNoise"
                  baseFrequency=".024"
                  numOctaves="3"
                  seed="12"
                />
                <feColorMatrix
                  type="matrix"
                  values=".9 0 0 0 .12 .4 0 0 0 .05 .12 0 0 0 .015 0 0 0 .75 0"
                />
              </filter>
              <clipPath id={`${id}-disc`}>
                <circle cx="400" cy="400" r="247" />
              </clipPath>
            </defs>
            <circle
              className="solar-halo"
              cx="400"
              cy="400"
              r="398"
              fill={`url(#${id}-halo)`}
            />
            <g
              className="solar-prominences"
              fill="none"
              stroke={`url(#${id}-limb)`}
            >
              <path d="M518 181 C566 86 674 181 603 253" strokeWidth="2.2" />
              <path d="M526 179 C571 112 643 176 606 240" strokeWidth=".9" />
              <path d="M643 353 C723 318 729 408 646 426" strokeWidth="1.8" />
              <path d="M607 533 C689 595 565 650 537 605" strokeWidth="1.1" />
              <path d="M250 204 C207 147 172 220 189 274" strokeWidth="1" />
            </g>
            <circle cx="400" cy="400" r="247" fill={`url(#${id}-surface)`} />
            <g clipPath={`url(#${id}-disc)`}>
              <g className="solar-plasma">
                <rect
                  x="90"
                  y="90"
                  width="620"
                  height="620"
                  filter={`url(#${id}-plasma)`}
                />
              </g>
              <circle cx="400" cy="400" r="248" fill={`url(#${id}-shade)`} />
            </g>
            <circle
              cx="400"
              cy="400"
              r="247"
              fill="none"
              stroke={`url(#${id}-limb)`}
              strokeWidth="2"
            />
          </svg>
        </div>
        <div className="solar-horizon" />
        <div className="solar-scrim" />
      </div>
      <div className="solar-control-wrap">
        <button
          className="solar-control"
          type="button"
          onClick={() => setPaused(!paused)}
          disabled={!!reduced}
          aria-pressed={paused}
          aria-label={
            reduced
              ? "Solar background is still: reduced motion enabled"
              : paused
                ? "Play solar background animation"
                : "Pause solar background animation"
          }
        >
          <Sun size={12} aria-hidden="true" />
          <span>SOLAR ATMOSPHERE</span>
          {still ? (
            <Play size={11} aria-hidden="true" />
          ) : (
            <Pause size={11} aria-hidden="true" />
          )}
        </button>
      </div>
    </>
  );
}
