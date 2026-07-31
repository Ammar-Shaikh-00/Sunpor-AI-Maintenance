import { NavIcon } from "../icons";

export { NavIcon };
export const menuData = [
  {
    titleKey: "menu.sections.operations",
    items: [
      {
        labelKey: "menu.dashboard",
        icon: "dashboard",
        active: true,
        path: "/",
        permission: "signal.view",
      },
      {
        labelKey: "menu.productionRuns",
        icon: "list",
        path: "/production-runs",
        active: false,
        permission: "signal.view",
      },
      {
        labelKey: "menu.dataExport",
        icon: "export",
        path: "/data-export",
        active: false,
        permission: "signal.view",
      },
      {
        labelKey: "menu.signalsCharts",
        icon: "dashboard",
        path: "/signals-charts",
        active: false,
        permission: "signal.view",
      },
    ],
  },
  {
    titleKey: "menu.sections.operatorForms",
    items: [
      {
        labelKey: "menu.operatorAssist",
        icon: "allForms",
        path: "/operator",
        active: false,
        operatorOnly: true,
        anyOf: [
          "production.view",
          "event.view",
          "quality.view",
          "material_block.view",
        ],
      },
      {
        labelKey: "menu.allForms",
        icon: "allForms",
        path: "/forms/all",
        active: false,
        anyOf: [
          "production.view",
          "event.view",
          "quality.view",
          "material_block.view",
        ],
      },
      {
        labelKey: "menu.productionStart",
        icon: "playStart",
        path: "/forms/production-start",
        active: false,
        permission: "production.view",
      },
      {
        labelKey: "menu.extruderEvents",
        icon: "extruder",
        path: "/forms/extruder-events",
        active: false,
        permission: "event.view",
      },
      {
        labelKey: "menu.granulatorEvents",
        icon: "knife",
        path: "/forms/granulator-events",
        active: false,
        permission: "event.view",
      },
      {
        labelKey: "menu.cleaning",
        icon: "cleaning",
        path: "/forms/cleaning",
        active: false,
        permission: "event.view",
      },
      {
        labelKey: "menu.faults",
        icon: "alert",
        path: "/forms/faults",
        active: false,
        permission: "event.view",
      },
      {
        labelKey: "menu.materialBehavior",
        icon: "observe",
        path: "/forms/material-behavior",
        active: false,
        permission: "quality.view",
      },
      {
        labelKey: "menu.materialBlocking",
        icon: "block",
        path: "/forms/material-blocking",
        active: false,
        permission: "material_block.view",
      },
      {
        labelKey: "menu.dailyQuality",
        icon: "quality",
        path: "/forms/daily-quality",
        active: false,
        permission: "quality.view",
      },
    ],
  },
  {
    titleKey: "menu.sections.administration",
    items: [
      {
        labelKey: "menu.users",
        icon: "users",
        path: "/admin/users",
        active: false,
        permission: "user.view",
      },
      {
        labelKey: "menu.roles",
        icon: "shield",
        path: "/admin/roles",
        active: false,
        permission: "role.view",
      },
      {
        labelKey: "menu.dropdowns",
        icon: "dropdown",
        path: "/admin/dropdowns",
        active: false,
        permission: "dropdown.view",
      },
    ],
  },
];
