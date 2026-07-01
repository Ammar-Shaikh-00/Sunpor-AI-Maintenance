import { useState } from "react";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import safeApi, { ENDPOINTS } from "../../../api/safeApi";
import { useFormOptions, useProductionRuns } from "../../../hooks/useSunporData";
import { Field, FormCard, FormLoadState, inputClass, toLocalInputValue } from "./formUi";

export default function MaterialBlockingForm() {
  const { t } = useTranslation();
  const { options, loading, error } = useFormOptions();
  const { runs, loading: runsLoading, error: runsError } = useProductionRuns();
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    production_run_id: "",
    reason: "",
    from_time: toLocalInputValue(),
    to_time: toLocalInputValue(),
    affected_material: "",
    comment: "",
  });

  const onChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);

    try {
      await safeApi.post(ENDPOINTS.materialBlocks, {
        production_run_id: Number(form.production_run_id),
        reason: form.reason,
        from_time: new Date(form.from_time).toISOString(),
        to_time: new Date(form.to_time).toISOString(),
        affected_material: form.affected_material,
        comment: form.comment || null,
        created_by: options?.current_user_id,
      });
      toast.success(t("forms.materialBlocking.success"));
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("forms.materialBlocking.error"));
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

  return (
    <FormCard
      title={t("forms.materialBlocking.title")}
      description={t("forms.materialBlocking.description")}
    >
      <form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-2">
        <Field label={t("forms.common.productionRun")} required>
          <select
            name="production_run_id"
            value={form.production_run_id}
            onChange={onChange}
            className={inputClass}
          >
            <option value="">{t("forms.common.selectRun")}</option>
            {runs.map((run) => (
              <option key={run.id} value={run.id}>
                {t("forms.common.runOption", { id: run.id })}
              </option>
            ))}
          </select>
        </Field>

        <Field label={t("forms.common.reason")} required>
          <select name="reason" value={form.reason} onChange={onChange} className={inputClass}>
            <option value="">{t("common.select")}</option>
            {(options?.dropdowns?.material_block_reason || []).map((item) => (
              <option key={item.id} value={item.value}>
                {item.value}
              </option>
            ))}
          </select>
        </Field>

        <Field label={t("forms.common.from")} required>
          <input
            type="datetime-local"
            name="from_time"
            value={form.from_time}
            onChange={onChange}
            className={inputClass}
          />
        </Field>

        <Field label={t("forms.common.to")} required>
          <input
            type="datetime-local"
            name="to_time"
            value={form.to_time}
            onChange={onChange}
            className={inputClass}
          />
        </Field>

        <Field label={t("forms.common.affectedMaterial")} required>
          <input
            name="affected_material"
            value={form.affected_material}
            onChange={onChange}
            className={inputClass}
          />
        </Field>

        <Field label={t("common.comment")}>
          <textarea
            name="comment"
            value={form.comment}
            onChange={onChange}
            rows={3}
            className={inputClass}
          />
        </Field>

        <div className="md:col-span-2">
          <button
            type="submit"
            disabled={submitting}
            className="rounded-xl bg-violet-600 px-5 py-3 text-sm font-semibold text-white"
          >
            {submitting ? t("common.saving") : t("forms.materialBlocking.submit")}
          </button>
        </div>
      </form>
    </FormCard>
  );
}
