import {
  Beaker,
  Check,
  CircleHelp,
  Clock3,
  Factory,
  FileText,
  Grid2X2,
  Hexagon,
  Info,
  Lightbulb,
  MessageSquareText,
  Play,
  RefreshCw,
  Sun,
  UserRound,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import safeApi, { ENDPOINTS } from "../../../api/safeApi";
import {
  PRODUCTION_RUN_STATUS,
  isProductionRunEditable,
} from "../../../constants/productionRun";
import { useRecentEntries } from "../../../hooks/useRecentEntries";
import { useDeleteEntry } from "../../../hooks/useDeleteEntry";
import { useFormOptions } from "../../../hooks/useSunporData";
import { getApiErrorMessage } from "../../../utils/apiError";
import {
  displayInputToUtcIso,
  formatApiDateTime,
  formatDisplayClock,
  getDisplayTimezoneCityLabel,
} from "../../../utils/datetime";
import CurrentProductionRunBanner from "./CurrentProductionRunBanner";
import FormRecentEntries from "./FormRecentEntries";
import { getProductionStartColumns } from "./formEntryColumns";
import {
  FormLoadState,
  getLineName,
  getShiftName,
  toLocalInputValue,
} from "./formUi";

const PRODUCTION_START_SORT_KEYS = ["start_time", "created_at"];
const COMMENT_MAX = 200;
const FEATURED_MATERIAL_COUNT = 2;

function getRunForEntry(entry) {
  return entry;
}

function canEditProductionStart(entry) {
  return isProductionRunEditable(entry);
}

function createProductionStartForm(defaults = {}) {
  return {
    company_id: defaults.company_id || "",
    production_line_id: defaults.production_line_id || "",
    material_type_id: defaults.material_type_id || "",
    shift_id: defaults.shift_id || "",
    is_trial: defaults.is_trial || "No",
    start_time: defaults.start_time || toLocalInputValue(),
    recipe_number: defaults.recipe_number || "",
    production_order: defaults.production_order || "",
    comment: defaults.comment || "",
  };
}

function runToProductionStartForm(run) {
  return createProductionStartForm({
    company_id: String(run.company_id),
    production_line_id: String(run.production_line_id),
    material_type_id: String(run.material_type_id),
    shift_id: String(run.shift_id),
    is_trial: run.is_trial ? "Yes" : "No",
    start_time: toLocalInputValue(new Date(run.start_time)),
    recipe_number: run.recipe_number || "",
    production_order: run.production_order || "",
    comment: run.comment || "",
  });
}

function defaultsFromOptions(options) {
  return {
    company_id: String(options?.companies?.[0]?.id || ""),
    production_line_id: String(options?.production_lines?.[0]?.id || ""),
    shift_id: String(options?.shifts?.[0]?.id || ""),
    start_time: toLocalInputValue(),
  };
}

function StepHeader({ number, title, subtitle, action }) {
  return (
    <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
      <div className="flex min-w-0 items-start gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
          {number}
        </div>
        <div className="min-w-0">
          <h2 className="text-base font-semibold text-slate-900 sm:text-lg">{title}</h2>
          {subtitle ? (
            <p className="mt-0.5 text-sm text-slate-500">{subtitle}</p>
          ) : null}
        </div>
      </div>
      {action}
    </div>
  );
}

function AutoInfoCard({ icon: Icon, label, value }) {
  return (
    <div className="flex min-w-0 items-start gap-3 rounded-2xl bg-[#C5C8CF]/70 px-3 py-3 sm:px-4">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
        <Icon className="h-5 w-5" aria-hidden="true" />
      </div>
      <div className="min-w-0">
        <div className="text-xs font-medium uppercase tracking-wide text-slate-400">
          {label}
        </div>
        <div className="mt-0.5 truncate text-sm font-semibold text-slate-900">
          {value || "—"}
        </div>
      </div>
    </div>
  );
}

function SummaryItem({ icon: Icon, label, value }) {
  return (
    <div className="flex min-w-0 items-center gap-2.5">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-500">
        <Icon className="h-4 w-4" aria-hidden="true" />
      </div>
      <div className="min-w-0">
        <div className="text-[11px] font-medium uppercase tracking-wide text-slate-400">
          {label}
        </div>
        <div className="truncate text-sm font-semibold text-slate-800">
          {value || "—"}
        </div>
      </div>
    </div>
  );
}

export default function ProductionStartForm() {
  const { t } = useTranslation();
  const { options, loading, error } = useFormOptions();
  const [submitting, setSubmitting] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [form, setForm] = useState(() => createProductionStartForm());
  const [showOptional, setShowOptional] = useState(true);
  const [showOtherMaterials, setShowOtherMaterials] = useState(false);
  const [now, setNow] = useState(() => new Date());
  const [showHelp, setShowHelp] = useState(false);
  const [completingId, setCompletingId] = useState(null);
  const [errors, setErrors] = useState({});

  const {
    entries,
    runsById,
    loading: entriesLoading,
  } = useRecentEntries(ENDPOINTS.productionRuns, {
    sortKeys: PRODUCTION_START_SORT_KEYS,
    refreshKey,
  });

  const columns = useMemo(
    () => getProductionStartColumns(t, options),
    [t, options]
  );

  const materialTypes = options?.material_types || [];
  const featuredMaterials = materialTypes.slice(0, FEATURED_MATERIAL_COUNT);
  const otherMaterials = materialTypes.slice(FEATURED_MATERIAL_COUNT);

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 30_000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!options || editingId) {
      return;
    }
    setForm((prev) => {
      const defaults = defaultsFromOptions(options);
      return {
        ...prev,
        company_id: prev.company_id || defaults.company_id,
        production_line_id: prev.production_line_id || defaults.production_line_id,
        shift_id: prev.shift_id || defaults.shift_id,
        start_time: toLocalInputValue(now),
        is_trial: prev.is_trial || "No",
      };
    });
  }, [options, editingId, now]);

  const resetForm = useCallback(() => {
    setForm(createProductionStartForm(defaultsFromOptions(options)));
    setEditingId(null);
    setShowOtherMaterials(false);
    setShowOptional(true);
    setErrors({});
  }, [options]);

  const cycleShift = () => {
    const shifts = options?.shifts || [];
    if (!shifts.length) {
      return;
    }
    const currentIndex = shifts.findIndex(
      (shift) => String(shift.id) === String(form.shift_id)
    );
    const next = shifts[(currentIndex + 1) % shifts.length];
    setForm((prev) => ({ ...prev, shift_id: String(next.id) }));
    toast.success(
      t("forms.productionStart.shiftChanged", { shift: next.name })
    );
  };

  const onEdit = (entry) => {
    setEditingId(entry.id);
    setForm(runToProductionStartForm(entry));
    setShowOptional(true);
    const isOther = otherMaterials.some(
      (item) => String(item.id) === String(entry.material_type_id)
    );
    setShowOtherMaterials(isOther);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const onComplete = async (entry) => {
    if (!isProductionRunEditable(entry)) {
      toast.error(t("forms.common.cannotCompleteInactive"));
      return;
    }

    const confirmed = window.confirm(
      t("forms.common.completeConfirm", { id: entry.id })
    );
    if (!confirmed) {
      return;
    }

    setCompletingId(entry.id);
    try {
      await safeApi.put(`${ENDPOINTS.productionRuns}/${entry.id}`, {
        status: PRODUCTION_RUN_STATUS.COMPLETED,
        end_time: displayInputToUtcIso(toLocalInputValue(new Date())),
      });
      toast.success(t("forms.common.completeSuccess"));
      if (editingId === entry.id) {
        resetForm();
      }
      setRefreshKey((value) => value + 1);
    } catch (completeError) {
      toast.error(
        getApiErrorMessage(completeError, t("forms.common.completeError"))
      );
    } finally {
      setCompletingId(null);
    }
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
    ENDPOINTS.productionRuns,
    handleDeleted
  );

  const selectMaterial = (materialId, fromOther = false) => {
    setForm((prev) => ({ ...prev, material_type_id: String(materialId) }));
    setShowOtherMaterials(fromOther);
    setErrors((prev) => {
      if (!prev.material_type_id) {
        return prev;
      }
      const next = { ...prev };
      delete next.material_type_id;
      return next;
    });
  };

  const onSubmit = async (event) => {
    event.preventDefault();

    const nextErrors = {};
    if (!form.material_type_id) {
      nextErrors.material_type_id = t("forms.productionStart.materialRequired");
    }
    if (!form.company_id || !form.production_line_id || !form.shift_id) {
      nextErrors.context = t("forms.productionStart.contextRequired");
    }
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      toast.error(nextErrors.material_type_id || nextErrors.context);
      return;
    }
    setErrors({});

    setSubmitting(true);
    try {
      const startTime = editingId
        ? displayInputToUtcIso(form.start_time)
        : displayInputToUtcIso(toLocalInputValue(new Date()));

      const payload = {
        company_id: Number(form.company_id),
        production_line_id: Number(form.production_line_id),
        material_type_id: Number(form.material_type_id),
        shift_id: Number(form.shift_id),
        operator_id: options?.current_user_id,
        is_trial: form.is_trial === "Yes",
        start_time: startTime,
        recipe_number: form.recipe_number || null,
        production_order: form.production_order || null,
        comment: form.comment || null,
      };

      if (editingId) {
        await safeApi.put(`${ENDPOINTS.productionRuns}/${editingId}`, payload);
        toast.success(t("forms.common.updateSuccess"));
      } else {
        await safeApi.post(ENDPOINTS.productionRuns, payload);
        toast.success(t("forms.productionStart.success"));
      }

      resetForm();
      setRefreshKey((value) => value + 1);
    } catch (submitError) {
      toast.error(
        getApiErrorMessage(
          submitError,
          editingId
            ? t("forms.common.updateError")
            : t("forms.productionStart.error")
        )
      );
    } finally {
      setSubmitting(false);
    }
  };

  const selectedMaterial = materialTypes.find(
    (item) => String(item.id) === String(form.material_type_id)
  );
  const lineName = getLineName(options, Number(form.production_line_id));
  const shiftName = getShiftName(options, Number(form.shift_id));
  const startTimeLabel = t("forms.productionStart.nowTime", {
    time: formatDisplayClock(now),
    zone: getDisplayTimezoneCityLabel(),
  });
  const trialLabel =
    form.is_trial === "Yes" ? t("common.yes") : t("common.no");

  if (loading || error) {
    return (
      <FormLoadState
        loading={loading}
        error={error}
        loadingLabel={t("forms.common.loadingOptions")}
      />
    );
  }

  return (
    <div className="mx-auto w-full max-w-5xl space-y-5">
      <CurrentProductionRunBanner />

      <div className="flex flex-wrap items-center justify-end gap-2">
        <button
          type="button"
          onClick={cycleShift}
          className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-slate-400/40 bg-[#C5C8CF] px-4 text-sm font-semibold text-slate-900 transition hover:bg-white"
        >
          <RefreshCw className="h-4 w-4" aria-hidden="true" />
          {t("forms.productionStart.changeShift")}
        </button>
      </div>

      <header className="flex items-start gap-3 rounded-[10px] bg-[#1E4FD6] px-4 py-4 text-white sm:gap-4 sm:px-5 sm:py-5">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white/15 ring-1 ring-white/25 sm:h-14 sm:w-14">
          <Play className="h-6 w-6 fill-white" aria-hidden="true" />
        </div>
        <div className="min-w-0 flex-1 pt-0.5">
          <h1 className="text-lg font-bold uppercase tracking-wide sm:text-xl">
            {t("forms.productionStart.title")}
          </h1>
          <p className="mt-1 text-xs leading-relaxed text-blue-100 sm:text-sm">
            {t("forms.productionStart.subtitle")}
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowHelp((prev) => !prev)}
          className="inline-flex min-h-11 items-center gap-1.5 rounded-[10px] border border-white/25 bg-white/10 px-3 text-sm font-medium text-white transition hover:bg-white/20"
          aria-expanded={showHelp}
        >
          <CircleHelp className="h-4 w-4" aria-hidden="true" />
          {t("forms.productionStart.help")}
        </button>
      </header>

      {showHelp ? (
        <div className="rounded-2xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-900">
          {t("forms.productionStart.helpText")}
        </div>
      ) : null}

      {editingId ? (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {t("forms.common.editingEntry", { id: editingId })}
        </div>
      ) : null}

      <section className="rounded-3xl border border-slate-400/30 bg-[#C5C8CF] p-4 sm:p-5">
        <div className="mb-3 flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold text-slate-800">
            {t("forms.productionStart.autoDetected")}
          </h2>
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-bold uppercase tracking-wide text-emerald-700 ring-1 ring-emerald-200">
            <Check className="h-3.5 w-3.5" aria-hidden="true" />
            {t("forms.productionStart.ok")}
          </span>
        </div>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
          <AutoInfoCard
            icon={UserRound}
            label={t("forms.common.operator")}
            value={options?.current_user?.name}
          />
          <AutoInfoCard
            icon={Factory}
            label={t("forms.common.productionLine")}
            value={lineName}
          />
          <AutoInfoCard
            icon={Sun}
            label={t("forms.common.shift")}
            value={shiftName}
          />
          <AutoInfoCard
            icon={Clock3}
            label={t("forms.common.startTime")}
            value={
              editingId
                ? formatApiDateTime(form.start_time, { withSeconds: false })
                : startTimeLabel
            }
          />
        </div>
      </section>

      <form onSubmit={onSubmit} className="space-y-5">
        <section className="rounded-3xl border border-slate-400/30 bg-[#C5C8CF] p-4 sm:p-5">
          <StepHeader
            number={1}
            title={t("forms.common.questions.materialType")}
            subtitle={t("forms.productionStart.stepMaterialHint")}
          />
          {errors.material_type_id ? (
            <div className="mb-3 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">
              {errors.material_type_id}
            </div>
          ) : null}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {featuredMaterials.map((material) => {
              const selected = String(form.material_type_id) === String(material.id);
              return (
                <button
                  key={material.id}
                  type="button"
                  onClick={() => selectMaterial(material.id, false)}
                  className={`relative flex min-h-[7.5rem] flex-col items-center justify-center gap-3 rounded-2xl border-2 px-4 py-5 text-center transition ${
                    selected
                      ? "border-blue-500 bg-blue-50 shadow-sm"
                      : "border-slate-200 bg-[#C5C8CF] hover:border-blue-200 hover:bg-slate-50"
                  }`}
                >
                  {selected ? (
                    <span className="absolute right-3 top-3 flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-white">
                      <Check className="h-3.5 w-3.5" aria-hidden="true" />
                    </span>
                  ) : null}
                  <span
                    className={`flex h-12 w-12 items-center justify-center rounded-full ${
                      selected
                        ? "bg-blue-600 text-white"
                        : "bg-slate-100 text-slate-500"
                    }`}
                  >
                    <Hexagon className="h-6 w-6" aria-hidden="true" />
                  </span>
                  <span className="text-sm font-semibold text-slate-900">
                    {material.code}
                  </span>
                </button>
              );
            })}

            {otherMaterials.length ? (
              <button
                type="button"
                onClick={() => {
                  setShowOtherMaterials(true);
                  if (
                    featuredMaterials.some(
                      (item) => String(item.id) === String(form.material_type_id)
                    )
                  ) {
                    setForm((prev) => ({ ...prev, material_type_id: "" }));
                  }
                }}
                className={`relative flex min-h-[7.5rem] flex-col items-center justify-center gap-3 rounded-2xl border-2 px-4 py-5 text-center transition ${
                  showOtherMaterials ||
                  otherMaterials.some(
                    (item) => String(item.id) === String(form.material_type_id)
                  )
                    ? "border-blue-500 bg-blue-50 shadow-sm"
                    : "border-slate-200 bg-[#C5C8CF] hover:border-blue-200 hover:bg-slate-50"
                }`}
              >
                <span className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-500">
                  <Grid2X2 className="h-6 w-6" aria-hidden="true" />
                </span>
                <span className="text-sm font-semibold text-slate-900">
                  {t("forms.productionStart.otherMaterial")}
                </span>
              </button>
            ) : null}
          </div>

          {showOtherMaterials && otherMaterials.length ? (
            <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
              {otherMaterials.map((material) => {
                const selected =
                  String(form.material_type_id) === String(material.id);
                return (
                  <button
                    key={material.id}
                    type="button"
                    onClick={() => selectMaterial(material.id, true)}
                    className={`flex min-h-12 items-center justify-between rounded-xl border px-4 text-left text-sm font-semibold transition ${
                      selected
                        ? "border-blue-500 bg-blue-50 text-blue-900"
                        : "border-slate-200 bg-[#C5C8CF] text-slate-700 hover:border-blue-200"
                    }`}
                  >
                    {material.code}
                    {selected ? <Check className="h-4 w-4" /> : null}
                  </button>
                );
              })}
            </div>
          ) : null}
        </section>

        <section className="rounded-3xl border border-slate-400/30 bg-[#C5C8CF] p-4 sm:p-5">
          <StepHeader
            number={2}
            title={t("forms.common.questions.runComment")}
            subtitle={t("forms.productionStart.stepOptionalHint")}
            action={
              <button
                type="button"
                onClick={() => setShowOptional((prev) => !prev)}
                className="text-sm font-semibold text-blue-600 hover:text-blue-700"
              >
                {showOptional
                  ? t("forms.productionStart.hideOptional")
                  : t("forms.productionStart.showOptional")}
              </button>
            }
          />

          {showOptional ? (
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <div className="mb-2 text-sm font-semibold text-[#1E4FD6]">
                  {t("forms.common.questions.isTrial")}
                </div>
                <div className="inline-flex rounded-xl border border-slate-200 bg-slate-50 p-1">
                  {["Yes", "No"].map((value) => {
                    const selected = form.is_trial === value;
                    return (
                      <button
                        key={value}
                        type="button"
                        onClick={() =>
                          setForm((prev) => ({ ...prev, is_trial: value }))
                        }
                        className={`min-h-10 min-w-20 rounded-lg px-4 text-sm font-semibold transition ${
                          selected
                            ? "bg-blue-600 text-white shadow-sm"
                            : "text-slate-600 hover:bg-white"
                        }`}
                      >
                        {value === "Yes" ? t("common.yes") : t("common.no")}
                      </button>
                    );
                  })}
                </div>
              </div>

              <label className="flex min-w-0 flex-col gap-1.5">
                <span className="text-sm font-semibold text-[#1E4FD6]">
                  {t("forms.common.questions.recipeNumber")}
                </span>
                <input
                  type="text"
                  value={form.recipe_number}
                  onChange={(event) =>
                    setForm((prev) => ({
                      ...prev,
                      recipe_number: event.target.value,
                    }))
                  }
                  placeholder={t("forms.productionStart.recipePlaceholder")}
                  className="min-h-11 w-full rounded-xl border border-slate-200 px-3 text-sm outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                />
              </label>

              <label className="flex min-w-0 flex-col gap-1.5">
                <span className="text-sm font-semibold text-[#1E4FD6]">
                  {t("forms.common.questions.productionOrder")}
                </span>
                <input
                  value={form.production_order}
                  onChange={(event) =>
                    setForm((prev) => ({
                      ...prev,
                      production_order: event.target.value,
                    }))
                  }
                  placeholder={t("forms.productionStart.productionOrderPlaceholder")}
                  className="min-h-11 w-full rounded-xl border border-slate-200 px-3 text-sm outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                />
              </label>

              <label className="flex min-w-0 flex-col gap-1.5 sm:col-span-2">
                <span className="text-sm font-medium text-slate-700">
                  {t("forms.productionStart.commentOptional")}
                </span>
                <textarea
                  value={form.comment}
                  maxLength={COMMENT_MAX}
                  onChange={(event) =>
                    setForm((prev) => ({
                      ...prev,
                      comment: event.target.value,
                    }))
                  }
                  rows={3}
                  placeholder={t("forms.productionStart.commentPlaceholder")}
                  className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                />
                <span className="self-end text-xs text-slate-400">
                  {form.comment.length} / {COMMENT_MAX}
                </span>
              </label>
            </div>
          ) : null}
        </section>

        <section className="rounded-3xl border border-slate-400/30 bg-[#C5C8CF] p-4 sm:p-5">
          <StepHeader
            number={3}
            title={t("forms.productionStart.stepReviewTitle")}
            subtitle={t("forms.productionStart.stepReviewHint")}
          />

          <div className="mb-5 grid grid-cols-2 gap-4 rounded-2xl bg-slate-50 px-4 py-4 lg:grid-cols-4">
            <SummaryItem
              icon={Hexagon}
              label={t("forms.common.materialType")}
              value={selectedMaterial?.code}
            />
            <SummaryItem
              icon={FileText}
              label={t("forms.productionStart.recipeShort")}
              value={form.recipe_number?.trim() || "—"}
            />
            <SummaryItem
              icon={Beaker}
              label={t("common.trial")}
              value={trialLabel}
            />
            <SummaryItem
              icon={MessageSquareText}
              label={t("common.comment")}
              value={form.comment?.trim() || "—"}
            />
          </div>

          {errors.context ? (
            <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">
              {errors.context}
            </div>
          ) : null}

          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex min-h-12 flex-1 items-center justify-center gap-2 rounded-[10px] bg-[#1E4FD6] px-6 text-sm font-semibold text-white shadow-sm transition hover:bg-[#1A44B8] disabled:opacity-60"
            >
              <Play className="h-5 w-5 fill-white" aria-hidden="true" />
              {submitting
                ? t("common.saving")
                : editingId
                  ? t("forms.common.updateEntry")
                  : t("forms.common.captureNow")}
            </button>
            {editingId ? (
              <button
                type="button"
                onClick={resetForm}
                className="min-h-14 rounded-2xl border border-slate-400/40 bg-[#C5C8CF] px-5 text-sm font-semibold text-slate-900 transition hover:bg-white sm:w-auto"
              >
                {t("forms.common.cancelEdit")}
              </button>
            ) : null}
          </div>
        </section>
      </form>

      <div className="flex items-start gap-3 rounded-2xl border border-sky-100 bg-sky-50 px-4 py-3 text-sm text-sky-900">
        <Lightbulb className="mt-0.5 h-5 w-5 shrink-0 text-sky-600" aria-hidden="true" />
        <p>{t("forms.productionStart.tip")}</p>
      </div>

      <section className="rounded-3xl border border-slate-400/30 bg-[#C5C8CF] p-4 sm:p-5">
        <div className="mb-1 flex items-center gap-2">
          <Info className="h-4 w-4 text-slate-400" aria-hidden="true" />
          <h2 className="text-base font-semibold text-slate-900">
            {t("forms.common.recentEntries")}
          </h2>
        </div>
        <FormRecentEntries
          entries={entries}
          columns={columns}
          runsById={runsById}
          loading={entriesLoading}
          onEdit={onEdit}
          onComplete={onComplete}
          completingId={completingId}
          onDelete={onDelete}
          deletingId={deletingId}
          getRunForEntry={getRunForEntry}
          canEdit={canEditProductionStart}
          canComplete={canEditProductionStart}
          canDelete={canEditProductionStart}
          hideHeader
        />
      </section>
    </div>
  );
}
