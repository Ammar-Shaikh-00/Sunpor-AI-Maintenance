import {
  buildOptions,
  checkboxField,
  radioField,
  runSelectField,
  selectField,
  textField,
  textareaField,
} from "../sharedFields";

const GRADE_OPTIONS = buildOptions([
  ["very_good", "Sehr gut"],
  ["good", "Gut"],
  ["borderline", "Grenzwertig"],
  ["poor", "Schlecht"],
]);

const AMOUNT_OPTIONS = buildOptions([
  ["none", "Keine"],
  ["few", "Wenige"],
  ["many", "Viele"],
]);

function datetimeField(id, label) {
  return { id, type: "datetime_flags", label, flags: [], showWeekday: true };
}

/**
 * The quality form is inspector-facing and card driven: each card is one step
 * of the inspection, the flat `layout` below is derived from the cards.
 */
const cards = [
  {
    id: "production_information",
    title: "Produktionsinformationen",
    layout: [
      ["production_run", "production_line"],
      ["machine", "recipe"],
      ["material", "batch"],
      ["sample_number"],
    ],
  },
  {
    id: "inspection_period",
    title: "Prüfzeitraum",
    layout: [["production_from", "production_to"], ["quality_inspection"]],
  },
  {
    id: "inspector",
    title: "Prüfer",
    layout: [["inspector_role", "inspector_name"]],
  },
  {
    id: "quality_characteristics",
    title: "Qualitätsmerkmale",
    layout: [
      ["particle_size_distribution", "particle_size"],
      ["particle_shape", "open_holes"],
      ["lumps", "twin_beads"],
      ["boat_shapes", "dust_formation"],
      ["foaming_behavior"],
      ["bulk_density", "residual_moisture"],
    ],
  },
  {
    id: "linked_events",
    title: "Produktionsereignisse verknüpfen",
    layout: [["linked_events"]],
  },
  {
    id: "assessment",
    title: "Bewertung",
    layout: [["overall_assessment", "assessment_confidence"]],
  },
  {
    id: "suspected_cause",
    title: "Vermutete Ursache",
    layout: [["suspected_cause"]],
  },
  {
    id: "comments",
    title: "Kommentare",
    layout: [["comment"]],
  },
  {
    id: "attachments",
    title: "Anhänge",
    layout: [["attachments"]],
  },
];

