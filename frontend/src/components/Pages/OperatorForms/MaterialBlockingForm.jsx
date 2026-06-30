import { useState } from "react";
import toast from "react-hot-toast";
import safeApi, { ENDPOINTS } from "../../../api/safeApi";
import { useFormOptions, useProductionRuns } from "../../../hooks/useSunporData";
import { Field, FormCard, inputClass, toLocalInputValue } from "./formUi";

export default function MaterialBlockingForm() {
  const { options, loading } = useFormOptions();
  const { runs } = useProductionRuns();
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
      toast.success("Material block saved");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to save material block");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="text-slate-500">Loading...</div>;

  return (
    <FormCard
      title="Subsequent Material Blocking"
      description="Record a later-identified problematic production period."
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

        <Field label="Reason" required>
          <select name="reason" value={form.reason} onChange={onChange} className={inputClass}>
            <option value="">Select...</option>
            {(options?.dropdowns?.material_block_reason || []).map((item) => (
              <option key={item.id} value={item.value}>
                {item.value}
              </option>
            ))}
          </select>
        </Field>

        <Field label="From" required>
          <input
            type="datetime-local"
            name="from_time"
            value={form.from_time}
            onChange={onChange}
            className={inputClass}
          />
        </Field>

        <Field label="To" required>
          <input
            type="datetime-local"
            name="to_time"
            value={form.to_time}
            onChange={onChange}
            className={inputClass}
          />
        </Field>

        <Field label="Affected Material" required>
          <input
            name="affected_material"
            value={form.affected_material}
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
            {submitting ? "Saving..." : "Save Material Block"}
          </button>
        </div>
      </form>
    </FormCard>
  );
}
