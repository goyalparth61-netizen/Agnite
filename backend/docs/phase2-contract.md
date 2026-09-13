# AGNITE Phase 2 — Frontend/Backend Analysis Contract (Updated with Corrections)

## 1. Existing Frontend TypeScript Types (`src/ai/thermalEngine.ts`)

### Observation
```typescript
export interface Observation {
  id: string;
  latitude: number;
  longitude: number;
  observedAt: string; // ISO-8601 UTC
  frp: number; // Fire Radiative Power (MW)
  brightness?: number; // Brightness temperature (Kelvin)
  source: "demo" | "imported" | "manual" | "firms";
  sensor?: string;
  confidence?: string | number;
}
```

### AnalysisContext
```typescript
export interface AnalysisContext {
  industrialDistanceKm: number | null;
  landCover: "forest" | "urban" | "industrial" | "other" | "unknown";
  windKph: number | null;
}
```

### ThermalClass
```typescript
export type ThermalClass =
  | "Industrial Fire"
  | "Persistent Industrial Heat"
  | "Forest / Natural Fire"
  | "Other Thermal Anomaly";
```

### AnalysisResult
```typescript
export interface AnalysisResult {
  model: {
    name: string;
    version: string;
    method?: string; // "heuristic" | "ml"
    trainingSource: string | null;
    metrics?: Record<string, number> | null;
    sampleCount: number | null;
    syntheticValidationAccuracy?: number | null; // Optional, not permanent
    limitations: string[];
  };
  classification: ThermalClass | "Insufficient evidence";
  status: "classified" | "abstained";
  /** Model confidence / relative score (0.0 - 1.0 or null if abstained) */
  modelScore: number | null;
  scores: { label: string; score: number }[];
  risk: {
    index: number; // 0 to 100
    level: "Low" | "Moderate" | "High" | "Critical";
    method: string;
    factors?: string[];
  };
  summary: string;
  evidence: { label: string; value: string; detail: string }[];
  contributions: {
    feature: string;
    value: number;
    contribution: number;
    direction: "supports" | "opposes";
  }[];
  history: {
    observedAt: string;
    frp: number;
    baseline: number | null;
  }[];
  statistics: {
    included: number;
    excluded: number;
    distinctTimes: number;
    spanHours: number;
    currentFrp: number;
    baselineFrp: number | null;
    changePercent: number | null;
    persistence: number;
    center: { latitude: number; longitude: number };
  };
  /** What-if risk scenarios based on current conditions — NOT future-fire predictions */
  scenarios: {
    horizon: "24h" | "48h" | "7d";
    low: number;
    central: number;
    high: number;
    label: string;
    assumption: string;
  }[];
  warnings: string[];

  // Phase 2 Additions
  method?: string; // "heuristic" | "ml"
  confidence?: number; // 0 - 100
  persistence?: {
    score: number; // 0 - 100
    status: "INSUFFICIENT_HISTORY" | "LOW_PERSISTENCE" | "MODERATE_PERSISTENCE" | "HIGH_PERSISTENCE";
  };
  recurrenceSignal?: "LOW" | "MODERATE" | "HIGH" | "INSUFFICIENT_HISTORY";
}
```

---

## 2. Four Architectural Corrections Applied

1. **Fallback Classifier**: Implemented as transparent deterministic rules/heuristics under `agnite-heuristic-v1`, `method: "heuristic"`. Does not claim to be a trained ML model.
2. **Model Metadata Contract**: Generic structure supporting both heuristic and real ML (via `metrics`, `sampleCount`, `trainingSource`), avoiding rigid dependency on `syntheticValidationAccuracy`.
3. **What-If Risk Scenarios (Not Predictions)**: Horizons 24h, 48h, 7d are deterministic what-if scenario ranges based on maintaining, easing, or escalating thermal conditions. `recurrenceSignal` captures historical recurrence features without fabricating future fire dates.
4. **Pipeline Order**:
   `Selected Observation -> Hotspot Service -> History Service -> Base Feature Extraction -> Persistence Service -> Final HotspotFeatures -> Classification -> Risk -> Explainability -> AnalysisResult`.
   No circular dependencies.
