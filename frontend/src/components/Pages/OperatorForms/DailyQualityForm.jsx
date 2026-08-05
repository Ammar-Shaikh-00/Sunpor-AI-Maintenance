import {
  ClipboardList,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import safeApi, { ENDPOINTS } from "../../../api/safeApi";
import { useRecentEntries } from "../../../hooks/useRecentEntries";
import { useDeleteEntry } from "../../../hooks/useDeleteEntry";
import { useFormOptions, useProductionRuns } from "../../../hooks/useSunporData";
import { getApiErrorMessage } from "../../../utils/apiError";
import FormRecentEntries from "./FormRecentEntries";
import {
  FormLoadState,
  getInputClass,
  getLineName,
  getSelectedRun,
  getShiftName,
  mergeRunsForSelect,
  parseProductionRunId,
  displayInputToUtcIso,
  toLocalInputValue,
} from "./formUi";
import {
  QuestionnaireCard,
  QuestionnaireContext,
  QuestionnaireFooter,
  QuestionnaireGrid,
  QuestionnaireHeader,
  QuestionnaireRunSelect,
  QuestionnaireShell,
  QuestionCell,
  QuestionRow,
  RecentEntriesCard,
} from "./questionnaireFormUi";
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
    <QuestionnaireShell>
      {editingId ? (
        <div className="rounded-[10px] border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {t("forms.common.editingEntry", { id: editingId })}
        </div>
      ) : null}

      <form onSubmit={onSubmit} noValidate>
        <QuestionnaireCard
          header={
            <QuestionnaireHeader
              icon={ClipboardList}
              title={t("forms.dailyQuality.title")}
              description={t("forms.dailyQuality.description")}
            />
          }
          footer={
            <QuestionnaireFooter
              submitting={submitting}
              editing={Boolean(editingId)}
              submitLabel={t("forms.common.captureNow")}
              updateLabel={t("forms.common.updateEntry")}
              savingLabel={t("common.saving")}
              onCancel={editingId ? resetForm : undefined}
              cancelLabel={
                editingId ? t("forms.common.cancelEdit") : t("common.cancel")
              }
              showCancel={Boolean(editingId)}
            />
          }
        >
          <QuestionnaireContext
            items={[
              {
                label: t("forms.common.productionRun"),
                value: selectedRun
                  ? t("forms.dailyQuality.runLabel", { id: selectedRun.id })
                  : "—",
              },
              { label: t("forms.common.productionLine"), value: lineName },
              { label: t("forms.common.shift"), value: form.shift || "—" },
              { label: t("forms.common.inputTime"), value: `${dateLabel} ${clockLabel}` },
            ]}
          />

          <QuestionnaireGrid>
            <QuestionCell
              number={1}
              question={t("forms.common.questions.productionRun")}
              required
              error={errors.production_run_id}
            >
              <QuestionnaireRunSelect
                runs={runOptions}
                value={form.production_run_id}
                onChange={(event) => {
                  setForm((prev) => ({
                    ...prev,
                    production_run_id: event.target.value,
                  }));
                  clearError("production_run_id");
                }}
                error={errors.production_run_id}
                emptyMessage={t("forms.common.noRunningRuns")}
              />
            </QuestionCell>

            <QuestionCell
              number={2}
              question={t("forms.common.questions.shift")}
              required
              error={errors.shift}
            >
              <select
                value={form.shift}
                onChange={(event) => {
                  setForm((prev) => ({ ...prev, shift: event.target.value }));
                  clearError("shift");
                }}
                className={getInputClass(Boolean(errors.shift))}
              >
                <option value="">{t("forms.common.pleaseSelect")}</option>
                {(options?.shifts || []).map((item) => (
                  <option key={item.id} value={item.name}>
                    {item.name}
                  </option>
                ))}
              </select>
            </QuestionCell>
          </QuestionnaireGrid>

          <QuestionRow
            number={3}
            question={t("forms.common.questions.inputTime")}
            required
            error={errors.input_time}
          >
            <input
              type="datetime-local"
              value={form.input_time}
              onChange={(event) => {
                setForm((prev) => ({ ...prev, input_time: event.target.value }));
                clearError("input_time");
              }}
              className={getInputClass(Boolean(errors.input_time))}
            />
          </QuestionRow>

          <QuestionnaireGrid columns={3}>
            <QuestionCell
              number={4}
              question={t("forms.common.questions.openHoles")}
              required
              error={errors.open_holes_percent}
            >
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
            </QuestionCell>

            <QuestionCell
              number={5}
              question={t("forms.common.questions.sieveDistribution")}
              required
              error={errors.sieve_distribution_percent}
            >
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
            </QuestionCell>

            <QuestionCell
              number={6}
              question={t("forms.common.questions.foamingBehavior")}
              required
              error={errors.foaming_behavior}
              className="sm:col-span-1 sm:border-r-0"
            >
              <FoamingBehaviorCard
                value={form.foaming_behavior}
                options={foamingOptions}
                onChange={(value) => {
                  setForm((prev) => ({ ...prev, foaming_behavior: value }));
                  clearError("foaming_behavior");
                }}
              />
            </QuestionCell>
          </QuestionnaireGrid>

          <QuestionRow number={7} question={t("forms.common.questions.comment")}>
            <textarea
              value={form.comment}
              maxLength={COMMENT_MAX}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, comment: event.target.value }))
              }
              rows={3}
              placeholder={t("forms.dailyQuality.commentPlaceholder")}
              className={getInputClass(false)}
            />
            <span className="mt-1 block self-end text-right text-xs text-slate-400">
              {form.comment.length}/{COMMENT_MAX}
            </span>
          </QuestionRow>
        </QuestionnaireCard>
      </form>

      <RecentEntriesCard
        title={t("forms.common.recentEntries")}
        hint={t("forms.dailyQuality.recentHint")}
      >
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
      </RecentEntriesCard>
    </QuestionnaireShell>
  );
}
