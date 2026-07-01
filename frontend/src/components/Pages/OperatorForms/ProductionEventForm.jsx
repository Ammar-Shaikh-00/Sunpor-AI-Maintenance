import { useState } from "react";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import safeApi, { ENDPOINTS } from "../../../api/safeApi";
import { useFormOptions, useProductionRuns } from "../../../hooks/useSunporData";
import { Field, FormCard, FormLoadState, inputClass, toLocalInputValue } from "./formUi";

export default function ProductionEventForm({
  title,
  description,
  defaultLevel1,
  level2OptionsKey,
  level3OptionsKey,
}) {
  const { t } = useTranslation();
  const { options, loading, error } = useFormOptions();
  const { runs, loading: runsLoading, error: runsError } = useProductionRuns();
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    production_run_id: "",
    event_time: toLocalInputValue(),
    level_1: defaultLevel1,
    level_2: "",
    level_3: "",
    reason: "",
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
      await safeApi.post(ENDPOINTS.productionEvents, {
        production_run_id: Number(form.production_run_id),
        event_time: new Date(form.event_time).toISOString(),
        level_1: form.level_1,
        level_2: form.level_2,
        level_3: form.level_3,
        reason: form.reason || null,
        comment: form.comment || null,
        operator_id: options?.current_user_id,
      });
      toast.success(t("forms.events.success"));
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("forms.events.error"));
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

  const level2Options = options?.dropdowns?.[level2OptionsKey] || [];
  const level3Options = options?.dropdowns?.[level3OptionsKey] || [];

  return (
    <FormCard title={title} description={description}>
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
                {t("forms.common.runStatusOption", { id: run.id, status: run.status })}
              </option>
            ))}
          </select>
        </Field>

        <Field label={t("forms.common.eventTime")} required>
          <input
            type="datetime-local"
            name="event_time"
            value={form.event_time}
            onChange={onChange}
            className={inputClass}
          />
        </Field>

        <Field label={t("forms.common.level2")} required>
          <select name="level_2" value={form.level_2} onChange={onChange} className={inputClass}>
            <option value="">{t("common.select")}</option>
            {level2Options.map((item) => (
              <option key={item.id} value={item.value}>
                {item.value}
              </option>
            ))}
          </select>
        </Field>

        <Field label={t("forms.common.level3")} required>
          <select name="level_3" value={form.level_3} onChange={onChange} className={inputClass}>
            <option value="">{t("common.select")}</option>
            {level3Options.map((item) => (
              <option key={item.id} value={item.value}>
                {item.value}
              </option>
            ))}
          </select>
        </Field>

        <Field label={t("forms.common.reason")}>
          <input name="reason" value={form.reason} onChange={onChange} className={inputClass} />
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
            {submitting ? t("common.saving") : t("forms.common.saveEvent")}
          </button>
        </div>
      </form>
    </FormCard>
  );
}
