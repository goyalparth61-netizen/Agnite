import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import { startLocationAutofill } from "./ai/locationSelection";
import "./styles/global.css";
import "./styles/completion.css";
import "./styles/pages.css";
import "./styles/clarity.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

startLocationAutofill();