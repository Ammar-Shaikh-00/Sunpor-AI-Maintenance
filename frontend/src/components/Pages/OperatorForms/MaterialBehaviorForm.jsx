import { Microscope } from "lucide-react";
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
import { getMaterialBehaviorColumns } from "./formEntryColumns";
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

function createMaterialBehaviorForm() {
  return {
    production_run_id: "",
    event_time: toLocalInputValue(),
    behavior_type: "",
    severity: "1",
    comment: "",
  };
}

function entryToMaterialBehaviorForm(entry) {
  return {
    production_run_id: String(entry.production_run_id),
    event_time: toLocalInputValue(new Date(entry.event_time)),
    behavior_type: entry.behavior_type,
    severity: String(entry.severity),
    comment: entry.comment || "",
  };
}

export default function MaterialBehaviorForm() {
  const { t } = useTranslation();
  const { options, loading, error } = useFormOptions();
  const { runs, loading: runsLoading, error: runsError } = useProductionRuns(50, {
    runningOnly: true,
  });
  const [submitting, setSubmitting] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [form, setForm] = useState(createMaterialBehaviorForm);
  const [errors, setErrors] = useState({});

  const {
    entries,
    runsById,
    loading: entriesLoading,
  } = useRecentEntries(ENDPOINTS.materialBehavior, {
    sortKeys: ["event_time", "created_at"],
    refreshKey,
  });

  const columns = useMemo(() => getMaterialBehaviorColumns(t), [t]);

  const runOptions = useMemo(
    () => mergeRunsForSelect(runs, runsById, form.production_run_id),
    [runs, runsById, form.production_run_id]
  );

  const selectedRun = useMemo(
    () => getSelectedRun(runOptions, form.production_run_id),
    [runOptions, form.production_run_id]
  );

  const resetForm = useCallback(() => {
    const next = createMaterialBehaviorForm();
    if (runs.length === 1) {
      next.production_run_id = String(runs[0].id);
    }
    setForm(next);
    setEditingId(null);
    setErrors({});
  }, [runs]);

  useEffect(() => {
    if (runs.length === 1 && !form.production_run_id && !editingId) {
      setForm((prev) => ({ ...prev, production_run_id: String(runs[0].id) }));
    }
  }, [runs, form.production_run_id, editingId]);

  const onChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => {
      if (!prev[name]) {
        return prev;
      }
      const next = { ...prev };
      delete next[name];
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
    if (!form.behavior_type) {
      nextErrors.behavior_type = t("forms.common.behaviorTypeRequired");
    }

    const severity = Number(form.severity);
    if (form.severity === "" || Number.isNaN(severity)) {
      nextErrors.severity = t("forms.common.severityRequired");
    } else if (severity < 1 || severity > 5) {
      nextErrors.severity = t("forms.common.severityRange");
    }

    return nextErrors;
  };

  const onEdit = (entry) => {
    setEditingId(entry.id);
    setForm(entryToMaterialBehaviorForm(entry));
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
    ENDPOINTS.materialBehavior,
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
        event_time: displayInputToUtcIso(form.event_time),
        behavior_type: form.behavior_type,
        severity: Number(form.severity),
        comment: form.comment || null,
        operator_id: options?.current_user_id,
      };

      if (editingId) {
        await safeApi.put(`${ENDPOINTS.materialBehavior}/${editingId}`, payload);
        toast.success(t("forms.common.updateSuccess"));
      } else {
        await safeApi.post(ENDPOINTS.materialBehavior, payload);
        toast.success(t("forms.materialBehavior.success"));
      }

      resetForm();
      setRefreshKey((value) => value + 1);
    } catch (submitError) {
      toast.error(
        getApiErrorMessage(
          submitError,
          editingId ? t("forms.common.updateError") : t("forms.materialBehavior.error")
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
        loadingLabel={t("forms.common.loading")}
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
              icon={Microscope}
              title={t("forms.materialBehavior.title")}
              description={t("forms.materialBehavior.description")}
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
              question={t("forms.common.questions.behaviorType")}
              required
              error={errors.behavior_type}
            >
              <select
                name="behavior_type"
                value={form.behavior_type}
                onChange={onChange}
                aria-invalid={errors.behavior_type ? "true" : undefined}
                className={getInputClass(Boolean(errors.behavior_type))}
              >
                <option value="">{t("forms.common.pleaseSelect")}</option>
                {(options?.dropdowns?.material_behavior_type || []).map((item) => (
                  <option key={item.id} value={item.value}>
                    {translateDropdownValue(t, item.value)}
                  </option>
                ))}
              </select>
            </QuestionCell>

            <QuestionCell
              number={4}
              question={t("forms.common.questions.severity")}
              required
              error={errors.severity}
            >
              <input
                type="number"
                min="1"
                max="5"
                name="severity"
                value={form.severity}
                onChange={onChange}
                aria-invalid={errors.severity ? "true" : undefined}
                className={getInputClass(Boolean(errors.severity))}
              />
            </QuestionCell>
          </QuestionnaireGrid>

          <QuestionRow number={5} question={t("forms.common.questions.comment")}>
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
