import { formatEntryDateTime, formatEntryText } from "../../../utils/formEntryUtils";
import { getLineName, getMaterialCode, getShiftName } from "./formUi";

export function getProductionEventColumns(t) {
  return [
    {
      key: "event_time",
      label: t("forms.common.eventTime"),
      type: "datetime",
    },
    {
      key: "production_run_id",
      label: t("forms.common.productionRun"),
      render: (entry, { runsById, t: translate }) => {
        const run = runsById[entry.production_run_id];
        if (!run) {
          return `#${entry.production_run_id}`;
        }
        return translate("forms.common.runStatusOption", {
          id: run.id,
          status: run.status,
        });
      },
    },
    { key: "level_2", label: t("forms.common.level2") },
    { key: "level_3", label: t("forms.common.level3") },
    { key: "reason", label: t("forms.common.reason") },
    {
      key: "comment",
      label: t("common.comment"),
      render: (entry) => formatEntryText(entry.comment),
    },
  ];
}

export function getMaterialBehaviorColumns(t) {
  return [
    { key: "event_time", label: t("forms.common.eventTime"), type: "datetime" },
    {
      key: "production_run_id",
      label: t("forms.common.productionRun"),
      render: (entry, { runsById, t: translate }) => {
        const run = runsById[entry.production_run_id];
        if (!run) {
          return `#${entry.production_run_id}`;
        }
        return translate("forms.common.runStatusOption", {
          id: run.id,
          status: run.status,
        });
      },
    },
    { key: "behavior_type", label: t("forms.materialBehavior.behaviorType") },
    { key: "severity", label: t("forms.materialBehavior.severity") },
    {
      key: "comment",
      label: t("common.comment"),
      render: (entry) => formatEntryText(entry.comment),
    },
  ];
}

export function getMaterialBlockingColumns(t) {
  return [
    { key: "from_time", label: t("forms.common.from"), type: "datetime" },
    { key: "to_time", label: t("forms.common.to"), type: "datetime" },
    {
      key: "production_run_id",
      label: t("forms.common.productionRun"),
      render: (entry, { runsById, t: translate }) => {
        const run = runsById[entry.production_run_id];
        if (!run) {
          return `#${entry.production_run_id}`;
        }
        return translate("forms.common.runStatusOption", {
          id: run.id,
          status: run.status,
        });
      },
    },
    { key: "reason", label: t("forms.common.reason") },
    { key: "affected_material", label: t("forms.common.affectedMaterial") },
    {
      key: "comment",
      label: t("common.comment"),
      render: (entry) => formatEntryText(entry.comment),
    },
  ];
}

export function getDailyQualityColumns(t) {
  return [
    { key: "input_time", label: t("forms.common.inputTime"), type: "datetime" },
    {
      key: "production_run_id",
      label: t("forms.common.productionRun"),
      render: (entry, { runsById, t: translate }) => {
        const run = runsById[entry.production_run_id];
        if (!run) {
          return `#${entry.production_run_id}`;
        }
        return translate("forms.common.runStatusOption", {
          id: run.id,
          status: run.status,
        });
      },
    },
    { key: "shift", label: t("forms.common.shift") },
    { key: "open_holes_percent", label: t("forms.dailyQuality.openHoles") },
    { key: "sieve_distribution_percent", label: t("forms.dailyQuality.sieveDistribution") },
    { key: "foaming_behavior", label: t("forms.dailyQuality.foamingBehavior") },
  ];
}

export function getProductionStartColumns(t, options) {
  return [
    { key: "id", label: t("forms.common.productionRun"), render: (entry) => `#${entry.id}` },
    { key: "status", label: t("common.status") },
    {
      key: "material_type_id",
      label: t("forms.common.materialType"),
      render: (entry) => getMaterialCode(options, entry.material_type_id),
    },
    {
      key: "shift_id",
      label: t("forms.common.shift"),
      render: (entry) => getShiftName(options, entry.shift_id),
    },
    {
      key: "start_time",
      label: t("forms.common.startTime"),
      render: (entry) => formatEntryDateTime(entry.start_time),
    },
    {
      key: "production_line_id",
      label: t("forms.common.productionLine"),
      render: (entry) => getLineName(options, entry.production_line_id),
    },
  ];
}
