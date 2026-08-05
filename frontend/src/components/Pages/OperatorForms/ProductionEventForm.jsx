import { Wrench } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import safeApi, { ENDPOINTS } from "../../../api/safeApi";
import { useRecentEntries } from "../../../hooks/useRecentEntries";
import { useDeleteEntry } from "../../../hooks/useDeleteEntry";
import { useFormOptions, useProductionRuns } from "../../../hooks/useSunporData";
import { getApiErrorMessage } from "../../../utils/apiError";
import { translateDropdownValue } from "../../../utils/dropdownLabels";
import FormRecentEntries from "./FormRecentEntries";
import { getProductionEventColumns } from "./formEntryColumns";
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

function resolveLevel3OptionsKey(level3OptionsKey, level2) {
  if (typeof level3OptionsKey === "function") {
    return level3OptionsKey(level2);
  }
  return level3OptionsKey;
}

function createEventForm(defaultLevel1) {
  return {
    production_run_id: "",
    event_time: toLocalInputValue(),
    level_1: defaultLevel1,
    level_2: "",
    level_3: "",
    reason: "",
    comment: "",
  };
}

function entryToEventForm(entry) {
  return {
    production_run_id: String(entry.production_run_id),
    event_time: toLocalInputValue(new Date(entry.event_time)),
    level_1: entry.level_1,
    level_2: entry.level_2,
    level_3: entry.level_3 || "",
    reason: entry.reason || "",
    comment: entry.comment || "",
  };
}

