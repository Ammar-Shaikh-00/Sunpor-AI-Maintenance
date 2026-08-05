import i18n from "../../../i18n";
import {
  displayInputToUtcIso,
  toDisplayInputValue,
} from "../../../utils/datetime";
import { translateDropdownValue } from "../../../utils/dropdownLabels";

export function FormCard({ title, description, children }) {
  return (
    <section className="mx-auto w-full max-w-5xl rounded-2xl border border-slate-400/30 bg-[#C5C8CF] p-4 shadow-sm sm:p-6">
      <div className="mb-4 sm:mb-5">
        <h2 className="text-lg font-bold text-slate-900 sm:text-xl">{title}</h2>
        {description ? (
          <p className="mt-1 text-sm text-slate-500">{description}</p>
        ) : null}
      </div>
      {children}
    </section>
  );
}

export function Field({ label, children, required = false, error }) {
  return (
    <label className="flex min-w-0 flex-col gap-1">
      <span className="text-sm font-medium text-slate-700">
        {label}
        {required ? <span className="text-rose-500"> *</span> : null}
      </span>
      {children}
      {error ? (
        <span className="text-xs font-medium text-rose-600">{error}</span>
      ) : null}
    </label>
  );
}

export const inputClass =
  "w-full min-w-0 max-w-full rounded-xl border border-slate-300 bg-white px-3 py-3 text-sm outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100 sm:px-4";

export const inputErrorClass =
  "w-full min-w-0 max-w-full rounded-xl border border-rose-400 bg-white px-3 py-3 text-sm outline-none transition focus:border-rose-400 focus:ring-2 focus:ring-rose-100 sm:px-4";

/** Return the input class with error styling applied when `hasError` is truthy. */
export function getInputClass(hasError = false) {
  return hasError ? inputErrorClass : inputClass;
}

export const primaryButtonClass =
  "inline-flex min-h-11 w-full items-center justify-center rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60 sm:w-auto";

export const secondaryButtonClass =
  "inline-flex min-h-11 w-full items-center justify-center rounded-xl border border-slate-400/40 bg-[#C5C8CF] px-5 py-3 text-sm font-semibold text-slate-900 transition hover:bg-white sm:w-auto";

export function SelectField({ value, onChange, options, placeholder = "Select..." }) {
  return (
    <select value={value} onChange={onChange} className={inputClass}>
      <option value="">{placeholder}</option>
      {options.map((option) => (
        <option key={option.value || option.id || option} value={option.value || option.id || option}>
          {option.label || option.name || option.code || option.value || option}
        </option>
      ))}
    </select>
  );
}

export function toLocalInputValue(date = new Date()) {
  return toDisplayInputValue(date);
}

export { displayInputToUtcIso, toDisplayInputValue };

export function FormLoadState({ loading, error, loadingLabel, children }) {
  if (loading) {
    return <div className="px-1 text-slate-500">{loadingLabel}</div>;
  }

  if (error) {
    return <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</div>;
  }

  return children;
}

export function getShiftName(options, shiftId) {
  const name = (options?.shifts || []).find((item) => item.id === shiftId)?.name;
  if (!name) {
    return "—";
  }
  return translateDropdownValue(i18n.t.bind(i18n), name);
}

export function getLineName(options, lineId) {
  return (options?.production_lines || []).find((item) => item.id === lineId)?.name || "—";
}

export function getMaterialCode(options, materialTypeId) {
  return (options?.material_types || []).find((item) => item.id === materialTypeId)?.code || "—";
}

export function mergeRunsForSelect(runs, runsById, selectedRunId) {
  const map = new Map((runs || []).map((run) => [run.id, run]));
  const id = Number(selectedRunId);

  if (id && runsById?.[id] && !map.has(id)) {
    map.set(id, runsById[id]);
  }

  return [...map.values()];
}

export function getSelectedRun(runs, runId) {
  return (runs || []).find((run) => String(run.id) === String(runId)) || null;
}

export function ReadOnlyField({ label, value }) {
  return (
    <label className="flex min-w-0 flex-col gap-1">
      <span className="text-sm font-medium text-slate-700">{label}</span>
      <input value={value || "—"} readOnly className={`${inputClass} bg-slate-50 text-slate-600`} />
    </label>
  );
}

export function parseProductionRunId(value) {
  if (value === "" || value === null || value === undefined) {
    return null;
  }

  const id = Number(value);
  if (!Number.isInteger(id) || id <= 0) {
    return null;
  }

  return id;
}

export function ProductionRunSelect({
  runs,
  value,
  onChange,
  label,
  selectLabel,
  showStatus = true,
  emptyMessage,
  error,
}) {
  return (
    <div className="flex min-w-0 flex-col gap-1">
      <Field label={label} required error={error}>
        <select
          name="production_run_id"
          value={value}
          onChange={onChange}
          aria-invalid={error ? "true" : undefined}
          className={getInputClass(Boolean(error))}
        >
          <option value="">{selectLabel}</option>
          {runs.map((run) => (
            <option key={run.id} value={run.id}>
              {showStatus ? `Run #${run.id} - ${run.status}` : `Run #${run.id}`}
            </option>
          ))}
        </select>
      </Field>
      {!runs.length && emptyMessage ? (
        <p className="text-sm text-amber-700">{emptyMessage}</p>
      ) : null}
    </div>
  );
}
