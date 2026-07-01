import { useTranslation } from "react-i18next";
import ProductionEventForm from "./ProductionEventForm";

export default function ExtruderEventsForm() {
  const { t } = useTranslation();

  return (
    <ProductionEventForm
      title={t("forms.extruderEvents.title")}
      description={t("forms.extruderEvents.description")}
      defaultLevel1="Extruder"
      level2OptionsKey="extruder_level_2"
      level3OptionsKey="extruder_level_3"
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
      level3OptionsKey="granulator_level_3"
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
      level3OptionsKey="cleaning_level_3"
    />
  );
}

export function FaultsForm() {
  const { t } = useTranslation();

  return (
    <ProductionEventForm
      title={t("forms.faults.title")}
      description={t("forms.faults.description")}
      defaultLevel1="Faults"
      level2OptionsKey="fault_level_2"
      level3OptionsKey="fault_mechanical_level_3"
    />
  );
}
