import {
  CalendarClock,
  MessageSquareText,
  Package,
  ShieldAlert,
  TriangleAlert,
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
import { getMaterialBlockingColumns } from "./formEntryColumns";
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
  FormHero,
  FormSection,
  IconField,
  OperatorFormShell,
  RecentEntriesCard,
  RunSelectField,
  SubmitBar,
} from "./operatorFormUi";

function createMaterialBlockingForm() {
  return {
    production_run_id: "",
    reason: "",
    from_time: toLocalInputValue(),
    to_time: toLocalInputValue(),
    affected_material: "",
    comment: "",
  };
}

function entryToMaterialBlockingForm(entry) {
  return {
    production_run_id: String(entry.production_run_id),
    reason: entry.reason,
    from_time: toLocalInputValue(new Date(entry.from_time)),
    to_time: toLocalInputValue(new Date(entry.to_time)),
    affected_material: entry.affected_material,
    comment: entry.comment || "",
  };
}

export default function MaterialBlockingForm() {
  const { t } = useTranslation();
  const { options, loading, error } = useFormOptions();
  const { runs, loading: runsLoading, error: runsError } = useProductionRuns(50, {
    runningOnly: true,
  });
  const [submitting, setSubmitting] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [form, setForm] = useState(createMaterialBlockingForm);
  const [errors, setErrors] = useState({});

  const {
    entries,
    runsById,
    loading: entriesLoading,
  } = useRecentEntries(ENDPOINTS.materialBlocks, {
    sortKeys: ["from_time", "created_at"],
    refreshKey,
  });

  const columns = useMemo(() => getMaterialBlockingColumns(t), [t]);

  const runOptions = useMemo(
    () => mergeRunsForSelect(runs, runsById, form.production_run_id),
    [runs, runsById, form.production_run_id]
  );

  const selectedRun = useMemo(
    () => getSelectedRun(runOptions, form.production_run_id),
    [runOptions, form.production_run_id]
  );

  const resetForm = useCallback(() => {
    const next = createMaterialBlockingForm();
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
      if (!prev[name] && !(name === "to_time" && prev.to_time)) {
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
    if (!form.reason) {
      nextErrors.reason = t("forms.common.reasonRequired");
    }
    if (!form.from_time) {
      nextErrors.from_time = t("forms.common.fromRequired");
    }
    if (!form.to_time) {
      nextErrors.to_time = t("forms.common.toRequired");
    }
    if (
      form.from_time &&
      form.to_time &&
      new Date(form.to_time).getTime() <= new Date(form.from_time).getTime()
    ) {
      nextErrors.to_time = t("forms.common.toAfterFrom");
    }
    if (!form.affected_material.trim()) {
      nextErrors.affected_material = t("forms.common.affectedMaterialRequired");
    }

    return nextErrors;
  };

  const onEdit = (entry) => {
    setEditingId(entry.id);
    setForm(entryToMaterialBlockingForm(entry));
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
    ENDPOINTS.materialBlocks,
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
        reason: form.reason,
        from_time: displayInputToUtcIso(form.from_time),
        to_time: displayInputToUtcIso(form.to_time),
        affected_material: form.affected_material,
        comment: form.comment || null,
        created_by: options?.current_user_id,
      };

      if (editingId) {
        await safeApi.put(`${ENDPOINTS.materialBlocks}/${editingId}`, payload);
        toast.success(t("forms.common.updateSuccess"));
      } else {
        await safeApi.post(ENDPOINTS.materialBlocks, payload);
        toast.success(t("forms.materialBlocking.success"));
      }

      resetForm();
      setRefreshKey((value) => value + 1);
    } catch (submitError) {
      toast.error(
        getApiErrorMessage(
          submitError,
          editingId ? t("forms.common.updateError") : t("forms.materialBlocking.error")
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
    <OperatorFormShell>
      <FormHero
        icon={ShieldAlert}
        title={t("forms.materialBlocking.title")}
        description={t("forms.materialBlocking.description")}
        run={selectedRun}
        runLabel={runLabel}
        lineName={lineName}
        shiftName={shiftName}
        metaItems={[
          { label: t("forms.common.productionRun"), value: runLabel },
          { label: t("forms.common.productionLine"), value: lineName },
          { label: t("forms.common.shift"), value: shiftName },
          {
            label: t("forms.common.operator"),
            value: options?.current_user?.name,
          },
        ]}
      />

      {editingId ? (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {t("forms.common.editingEntry", { id: editingId })}
        </div>
      ) : null}

      <form onSubmit={onSubmit} noValidate className="space-y-5">
        <FormSection title={t("forms.common.detailsSection")}>
          <div className="grid gap-4 sm:grid-cols-2">
            <RunSelectField
              runs={runOptions}
              value={form.production_run_id}
              onChange={onChange}
              error={errors.production_run_id}
              emptyMessage={t("forms.common.noRunningRuns")}
            />

            <IconField
              icon={TriangleAlert}
              label={t("forms.common.reason")}
              required
              error={errors.reason}
              className="sm:col-span-2"
            >
              <select
                name="reason"
                value={form.reason}
                onChange={onChange}
                aria-invalid={errors.reason ? "true" : undefined}
                className={getInputClass(Boolean(errors.reason))}
              >
                <option value="">{t("common.select")}</option>
                {(options?.dropdowns?.material_block_reason || []).map((item) => (
                  <option key={item.id} value={item.value}>
                    {item.value}
                  </option>
                ))}
              </select>
            </IconField>

            <IconField
              icon={CalendarClock}
              label={t("forms.common.from")}
              required
              error={errors.from_time}
            >
              <input
                type="datetime-local"
                name="from_time"
                value={form.from_time}
                onChange={onChange}
                aria-invalid={errors.from_time ? "true" : undefined}
                className={getInputClass(Boolean(errors.from_time))}
              />
            </IconField>

            <IconField
              icon={CalendarClock}
              label={t("forms.common.to")}
              required
              error={errors.to_time}
            >
              <input
                type="datetime-local"
                name="to_time"
                value={form.to_time}
                onChange={onChange}
                aria-invalid={errors.to_time ? "true" : undefined}
                className={getInputClass(Boolean(errors.to_time))}
              />
            </IconField>

            <IconField
              icon={Package}
              label={t("forms.common.affectedMaterial")}
              required
              error={errors.affected_material}
              className="sm:col-span-2"
            >
              <input
                name="affected_material"
                value={form.affected_material}
                onChange={onChange}
                aria-invalid={errors.affected_material ? "true" : undefined}
                className={getInputClass(Boolean(errors.affected_material))}
              />
            </IconField>

            <IconField
              icon={MessageSquareText}
              label={t("common.comment")}
              className="sm:col-span-2"
            >
              <textarea
                name="comment"
                value={form.comment}
                onChange={onChange}
                rows={3}
                className={getInputClass(false)}
              />
            </IconField>
          </div>
        </FormSection>

        <SubmitBar
          submitting={submitting}
          editing={Boolean(editingId)}
          submitLabel={t("forms.materialBlocking.submit")}
          updateLabel={t("forms.common.updateEntry")}
          savingLabel={t("common.saving")}
          onCancel={resetForm}
          cancelLabel={t("forms.common.cancelEdit")}
        />
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
    </OperatorFormShell>
  );
}
