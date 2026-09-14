import { MotionConfig } from "framer-motion";
import { lazy, Suspense, useEffect, useState } from "react";
import Home from "./pages/Home";

const Workspace = lazy(() => import("./pages/Workspace"));
const EmailAlerts = lazy(() => import("./pages/EmailAlerts"));

type AppRoute = "home" | "workspace" | "email-alerts";

function routeFromHash(hash: string): AppRoute {
  if (hash.startsWith("#/email-alerts")) return "email-alerts";
  if (hash.startsWith("#/workspace")) return "workspace";
  return "home";
}

export default function App() {
  const [route, setRoute] = useState<AppRoute>(() => routeFromHash(window.location.hash));

  useEffect(() => {
    const update = () => setRoute(routeFromHash(window.location.hash));
    window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update);
  }, []);

  return (
    <MotionConfig reducedMotion="user">
      {route === "email-alerts" ? (
        <Suspense fallback={<main className="container section">Loading alerts…</main>}>
          <EmailAlerts />
        </Suspense>
      ) : route === "workspace" ? (
        <Suspense
          fallback={
            <main className="container section" role="status">
              Loading AGNITE workspace…
            </main>
          }
        >
          <Workspace />
        </Suspense>
      ) : (
        <Home />
      )}
    </MotionConfig>
  );
}
