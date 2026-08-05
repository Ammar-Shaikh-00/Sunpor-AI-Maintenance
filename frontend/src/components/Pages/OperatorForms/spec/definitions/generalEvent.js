import {
  buildOptions,
  checkboxField,
  durationOptions,
  eventTimeField,
  informedField,
  operatorCommentField,
  radioField,
  runSelectField,
} from "../sharedFields";

const INFORMED_KEYS = [
  "shift_supervisor",
  "production_manager",
  "maintenance",
  "electrical",
  "automation",
  "quality",
  "plant_management",
  "other",
];

export default {
  id: "general_event",
  accent: "#B8860B",
  title: "ALLGEMEINES EREIGNIS",
  description:
    "Erfassen Sie hier außergewöhnliche Ereignisse, die keiner bestimmten Prozessstation (Dosierung, Extruder, Siebwechsler, Düse, Wasserbox oder Granulator) zugeordnet werden können.",
  submitLabel: "Ereignis speichern",
  layout: [
    ["production_run", "event_time"],
    ["category", "what_happened"],
    ["affected_areas", "production_status"],
    ["duration", "informed_persons"],
    ["measures_taken", "result"],
    ["comment"],
    ["attachments"],
  ],
  fields: [
    runSelectField(),
    eventTimeField(),

    radioField(
      "category",
      "Kategorie",
      buildOptions([
        ["safety", "Sicherheit"],
        ["infrastructure", "Infrastruktur"],
        ["energy_supply", "Energieversorgung"],
        ["automation", "Automatisierung"],
        ["production", "Produktion"],
        ["personnel", "Personal"],
        ["environment", "Umwelt"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "category_other" },
    ),

    checkboxField(
      "what_happened",
      "Was ist passiert?",
      buildOptions([
        ["power_outage", "Stromausfall"],
        ["compressed_air_failure", "Druckluftausfall"],
        ["cooling_water_failed", "Kühlwasser ausgefallen"],
        ["network_failed", "Netzwerk ausgefallen"],
        ["plc_malfunction", "SPS-Störung"],
        ["hmi_failed", "HMI ausgefallen"],
        ["scada_wincc_failed", "SCADA / WinCC ausgefallen"],
        ["sensor_failed", "Sensor ausgefallen"],
        ["communication_error", "Kommunikationsfehler"],
        ["safety_circuit_triggered", "Sicherheitskreis ausgelöst"],
        ["emergency_stop_actuated", "Not-Halt betätigt"],
        ["fire_alarm", "Brandalarm"],
        ["fire", "Brand"],
        ["water_damage", "Wasserschaden"],
        ["foreign_body_discovered", "Fremdkörper entdeckt"],
        ["raw_material_mixed_up", "Rohstoff verwechselt"],
        ["wrong_recipe_started", "Falsche Rezeptur gestartet"],
        ["wrong_production_order", "Falscher Produktionsauftrag"],
        ["shift_change_problem", "Problem beim Schichtwechsel"],
        ["cleaning_work", "Reinigungsarbeiten"],
        ["planned_maintenance", "Geplante Wartung"],
        ["unplanned_maintenance", "Ungeplante Wartung"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "what_happened_other" },
    ),

    checkboxField(
      "affected_areas",
      "Welche Bereiche waren betroffen?",
      buildOptions([
        ["dosing", "Dosierung"],
        ["extruder", "Extruder"],
        ["screen_changer", "Siebwechsler"],
        ["die", "Düse"],
        ["water_box", "Wasserbox"],
        ["granulator", "Granulator"],
        ["entire_plant", "Gesamte Anlage"],
        ["warehouse", "Lager"],
        ["quality", "Qualität"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "affected_areas_other" },
    ),

    radioField(
      "production_status",
      "Produktionsstatus",
      buildOptions([
        ["production_continued", "Produktion lief weiter"],
        ["production_reduced", "Produktion reduziert"],
        ["briefly_stopped", "Kurz gestoppt"],
        ["completely_stopped", "Vollständig gestoppt"],
      ]),
    ),

    radioField(
      "duration",
      "Dauer",
      durationOptions([
        "under_5_min",
        "min_5_15",
        "min_15_30",
        "min_30_60",
        "hours_1_2",
        "over_2_hours",
      ]),
    ),

    informedField(INFORMED_KEYS),

    checkboxField(
      "measures_taken",
      "Maßnahmen",
      buildOptions([
        ["production_stopped", "Produktion gestoppt"],
        ["restart_performed", "Neustart durchgeführt"],
        ["technician_called", "Techniker gerufen"],
        ["electrician_called", "Elektriker gerufen"],
        ["plant_reset", "Anlage zurückgesetzt"],
        ["sensor_replaced", "Sensor getauscht"],
        ["plc_restarted", "SPS neu gestartet"],
        ["network_restored", "Netzwerk wiederhergestellt"],
        ["cleaning_performed", "Reinigung durchgeführt"],
        ["no_measure", "Keine Maßnahme"],
        ["other", "Sonstiges"],
      ]),
      { otherTextKey: "measures_taken_other" },
    ),

    radioField(
      "result",
      "Ergebnis",
      buildOptions([
        ["problem_resolved", "Problem behoben"],
        ["partially_resolved", "Teilweise behoben"],
        ["still_exists", "Problem besteht weiterhin"],
        ["observation_ongoing", "Beobachtung läuft"],
      ]),
      { required: true },
    ),

    operatorCommentField(
      [
        "Was ist passiert?",
        "Welche Bereiche waren betroffen?",
        "Welche Maßnahmen wurden eingeleitet?",
        "Was hat sich danach verändert?",
        "Gibt es Hinweise für die nächste Schicht?",
      ],
      { label: "Kommentar" },
    ),

    {
      id: "attachments",
      type: "file",
      label: "Anhänge",
      multi: true,
      colSpan: 2,
      hint: "Fotos, Dokumente und sonstige Dateien",
      options: buildOptions([
        ["photos", "Fotos"],
        ["documents", "Dokumente"],
        ["other_files", "Sonstige Dateien"],
      ]),
    },
  ],
};