export default {
  id: "quality",
  accent: "#008080",
  title: "QUALITÄTSDATEN",
  description:
    "Erfassen Sie hier die Ergebnisse der Qualitätsprüfung und verknüpfen Sie diese mit den zugehörigen Produktionsereignissen.",
  submitLabel: "Qualitätsdaten speichern",
  cards,
  layout: cards.flatMap((card) => card.layout),
  fields: [
    runSelectField(),
    selectField("production_line", "Produktionslinie", {
      required: true,
      optionsSource: "production_lines",
      placeholder: "Produktionslinie auswählen",
    }),
    selectField("machine", "Maschine", {
      required: true,
      optionsSource: "machines",
      placeholder: "Maschine auswählen",
    }),
    selectField("recipe", "Rezeptur", {
      optionsSource: "recipes",
      placeholder: "Rezeptur auswählen",
    }),
    selectField("material", "Material", {
      optionsSource: "materials",
      placeholder: "Material auswählen",
    }),
    selectField("batch", "Charge", {
      optionsSource: "batches",
      placeholder: "Charge auswählen",
    }),
    textField("sample_number", "Probennummer", {
      placeholder: "z. B. 2026-145-03",
    }),

    datetimeField("production_from", "Produktion von"),
    datetimeField("production_to", "Produktion bis"),
    datetimeField("quality_inspection", "Qualitätsprüfung"),

    radioField(
      "inspector_role",
      "Prüfer",
      buildOptions([
        ["laboratory", "Labor"],
        ["quality_assurance", "Qualitätssicherung"],
        ["production_manager", "Produktionsleiter"],
        ["shift_supervisor", "Schichtführer"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "inspector_role_other" },
    ),
    textField("inspector_name", "Name des Prüfers", {
      placeholder: "Vor- und Nachname",
    }),

    radioField(
      "particle_size_distribution",
      "Korngrößenverteilung",
      GRADE_OPTIONS,
    ),
    radioField(
      "particle_size",
      "Korngröße",
      buildOptions([
        ["ok", "In Ordnung"],
        ["too_small", "Zu klein"],
        ["too_large", "Zu groß"],
        ["fluctuating", "Schwankend"],
      ]),
    ),
    radioField("particle_shape", "Kornform", GRADE_OPTIONS),
    radioField("open_holes", "Offene Löcher", AMOUNT_OPTIONS),
    radioField("lumps", "Klumpen", AMOUNT_OPTIONS),
    radioField("twin_beads", "Zwillinge", AMOUNT_OPTIONS),
    radioField("boat_shapes", "Schiffchen", AMOUNT_OPTIONS),
    radioField("dust_formation", "Staubbildung", AMOUNT_OPTIONS),
    radioField(
      "foaming_behavior",
      "Schäumverhalten",
      buildOptions([
        ["very_good", "Sehr gut"],
        ["good", "Gut"],
        ["poor", "Schlecht"],
      ]),
    ),
    textField("bulk_density", "Schüttdichte", {
      inputMode: "decimal",
      unit: "g/l",
      placeholder: "z. B. 16,5",
    }),
    textField("residual_moisture", "Restfeuchte", {
      inputMode: "decimal",
      unit: "%",
      placeholder: "z. B. 0,4",
    }),

    {
      id: "linked_events",
      type: "quality_link",
      label: "Produktionsereignisse verknüpfen",
      multi: true,
      options: [],
      hint: "Mehrfachauswahl möglich",
      colSpan: 2,
      filters: [
        { id: "search", type: "search", label: "Ereignis suchen" },
        { id: "period", type: "period", label: "Nach Zeitraum filtern" },
        { id: "operator", type: "operator", label: "Nach Operator filtern" },
      ],
    },

    radioField(
      "overall_assessment",
      "Gesamtbewertung",
      buildOptions([
        ["release", "Freigabe"],
        ["release_with_restriction", "Freigabe mit Einschränkung"],
        ["rework", "Nacharbeit"],
        ["hold", "Sperrung"],
        ["scrap", "Ausschuss"],
      ]),
      { required: true },
    ),
    radioField(
      "assessment_confidence",
      "Sicherheit der Bewertung",
      buildOptions([
        ["very_certain", "Sehr sicher"],
        ["probable", "Wahrscheinlich"],
        ["assumption", "Vermutung"],
      ]),
    ),

    checkboxField(
      "suspected_cause",
      "Vermutete Ursache",
      buildOptions([
        ["dosing", "Dosierung"],
        ["extruder", "Extruder"],
        ["screen_changer", "Siebwechsler"],
        ["die", "Düse"],
        ["water_box", "Wasserbox"],
        ["granulator_knives", "Granulator / Messer"],
        ["material", "Material"],
        ["recipe", "Rezeptur"],
        ["operation", "Bedienung"],
        ["unknown", "Unbekannt"],
      ]),
      { colSpan: 2 },
    ),

    textareaField("comment", "Kommentar", {
      required: true,
      colSpan: 2,
      rows: 6,
      placeholder:
        "Beobachtungen der Qualitätsprüfung, Auffälligkeiten und Empfehlungen",
    }),

    {
      id: "attachments",
      type: "file",
      label: "Anhänge",
      multi: true,
      colSpan: 2,
      hint: "Prüfbericht, Laborbericht, Fotos und Dokumente",
      options: buildOptions([
        ["inspection_report", "Prüfbericht"],
        ["laboratory_report", "Laborbericht"],
        ["photos", "Fotos"],
        ["documents", "Dokumente"],
      ]),
    },
  ],
};
