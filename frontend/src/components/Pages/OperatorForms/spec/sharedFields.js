/**
 * Reusable field builders for the Sanpor operator input forms.
 *
 * Every option `value` is a stable English key: it is persisted, exported and
 * consumed as a feature by the prediction models, so it must never change once
 * released. Every `label` is the German text shown to the operator.
 */

export const MULTI_SELECT_HINT = "Mehrfachauswahl möglich";

/** Builds an option list from `[value, germanLabel]` pairs. */
export function buildOptions(pairs) {
  return pairs.map(([value, label]) => ({ value, label }));
}

/** Picks labelled options out of a catalog, preserving the requested order. */
function pickOptions(catalog, keys) {
  return keys.map((key) => ({ value: key, label: catalog[key] }));
}

export function radioField(id, label, options, extra = {}) {
  return { id, type: "radio", label, options, ...extra };
}

export function checkboxField(id, label, options, extra = {}) {
  return {
    id,
    type: "checkbox",
    label,
    multi: true,
    hint: MULTI_SELECT_HINT,
    options,
    ...extra,
  };
}

export function selectField(id, label, extra = {}) {
  return { id, type: "select", label, options: [], ...extra };
}

export function textField(id, label, extra = {}) {
  return { id, type: "text", label, ...extra };
}

export function textareaField(id, label, extra = {}) {
  return { id, type: "textarea", label, ...extra };
}

const DURATION_LABELS = {
  noticed_immediately: "Sofort bemerkt",
  under_5_min: "< 5 Minuten",
  under_10_min: "< 10 Minuten",
  min_5_15: "5–15 Minuten",
  min_10_30: "10–30 Minuten",
  min_15_30: "15–30 Minuten",
  min_30_60: "30–60 Minuten",
  hours_1_2: "1–2 Stunden",
  over_2_hours: "Mehr als 2 Stunden",
  unknown: "Unbekannt",
  not_yet_resolved: "Noch nicht behoben",
};

const RESULT_LABELS = {
  fully_resolved: "Problem vollständig behoben",
  partially_resolved: "Teilweise behoben",
  no_change: "Keine Veränderung",
  still_exists: "Problem besteht weiterhin",
  observation_ongoing: "Beobachtung läuft",
  other: "Sonstiges",
};

const INFORMED_LABELS = {
  nobody: "Niemand",
  shift_supervisor: "Schichtführer",
  production_manager: "Produktionsleiter",
  quality_assurance: "Qualitätssicherung",
  maintenance: "Instandhaltung",
  laboratory: "Labor",
  electrical: "Elektrik",
  automation: "Automatisierung",
  quality: "Qualität",
  plant_management: "Werksleitung",
  other: "Sonstiges",
};

export const DEFAULT_RESULT_KEYS = [
  "fully_resolved",
  "partially_resolved",
  "no_change",
  "still_exists",
  "observation_ongoing",
  "other",
];

export const DEFAULT_INFORMED_KEYS = [
  "nobody",
  "shift_supervisor",
  "production_manager",
  "quality_assurance",
  "maintenance",
  "laboratory",
  "other",
];

/** Shared "Ergebnis" option set; pass a key subset for shorter form variants. */
export function resultOptions(keys = DEFAULT_RESULT_KEYS) {
  return pickOptions(RESULT_LABELS, keys);
}

/** Shared "Wurde jemand informiert?" option set. */
export function informedOptions(keys = DEFAULT_INFORMED_KEYS) {
  return pickOptions(INFORMED_LABELS, keys);
}

export function durationOptions(keys) {
  return pickOptions(DURATION_LABELS, keys);
}

export function resultField(keys = DEFAULT_RESULT_KEYS, extra = {}) {
  return radioField("result", "Ergebnis", resultOptions(keys), {
    required: true,
    otherTextKey: keys.includes("other") ? "result_other" : undefined,
    ...extra,
  });
}

export function informedField(keys = DEFAULT_INFORMED_KEYS, extra = {}) {
  return checkboxField(
    "informed_persons",
    "Wurde jemand informiert?",
    informedOptions(keys),
    { otherTextKey: "informed_persons_other", ...extra },
  );
}

export function runSelectField() {
  return {
    id: "production_run",
    type: "run_select",
    label: "Produktionslauf",
    required: true,
  };
}

export function eventTimeField() {
  return {
    id: "event_time",
    type: "event_time",
    label: "Ereigniszeit",
    required: true,
  };
}

/**
 * The six timeline fields that open every station form. The dosing form defines
 * the wording; all other station forms reuse it so the chronological block
 * looks and behaves identically everywhere.
 */
export function timelineFields({ includeResolutionDuration = true } = {}) {
  const fields = [
    eventTimeField(),
    {
      id: "problem_first_occurred",
      type: "datetime_flags",
      label: "Wann ist das Problem erstmals aufgetreten?",
      flags: [{ id: "unknown", label: "Unbekannt" }],
    },
    {
      id: "problem_noticed",
      type: "datetime_flags",
      label: "Wann wurde das Problem bemerkt?",
      flags: [{ id: "noticed_immediately", label: "Sofort bemerkt" }],
    },
    {
      id: "problem_resolved",
      type: "datetime_flags",
      label: "Wann wurde das Problem behoben?",
      flags: [{ id: "not_yet_resolved", label: "Noch nicht behoben" }],
    },
    radioField(
      "duration_before_discovery",
      "Wie lange bestand das Problem vor der Entdeckung?",
      durationOptions([
        "noticed_immediately",
        "under_10_min",
        "min_10_30",
        "min_30_60",
        "hours_1_2",
        "over_2_hours",
        "unknown",
      ]),
    ),
  ];

  if (includeResolutionDuration) {
    fields.push(
      radioField(
        "duration_resolution",
        "Wie lange dauerte die Behebung?",
        durationOptions([
          "under_10_min",
          "min_10_30",
          "min_30_60",
          "hours_1_2",
          "over_2_hours",
          "not_yet_resolved",
        ]),
      ),
    );
  }

  return fields;
}

/** Standard free-text closing question; `prompts` are rendered as guidance. */
export function operatorCommentField(prompts, extra = {}) {
  return textareaField("comment", "Kommentar des Operators", {
    required: true,
    colSpan: 2,
    rows: 6,
    hint: "Bitte beschreiben Sie kurz:",
    prompts,
    placeholder: prompts.join("\n"),
    ...extra,
  });
}
