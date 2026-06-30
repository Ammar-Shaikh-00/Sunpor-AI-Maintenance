import { useState } from "react";
import toast from "react-hot-toast";
import safeApi, { ENDPOINTS } from "../../../api/safeApi";
import { useFormOptions } from "../../../hooks/useSunporData";
import { Field, FormCard, inputClass, toLocalInputValue } from "./formUi";

export default function ProductionStartForm() {
  const { options, loading } = useFormOptions();
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

  if (loading) {
    return <div className="text-slate-500">Loading form options...</div>;
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
      toast.success("Production run started");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to save production run");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <FormCard
      title="Production Start / Product"
      description="Record the start of a production run with material type and shift."
    >
      <form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-2">
        <Field label="Company" required>
          <select
            name="company_id"
            value={form.company_id}
            onChange={onChange}
            className={inputClass}
          >
            <option value="">Select...</option>
            {(options?.companies || []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Production Line" required>
          <select
            name="production_line_id"
            value={form.production_line_id}
            onChange={onChange}
            className={inputClass}
          >
            <option value="">Select...</option>
            {(options?.production_lines || []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Material Type" required>
          <select
            name="material_type_id"
            value={form.material_type_id}
            onChange={onChange}
            className={inputClass}
          >
            <option value="">Select...</option>
            {(options?.material_types || []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.code}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Shift" required>
          <select
            name="shift_id"
            value={form.shift_id}
            onChange={onChange}
            className={inputClass}
          >
            <option value="">Select...</option>
            {(options?.shifts || []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Trial">
          <select
            name="is_trial"
            value={form.is_trial}
            onChange={onChange}
            className={inputClass}
          >
            {(options?.dropdowns?.trial_option || [{ value: "No" }, { value: "Yes" }]).map(
              (item) => (
                <option key={item.value} value={item.value}>
                  {item.value}
                </option>
              )
            )}
          </select>
        </Field>

        <Field label="Start Time" required>
          <input
            type="datetime-local"
            name="start_time"
            value={form.start_time}
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
            className="rounded-xl bg-violet-600 px-5 py-3 text-sm font-semibold text-white hover:bg-violet-700 disabled:opacity-60"
          >
            {submitting ? "Saving..." : "Start Production Run"}
          </button>
        </div>
      </form>
    </FormCard>
  );
}
