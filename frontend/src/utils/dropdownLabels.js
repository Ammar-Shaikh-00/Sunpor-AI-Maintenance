/**
 * Translate a stored dropdown value for display.
 * Stored API/DB values stay in English; the UI shows German via de.json.
 */
export function translateDropdownValue(t, value) {
  if (value == null || value === "") {
    return value;
  }
  const text = String(value);
  return t(`dropdownValues.${text}`, { defaultValue: text });
}
