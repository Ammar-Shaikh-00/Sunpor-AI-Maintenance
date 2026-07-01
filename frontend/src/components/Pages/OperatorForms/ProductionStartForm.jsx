import { useState } from "react";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import safeApi, { ENDPOINTS } from "../../../api/safeApi";
import { useFormOptions } from "../../../hooks/useSunporData";
import { Field, FormCard, FormLoadState, inputClass, toLocalInputValue } from "./formUi";

export default function ProductionStartForm() {
  const { t } = useTranslation();
  const { options, loading, error } = useFormOptions();
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    company_id: "",
    production_line_id: "",
    material_type_id: "",
    shift_id: "",
    is_trial: "No",
    start_time: toLocalInputValue(),
    comment: "",
  });

  if (loading || error) {
    return (
      <FormLoadState
        loading={loading}
        error={error}
        loadingLabel={t("forms.common.loadingOptions")}
      />
    );
  }

  const onChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);

    try {
      const payload = {
        company_id: Number(form.company_id),
        production_line_id: Number(form.production_line_id),
        material_type_id: Number(form.material_type_id),
        shift_id: Number(form.shift_id),
        operator_id: options?.current_user_id,
        is_trial: form.is_trial === "Yes",
        start_time: new Date(form.start_time).toISOString(),
        comment: form.comment || null,
        status: "CREATED",
      };

      await safeApi.post(ENDPOINTS.productionRuns, payload);
      toast.success(t("forms.productionStart.success"));
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("forms.productionStart.error"));
    } finally {
      setSubmitting(false);
    }
  };

  const trialLabel = (value) =>
    value === "Yes" ? t("common.yes") : value === "No" ? t("common.no") : value;

  return (
    <FormCard
      title={t("forms.productionStart.title")}
      description={t("forms.productionStart.description")}
    >
      <form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-2">
        <Field label={t("forms.common.company")} required>
          <select
            name="company_id"
            value={form.company_id}
            onChange={onChange}
            className={inputClass}
          >
            <option value="">{t("common.select")}</option>
            {(options?.companies || []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </Field>

        <Field label={t("forms.common.productionLine")} required>
          <select
            name="production_line_id"
            value={form.production_line_id}
            onChange={onChange}
            className={inputClass}
          >
            <option value="">{t("common.select")}</option>
            {(options?.production_lines || []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </Field>

        <Field label={t("forms.common.materialType")} required>
          <select
            name="material_type_id"
            value={form.material_type_id}
            onChange={onChange}
            className={inputClass}
          >
            <option value="">{t("common.select")}</option>
            {(options?.material_types || []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.code}
              </option>
            ))}
          </select>
        </Field>

        <Field label={t("forms.common.shift")} required>
          <select
            name="shift_id"
            value={form.shift_id}
            onChange={onChange}
            className={inputClass}
          >
            <option value="">{t("common.select")}</option>
            {(options?.shifts || []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </Field>

        <Field label={t("common.trial")}>
          <select
            name="is_trial"
            value={form.is_trial}
            onChange={onChange}
            className={inputClass}
          >
            {(options?.dropdowns?.trial_option || [{ value: "No" }, { value: "Yes" }]).map(
              (item) => (
                <option key={item.value} value={item.value}>
                  {trialLabel(item.value)}
                </option>
              )
            )}
          </select>
        </Field>

        <Field label={t("forms.common.startTime")} required>
          <input
            type="datetime-local"
            name="start_time"
            value={form.start_time}
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
            className="rounded-xl bg-violet-600 px-5 py-3 text-sm font-semibold text-white hover:bg-violet-700 disabled:opacity-60"
          >
            {submitting ? t("common.saving") : t("forms.productionStart.submit")}
          </button>
        </div>
      </form>
    </FormCard>
  );
}
