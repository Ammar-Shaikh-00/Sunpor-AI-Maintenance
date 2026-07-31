import { AlertTriangle, Factory, Scissors, SprayCan } from "lucide-react";
import { useTranslation } from "react-i18next";
import ProductionEventForm from "./ProductionEventForm";

export default function ExtruderEventsForm() {
  const { t } = useTranslation();

  const resolveExtruderLevel3Key = (level2) => {
    switch (level2) {
      case "Heating Up":
        return "extruder_heating_level_3";
      case "Shutting Down":
        return "extruder_shutdown_level_3";
      case "Screen Change":
        return "extruder_screen_change_level_3";
      case "Nozzle":
        return "extruder_nozzle_level_3";
      case "Low Production":
        return "extruder_low_production_level_3";
      default:
        return null;
    }
  };

  return (
    <ProductionEventForm
      title={t("forms.extruderEvents.title")}
      description={t("forms.extruderEvents.description")}
      defaultLevel1="Extruder"
      level2OptionsKey="extruder_level_2"
      level3OptionsKey={resolveExtruderLevel3Key}
      level3Required
      icon={Factory}
    />
  );
}

export function GranulatorEventsForm() {
  const { t } = useTranslation();

  return (
    <ProductionEventForm
      title={t("forms.granulatorEvents.title")}
      description={t("forms.granulatorEvents.description")}
      defaultLevel1="Granulator"
      level2OptionsKey="granulator_level_2"
      level3OptionsKey={(level2) =>
        level2 === "Knife" ? "granulator_knife_level_3" : null
      }
      level3Required
      icon={Scissors}
    />
  );
}

export function CleaningEventsForm() {
  const { t } = useTranslation();

  return (
    <ProductionEventForm
      title={t("forms.cleaningEvents.title")}
      description={t("forms.cleaningEvents.description")}
      defaultLevel1="Cleaning"
      level2OptionsKey="cleaning_level_2"
      level3OptionsKey={(level2) => (level2 ? "cleaning_level_3" : null)}
      level3Required
      icon={SprayCan}
    />
  );
}

export function FaultsForm() {
  const { t } = useTranslation();

  return (
    <ProductionEventForm
      title={t("forms.faults.title")}
      description={t("forms.faults.description")}
      defaultLevel1="Malfunctions"
      level2OptionsKey="fault_level_2"
      level3OptionsKey={(level2) => {
        if (level2 === "Electrical Malfunction") {
          return "fault_electrical_level_3";
        }
        if (level2 === "Mechanical Malfunction") {
          return "fault_mechanical_level_3";
        }
        return null;
      }}
      level3Required
      icon={AlertTriangle}
    />
  );
}
