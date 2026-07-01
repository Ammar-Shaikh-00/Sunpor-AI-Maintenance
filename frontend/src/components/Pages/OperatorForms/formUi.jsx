export function FormCard({ title, description, children }) {
  return (
    <section className="rounded-2xl border border-violet-200 bg-white p-6 shadow-sm">
      <div className="mb-5">
        <h2 className="text-xl font-bold text-slate-900">{title}</h2>
        {description ? (
          <p className="mt-1 text-sm text-slate-500">{description}</p>
        ) : null}
      </div>
      {children}
    </section>
  );
}

export function Field({ label, children, required = false }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-sm font-medium text-slate-700">
        {label}
        {required ? <span className="text-rose-500"> *</span> : null}
      </span>
      {children}
    </label>
  );
}

export const inputClass =
  "rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-violet-400 focus:ring-2 focus:ring-violet-100";

export function SelectField({ value, onChange, options, placeholder = "Select..." }) {
  return (
    <select value={value} onChange={onChange} className={inputClass}>
      <option value="">{placeholder}</option>
      {options.map((option) => (
        <option key={option.value || option.id || option} value={option.value || option.id || option}>
          {option.label || option.name || option.code || option.value || option}
        </option>
      ))}
    </select>
  );
}

export function toLocalInputValue(date = new Date()) {
  const offset = date.getTimezoneOffset();
  const local = new Date(date.getTime() - offset * 60 * 1000);
  return local.toISOString().slice(0, 16);
}

export function FormLoadState({ loading, error, loadingLabel, children }) {
  if (loading) {
    return <div className="text-slate-500">{loadingLabel}</div>;
  }

  if (error) {
    return <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</div>;
  }

  return children;
}
