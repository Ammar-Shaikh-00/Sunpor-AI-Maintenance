/**
 * Capture-hub category metadata for the operator input forms.
 *
 * `icon` is a key resolved by the UI to a lucide icon component so this module
 * stays free of React/asset imports and can be reused by exports and tests.
 */

export const FORM_CATEGORIES = [
  {
    id: "dosing_material",
    path: "/forms/dosing-material",
    accent: "#C05D1E",
    icon: "package",
    title: "Dosierung / Material",
    description:
      "Erfassen Sie alle Ereignisse rund um die Dosierung sowie eingesetzte Rohstoffe und Materialien.",
    examples:
      "Dosierabweichungen, Materialauffälligkeiten, Chargenprobleme, Pentan, Stickstoff, Graphit, Rezyklat, Feuchtigkeit, Fremdmaterial, Rohstoffwechsel und weitere Materialereignisse.",
    ctaLabel: "Jetzt erfassen",
    hasForm: true,
  },
  {
    id: "extruder",
    path: "/forms/extruder",
    accent: "#8E4A1E",
    icon: "factory",
    title: "Extruder",
    description:
      "Erfassen Sie alle Ereignisse, Beobachtungen und Eingriffe am Extruder.",
    examples:
      "Druck, Temperatur, Drehmoment, Schneckendrehzahl, Massetemperatur, Trendabweichungen, Prozessinstabilitäten, geänderte Einstellungen und Bedienereingriffe.",
    ctaLabel: "Jetzt erfassen",
    hasForm: true,
  },
  {
    id: "screen_changer",
    path: "/forms/screen-changer",
    accent: "#0055D4",
    icon: "filter",
    title: "Siebwechsler",
    description: "Erfassen Sie alle Ereignisse rund um den Siebwechsler.",
    examples:
      "Siebwechsel, Siebkontrolle, Differenzdruck, Verstopfungen, Druckanstieg, Materialablagerungen, Wartungsarbeiten und weitere Auffälligkeiten.",
    ctaLabel: "Jetzt erfassen",
    hasForm: true,
  },
  {
    id: "die",
    path: "/forms/die",
    accent: "#7D32A8",
    icon: "circle-dot",
    title: "Düse / Düsenplatte",
    description:
      "Erfassen Sie alle Ereignisse rund um die Düse und die Düsenplatte.",
    examples:
      "Düsenkontrolle, Düsenreinigung, Düsenwechsel, Reinigung der Düsenplatte, verstopfte Löcher, Materialaustritt, Ablagerungen und Beschädigungen.",
    ctaLabel: "Jetzt erfassen",
    hasForm: true,
  },
  {
    id: "water_box",
    path: "/forms/water-box",
    accent: "#458B42",
    icon: "droplets",
    title: "Wasserbox",
    description:
      "Erfassen Sie alle Ereignisse rund um den Kühlprozess in der Wasserbox.",
    examples:
      "Wassertemperatur, Wasserdruck, Wasserdurchflussmenge, Kühlprobleme, Leckagen, Verstopfungen, Alarme und weitere Auffälligkeiten.",
    ctaLabel: "Jetzt erfassen",
    hasForm: true,
  },
  {
    id: "granulator",
    path: "/forms/granulator",
    accent: "#5A6168",
    icon: "scissors",
    title: "Granulator / Messer",
    description:
      "Erfassen Sie alle Ereignisse rund um den Granulator und die Messer.",
    examples:
      "Messerwechsel, Messerschliff, Messerkontrolle, Granulatorkontrolle, schlechte Schnittqualität, Staubanteil, Kornform, Granulatorstörungen und weitere Auffälligkeiten.",
    ctaLabel: "Jetzt erfassen",
    hasForm: true,
  },
  {
    id: "quality",
    path: "/forms/quality",
    accent: "#008080",
    icon: "flask-conical",
    title: "Qualitätsdaten",
    description:
      "Erfassen Sie hier die Ergebnisse der Qualitätsprüfung und verknüpfen Sie diese mit den zugehörigen Produktionsereignissen.",
    examples:
      "Siebanalyse, Klumpen, offene Löcher, Zwillinge, Korngrößenverteilung, Kornform, Schüttdichte, Schäumverhalten sowie Freigaben oder Sperrungen von Chargen.",
    ctaLabel: "Jetzt erfassen",
    hasForm: true,
  },
  {
    id: "general_event",
    path: "/forms/general-event",
    accent: "#B8860B",
    icon: "clipboard-list",
    title: "Allgemeines Ereignis",
    description:
      "Erfassen Sie hier außergewöhnliche Ereignisse, die keiner Prozessstation eindeutig zugeordnet werden können.",
    examples:
      "Stromausfälle, Druckluftausfälle, Netzwerkstörungen, SPS-Störungen, HMI-Störungen, Brandalarme, Sicherheitsereignisse und weitere allgemeine Vorfälle.",
    ctaLabel: "Ereignis erfassen",
    hasForm: true,
  },
  {
    id: "recent_entries",
    path: "/forms/recent-entries",
    accent: "#0047AB",
    icon: "file-text",
    title: "Letzte Einträge",
    description:
      "Hier finden Sie alle bereits erfassten Produktionsereignisse und Qualitätsprüfungen. Einträge können gesucht, gefiltert, geöffnet und – sofern berechtigt – bearbeitet werden.",
    examples:
      "Produktionsereignisse anzeigen, Qualitätsdaten öffnen, nach Produktionslauf, Charge oder Operator suchen, Ereignisse filtern und bereits erfasste Einträge bearbeiten.",
    ctaLabel: "Einträge anzeigen",
    hasForm: false,
  },
];

export const FORM_CATEGORY_MAP = Object.fromEntries(
  FORM_CATEGORIES.map((category) => [category.id, category]),
);

export function getCategory(categoryId) {
  return FORM_CATEGORY_MAP[categoryId] ?? null;
}

export function getCategoryByPath(path) {
  return FORM_CATEGORIES.find((category) => category.path === path) ?? null;
}
