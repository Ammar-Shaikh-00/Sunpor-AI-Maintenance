import { useState } from "react";
import toast from "react-hot-toast";
import safeApi, { ENDPOINTS } from "../../../api/safeApi";
import { useFormOptions, useProductionRuns } from "../../../hooks/useSunporData";
import { Field, FormCard, inputClass, toLocalInputValue } from "./formUi";

export default function ProductionEventForm({
  title,
  description,
  defaultLevel1,
  level2OptionsKey,
  level3OptionsKey,
}) {
  const { options, loading } = useFormOptions();
  const { runs } = useProductionRuns();
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
      toast.success("Event saved");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to save event");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="text-slate-500">Loading form options...</div>;
  }

  const level2Options = options?.dropdowns?.[level2OptionsKey] || [];
  const level3Options = options?.dropdowns?.[level3OptionsKey] || [];

  return (
    <FormCard title={title} description={description}>
      <form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-2">
        <Field label="Production Run" required>
          <select
            name="production_run_id"
            value={form.production_run_id}
            onChange={onChange}
            className={inputClass}
          >
            <option value="">Select run...</option>
            {runs.map((run) => (
              <option key={run.id} value={run.id}>
                Run #{run.id} - {run.status}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Event Time" required>
          <input
            type="datetime-local"
            name="event_time"
            value={form.event_time}
            onChange={onChange}
            className={inputClass}
          />
        </Field>

        <Field label="Level 2" required>
          <select name="level_2" value={form.level_2} onChange={onChange} className={inputClass}>
            <option value="">Select...</option>
            {level2Options.map((item) => (
              <option key={item.id} value={item.value}>
                {item.value}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Level 3" required>
          <select name="level_3" value={form.level_3} onChange={onChange} className={inputClass}>
            <option value="">Select...</option>
            {level3Options.map((item) => (
              <option key={item.id} value={item.value}>
                {item.value}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Reason">
          <input name="reason" value={form.reason} onChange={onChange} className={inputClass} />
        </Field>

        <Field label="Comment">
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
            {submitting ? "Saving..." : "Save Event"}
          </button>
        </div>
      </form>
    </FormCard>
  );
}
