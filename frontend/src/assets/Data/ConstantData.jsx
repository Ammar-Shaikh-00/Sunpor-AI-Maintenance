export const menuData = [
  {
    titleKey: "menu.sections.operations",
    items: [
      {
        labelKey: "menu.dashboard",
        icon: "dashboard",
        active: true,
        path: "/",
      },
      {
        labelKey: "menu.productionRuns",
        icon: "list",
        path: "/production-runs",
        active: false,
      },
      {
        labelKey: "menu.dataExport",
        icon: "export",
        path: "/data-export",
        active: false,
      },
    ],
  },
  {
    titleKey: "menu.sections.operatorForms",
    items: [
      {
        labelKey: "menu.productionStart",
        icon: "playStart",
        path: "/forms/production-start",
        active: false,
      },
      {
        labelKey: "menu.extruderEvents",
        icon: "extruder",
        path: "/forms/extruder-events",
        active: false,
      },
      {
        labelKey: "menu.granulatorEvents",
        icon: "knife",
        path: "/forms/granulator-events",
        active: false,
      },
      {
        labelKey: "menu.cleaning",
        icon: "cleaning",
        path: "/forms/cleaning",
        active: false,
      },
      {
        labelKey: "menu.faults",
        icon: "alert",
        path: "/forms/faults",
        active: false,
      },
      {
        labelKey: "menu.materialBehavior",
        icon: "observe",
        path: "/forms/material-behavior",
        active: false,
      },
      {
        labelKey: "menu.materialBlocking",
        icon: "block",
        path: "/forms/material-blocking",
        active: false,
      },
      {
        labelKey: "menu.dailyQuality",
        icon: "quality",
        path: "/forms/daily-quality",
        active: false,
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
    ],
  },
];

export function NavIcon({ name, active = false }) {
  const common = "w-5 h-5 shrink-0";
  const stroke = active ? "#6D28D9" : "#8B5CF6";

  const Svg = ({ children }) => (
    <svg
      viewBox="0 0 24 24"
      className={common}
      fill="none"
      stroke={stroke}
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  );

  switch (name) {
    case "dashboard":
      return (
        <Svg>
          <path d="M4 13V6a2 2 0 0 1 2-2h4v9H4z" />
          <path d="M14 20v-7h6v5a2 2 0 0 1-2 2h-4z" />
          <path d="M14 4h4a2 2 0 0 1 2 2v4h-6V4z" />
          <path d="M4 17h6v3H6a2 2 0 0 1-2-2v-1z" />
        </Svg>
      );
    case "list":
      return (
        <Svg>
          <path d="M8 6h13" />
          <path d="M8 12h13" />
          <path d="M8 18h13" />
          <path d="M3 6h.01" />
          <path d="M3 12h.01" />
          <path d="M3 18h.01" />
        </Svg>
      );
    case "playStart":
      return (
        <Svg>
          <circle cx="12" cy="12" r="9" />
          <path d="M10 8.5v7l5.5-3.5L10 8.5z" />
        </Svg>
      );
    case "extruder":
      return (
        <Svg>
          <rect x="3" y="9" width="18" height="6" rx="2" />
          <path d="M6 12h3" />
          <path d="M11 12h3" />
          <path d="M16 12h3" />
          <path d="M3 12H1" />
          <path d="M23 12h-2" />
        </Svg>
      );
    case "knife":
      return (
        <Svg>
          <path d="M5 19L19 5" />
          <path d="M7 17l2 2" />
          <path d="M15 7l2-2" />
        </Svg>
      );
    case "cleaning":
      return (
        <Svg>
          <path d="M12 2.5c-2.5 4.5-7 6.5-7 11a7 7 0 0 0 14 0c0-4.5-4.5-6.5-7-11z" />
        </Svg>
      );
    case "alert":
      return (
        <Svg>
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <path d="M12 9v4" />
          <path d="M12 17h.01" />
        </Svg>
      );
    case "observe":
      return (
        <Svg>
          <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" />
          <circle cx="12" cy="12" r="3" />
        </Svg>
      );
    case "block":
      return (
        <Svg>
          <circle cx="12" cy="12" r="9" />
          <path d="M4.5 4.5l15 15" />
        </Svg>
      );
    case "quality":
      return (
        <Svg>
          <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2" />
          <rect x="9" y="3" width="6" height="4" rx="1" />
          <path d="M9 14l2 2 4-4" />
        </Svg>
      );
    case "users":
      return (
        <Svg>
          <path d="M16 11a3 3 0 1 0-6 0" />
          <path d="M3 21a7 7 0 0 1 14 0" />
          <path d="M18 8a2.5 2.5 0 1 0 0 5" />
          <path d="M21 21a5 5 0 0 0-4-2" />
        </Svg>
      );
    case "shield":
      return (
        <Svg>
          <path d="M12 3l8 3v6c0 5-3.5 8.5-8 9-4.5-.5-8-4-8-9V6l8-3z" />
          <path d="M9 12l2 2 4-4" />
        </Svg>
      );
    case "export":
      return (
        <Svg>
          <path d="M12 3v12" />
          <path d="M8 11l4 4 4-4" />
          <path d="M4 21h16" />
        </Svg>
      );
    default:
      return (
        <Svg>
          <circle cx="12" cy="12" r="3" />
        </Svg>
      );
  }
}
