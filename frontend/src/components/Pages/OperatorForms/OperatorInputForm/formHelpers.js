/**
 * Helpers for schema-driven operator forms: validation, ISO times, titles, status.
 */

export function buildInitialValues(definition) {
  const values = {};
  for (const field of definition.fields || []) {
    if (field.type === "event_time") {
      values[field.id] = { mode: "now", date: "", time: "" };
    } else if (field.type === "datetime_flags") {
      values[field.id] = { date: "", time: "" };
    } else if (field.type === "checkbox" || field.multi) {
      values[field.id] = field.otherTextKey ? { values: [], other: "" } : [];
    } else if (field.type === "radio" && field.otherTextKey) {
      values[field.id] = { value: "", other: "" };
    } else if (field.type === "select" && (field.allowOther || field.flags)) {
      values[field.id] = { value: "", other: "" };
    } else if (field.type === "quality_link") {
      values[field.id] = [];
    } else {
      values[field.id] = field.type === "run_select" ? null : "";
    }
  }
  return values;
}

function pad(value) {
  return String(value).padStart(2, "0");
}

export function toLocalDateParts(date = new Date()) {
  return {
    date: `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`,
    time: `${pad(date.getHours())}:${pad(date.getMinutes())}`,
  };
}

export function combineDateTime(dateStr, timeStr) {
  if (!dateStr || !timeStr) return null;
  const isoLocal = `${dateStr}T${timeStr}:00`;
  const parsed = new Date(isoLocal);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed.toISOString();
}

export function resolveEventTimeIso(eventTimeValue) {
  if (!eventTimeValue || eventTimeValue.mode !== "past") {
    return new Date().toISOString();
  }
  return combineDateTime(eventTimeValue.date, eventTimeValue.time);
}

function unwrapRadio(value) {
  if (value && typeof value === "object" && "value" in value) {
    return value.value;
  }
  return value;
}

function unwrapCheckbox(value) {
  if (value && typeof value === "object" && Array.isArray(value.values)) {
    return value.values;
  }
  return Array.isArray(value) ? value : [];
}

export function validateFormValues(definition, values) {
  const errors = {};
  for (const field of definition.fields || []) {
    if (!field.required) continue;
    const raw = values[field.id];

    if (field.type === "run_select" && !raw) {
      errors[field.id] = "Pflichtfeld";
      continue;
    }
    if (field.type === "event_time") {
      if (raw?.mode === "past" && (!raw.date || !raw.time)) {
        errors[field.id] = "Datum und Uhrzeit erforderlich";
      }
      continue;
    }
    if (field.type === "radio") {
      if (!unwrapRadio(raw)) errors[field.id] = "Bitte auswählen";
      continue;
    }
    if (field.type === "checkbox" || field.multi) {
      if (!unwrapCheckbox(raw).length) errors[field.id] = "Bitte auswählen";
      continue;
    }
    if (field.type === "textarea" || field.type === "text") {
      if (!String(raw || "").trim()) errors[field.id] = "Pflichtfeld";
    }
  }
  return errors;
}

export function deriveEntryTitle(definition, values) {
  const recordType = unwrapRadio(values.record_type);
  if (recordType) {
    const field = definition.fields.find((item) => item.id === "record_type");
    const option = field?.options?.find((item) => item.value === recordType);
    if (option) return option.label;
  }

  const category = unwrapRadio(values.category);
  if (category) {
    const field = definition.fields.find((item) => item.id === "category");
    const option = field?.options?.find((item) => item.value === category);
    if (option) return option.label;
  }

  const assessment = unwrapRadio(values.overall_assessment);
  if (assessment) {
    const field = definition.fields.find(
      (item) => item.id === "overall_assessment"
    );
    const option = field?.options?.find((item) => item.value === assessment);
    if (option) return `Qualitätsprüfung · ${option.label}`;
    return "Qualitätsprüfung abgeschlossen";
  }

  return definition.title;
}

export function deriveEntryStatus(definition, values) {
  const result = unwrapRadio(values.result);
  if (result === "fully_resolved" || result === "problem_resolved") {
    return "resolved";
  }
  if (
    result === "still_exists" ||
    result === "observation_ongoing" ||
    result === "no_change" ||
    result === "partially_resolved"
  ) {
    return result === "partially_resolved" ? "open" : "open";
  }

  const assessment = unwrapRadio(values.overall_assessment);
  if (assessment === "release") return "released";
  if (assessment === "release_with_restriction") return "released";
  if (assessment === "hold") return "hold";
  if (assessment === "scrap") return "scrap";
  if (assessment === "rework") return "open";

  return "open";
}

export function buildSubmitPayload(definition, values, runs, formOptions = null) {
  const eventTime = resolveEventTimeIso(values.event_time);
  const runId = values.production_run || null;
  const run = runs.find((item) => item.id === runId);

  let material =
    typeof values.affected_material === "object"
      ? values.affected_material?.other || values.affected_material?.value
      : values.affected_material || values.material;

  if (material && formOptions) {
    const materials =
      formOptions.materials || formOptions.material_types || [];
    const match = materials.find(
      (item) => String(item.id) === String(material)
    );
    if (match) {
      material =
        match.code && match.description && match.description !== match.code
          ? `${match.code} — ${match.description}`
          : match.code || match.description || material;
    }
  }

  const batch =
    typeof values.affected_batch === "object"
      ? values.affected_batch?.unknown
        ? "Unbekannt"
        : values.affected_batch?.value
      : values.affected_batch || values.batch;

  return {
    category: definition.id,
    production_run_id: runId,
    event_time: eventTime,
    title: deriveEntryTitle(definition, values),
    status: deriveEntryStatus(definition, values),
    batch_label: batch ? String(batch) : null,
    material_label: material ? String(material) : null,
    recipe_label: run?.recipe_number || values.recipe || null,
    machine_label: values.machine || null,
    comment:
      typeof values.comment === "string" ? values.comment.trim() : null,
    payload: values,
  };
}

export function fieldIndexMap(definition) {
  const map = {};
  let index = 1;
  for (const row of definition.layout || []) {
    for (const fieldId of row) {
      map[fieldId] = index;
      index += 1;
    }
  }
  return map;
}