export default function ProductionEventForm({
  title,
  description,
  defaultLevel1,
  level2OptionsKey,
  level3OptionsKey,
  level3Required = true,
  icon: HeroIcon = Wrench,
}) {
  const { t } = useTranslation();
  const { options, loading, error } = useFormOptions();
  const { runs, loading: runsLoading, error: runsError } = useProductionRuns(50, {
    runningOnly: true,
  });
  const [submitting, setSubmitting] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [form, setForm] = useState(() => createEventForm(defaultLevel1));
  const [errors, setErrors] = useState({});

  const entryFilter = useCallback(
    (entry) => entry.level_1 === defaultLevel1,
    [defaultLevel1]
  );

  const {
    entries,
    runsById,
    loading: entriesLoading,
  } = useRecentEntries(ENDPOINTS.productionEvents, {
    filter: entryFilter,
    sortKeys: ["event_time", "created_at"],
    refreshKey,
  });

  const columns = useMemo(() => getProductionEventColumns(t), [t]);

  const runOptions = useMemo(
    () => mergeRunsForSelect(runs, runsById, form.production_run_id),
    [runs, runsById, form.production_run_id]
  );

  const selectedRun = useMemo(
    () => getSelectedRun(runOptions, form.production_run_id),
    [runOptions, form.production_run_id]
  );

  const activeLevel3Key = resolveLevel3OptionsKey(level3OptionsKey, form.level_2);
  const level2Options = options?.dropdowns?.[level2OptionsKey] || [];
  const level3Options = activeLevel3Key ? options?.dropdowns?.[activeLevel3Key] || [] : [];

  const resetForm = useCallback(() => {
    const next = createEventForm(defaultLevel1);
    if (runs.length === 1) {
      next.production_run_id = String(runs[0].id);
    }
    setForm(next);
    setEditingId(null);
    setErrors({});
  }, [defaultLevel1, runs]);

  useEffect(() => {
    if (runs.length === 1 && !form.production_run_id && !editingId) {
      setForm((prev) => ({ ...prev, production_run_id: String(runs[0].id) }));
    }
  }, [runs, form.production_run_id, editingId]);

  const onChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => {
      const next = { ...prev, [name]: value };
      if (name === "level_2") {
        next.level_3 = "";
      }
      return next;
    });
    setErrors((prev) => {
      if (!prev[name] && !(name === "level_2" && prev.level_3)) {
        return prev;
      }
      const next = { ...prev };
      delete next[name];
      if (name === "level_2") {
        delete next.level_3;
      }
      return next;
    });
  };

  const validate = () => {
    const nextErrors = {};

    if (!parseProductionRunId(form.production_run_id)) {
      nextErrors.production_run_id = t("forms.common.productionRunRequired");
    }
    if (!form.event_time) {
      nextErrors.event_time = t("forms.common.eventTimeRequired");
    }
    if (!form.level_2) {
      nextErrors.level_2 = t("forms.common.level2Required");
    }
    if (level3Required && !form.level_3) {
      nextErrors.level_3 = t("forms.common.level3Required");
    }

    return nextErrors;
  };

  const onEdit = (entry) => {
    setEditingId(entry.id);
    setForm(entryToEventForm(entry));
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const onCancelEdit = () => {
    resetForm();
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
    ENDPOINTS.productionEvents,
    handleDeleted
  );

  const buildPayload = (productionRunId) => {
    const level3Value = form.level_3 || (level3Required ? "" : form.level_2);

    return {
      production_run_id: productionRunId,
      event_time: displayInputToUtcIso(form.event_time),
      level_1: form.level_1,
      level_2: form.level_2,
      level_3: level3Value,
      reason: form.reason || null,
      comment: form.comment || null,
      operator_id: options?.current_user_id,
    };
  };

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
      const payload = buildPayload(productionRunId);

      if (editingId) {
        await safeApi.put(`${ENDPOINTS.productionEvents}/${editingId}`, payload);
        toast.success(t("forms.common.updateSuccess"));
      } else {
        await safeApi.post(ENDPOINTS.productionEvents, payload);
        toast.success(t("forms.events.success"));
      }

      resetForm();
      setRefreshKey((value) => value + 1);
    } catch (submitError) {
      toast.error(
        getApiErrorMessage(
          submitError,
          editingId ? t("forms.common.updateError") : t("forms.events.error")
        )
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (loading || runsLoading) {
    return (
      <FormLoadState
        loading
        loadingLabel={t("forms.common.loadingOptions")}
      />
    );
  }

  if (error || runsError) {
    return <FormLoadState error={error || runsError} />;
  }

  const runLabel = selectedRun
    ? t("forms.common.runOption", { id: selectedRun.id })
    : "—";
  const lineName = getLineName(options, selectedRun?.production_line_id);
  const shiftName = getShiftName(options, selectedRun?.shift_id);

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
              icon={HeroIcon}
              title={title}
              description={description}
            />
          }
          footer={
            <QuestionnaireFooter
              submitting={submitting}
              editing={Boolean(editingId)}
              submitLabel={t("forms.common.captureNow")}
              updateLabel={t("forms.common.updateEntry")}
              savingLabel={t("common.saving")}
              onCancel={editingId ? onCancelEdit : undefined}
              cancelLabel={
                editingId ? t("forms.common.cancelEdit") : t("common.cancel")
              }
              showCancel={Boolean(editingId)}
            />
          }
        >
          <QuestionnaireContext
            items={[
              { label: t("forms.common.productionRun"), value: runLabel },
              { label: t("forms.common.productionLine"), value: lineName },
              { label: t("forms.common.shift"), value: shiftName },
              {
                label: t("forms.common.operator"),
                value: options?.current_user?.name,
              },
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
                onChange={onChange}
                error={errors.production_run_id}
                emptyMessage={t("forms.common.noRunningRuns")}
              />
            </QuestionCell>

            <QuestionCell
              number={2}
              question={t("forms.common.questions.eventTime")}
              required
              error={errors.event_time}
            >
              <input
                type="datetime-local"
                name="event_time"
                value={form.event_time}
                onChange={onChange}
                aria-invalid={errors.event_time ? "true" : undefined}
                className={getInputClass(Boolean(errors.event_time))}
              />
            </QuestionCell>
          </QuestionnaireGrid>

          <QuestionnaireGrid>
            <QuestionCell
              number={3}
              question={t("forms.common.questions.level2")}
              required
              error={errors.level_2}
            >
              <select
                name="level_2"
                value={form.level_2}
                onChange={onChange}
                aria-invalid={errors.level_2 ? "true" : undefined}
                className={getInputClass(Boolean(errors.level_2))}
              >
                <option value="">{t("forms.common.pleaseSelect")}</option>
                {level2Options.map((item) => (
                  <option key={item.id} value={item.value}>
                    {translateDropdownValue(t, item.value)}
                  </option>
                ))}
              </select>
            </QuestionCell>

            {level3Required ? (
              <QuestionCell
                number={4}
                question={t("forms.common.questions.level3")}
                required
                error={errors.level_3}
              >
                <select
                  name="level_3"
                  value={form.level_3}
                  onChange={onChange}
                  disabled={!form.level_2}
                  aria-invalid={errors.level_3 ? "true" : undefined}
                  className={getInputClass(Boolean(errors.level_3))}
                >
                  <option value="">{t("forms.common.pleaseSelect")}</option>
                  {level3Options.map((item) => (
                    <option key={item.id} value={item.value}>
                      {translateDropdownValue(t, item.value)}
                    </option>
                  ))}
                </select>
              </QuestionCell>
            ) : (
              <QuestionCell
                number={4}
                question={t("forms.common.questions.reason")}
              >
                <input
                  name="reason"
                  value={form.reason}
                  onChange={onChange}
                  className={getInputClass(false)}
                  placeholder={t("forms.common.questions.reason")}
                />
              </QuestionCell>
            )}
          </QuestionnaireGrid>

          {level3Required ? (
            <QuestionRow number={5} question={t("forms.common.questions.reason")}>
              <input
                name="reason"
                value={form.reason}
                onChange={onChange}
                className={getInputClass(false)}
                placeholder={t("forms.common.questions.reason")}
              />
            </QuestionRow>
          ) : null}

          <QuestionRow
            number={level3Required ? 6 : 5}
            question={t("forms.common.questions.comment")}
          >
            <textarea
              name="comment"
              value={form.comment}
              onChange={onChange}
              rows={3}
              className={getInputClass(false)}
              placeholder={t("forms.common.questions.comment")}
            />
          </QuestionRow>
        </QuestionnaireCard>
      </form>

      <RecentEntriesCard
        title={t("forms.common.recentEntries")}
        hint={t("forms.common.recentEntriesHint")}
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
