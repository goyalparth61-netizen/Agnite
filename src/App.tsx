import { MotionConfig } from "framer-motion";
import { lazy, Suspense, useEffect, useState } from "react";
import Home from "./pages/Home";
const Workspace = lazy(() => import("./pages/Workspace"));
export default function App() {
  const [workspace, setWorkspace] = useState(() => window.location.hash.startsWith("#/workspace"));
  useEffect(() => {
    const update = () => setWorkspace(window.location.hash.startsWith("#/workspace"));
    window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update);
  }, []);
  return (
    <MotionConfig reducedMotion="user">
      {workspace ? <Suspense fallback={<main className="container section" role="status">Loading AGNITE workspace…</main>}><Workspace /></Suspense> : <Home />}
    </MotionConfig>
  );
}
