export const menuData = [
  {
    title: "Operations",
    items: [
      {
        label: "Dashboard",
        icon: "dashboard",
        active: true,
        path: "/",
      },
      {
        label: "Production Runs",
        icon: "productionRun",
        path: "/production-runs",
        active: false,
      },
    ],
  },
  {
    title: "Operator Forms",
    items: [
      {
        label: "Production Start",
        icon: "productionRun",
        path: "/forms/production-start",
        active: false,
      },
      {
        label: "Extruder Events",
        icon: "machines",
        path: "/forms/extruder-events",
        active: false,
      },
      {
        label: "Granulator / Knife",
        icon: "machines",
        path: "/forms/granulator-events",
        active: false,
      },
      {
        label: "Cleaning",
        icon: "settings",
        path: "/forms/cleaning",
        active: false,
      },
      {
        label: "Faults",
        icon: "alarms",
        path: "/forms/faults",
        active: false,
      },
      {
        label: "Material Behavior",
        icon: "profile",
        path: "/forms/material-behavior",
        active: false,
      },
      {
        label: "Material Blocking",
        icon: "tickets",
        path: "/forms/material-blocking",
        active: false,
      },
      {
        label: "Daily Quality",
        icon: "reports",
        path: "/forms/daily-quality",
        active: false,
      },
    ],
  },
];

export function NavIcon({ name, active }) {
  const common = "w-5 h-5";
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
    case "machines":
      return (
        <Svg>
          <rect x="4" y="6" width="16" height="10" rx="2" />
          <path d="M7 20h10" />
          <path d="M8 10h8" />
        </Svg>
      );
    case "productionRun":
      return (
        <Svg>
          <path d="M12 8a4 4 0 1 1 0 8a4 4 0 0 1 0-8z" />
          <path d="M11 10l4 2-4 2z" />
        </Svg>
      );
    case "profile":
      return (
        <Svg>
          <path d="M16 11a4 4 0 1 0-8 0" />
          <path d="M4 21a8 8 0 0 1 16 0" />
        </Svg>
      );
    case "alarms":
      return (
        <Svg>
          <path d="M18 8a6 6 0 1 0-12 0c0 7-2 7-2 7h16s-2 0-2-7" />
          <path d="M9.5 19a2.5 2.5 0 0 0 5 0" />
        </Svg>
      );
    case "tickets":
      return (
        <Svg>
          <path d="M4 9a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2" />
          <path d="M6 7v10a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7" />
        </Svg>
      );
    case "reports":
      return (
        <Svg>
          <rect x="6" y="4" width="12" height="16" rx="2" />
          <path d="M9 9h6" />
          <path d="M9 13h6" />
        </Svg>
      );
    case "settings":
      return (
        <Svg>
          <path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z" />
          <path d="M19.4 15a1.8 1.8 0 0 0 .4 2l-1.2 2.1a2 2 0 0 1-2.3.9l-1.6-.6a8.2 8.2 0 0 1-1.7 1l-.2 1.7a2 2 0 0 1-2 1.8h-2.4a2 2 0 0 1-2-1.8l-.2-1.7a8.2 8.2 0 0 1-1.7-1l-1.6.6a2 2 0 0 1-2.3-.9L4.2 17a1.8 1.8 0 0 0 .4-2 8 8 0 0 1 0-2l-.4-2 1.2-2.1a2 2 0 0 1 2.3-.9l1.6.6a8.2 8.2 0 0 1 1.7-1l.2-1.7a2 2 0 0 1 2-1.8h2.4a2 2 0 0 1 2 1.8l.2 1.7a8.2 8.2 0 0 1 1.7 1l1.6-.6a2 2 0 0 1 2.3.9l1.2 2.1-.4 2a8 8 0 0 1 0 2z" />
        </Svg>
      );
    default:
      return null;
  }
}
