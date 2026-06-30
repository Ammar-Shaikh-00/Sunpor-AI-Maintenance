import ProductionEventForm from "./ProductionEventForm";

export default function ExtruderEventsForm() {
  return (
    <ProductionEventForm
      title="Extruder Events"
      description="Record extruder production phases and maintenance events."
      defaultLevel1="Extruder"
      level2OptionsKey="extruder_level_2"
      level3OptionsKey="extruder_level_3"
    />
  );
}

export function GranulatorEventsForm() {
  return (
    <ProductionEventForm
      title="Granulator / Knife"
      description="Record knife change and sharpening events."
      defaultLevel1="Granulator"
      level2OptionsKey="granulator_level_2"
      level3OptionsKey="granulator_level_3"
    />
  );
}

export function CleaningEventsForm() {
  return (
    <ProductionEventForm
      title="Cleaning"
      description="Record cleaning activities for water basin, centrifuge, and general cleaning."
      defaultLevel1="Cleaning"
      level2OptionsKey="cleaning_level_2"
      level3OptionsKey="cleaning_level_3"
    />
  );
}

export function FaultsForm() {
  return (
    <ProductionEventForm
      title="Faults"
      description="Record mechanical and electrical faults."
      defaultLevel1="Faults"
      level2OptionsKey="fault_level_2"
      level3OptionsKey="fault_mechanical_level_3"
    />
  );
}
