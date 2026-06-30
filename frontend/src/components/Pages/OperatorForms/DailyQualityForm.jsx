import { useState } from "react";
import toast from "react-hot-toast";
import safeApi, { ENDPOINTS } from "../../../api/safeApi";
import { useFormOptions, useProductionRuns } from "../../../hooks/useSunporData";
import { Field, FormCard, inputClass, toLocalInputValue } from "./formUi";

export default function DailyQualityForm() {
  const { options, loading } = useFormOptions();
  const { runs } = useProductionRuns();
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    production_run_id: "",
    shift: "",
    input_time: toLocalInputValue(),
    open_holes_percent: "",
    sieve_distribution_percent: "",
    foaming_behavior: "",
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
      await safeApi.post(ENDPOINTS.dailyQuality, {
        production_run_id: Number(form.production_run_id),
        shift: form.shift,
        input_time: new Date(form.input_time).toISOString(),
        open_holes_percent: Number(form.open_holes_percent),
        sieve_distribution_percent: Number(form.sieve_distribution_percent),
        foaming_behavior: form.foaming_behavior,
        comment: form.comment || null,
      });
      toast.success("Daily quality data saved");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to save quality data");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="text-slate-500">Loading...</div>;

  return (
    <FormCard
      title="Daily Quality Data"
      description="Enter open holes, sieve analysis, and foaming behavior."
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

        <Field label="Shift" required>
          <select name="shift" value={form.shift} onChange={onChange} className={inputClass}>
            <option value="">Select...</option>
            {(options?.shifts || []).map((item) => (
              <option key={item.id} value={item.name}>
                {item.name}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Input Time" required>
          <input
            type="datetime-local"
            name="input_time"
            value={form.input_time}
            onChange={onChange}
            className={inputClass}
          />
        </Field>

        <Field label="Open Holes %" required>
          <input
            type="number"
            step="0.01"
            name="open_holes_percent"
            value={form.open_holes_percent}
            onChange={onChange}
            className={inputClass}
          />
        </Field>

        <Field label="Sieve Distribution %" required>
          <input
            type="number"
            step="0.01"
            name="sieve_distribution_percent"
            value={form.sieve_distribution_percent}
            onChange={onChange}
            className={inputClass}
          />
        </Field>

        <Field label="Foaming Behavior" required>
          <select
            name="foaming_behavior"
            value={form.foaming_behavior}
            onChange={onChange}
            className={inputClass}
          >
            <option value="">Select...</option>
            {(options?.dropdowns?.foaming_behavior || []).map((item) => (
              <option key={item.id} value={item.value}>
                {item.value}
              </option>
            ))}
          </select>
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
            {submitting ? "Saving..." : "Save Quality Data"}
          </button>
        </div>
      </form>
    </FormCard>
  );
}
