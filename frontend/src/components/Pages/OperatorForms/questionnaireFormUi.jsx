import { ArrowRight, X } from "lucide-react";
import { useTranslation } from "react-i18next";
import { getInputClass } from "./formUi";

/** Page wrapper for questionnaire-style operator forms. */
export function QuestionnaireShell({ children }) {
  return <div className="mx-auto w-full max-w-6xl space-y-5">{children}</div>;
}

/**
 * Dark-blue form header matching the shared screenshot:
 * icon + title + subtitle + optional close action.
 */
export function QuestionnaireHeader({
  icon: Icon,
  title,
  description,
  onClose,
}) {
  return (
    <header className="flex items-start gap-3 rounded-t-[10px] bg-[#1E4FD6] px-4 py-4 text-white sm:gap-4 sm:px-5 sm:py-5">
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white/15 ring-1 ring-white/25 sm:h-12 sm:w-12">
        {Icon ? <Icon className="h-5 w-5 sm:h-6 sm:w-6" aria-hidden="true" /> : null}
      </div>
      <div className="min-w-0 flex-1">
        <h1 className="text-lg font-bold uppercase tracking-wide sm:text-xl">
          {title}
        </h1>
        {description ? (
          <p className="mt-1 text-xs leading-relaxed text-blue-100 sm:text-sm">
            {description}
          </p>
        ) : null}
      </div>
      {onClose ? (
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg p-1.5 text-white/80 transition hover:bg-white/15 hover:text-white"
          aria-label="Close"
        >
          <X className="h-5 w-5" />
        </button>
      ) : null}
    </header>
  );
}

/** White card body that hosts the numbered question grid. */
export function QuestionnaireCard({ header, children, footer }) {
  return (
    <section className="overflow-hidden rounded-[10px] border border-slate-200 bg-white shadow-sm">
      {header}
      <div className="bg-white">{children}</div>
      {footer}
    </section>
  );
}

/**
 * Responsive grid with light-blue dividers between question cells.
 * Use QuestionCell children with optional colSpan.
 */
export function QuestionnaireGrid({ children, columns = 2 }) {
  const colClass =
    columns === 3
      ? "sm:grid-cols-3"
      : columns === 1
        ? "sm:grid-cols-1"
        : "sm:grid-cols-2";

  return (
    <div
      className={`grid grid-cols-1 border-t border-sky-100 ${colClass} [&>*]:border-b [&>*]:border-sky-100 sm:[&>*:nth-child(odd)]:border-r`}
    >
      {children}
    </div>
  );
}

/** One numbered question cell. */
export function QuestionCell({
  number,
  question,
  required = false,
  error,
  hint,
  className = "",
  children,
}) {
  return (
    <div
      className={`flex min-w-0 flex-col gap-2.5 border-sky-100 p-4 sm:p-5 ${className}`}
    >
      <div className="flex items-start gap-2">
        <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-[#1E4FD6]/10 text-xs font-bold text-[#1E4FD6]">
          {number}
        </span>
        <p className="text-sm font-semibold leading-snug text-[#1E4FD6] sm:text-[15px]">
          {question}
          {required ? <span className="text-[#1E4FD6]"> *</span> : null}
        </p>
      </div>
      <div className="min-w-0 pl-8">{children}</div>
      {hint && !error ? (
        <p className="pl-8 text-xs text-slate-400">{hint}</p>
      ) : null}
      {error ? (
        <p className="pl-8 text-xs font-medium text-rose-600">{error}</p>
      ) : null}
    </div>
  );
}

/** Full-width row for comment / spanning fields. */
export function QuestionRow({
  number,
  question,
  required = false,
  error,
  hint,
  children,
}) {
  return (
    <div className="border-t border-sky-100 p-4 sm:p-5">
      <div className="flex items-start gap-2">
        <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-[#1E4FD6]/10 text-xs font-bold text-[#1E4FD6]">
          {number}
        </span>
        <p className="text-sm font-semibold leading-snug text-[#1E4FD6] sm:text-[15px]">
          {question}
          {required ? <span className="text-[#1E4FD6]"> *</span> : null}
        </p>
      </div>
      <div className="mt-2.5 min-w-0 pl-8">{children}</div>
      {hint && !error ? (
        <p className="mt-1 pl-8 text-xs text-slate-400">{hint}</p>
      ) : null}
      {error ? (
        <p className="mt-1 pl-8 text-xs font-medium text-rose-600">{error}</p>
      ) : null}
    </div>
  );
}

/** Compact run context strip under the header. */
export function QuestionnaireContext({ items = [] }) {
  if (!items.length) {
    return null;
  }
  return (
    <div className="flex flex-wrap gap-2 border-b border-sky-100 bg-slate-50 px-4 py-3 sm:px-5">
      {items.map((item) => (
        <div
          key={item.label}
          className="rounded-lg bg-white px-3 py-1.5 text-xs ring-1 ring-slate-200"
        >
          <span className="font-medium text-slate-400">{item.label}: </span>
          <span className="font-semibold text-slate-800">{item.value || "—"}</span>
        </div>
      ))}
    </div>
  );
}

/** Footer with Cancel + primary capture button. */
export function QuestionnaireFooter({
  submitting,
  editing = false,
  submitLabel,
  updateLabel,
  savingLabel,
  onCancel,
  cancelLabel,
  showCancel = true,
}) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col gap-3 border-t border-sky-100 bg-slate-50 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-5">
      {showCancel && onCancel ? (
        <button
          type="button"
          onClick={onCancel}
          className="inline-flex min-h-11 items-center justify-center rounded-[10px] border border-slate-300 bg-white px-5 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
        >
          {cancelLabel || t("common.cancel")}
        </button>
      ) : (
        <span />
      )}
      <button
        type="submit"
        disabled={submitting}
        className="inline-flex min-h-12 items-center justify-center gap-2 rounded-[10px] bg-[#1E4FD6] px-6 text-sm font-semibold text-white shadow-sm transition hover:bg-[#1A44B8] disabled:opacity-60 sm:min-w-[12rem]"
      >
        {submitting
          ? savingLabel
          : editing
            ? updateLabel
            : submitLabel}
        {!submitting ? <ArrowRight className="h-4 w-4" aria-hidden="true" /> : null}
      </button>
    </div>
  );
}

/** Production-run select for questionnaire cells. */
export function QuestionnaireRunSelect({
  runs,
  value,
  onChange,
  error,
  emptyMessage,
}) {
  const { t } = useTranslation();
  return (
    <>
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
        <p className="mt-1 text-sm text-amber-700">{emptyMessage}</p>
      ) : null}
    </>
  );
}

export function RecentEntriesCard({ title, hint, children }) {
  return (
    <section className="overflow-hidden rounded-[10px] border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
      <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
      {hint ? <p className="mt-1 text-sm text-slate-500">{hint}</p> : null}
      <div className="mt-2">{children}</div>
    </section>
  );
}
