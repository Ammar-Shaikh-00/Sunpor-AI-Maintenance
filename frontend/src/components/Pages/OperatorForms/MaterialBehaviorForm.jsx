import { useState } from "react";
import toast from "react-hot-toast";
import safeApi, { ENDPOINTS } from "../../../api/safeApi";
import { useFormOptions, useProductionRuns } from "../../../hooks/useSunporData";
import { Field, FormCard, inputClass, toLocalInputValue } from "./formUi";

export default function MaterialBehaviorForm() {
  const { options, loading } = useFormOptions();
  const { runs } = useProductionRuns();
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    production_run_id: "",
    event_time: toLocalInputValue(),
    behavior_type: "",
    severity: "1",
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
      await safeApi.post(ENDPOINTS.materialBehavior, {
        production_run_id: Number(form.production_run_id),
        event_time: new Date(form.event_time).toISOString(),
        behavior_type: form.behavior_type,
        severity: Number(form.severity),
        comment: form.comment || null,
        operator_id: options?.current_user_id,
      });
      toast.success("Material behavior saved");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to save material behavior");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="text-slate-500">Loading...</div>;

  return (
    <FormCard
      title="Material Behavior"
      description="Record early quality observations from production."
    >
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
                Run #{run.id}
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

        <Field label="Behavior Type" required>
          <select
            name="behavior_type"
            value={form.behavior_type}
            onChange={onChange}
            className={inputClass}
          >
            <option value="">Select...</option>
            {(options?.dropdowns?.material_behavior_type || []).map((item) => (
              <option key={item.id} value={item.value}>
                {item.value}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Severity (1-5)" required>
          <input
            type="number"
            min="1"
            max="5"
            name="severity"
            value={form.severity}
            onChange={onChange}
            className={inputClass}
          />
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
            className="rounded-xl bg-violet-600 px-5 py-3 text-sm font-semibold text-white"
          >
            {submitting ? "Saving..." : "Save Material Behavior"}
          </button>
        </div>
      </form>
    </FormCard>
  );
}
