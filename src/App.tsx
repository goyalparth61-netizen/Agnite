import { MotionConfig } from "framer-motion";
import { lazy, Suspense, useEffect, useState } from "react";
import Home from "./pages/Home";

const Platform = lazy(() => import("./pages/Platform"));
const Intelligence = lazy(() => import("./pages/Intelligence"));
const Risk = lazy(() => import("./pages/Risk"));
const Learn = lazy(() => import("./pages/Learn"));
const About = lazy(() => import("./pages/About"));
const Workspace = lazy(() => import("./pages/Workspace"));
const EmailAlerts = lazy(() => import("./pages/EmailAlerts"));

type AppRoute =
  | "home"
  | "platform"
  | "intelligence"
  | "risk"
  | "learn"
  | "about"
  | "workspace"
  | "email-alerts";

function routeFromHash(hash: string): AppRoute {
  if (hash.startsWith("#/workspace")) return "workspace";
  if (hash.startsWith("#/email-alerts")) return "email-alerts";
  if (hash.startsWith("#/platform")) return "platform";
  if (hash.startsWith("#/intelligence")) return "intelligence";
  if (hash.startsWith("#/risk")) return "risk";
  if (hash.startsWith("#/learn")) return "learn";
  if (hash.startsWith("#/about")) return "about";
  return "home";
}

const pageMap: Record<Exclude<AppRoute, "home" | "workspace" | "email-alerts">, React.LazyExoticComponent<() => JSX.Element>> = {
  platform: Platform,
  intelligence: Intelligence,
  risk: Risk,
  learn: Learn,
  about: About,
};

export default function App() {
  const [route, setRoute] = useState<AppRoute>(() => routeFromHash(window.location.hash));

  useEffect(() => {
    const update = () => {
      setRoute(routeFromHash(window.location.hash));
      window.scrollTo({ top: 0, behavior: "auto" });
    };
    window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update);
  }, []);

  let content;
  if (route === "home") content = <Home />;
  else if (route === "workspace") content = <Workspace />;
  else if (route === "email-alerts") content = <EmailAlerts />;
  else {
    const Page = pageMap[route];
    content = <Page />;
  }

  return (
    <MotionConfig reducedMotion="user">
      <Suspense fallback={<main className="container section" role="status">Loading AGNITE…</main>}>
        {content}
      </Suspense>
    </MotionConfig>
  );
}
