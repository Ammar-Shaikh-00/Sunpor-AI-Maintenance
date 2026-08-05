import cleaningIcon from "../../../assets/svg/cleaning.svg";
import extruderIcon from "../../../assets/svg/extruder-events.svg";
import materialBehaviorIcon from "../../../assets/svg/material-behavior.svg";
import materialBlockIcon from "../../../assets/svg/material-berrier.svg";
import granulatorIcon from "../../../assets/svg/granulator.svg";
import productionStartIcon from "../../../assets/operator-form-icons-png/Production-start.png";
import qualityIcon from "../../../assets/svg/quality.svg";
import reportProblemIcon from "../../../assets/svg/report-problem.svg";

export const OPERATOR_FORM_HUB_ITEMS = [
  {
    id: "productionStart",
    path: "/forms/production-start",
    image: productionStartIcon,
    titleKey: "allForms.cards.productionStart.title",
    descriptionKey: "allForms.cards.productionStart.description",
  },
  {
    id: "extruderEvents",
    path: "/forms/extruder-events",
    image: extruderIcon,
    titleKey: "allForms.cards.extruderEvents.title",
    descriptionKey: "allForms.cards.extruderEvents.description",
  },
  {
    id: "granulatorEvents",
    path: "/forms/granulator-events",
    image: granulatorIcon,
    titleKey: "allForms.cards.granulatorEvents.title",
    descriptionKey: "allForms.cards.granulatorEvents.description",
  },
  {
    id: "cleaning",
    path: "/forms/cleaning",
    image: cleaningIcon,
    titleKey: "allForms.cards.cleaning.title",
    descriptionKey: "allForms.cards.cleaning.description",
  },
  {
    id: "faults",
    path: "/forms/faults",
    image: reportProblemIcon,
    titleKey: "allForms.cards.faults.title",
    descriptionKey: "allForms.cards.faults.description",
  },
  {
    id: "materialBehavior",
    path: "/forms/material-behavior",
    image: materialBehaviorIcon,
    titleKey: "allForms.cards.materialBehavior.title",
    descriptionKey: "allForms.cards.materialBehavior.description",
  },
  {
    id: "materialBlocking",
    path: "/forms/material-blocking",
    image: materialBlockIcon,
    titleKey: "allForms.cards.materialBlocking.title",
    descriptionKey: "allForms.cards.materialBlocking.description",
  },
  {
    id: "dailyQuality",
    path: "/forms/daily-quality",
    image: qualityIcon,
    titleKey: "allForms.cards.dailyQuality.title",
    descriptionKey: "allForms.cards.dailyQuality.description",
  },
];
