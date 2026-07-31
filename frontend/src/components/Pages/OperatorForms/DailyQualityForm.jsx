import {
  CalendarClock,
  ClipboardList,
  Save,
  Sun,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import safeApi, { ENDPOINTS } from "../../../api/safeApi";
import { PRODUCTION_RUN_STATUS } from "../../../constants/productionRun";
import { useRecentEntries } from "../../../hooks/useRecentEntries";
import { useDeleteEntry } from "../../../hooks/useDeleteEntry";
import { useFormOptions, useProductionRuns } from "../../../hooks/useSunporData";
import { getApiErrorMessage } from "../../../utils/apiError";
import FormRecentEntries from "./FormRecentEntries";
import {
  FormLoadState,
  getLineName,
  getSelectedRun,
  getShiftName,
  mergeRunsForSelect,
  parseProductionRunId,
  displayInputToUtcIso,
  toLocalInputValue,
} from "./formUi";
import { formatApiDate } from "../../../utils/datetime";
import {
  CircleDot,
  FoamingBadge,
  FoamingBehaviorCard,
  Grid3X3,
  PercentBadge,
  PercentMetricCard,
} from "./qualityFormUi";

const COMMENT_MAX = 500;
const DEFAULT_FOAMING = ["OK", "Not OK", "Bad"];

function createDailyQualityForm() {
  return {
    production_run_id: "",
    shift: "",
    input_time: toLocalInputValue(),
    open_holes_percent: 0,
    sieve_distribution_percent: 0,
    foaming_behavior: "OK",
    comment: "",
  };
}

function entryToDailyQualityForm(entry) {
  return {
    production_run_id: String(entry.production_run_id),
    shift: entry.shift,
    input_time: toLocalInputValue(new Date(entry.input_time)),
    open_holes_percent: Number(entry.open_holes_percent) || 0,
    sieve_distribution_percent: Number(entry.sieve_distribution_percent) || 0,
    foaming_behavior: entry.foaming_behavior || "OK",
    comment: entry.comment || "",
  };
}

function mergeFoamingOptions(dropdownValues) {
  const fromApi = (dropdownValues || []).map((item) => item.value || item);
  const merged = [...fromApi];
  for (const value of DEFAULT_FOAMING) {
    if (!merged.includes(value)) {
      merged.push(value);
    }
  }
  return merged.length ? merged : DEFAULT_FOAMING;
}

function StatusPill({ status }) {
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

export default function DailyQualityForm() {
  const { t } = useTranslation();
  const { options, loading, error } = useFormOptions();
  const { runs, loading: runsLoading, error: runsError } = useProductionRuns(50, {
    runningOnly: true,
  });
  const [submitting, setSubmitting] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [form, setForm] = useState(createDailyQualityForm);
  const [errors, setErrors] = useState({});
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 30000);
    return () => clearInterval(timer);
  }, []);

  const {
    entries,
    runsById,
    loading: entriesLoading,
  } = useRecentEntries(ENDPOINTS.dailyQuality, {
    sortKeys: ["input_time", "created_at"],
    refreshKey,
  });

  const foamingOptions = useMemo(
    () => mergeFoamingOptions(options?.dropdowns?.foaming_behavior),
    [options]
  );

  const columns = useMemo(
    () => [
      {
        key: "input_time",
        label: t("forms.common.inputTime"),
        type: "datetime",
      },
      {
        key: "open_holes_percent",
        label: t("forms.dailyQuality.openHolesShort"),
        render: (entry) => (
          <PercentBadge value={entry.open_holes_percent} typicalMax={30} />
        ),
      },
      {
        key: "sieve_distribution_percent",
        label: t("forms.dailyQuality.sieveShort"),
        render: (entry) => (
          <PercentBadge value={entry.sieve_distribution_percent} typicalMax={100} />
        ),
      },
      {
        key: "foaming_behavior",
        label: t("forms.dailyQuality.foamingBehavior"),
        render: (entry) => <FoamingBadge value={entry.foaming_behavior} />,
      },
      {
        key: "operator_id",
        label: t("forms.common.user"),
        render: (entry) => {
          if (!entry.operator_id) {
            return "—";
          }
          if (options?.current_user_id === entry.operator_id) {
            return options?.current_user?.name || t("forms.common.user");
          }
          return `#${entry.operator_id}`;
        },
      },
    ],
    [options, t]
  );

  const runOptions = useMemo(
    () => mergeRunsForSelect(runs, runsById, form.production_run_id),
    [runs, runsById, form.production_run_id]
  );

  const selectedRun = useMemo(
    () => getSelectedRun(runOptions, form.production_run_id),
    [runOptions, form.production_run_id]
  );

  const resetForm = useCallback(() => {
    const next = createDailyQualityForm();
    if (runs.length === 1) {
      next.production_run_id = String(runs[0].id);
    } else if (runs.length > 0) {
      next.production_run_id = String(runs[0].id);
    }
    setForm(next);
    setEditingId(null);
    setErrors({});
  }, [runs]);

  const clearError = useCallback((field) => {
    setErrors((prev) => {
      if (!prev[field]) {
        return prev;
      }
      const next = { ...prev };
      delete next[field];
      return next;
    });
  }, []);

  const validate = useCallback(() => {
    const nextErrors = {};

    if (!parseProductionRunId(form.production_run_id)) {
      nextErrors.production_run_id = t("forms.common.productionRunRequired");
    }
    if (!form.shift) {
      nextErrors.shift = t("forms.dailyQuality.shiftRequired");
    }
    if (!form.input_time) {
      nextErrors.input_time = t("forms.common.eventTimeRequired");
    }
    if (!form.foaming_behavior) {
      nextErrors.foaming_behavior = t("forms.dailyQuality.foamingRequired");
    }

    const openHoles = Number(form.open_holes_percent);
    if (Number.isNaN(openHoles) || openHoles < 0 || openHoles > 100) {
      nextErrors.open_holes_percent = t("forms.common.percentRange");
    }
    const sieve = Number(form.sieve_distribution_percent);
    if (Number.isNaN(sieve) || sieve < 0 || sieve > 100) {
      nextErrors.sieve_distribution_percent = t("forms.common.percentRange");
    }

    return nextErrors;
  }, [form, t]);

  useEffect(() => {
    if (!editingId && runs.length > 0 && !form.production_run_id) {
      setForm((prev) => ({ ...prev, production_run_id: String(runs[0].id) }));
    }
  }, [runs, form.production_run_id, editingId]);

  useEffect(() => {
    if (!selectedRun || editingId) {
      return;
    }
    const shiftName = getShiftName(options, selectedRun.shift_id);
    if (shiftName !== "—") {
      setForm((prev) => ({ ...prev, shift: shiftName }));
    }
  }, [selectedRun, options, editingId]);

  const onEdit = (entry) => {
    setEditingId(entry.id);
    setForm(entryToDailyQualityForm(entry));
    setErrors({});
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleDeleted = useCallback(
    (entry) => {
      if (editingId === entry.id) {
        resetForm();
      }
      setRefreshKey((value) => value + 1);
    },
    [editingId, resetForm]
  );

  const { onDelete, deletingId } = useDeleteEntry(
    ENDPOINTS.dailyQuality,
    handleDeleted
  );

  const onSubmit = async (event) => {
    event.preventDefault();

    const nextErrors = validate();
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      toast.error(t("forms.common.fixErrors"));
      return;
    }
    setErrors({});

    const productionRunId = parseProductionRunId(form.production_run_id);

    setSubmitting(true);

    try {
      const payload = {
        production_run_id: productionRunId,
        shift: form.shift,
        input_time: displayInputToUtcIso(form.input_time),
        open_holes_percent: Number(form.open_holes_percent),
        sieve_distribution_percent: Number(form.sieve_distribution_percent),
        foaming_behavior: form.foaming_behavior,
        comment: form.comment || null,
        operator_id: options?.current_user_id,
      };

      if (editingId) {
        await safeApi.put(`${ENDPOINTS.dailyQuality}/${editingId}`, payload);
        toast.success(t("forms.common.updateSuccess"));
      } else {
        await safeApi.post(ENDPOINTS.dailyQuality, payload);
        toast.success(t("forms.dailyQuality.success"));
      }

      resetForm();
      setRefreshKey((value) => value + 1);
    } catch (submitError) {
      toast.error(
        getApiErrorMessage(
          submitError,
          editingId ? t("forms.common.updateError") : t("forms.dailyQuality.error")
        )
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (loading || runsLoading) {
    return (
      <FormLoadState loading loadingLabel={t("forms.common.loading")} />
    );
  }

  if (error || runsError) {
    return <FormLoadState error={error || runsError} />;
  }

  const lineName = getLineName(options, selectedRun?.production_line_id);
  const clockLabel = now.toLocaleTimeString("de-DE", {
    hour: "2-digit",
    minute: "2-digit",
  });
  const dateLabel = form.input_time
    ? formatApiDate(form.input_time)
    : formatApiDate(now);

  return (
    <div className="mx-auto w-full max-w-6xl space-y-5">
      <section className="rounded-3xl border border-slate-400/30 bg-[#C5C8CF] p-4 sm:p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-2 text-sm text-slate-600">
            {selectedRun ? (
              <>
                <span className="font-semibold text-slate-900">
                  {t("forms.dailyQuality.runLabel", { id: selectedRun.id })}
                </span>
                <StatusPill status={selectedRun.status} />
                <span className="text-slate-300">·</span>
                <span>{lineName}</span>
                <span className="text-slate-300">·</span>
                <span>{form.shift || "—"}</span>
                <span className="text-slate-300">·</span>
                <span>{dateLabel}</span>
                <span className="text-slate-300">·</span>
                <span>{clockLabel}</span>
              </>
            ) : (
              <span className="text-amber-700">{t("forms.common.noRunningRuns")}</span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <div className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700">
              <Sun className="h-4 w-4 text-amber-500" />
              {form.shift || t("forms.common.shift")}
            </div>
          </div>
        </div>

        <div className="mt-5 flex items-start gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-100 text-blue-700">
            <ClipboardList className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">
              {t("forms.dailyQuality.title")}
            </h1>
            <p className="mt-1 text-sm text-slate-500 sm:text-base">
              {t("forms.dailyQuality.description")}
            </p>
          </div>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <div className="text-xs font-medium uppercase tracking-wide text-slate-400">
              {t("forms.common.productionRun")}
            </div>
            <div className="mt-1 text-sm font-semibold text-slate-900">
              {selectedRun
                ? t("forms.dailyQuality.runLabel", { id: selectedRun.id })
                : "—"}
            </div>
          </div>
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <div className="text-xs font-medium uppercase tracking-wide text-slate-400">
              {t("forms.common.productionLine")}
            </div>
            <div className="mt-1 text-sm font-semibold text-slate-900">{lineName}</div>
          </div>
          <div
            className={`rounded-2xl bg-slate-50 px-4 py-3 ${
              errors.shift ? "ring-1 ring-rose-400" : ""
            }`}
          >
            <div className="text-xs font-medium uppercase tracking-wide text-slate-400">
              {t("forms.common.shift")}
            </div>
            <select
              value={form.shift}
              onChange={(event) => {
                setForm((prev) => ({ ...prev, shift: event.target.value }));
                clearError("shift");
              }}
              className="mt-1 w-full rounded-lg border-0 bg-transparent p-0 text-sm font-semibold text-slate-900 outline-none"
            >
              <option value="">{t("common.select")}</option>
              {(options?.shifts || []).map((item) => (
                <option key={item.id} value={item.name}>
                  {item.name}
                </option>
              ))}
            </select>
            {errors.shift ? (
              <div className="mt-1 text-xs font-medium text-rose-600">
                {errors.shift}
              </div>
            ) : null}
          </div>
          <div
            className={`rounded-2xl bg-slate-50 px-4 py-3 ${
              errors.input_time ? "ring-1 ring-rose-400" : ""
            }`}
          >
            <div className="text-xs font-medium uppercase tracking-wide text-slate-400">
              {t("forms.common.inputTime")}
            </div>
            <div className="mt-1 flex items-center gap-2">
              <CalendarClock className="h-4 w-4 text-slate-400" />
              <input
                type="datetime-local"
                value={form.input_time}
                onChange={(event) => {
                  setForm((prev) => ({ ...prev, input_time: event.target.value }));
                  clearError("input_time");
                }}
                className="w-full min-w-0 max-w-full rounded-lg border-0 bg-transparent p-0 text-sm font-semibold text-slate-900 outline-none"
              />
            </div>
            {errors.input_time ? (
              <div className="mt-1 text-xs font-medium text-rose-600">
                {errors.input_time}
              </div>
            ) : null}
          </div>
        </div>

        {runOptions.length > 1 ? (
          <div className="mt-4">
            <label className="text-xs font-medium uppercase tracking-wide text-slate-400">
              {t("forms.common.selectRun")}
            </label>
            <select
              value={form.production_run_id}
              onChange={(event) => {
                setForm((prev) => ({
                  ...prev,
                  production_run_id: event.target.value,
                }));
                clearError("production_run_id");
              }}
              className={`mt-1 w-full rounded-xl border bg-[#C5C8CF] px-3 py-2.5 text-sm font-medium text-slate-800 ${
                errors.production_run_id
                  ? "border-rose-400"
                  : "border-slate-200"
              }`}
            >
              {runOptions.map((run) => (
                <option key={run.id} value={run.id}>
                  {t("forms.common.runStatusOption", {
                    id: run.id,
                    status: run.status,
                  })}
                </option>
              ))}
            </select>
            {errors.production_run_id ? (
              <div className="mt-1 text-xs font-medium text-rose-600">
                {errors.production_run_id}
              </div>
            ) : null}
          </div>
        ) : null}
      </section>

      <form onSubmit={onSubmit} noValidate className="space-y-5">
        {editingId ? (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {t("forms.common.editingEntry", { id: editingId })}
          </div>
        ) : null}

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <div>
            <PercentMetricCard
              label={t("forms.dailyQuality.openHoles")}
              value={form.open_holes_percent}
              onChange={(value) => {
                setForm((prev) => ({ ...prev, open_holes_percent: value }));
                clearError("open_holes_percent");
              }}
              min={0}
              max={100}
              typicalMax={30}
              infoText={t("forms.dailyQuality.openHolesHint")}
              icon={CircleDot}
            />
            {errors.open_holes_percent ? (
              <div className="mt-1 text-xs font-medium text-rose-600">
                {errors.open_holes_percent}
              </div>
            ) : null}
          </div>
          <div>
            <PercentMetricCard
              label={t("forms.dailyQuality.sieveAnalysis")}
              value={form.sieve_distribution_percent}
              onChange={(value) => {
                setForm((prev) => ({
                  ...prev,
                  sieve_distribution_percent: value,
                }));
                clearError("sieve_distribution_percent");
              }}
              min={0}
              max={100}
              typicalMax={100}
              infoText={t("forms.dailyQuality.sieveHint")}
              icon={Grid3X3}
            />
            {errors.sieve_distribution_percent ? (
              <div className="mt-1 text-xs font-medium text-rose-600">
                {errors.sieve_distribution_percent}
              </div>
            ) : null}
          </div>
          <div>
            <FoamingBehaviorCard
              value={form.foaming_behavior}
              options={foamingOptions}
              onChange={(value) => {
                setForm((prev) => ({ ...prev, foaming_behavior: value }));
                clearError("foaming_behavior");
              }}
            />
            {errors.foaming_behavior ? (
              <div className="mt-1 text-xs font-medium text-rose-600">
                {errors.foaming_behavior}
              </div>
            ) : null}
          </div>
        </div>

        <div className="rounded-3xl border border-slate-400/30 bg-[#C5C8CF] p-4 sm:p-5">
          <label className="flex min-w-0 flex-col gap-2">
            <span className="text-sm font-semibold text-slate-800">
              {t("forms.dailyQuality.commentOptional")}
            </span>
            <textarea
              value={form.comment}
              maxLength={COMMENT_MAX}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, comment: event.target.value }))
              }
              rows={3}
              placeholder={t("forms.dailyQuality.commentPlaceholder")}
              className="w-full min-w-0 rounded-2xl border border-slate-200 px-3 py-3 text-sm text-slate-800 outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100 sm:px-4"
            />
            <span className="self-end text-xs text-slate-400">
              {form.comment.length}/{COMMENT_MAX}
            </span>
          </label>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex min-h-14 flex-1 items-center justify-center gap-2 rounded-2xl bg-blue-700 px-5 text-base font-semibold text-white shadow-sm transition hover:bg-blue-800 disabled:opacity-60"
          >
            <Save className="h-5 w-5" />
            {submitting
              ? t("common.saving")
              : editingId
                ? t("forms.common.updateEntry")
                : t("forms.dailyQuality.submit")}
          </button>
          {editingId ? (
            <button
              type="button"
              onClick={resetForm}
              className="min-h-14 w-full rounded-2xl border border-slate-200 bg-[#C5C8CF] px-5 text-sm font-semibold text-slate-700 hover:bg-slate-50 sm:w-auto"
            >
              {t("forms.common.cancelEdit")}
            </button>
          ) : null}
        </div>
      </form>

      <section className="rounded-3xl border border-slate-400/30 bg-[#C5C8CF] p-4 sm:p-5">
        <h2 className="text-lg font-semibold text-slate-900">
          {t("forms.common.recentEntries")}
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          {t("forms.dailyQuality.recentHint")}
        </p>
        <div className="mt-2">
          <FormRecentEntries
            entries={entries}
            columns={columns}
            runsById={runsById}
            loading={entriesLoading}
            onEdit={onEdit}
            onDelete={onDelete}
            deletingId={deletingId}
            hideHeader
          />
        </div>
      </section>
    </div>
  );
}
