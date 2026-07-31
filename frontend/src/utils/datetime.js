import { useBackendStore } from "../store/backendStore";

const DEFAULT_DISPLAY_TIMEZONE = "Europe/Vienna";
const DEFAULT_LOCALE = "de-DE";

export function getDisplayTimezone() {
  return (
    useBackendStore.getState().appConfig.displayTimezone || DEFAULT_DISPLAY_TIMEZONE
  );
}

function partsFromDate(date, timeZone) {
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });

  return Object.fromEntries(
    formatter.formatToParts(date).map((part) => [part.type, part.value])
  );
}

/** Format API datetime for UI (backend already converts to display timezone). */
export function formatApiDateTime(
  value,
  {
    locale = DEFAULT_LOCALE,
    timeZone = getDisplayTimezone(),
    withSeconds = true,
  } = {}
) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return new Intl.DateTimeFormat(locale, {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    ...(withSeconds ? { second: "2-digit" } : {}),
  }).format(date);
}

export function formatApiDate(value, options = {}) {
  return formatApiDateTime(value, { ...options, withSeconds: false });
}

export function formatApiTime(value, options = {}) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return new Intl.DateTimeFormat(options.locale || DEFAULT_LOCALE, {
    timeZone: options.timeZone || getDisplayTimezone(),
    hour: "2-digit",
    minute: "2-digit",
    second: options.withSeconds === false ? undefined : "2-digit",
  }).format(date);
}

/** datetime-local value in the configured display timezone. */
export function toDisplayInputValue(
  value,
  timeZone = getDisplayTimezone()
) {
  if (!value) {
    return "";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const parts = partsFromDate(date, timeZone);
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
}

/** Convert datetime-local wall clock (display TZ) to UTC ISO for API writes. */
export function displayInputToUtcIso(
  localValue,
  timeZone = getDisplayTimezone()
) {
  if (!localValue) {
    return null;
  }

  const [datePart, timePart] = localValue.split("T");
  if (!datePart || !timePart) {
    return null;
  }

  const [year, month, day] = datePart.split("-").map(Number);
  const [hour, minute] = timePart.split(":").map(Number);

  let utcMs = Date.UTC(year, month - 1, day, hour, minute, 0);

  for (let attempt = 0; attempt < 2; attempt += 1) {
    const parts = partsFromDate(new Date(utcMs), timeZone);
    const zonedMs = Date.UTC(
      Number(parts.year),
      Number(parts.month) - 1,
      Number(parts.day),
      Number(parts.hour),
      Number(parts.minute),
      Number(parts.second)
    );
    const targetMs = Date.UTC(year, month - 1, day, hour, minute, 0);
    utcMs -= zonedMs - targetMs;
  }

  return new Date(utcMs).toISOString();
}

/** Date input (yyyy-MM-dd) start/end as UTC ISO for API filters. */
export function displayDateStartToUtcIso(dateValue, timeZone = getDisplayTimezone()) {
  return displayInputToUtcIso(`${dateValue}T00:00`, timeZone);
}

export function displayDateEndToUtcIso(dateValue, timeZone = getDisplayTimezone()) {
  return displayInputToUtcIso(`${dateValue}T23:59`, timeZone);
}

export function nowInDisplayTimezoneParts(timeZone = getDisplayTimezone()) {
  return partsFromDate(new Date(), timeZone);
}

export function formatDisplayClock(
  date = new Date(),
  {
    locale = DEFAULT_LOCALE,
    timeZone = getDisplayTimezone(),
    withSeconds = false,
    withTimeZoneName = false,
  } = {}
) {
  return new Intl.DateTimeFormat(locale, {
    timeZone,
    hour: "2-digit",
    minute: "2-digit",
    ...(withSeconds ? { second: "2-digit" } : {}),
    ...(withTimeZoneName ? { timeZoneName: "short" } : {}),
  }).format(date);
}

export function getDisplayTimezoneRegion() {
  return (
    useBackendStore.getState().appConfig.displayTimezoneRegion || "austria"
  );
}

/** Short plant label for UI chips, e.g. Wien / Karachi / New York. */
export function getDisplayTimezoneCityLabel() {
  const region = getDisplayTimezoneRegion();
  const labels = {
    austria: "Wien",
    pakistan: "Karachi",
    usa: "New York",
  };
  return labels[region] || region;
}

const SECONDS_IN = {
  year: 365 * 24 * 3600,
  month: 30 * 24 * 3600,
  day: 24 * 3600,
  hour: 3600,
  minute: 60,
};

/**
 * Human-readable duration like "1y 2mo 3d 04h 05m 06s". Leading zero units are
 * dropped, but hours/minutes/seconds are always shown. Months and years use
 * approximate lengths (30 / 365 days).
 */
export function formatDuration(totalSeconds, { emptyLabel = "—" } = {}) {
  if (totalSeconds == null || Number.isNaN(Number(totalSeconds))) {
    return emptyLabel;
  }

  let remaining = Math.max(0, Math.floor(Number(totalSeconds)));

  const years = Math.floor(remaining / SECONDS_IN.year);
  remaining %= SECONDS_IN.year;
  const months = Math.floor(remaining / SECONDS_IN.month);
  remaining %= SECONDS_IN.month;
  const days = Math.floor(remaining / SECONDS_IN.day);
  remaining %= SECONDS_IN.day;
  const hours = Math.floor(remaining / SECONDS_IN.hour);
  remaining %= SECONDS_IN.hour;
  const minutes = Math.floor(remaining / SECONDS_IN.minute);
  const seconds = remaining % SECONDS_IN.minute;

  const parts = [];
  if (years) {
    parts.push(`${years}y`);
  }
  if (months || parts.length) {
    parts.push(`${months}mo`);
  }
  if (days || parts.length) {
    parts.push(`${days}d`);
  }
  parts.push(`${String(hours).padStart(2, "0")}h`);
  parts.push(`${String(minutes).padStart(2, "0")}m`);
  parts.push(`${String(seconds).padStart(2, "0")}s`);
  return parts.join(" ");
}

export function formatDisplayDate(
  date = new Date(),
  {
    locale = DEFAULT_LOCALE,
    timeZone = getDisplayTimezone(),
  } = {}
) {
  return new Intl.DateTimeFormat(locale, {
    timeZone,
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(date);
}
