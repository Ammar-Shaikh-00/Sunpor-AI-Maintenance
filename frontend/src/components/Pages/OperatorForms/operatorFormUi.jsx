import { Boxes, Save } from "lucide-react";
import { useTranslation } from "react-i18next";
import { PRODUCTION_RUN_STATUS } from "../../../constants/productionRun";
import { getInputClass } from "./formUi";

/** Outer page wrapper matching the Daily Quality layout width/spacing. */
export function OperatorFormShell({ children }) {
  return <div className="mx-auto w-full max-w-6xl space-y-5">{children}</div>;
}

export function StatusPill({ status }) {
  const isRunning = status === PRODUCTION_RUN_STATUS.RUNNING;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide ${
        isRunning
          ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200"
          : "bg-slate-100 text-slate-600 ring-1 ring-slate-200"
      }`}
    >
      {status || "—"}
    </span>
  );
}

/** Compact read-only info tile used in the hero meta grid. */
export function MetaCard({ label, value }) {
  return (
    <div className="rounded-2xl bg-slate-50 px-4 py-3">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-400">
        {label}
      </div>
      <div className="mt-1 truncate text-sm font-semibold text-slate-900">
        {value || "—"}
      </div>
    </div>
  );
}

/**
 * Hero header: run context strip, icon + title + description, and an optional
 * grid of read-only meta tiles.
 */
export function FormHero({
  icon: Icon,
  title,
  description,
  run,
  runLabel,
  lineName,
  shiftName,
  metaItems = [],
}) {
  const { t } = useTranslation();

  return (
    <section className="rounded-3xl border border-slate-400/30 bg-[#C5C8CF] p-4 sm:p-5">
      <div className="flex flex-wrap items-center gap-2 text-sm text-slate-600">
        {run ? (
          <>
            <span className="font-semibold text-slate-900">{runLabel}</span>
            <StatusPill status={run.status} />
            {lineName ? (
              <>
                <span className="text-slate-300">·</span>
                <span>{lineName}</span>
              </>
            ) : null}
            {shiftName && shiftName !== "—" ? (
              <>
                <span className="text-slate-300">·</span>
                <span>{shiftName}</span>
              </>
            ) : null}
          </>
        ) : (
          <span className="text-amber-700">{t("forms.common.noRunningRuns")}</span>
        )}
      </div>

      <div className="mt-5 flex items-start gap-3">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-blue-100 text-blue-700">
          {Icon ? <Icon className="h-6 w-6" aria-hidden="true" /> : null}
        </div>
        <div className="min-w-0">
          <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">{title}</h1>
          {description ? (
            <p className="mt-1 text-sm text-slate-500 sm:text-base">{description}</p>
          ) : null}
        </div>
      </div>

      {metaItems.length ? (
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {metaItems.map((item) => (
            <MetaCard key={item.label} label={item.label} value={item.value} />
          ))}
        </div>
      ) : null}
    </section>
  );
}

/** A titled body card (rounded-3xl) that groups the editable inputs. */
export function FormSection({ title, description, children }) {
  return (
    <section className="rounded-3xl border border-slate-400/30 bg-[#C5C8CF] p-4 sm:p-5">
      {title ? (
        <div className="mb-4">
          <h2 className="text-base font-semibold text-slate-900 sm:text-lg">
            {title}
          </h2>
          {description ? (
            <p className="mt-1 text-sm text-slate-500">{description}</p>
          ) : null}
        </div>
      ) : null}
      {children}
    </section>
  );
}

/** Labeled field with an icon badge and inline error support. */
export function IconField({
  icon: Icon,
  label,
  required = false,
  error,
  hint,
  children,
  className = "",
}) {
  return (
    <label className={`flex min-w-0 flex-col gap-1.5 ${className}`}>
      <span className="flex items-center gap-2 text-sm font-semibold text-slate-800">
        {Icon ? (
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
            <Icon className="h-4 w-4" aria-hidden="true" />
          </span>
        ) : null}
        <span>
          {label}
          {required ? <span className="text-rose-500"> *</span> : null}
        </span>
      </span>
      {children}
      {hint && !error ? (
        <span className="text-xs text-slate-400">{hint}</span>
      ) : null}
      {error ? (
        <span className="text-xs font-medium text-rose-600">{error}</span>
      ) : null}
    </label>
  );
}

/** Production run selector styled as an IconField, with validation support. */
export function RunSelectField({
  runs,
  value,
  onChange,
  error,
  emptyMessage,
  icon = Boxes,
  className = "sm:col-span-2",
}) {
  const { t } = useTranslation();
  return (
    <IconField
      icon={icon}
      label={t("forms.common.productionRun")}
      required
      error={error}
      className={className}
    >
      <select
        name="production_run_id"
        value={value}
        onChange={onChange}
        aria-invalid={error ? "true" : undefined}
        className={getInputClass(Boolean(error))}
      >
        <option value="">{t("forms.common.selectRun")}</option>
        {runs.map((run) => (
          <option key={run.id} value={run.id}>
            {t("forms.common.runStatusOption", {
              id: run.id,
              status: run.status,
            })}
          </option>
        ))}
      </select>
      {!runs.length && emptyMessage ? (
        <span className="text-sm text-amber-700">{emptyMessage}</span>
      ) : null}
    </IconField>
  );
}

/** Sticky-feel submit row with a prominent primary button and optional cancel. */
export function SubmitBar({
  submitting,
  editing = false,
  submitLabel,
  updateLabel,
  savingLabel,
  onCancel,
  cancelLabel,
  icon: Icon = Save,
}) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row">
      <button
        type="submit"
        disabled={submitting}
        className="inline-flex min-h-14 flex-1 items-center justify-center gap-2 rounded-2xl bg-blue-600 px-5 text-base font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:opacity-60"
      >
        {Icon ? <Icon className="h-5 w-5" aria-hidden="true" /> : null}
        {submitting ? savingLabel : editing ? updateLabel : submitLabel}
      </button>
      {editing && onCancel ? (
        <button
          type="button"
          onClick={onCancel}
          className="min-h-14 rounded-2xl border border-slate-400/40 bg-[#C5C8CF] px-5 text-sm font-semibold text-slate-900 transition hover:bg-white sm:w-auto"
        >
          {cancelLabel}
        </button>
      ) : null}
    </div>
  );
}

/** Styled recent-entries wrapper (title + hint) matching Daily Quality. */
export function RecentEntriesCard({ title, hint, children }) {
  return (
    <section className="rounded-3xl border border-slate-400/30 bg-[#C5C8CF] p-4 sm:p-5">
      <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
      {hint ? <p className="mt-1 text-sm text-slate-500">{hint}</p> : null}
      <div className="mt-2">{children}</div>
    </section>
  );
}
