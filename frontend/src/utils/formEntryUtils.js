import {
  formatApiDateTime,
  getDisplayTimezone,
} from "./datetime";

const DEFAULT_SORT_KEYS = [
  "created_at",
  "event_time",
  "input_time",
  "start_time",
  "from_time",
];

export function getEntryTimestamp(entry, sortKeys = DEFAULT_SORT_KEYS) {
  for (const key of sortKeys) {
    const value = entry?.[key];
    if (value) {
      return new Date(value).getTime();
    }
  }
  return 0;
}

export function sortEntriesByKeys(entries, sortKeys = DEFAULT_SORT_KEYS) {
  return [...entries].sort(
    (left, right) => getEntryTimestamp(right, sortKeys) - getEntryTimestamp(left, sortKeys)
  );
}

export function formatEntryDateTime(value, locale = "de-DE") {
  return formatApiDateTime(value, {
    locale,
    timeZone: getDisplayTimezone(),
  });
}

export function formatEntryText(value, maxLength = 80) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  const text = String(value);
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength)}…`;
}
