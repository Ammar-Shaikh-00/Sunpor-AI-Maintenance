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
  id: "die",
  accent: "#7D32A8",
  title: "DÜSE / DÜSENPLATTE",
  description:
    "Erfassen Sie hier alle Beobachtungen und Maßnahmen an Düse und Düsenplatte – Zustand, Materialaustritt, Verstopfungen und Verschleiß. Eigentliche Qualitätsmerkmale werden getrennt davon im Formular Qualitätsdaten bewertet.",
  submitLabel: "Jetzt erfassen",
  layout: [
    ["production_run", "event_time"],
    ["problem_first_occurred", "problem_noticed", "problem_resolved"],
    ["duration_before_discovery", "duration_resolution"],
    ["record_type", "affected_areas"],
    ["extruder_outlet_observations", "die_findings"],
    ["preceding_events", "measures_taken"],
    ["suspected_cause", "adjusted_areas"],
    ["informed_persons", "result"],
    ["comment"],
  ],
  fields: [
    runSelectField(),
    ...timelineFields(),

    radioField(
      "record_type",
      "Was möchten Sie erfassen?",
      buildOptions([
        ["die_inspected", "Düse kontrolliert"],
        ["die_cleaned", "Düse gereinigt"],
        ["die_changed", "Düse gewechselt"],
        ["die_plate_inspected", "Düsenplatte kontrolliert"],
        ["die_plate_cleaned", "Düsenplatte gereinigt"],
        ["die_plate_changed", "Düsenplatte gewechselt"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "record_type_other" },
    ),

    checkboxField(
      "affected_areas",
      "Welcher Bereich war betroffen?",
      buildOptions([
        ["die", "Düse"],
        ["die_plate", "Düsenplatte"],
        ["die_head", "Düsenkopf"],
        ["die_heating", "Düsenheizung"],
        ["adapter", "Adapter"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "affected_areas_other" },
    ),

    checkboxField(
      "extruder_outlet_observations",
      "Was wurde am Extruderaustritt beobachtet?",
      buildOptions([
        ["material_exiting_unevenly", "Material tritt ungleichmäßig aus"],
        ["individual_holes_blocked", "Einzelne Löcher verstopft"],
        ["multiple_holes_blocked", "Mehrere Löcher verstopft"],
        ["material_building_up_at_die", "Materialablagerung an der Düse"],
        ["material_dripping_afterward", "Material tropft nach"],
        ["material_exiting_sideways", "Material tritt seitlich aus"],
        ["material_strands", "Materialfäden"],
        ["unusual_behavior", "Ungewöhnliches Verhalten"],
        ["no_anomaly", "Keine Auffälligkeit"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "extruder_outlet_observations_other" },
    ),

    checkboxField(
      "die_findings",
      "Was wurde an der Düse festgestellt?",
      buildOptions([
        ["contaminated", "Verschmutzt"],
        ["blocked", "Verstopft"],
        ["damaged", "Beschädigt"],
        ["worn", "Verschlissen"],
        ["cracks_visible", "Risse sichtbar"],
        ["no_anomaly", "Keine Auffälligkeit"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "die_findings_other" },
    ),

    checkboxField(
      "preceding_events",
      "Was ist unmittelbar davor passiert?",
      buildOptions([
        ["material_change", "Materialwechsel"],
        ["batch_change", "Chargenwechsel"],
        ["dosing_changed", "Dosierung geändert"],
        ["extruder_adjusted", "Extruder angepasst"],
        ["screen_changed", "Sieb gewechselt"],
        ["production_start", "Produktionsstart"],
        ["restart", "Neustart"],
        ["cleaning", "Reinigung"],
        ["maintenance", "Wartung"],
        ["nothing", "Nichts"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "preceding_events_other" },
    ),

    checkboxField(
      "measures_taken",
      "Welche Maßnahme wurde durchgeführt?",
      buildOptions([
        ["die_cleaned", "Düse gereinigt"],
        ["die_changed", "Düse gewechselt"],
        ["die_plate_cleaned", "Düsenplatte gereinigt"],
        ["die_plate_changed", "Düsenplatte gewechselt"],
        ["pressure_reduced", "Druck reduziert"],
        ["temperature_adjusted", "Temperatur angepasst"],
        ["production_stopped", "Produktion gestoppt"],
        ["no_measure", "Keine Maßnahme"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "measures_taken_other" },
    ),

    checkboxField(
      "suspected_cause",
      "Vermutete Ursache",
      buildOptions([
        ["material_building_up", "Materialablagerung"],
        ["blockage", "Verstopfung"],
        ["wear", "Verschleiß"],
        ["temperature", "Temperatur"],
        ["pressure", "Druck"],
        ["material", "Material"],
        ["dosing", "Dosierung"],
        ["technical_defect", "Technischer Defekt"],
        ["unknown", "Unbekannt"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "suspected_cause_other" },
    ),

    checkboxField(
      "adjusted_areas",
      "Mussten weitere Bereiche angepasst werden?",
      buildOptions([
        ["dosing", "Dosierung"],
        ["extruder", "Extruder"],
        ["screen_changer", "Siebwechsler"],
        ["water_box", "Wasserbox"],
        ["granulator", "Granulator"],
        ["knives", "Messer"],
        ["none", "Keine"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "adjusted_areas_other" },
    ),

    informedField(INFORMED_KEYS),
    resultField(),

    operatorCommentField([
      "Was haben Sie an der Düse gesehen?",
      "Was war ungewöhnlich?",
      "Warum haben Sie diese Maßnahme gewählt?",
      "Was hat sich danach verändert?",
      "Gibt es etwas, das der nächste Operator wissen sollte?",
    ]),
  ],
};
