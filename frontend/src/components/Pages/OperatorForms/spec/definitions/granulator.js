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
  "quality_assurance",
  "other",
];

const RESULT_KEYS = [
  "fully_resolved",
  "partially_resolved",
  "no_change",
  "still_exists",
  "observation_ongoing",
];

export default {
  id: "granulator",
  accent: "#5A6168",
  title: "GRANULATOR / MESSER",
  description:
    "Erfassen Sie hier alle Beobachtungen, Störungen und Wartungsereignisse rund um den Granulator und die Messer. Diese Informationen unterstützen Verschleißerkennung, Wartungsprognose und die Verbesserung der Prozessstabilität.",
  submitLabel: "Jetzt erfassen",
  plantValues: [
    { id: "granulator_speed", label: "Granulatordrehzahl" },
    { id: "granulator_torque", label: "Granulator-Drehmoment" },
    { id: "knife_position", label: "Messerposition" },
    { id: "knife_contact_pressure", label: "Messeranpressdruck" },
    { id: "production_run", label: "Produktionslauf" },
    { id: "machine", label: "Maschine" },
    { id: "recipe", label: "Rezeptur" },
  ],
  layout: [
    ["production_run", "event_time"],
    ["problem_first_occurred", "problem_noticed", "problem_resolved"],
    ["duration_before_discovery", "duration_resolution"],
    ["record_type", "intervention_reason"],
    ["observations", "preceding_events"],
    ["measures_taken", "suspected_cause"],
    ["adjusted_areas", "informed_persons"],
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
        ["knife_change", "Messerwechsel"],
        ["knife_grinding", "Messer schleifen"],
        ["knife_inspection", "Messerkontrolle"],
        ["granulator_inspection", "Granulatorkontrolle"],
        ["granulator_malfunction", "Granulator-Störung"],
        ["cleaning", "Reinigung"],
        ["maintenance", "Wartung"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "record_type_other" },
    ),

    checkboxField(
      "intervention_reason",
      "Warum wurde eingegriffen?",
      buildOptions([
        ["knife_alarm", "Messeralarm"],
        [
          "cut_quality_insufficient",
          "Schnittqualität entspricht nicht mehr den Anforderungen",
        ],
        ["material_looks_unusual", "Material sieht ungewöhnlich aus"],
        ["regular_maintenance", "Regelmäßige Wartung"],
        ["shift_supervisor", "Schichtführer"],
        ["production_manager", "Produktionsleiter"],
        ["maintenance", "Instandhaltung"],
        ["other", "Sonstiges"],
      ]),
      {
        otherTextKey: "intervention_reason_other",
        note: "Messer werden gewechselt, wenn ein Messeralarm auftritt oder die Schnittqualität nicht mehr passt.",
      },
    ),

    checkboxField(
      "observations",
      "Was wurde beobachtet?",
      buildOptions([
        ["poor_cut_quality", "Schlechte Schnittqualität"],
        ["granules_too_large", "Granulat zu groß"],
        ["granules_too_small", "Granulat zu klein"],
        ["uneven_granule_size", "Ungleichmäßige Granulatgröße"],
        ["dust_formation", "Staubbildung"],
        ["material_accumulating", "Materialansammlung"],
        ["granulator_unusually_loud", "Granulator ungewöhnlich laut"],
        ["granulator_vibrating", "Granulator vibriert"],
        ["no_anomaly", "Keine Auffälligkeit"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "observations_other" },
    ),

    checkboxField(
      "preceding_events",
      "Was ist unmittelbar davor passiert?",
      buildOptions([
        ["production_start", "Produktionsstart"],
        ["material_change", "Materialwechsel"],
        ["batch_change", "Chargenwechsel"],
        ["die_changed", "Düse gewechselt"],
        ["screen_changed", "Sieb gewechselt"],
        ["water_box_adjusted", "Wasserbox angepasst"],
        ["maintenance", "Wartung"],
        ["cleaning", "Reinigung"],
        ["nothing_special", "Nichts Besonderes"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "preceding_events_other" },
    ),

    checkboxField(
      "measures_taken",
      "Welche Maßnahme wurde durchgeführt?",
      buildOptions([
        ["knives_changed", "Messer gewechselt"],
        ["knives_ground", "Messer geschliffen"],
        ["knives_adjusted", "Messer nachgestellt"],
        ["granulator_cleaned", "Granulator gereinigt"],
        ["granulator_checked", "Granulator geprüft"],
        ["production_reduced", "Produktion reduziert"],
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
        ["knives_dull", "Messer stumpf"],
        ["knives_worn", "Messer verschlissen"],
        ["knives_incorrectly_adjusted", "Messer falsch eingestellt"],
        ["granulator_problem", "Granulatorproblem"],
        ["material_problem", "Materialproblem"],
        ["water_box_problem", "Wasserbox-Problem"],
        ["die", "Düse"],
        ["unknown", "Unbekannt"],
        ["other", "Sonstiges"],
      ]),
      {
        otherTextKey: "suspected_cause_other",
        note: "Zwillinge entstehen überwiegend durch stumpfe oder verschlissene Messer. Probleme mit der Korngrößenverteilung können auch vom Granulator, der Drehzahl oder der Düse verursacht werden.",
      },
    ),

    checkboxField(
      "adjusted_areas",
      "Mussten weitere Bereiche angepasst werden?",
      buildOptions([
        ["water_box", "Wasserbox"],
        ["die", "Düse"],
        ["screen_changer", "Siebwechsler"],
        ["extruder", "Extruder"],
        ["dosing", "Dosierung"],
        ["none", "Keine"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "adjusted_areas_other" },
    ),

    informedField(INFORMED_KEYS),
    resultField(RESULT_KEYS),

    operatorCommentField([
      "Was wurde am Granulator oder an den Messern beobachtet?",
      "Warum wurde eingegriffen?",
      "Welche Maßnahme wurde durchgeführt?",
      "Was hat sich danach verändert?",
      "Gibt es Hinweise für die nächste Schicht?",
    ]),
  ],
};
