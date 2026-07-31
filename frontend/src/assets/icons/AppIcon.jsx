import {
  AlertIconPaths,
  AllFormsIconPaths,
  BlockIconPaths,
  CleaningIconPaths,
  ExtruderIconPaths,
  KnifeIconPaths,
  ObserveIconPaths,
  PlayStartIconPaths,
  QualityIconPaths,
} from "./operatorFormIconPaths";
import {
  DashboardIconPaths,
  DefaultIconPaths,
  DropdownIconPaths,
  ExportIconPaths,
  ListIconPaths,
  ShieldIconPaths,
  UsersIconPaths,
} from "./navigationIconPaths";

const ICON_COLORS = {
  nav: {
    default: "#2563EB",
    active: "#1D4ED8",
  },
  hub: {
    default: "#2563EB",
    active: "#1D4ED8",
  },
};

/** Operator hub icons — uniform blue per product screenshot. */
const HUB_ICON_BLUE = "#2563EB";

const BRAND_ICON_COLORS = {
  playStart: HUB_ICON_BLUE,
  extruder: HUB_ICON_BLUE,
  knife: HUB_ICON_BLUE,
  cleaning: HUB_ICON_BLUE,
  block: HUB_ICON_BLUE,
  allForms: HUB_ICON_BLUE,
  alert: HUB_ICON_BLUE,
  observe: HUB_ICON_BLUE,
  quality: HUB_ICON_BLUE,
};

const ICON_SIZES = {
  sm: {
    className: "h-5 w-5 shrink-0",
    strokeWidth: 1.8,
  },
  lg: {
    className: "h-14 w-14 shrink-0",
    strokeWidth: 1.9,
  },
};

const ICON_RENDERERS = {
  dashboard: DashboardIconPaths,
  list: ListIconPaths,
  playStart: PlayStartIconPaths,
  allForms: AllFormsIconPaths,
  extruder: ExtruderIconPaths,
  knife: KnifeIconPaths,
  cleaning: CleaningIconPaths,
  alert: AlertIconPaths,
  observe: ObserveIconPaths,
  block: BlockIconPaths,
  quality: QualityIconPaths,
  users: UsersIconPaths,
  shield: ShieldIconPaths,
  export: ExportIconPaths,
  dropdown: DropdownIconPaths,
};

function resolveStroke(variant, active) {
  const palette = ICON_COLORS[variant] || ICON_COLORS.nav;
  return active ? palette.active : palette.default;
}

export function AppIcon({
  name,
  size = "sm",
  active = false,
  variant = "nav",
  className,
}) {
  const IconPaths = ICON_RENDERERS[name] || DefaultIconPaths;
  const sizeConfig = ICON_SIZES[size] || ICON_SIZES.sm;
  const themeStroke = resolveStroke(variant, active);
  const paint = BRAND_ICON_COLORS[name] || themeStroke;

  return (
    <svg
      viewBox="0 0 24 24"
      className={className || sizeConfig.className}
      fill="none"
      stroke={paint}
      strokeWidth={sizeConfig.strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <IconPaths stroke={paint} fill={paint} />
    </svg>
  );
}

export function NavIcon({ name, active = false }) {
  return <AppIcon name={name} size="sm" active={active} variant="nav" />;
}

export function HubIcon({ name }) {
  return <AppIcon name={name} size="lg" active variant="hub" />;
}
