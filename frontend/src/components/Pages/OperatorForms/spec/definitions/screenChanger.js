import {
  buildOptions,
  checkboxField,
  informedField,
  operatorCommentField,
  radioField,
  resultField,
  runSelectField,
  timelineFields,
} from "../sharedFields";

const INFORMED_KEYS = [
  "nobody",
  "shift_supervisor",
  "production_manager",
  "maintenance",
  "other",
];

export default {
  id: "screen_changer",
  accent: "#0055D4",
  title: "SIEBWECHSLER",
  description:
    "Erfassen Sie hier alle Ereignisse, Beobachtungen und Maßnahmen rund um den Siebwechsler. Der Differenzdruck ist dabei das wichtigste Entscheidungskriterium für einen Siebwechsel.",
  submitLabel: "Jetzt erfassen",
  plantValues: [
    { id: "differential_pressure", label: "Differenzdruck" },
    { id: "pressure_before_screen", label: "Druck vor dem Sieb" },
    { id: "pressure_after_screen", label: "Druck nach dem Sieb" },
  ],
  layout: [
    ["production_run", "event_time"],
    ["problem_first_occurred", "problem_noticed", "problem_resolved"],
    ["duration_before_discovery", "duration_resolution"],
    ["record_type", "observations"],
    ["intervention_reason", "preceding_events"],
    ["measures_taken", "adjusted_areas"],
    ["suspected_cause", "informed_persons"],
    ["result"],
    ["comment"],
  ],
  fields: [
    runSelectField(),
    ...timelineFields(),

    radioField(
      "record_type",
      "Was möchten Sie erfassen?",
      buildOptions([
        ["screen_inspected", "Sieb kontrolliert"],
        ["screen_changed", "Sieb gewechselt"],
        ["screen_cleaned", "Sieb gereinigt"],
        ["screen_blocked", "Sieb verstopft"],
        ["differential_pressure_abnormal", "Differenzdruck auffällig"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "record_type_other" },
    ),

    checkboxField(
      "observations",
      "Was wurde beobachtet?",
      buildOptions([
        ["differential_pressure_rising", "Differenzdruck steigt"],
        ["differential_pressure_falling", "Differenzdruck fällt"],
        ["pressure_fluctuating", "Druck schwankt"],
        ["material_flow_uneven", "Materialfluss ungleichmäßig"],
        ["screen_blocked", "Sieb verstopft"],
        ["material_building_up", "Materialablagerungen"],
        ["alarm_triggered", "Alarm ausgelöst"],
        ["no_anomaly", "Keine Auffälligkeit"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "observations_other" },
    ),

    checkboxField(
      "intervention_reason",
      "Warum wurde eingegriffen?",
      buildOptions([
        ["differential_pressure_too_high", "Differenzdruck zu hoch"],
        ["alarm", "Alarm"],
        ["visual_inspection", "Sichtkontrolle"],
        ["experience", "Erfahrung"],
        ["regular_change", "Regelmäßiger Wechsel"],
        ["shift_supervisor", "Schichtführer"],
        ["production_manager", "Produktionsleiter"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "intervention_reason_other" },
    ),

    checkboxField(
      "preceding_events",
      "Was ist unmittelbar davor passiert?",
      buildOptions([
        ["material_change", "Materialwechsel"],
        ["batch_change", "Chargenwechsel"],
        ["dosing_changed", "Dosierung geändert"],
        ["extruder_adjusted", "Extruder angepasst"],
        ["production_start", "Produktionsstart"],
        ["restart", "Neustart"],
        ["maintenance", "Wartung"],
        ["cleaning", "Reinigung"],
        ["nothing", "Nichts"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "preceding_events_other" },
    ),

    checkboxField(
      "measures_taken",
      "Welche Maßnahme wurde durchgeführt?",
      buildOptions([
        ["screen_changed", "Sieb gewechselt"],
        ["screen_cleaned", "Sieb gereinigt"],
        ["differential_pressure_checked", "Differenzdruck geprüft"],
        ["extruder_adjusted", "Extruder angepasst"],
        ["production_reduced", "Produktion reduziert"],
        ["production_stopped", "Produktion gestoppt"],
        ["no_measure", "Keine Maßnahme"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "measures_taken_other" },
    ),

    checkboxField(
      "adjusted_areas",
      "Mussten weitere Bereiche angepasst werden?",
      buildOptions([
        ["dosing", "Dosierung"],
        ["extruder", "Extruder"],
        ["die", "Düse"],
        ["water_box", "Wasserbox"],
        ["granulator", "Granulator"],
        ["knives", "Messer"],
        ["none", "Keine"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "adjusted_areas_other" },
    ),

    checkboxField(
      "suspected_cause",
      "Vermutete Ursache",
      buildOptions([
        ["screen_contaminated", "Sieb verschmutzt"],
        ["screen_blocked", "Sieb verstopft"],
        ["material_problem", "Materialproblem"],
        ["dosing_problem", "Dosierproblem"],
        ["pressure_problem", "Druckproblem"],
        ["technical_defect", "Technischer Defekt"],
        ["wear", "Verschleiß"],
        ["unknown", "Unbekannt"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "suspected_cause_other" },
    ),

    informedField(INFORMED_KEYS),
    resultField(),

    operatorCommentField([
      "Was wurde am Siebwechsler beobachtet?",
      "Warum haben Sie eingegriffen?",
      "Warum war ein Siebwechsel notwendig?",
      "Was hat sich nach dem Wechsel verändert?",
      "Gibt es weitere Beobachtungen für den nächsten Operator?",
    ]),
  ],
};
