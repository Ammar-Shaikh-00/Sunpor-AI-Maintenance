import cleaningIcon from "../../../assets/operator-form-icons-png/Cleaning.png";
import extruderIcon from "../../../assets/operator-form-icons-png/Extruder-events.png";
import granulatorIcon from "../../../assets/operator-form-icons-png/Messer-Granulator.png";
import materialIcon from "../../../assets/operator-form-icons-png/Material-behaviour.png";
import qualityIcon from "../../../assets/operator-form-icons-png/Quality.png";
import screenChangerIcon from "../../../assets/operator-form-icons-png/Report-problem.png";

/** Card order and copy aligned with the operator navigation mockup. */
export const CAPTURE_HUB_CARD_ORDER = [
  "dosing_material",
  "extruder",
  "granulator",
  "water_box",
  "screen_changer",
  "die",
  "quality",
  "general_event",
  "recent_entries",
];

export const CAPTURE_HUB_DISPLAY = {
  dosing_material: {
    image: materialIcon,
    body:
      "Dosierabweichungen, Materialauffälligkeiten, Chargenprobleme, Pentan, Stickstoff, Graphit, Rezyklat und weitere Rohstoffe.",
  },
  extruder: {
    image: extruderIcon,
    body:
      "Druck, Temperatur, Drehmoment, Drehzahl und Trendabweichungen sowie durchgeführte Maßnahmen.",
  },
  granulator: {
    image: granulatorIcon,
    body:
      "Messerwechsel, Schärfen, Kontrolle, Schnittbild, Staubanteil, Zwillingsperlen, Korngröße und weitere Auffälligkeiten.",
  },
  water_box: {
    image: cleaningIcon,
    body:
      "Wassertemperatur, Wasserdruck, Durchfluss, Leckagen, Verstopfungen und Alarme.",
  },
  screen_changer: {
    image: screenChangerIcon,
    body:
      "Siebwechsel, Sieb kontrollieren, Differenzdruck, Formabweichungen, offene Löcher, Brocken und weitere Auffälligkeiten.",
  },
  die: {
    icon: "circle-dot",
    title: "Düse / Lochplatte",
    body:
      "Düse reinigen, Lochplatte prüfen, Ablagerungen, Beschädigungen, Formabweichungen und weitere Auffälligkeiten.",
  },
  quality: {
    image: qualityIcon,
    body:
      "Siebanalyse, Brocken, Zwillingsperlen, Zellstruktur, Kornverteilung, Aufschäumverhalten und weitere Qualitätsprobleme.",
  },
  general_event: {
    icon: "clipboard-list",
    body:
      "Ereignisse, die keiner der anderen Kategorien zugeordnet werden können.",
    ctaLabel: "Jetzt erfassen",
  },
  recent_entries: {
    icon: "file-text",
    body:
      "Übersicht der zuletzt erfassten Ereignisse mit der Möglichkeit zur Anzeige und Bearbeitung.",
    ctaLabel: "Jetzt erfassen",
  },
};
