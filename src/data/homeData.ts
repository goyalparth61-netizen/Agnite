export const pipeline = [
  ["Detect", "Thermal hotspots"],
  ["Contextualize", "Spatial + industrial context"],
  ["Classify", "AI anomaly classification"],
  ["Explain", "Evidence-based reasoning"],
  ["Predict", "Future risk window"],
  ["Monitor", "Continuous intelligence"],
];
export const sources = [
  ["NASA FIRMS", "Thermal detection records"],
  ["VIIRS", "Fine-scale thermal observations"],
  ["MODIS", "Broad-area thermal observations"],
  ["OpenStreetMap", "Connected street basemap; automatic industrial context is planned"],
  ["Land Cover", "Vegetation + surface types"],
  ["Satellite Imagery", "Surrounding visual context"],
  ["Historical Records", "Recurring hotspot baselines"],
];
export const hotspots = [
  {
    name: "Nagpur, Maharashtra",
    type: "Industrial Fire",
    x: 47,
    y: 53,
    risk: 86,
    confidence: 94,
    evidence:
      "A sudden thermal increase near an industrial footprint, with limited recurrence in the sample history.",
    factors: [
      "Industrial proximity",
      "Abrupt thermal increase",
      "Low historical persistence",
    ],
    action: "Prioritize verification with local operators before escalation.",
    history: [20, 22, 19, 24, 27, 48, 86],
  },
  {
    name: "Surat, Gujarat",
    type: "Persistent Industrial Heat",
    x: 32,
    y: 51,
    risk: 32,
    confidence: 91,
    evidence:
      "Repeated detections align with an industrial footprint and a stable thermal baseline.",
    factors: [
      "Repeated detections",
      "Industrial land use",
      "Stable thermal baseline",
    ],
    action: "Monitor for departures from the established baseline.",
    history: [30, 34, 29, 33, 31, 35, 32],
  },
  {
    name: "Similipal, Odisha",
    type: "Forest / Natural Fire",
    x: 64,
    y: 52,
    risk: 78,
    confidence: 89,
    evidence:
      "An emerging thermal cluster overlaps forest cover, away from the sample industrial footprints.",
    factors: [
      "Forest land cover",
      "Emerging thermal cluster",
      "Low industrial proximity",
    ],
    action: "Request field verification and assess nearby exposed areas.",
    history: [12, 15, 11, 18, 30, 54, 78],
  },
  {
    name: "Hyderabad, Telangana",
    type: "Other Thermal Anomaly",
    x: 44,
    y: 65,
    risk: 45,
    confidence: 72,
    evidence:
      "An isolated detection has insufficient temporal and spatial evidence for a fire classification.",
    factors: [
      "Isolated detection",
      "Mixed land use",
      "Limited supporting history",
    ],
    action: "Review the next observation and gather additional context.",
    history: [18, 14, 22, 17, 19, 26, 45],
  },
];
