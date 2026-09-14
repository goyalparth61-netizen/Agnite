import { MotionConfig } from "framer-motion";
import { lazy, Suspense, useEffect, useState } from "react";
import Home from "./pages/Home";
const Workspace = lazy(() => import("./pages/Workspace"));
const EmailAlerts = lazy(() => import("./pages/EmailAlerts"));
export default function App() {
  const [route, setRoute] = useState(() => window.location.hash);
  useEffect(() => {
    const update = () => setRoute(window.location.hash);
    window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update);
  }, []);
  return (
    <MotionConfig reducedMotion="user">
      {route.startsWith('#/email-alerts') ? <Suspense fallback={<main className="container section">Loading alerts…</main>}><EmailAlerts key={route} /></Suspense> : route.startsWith('#/workspace') ? <Suspense fallback={<main className="container section" role="status">Loading AGNITE workspace…</main>}><Workspace /></Suspense> : <Home />}
    </MotionConfig>
  );
}
