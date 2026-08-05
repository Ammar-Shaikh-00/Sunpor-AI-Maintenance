/**
 * Shared field widgets for schema-driven operator input forms.
 */

const inputClass =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20";

function QuestionShell({ index, label, required, hint, children, error }) {
  return (
    <div className="flex h-full flex-col border border-slate-200 bg-white p-3.5 sm:p-4">
      <div className="mb-3">
        <h3 className="text-sm font-semibold text-[#1E3A8A] sm:text-[0.95rem]">
          {index}. {label}
          {required ? <span className="text-red-500"> *</span> : null}
        </h3>
        {hint ? (
          <p className="mt-0.5 text-xs text-slate-500">({hint})</p>
        ) : null}
      </div>
      <div className="flex flex-1 flex-col gap-2">{children}</div>
      {error ? <p className="mt-2 text-xs font-medium text-red-600">{error}</p> : null}
    </div>
  );
}

function OptionList({ options, renderItem, columns = 2 }) {
  return (
    <div
      className={`grid gap-x-3 gap-y-2 ${
        columns === 1 ? "grid-cols-1" : "grid-cols-1 sm:grid-cols-2"
      }`}
    >
      {options.map((option) => renderItem(option))}
    </div>
  );
}

export function RunSelectField({ field, value, onChange, runs, disabled }) {
  return (
    <select
      className={inputClass}
      value={value ?? ""}
      disabled={disabled}
      onChange={(event) =>
        onChange(event.target.value ? Number(event.target.value) : null)
      }
    >
      <option value="">{field.placeholder || "Bitte auswählen"}</option>
      {runs.map((run) => (
        <option key={run.id} value={run.id}>
          Lauf #{run.id}
          {run.recipe_number ? ` · Rezept ${run.recipe_number}` : ""}
          {run.status ? ` · ${run.status}` : ""}
        </option>
      ))}
    </select>
  );
}

export function EventTimeField({ value, onChange }) {
  const mode = value?.mode || "now";
  return (
    <div className="flex flex-col gap-3">
      <label className="inline-flex items-center gap-2 text-sm text-slate-800">
        <input
          type="radio"
          name="event_time_mode"
          checked={mode === "now"}
          onChange={() => onChange({ ...value, mode: "now" })}
          className="h-4 w-4 accent-blue-600"
        />
        Jetzt (aktuelle Uhrzeit)
      </label>
      <label className="inline-flex items-center gap-2 text-sm text-slate-800">
        <input
          type="radio"
          name="event_time_mode"
          checked={mode === "past"}
          onChange={() => onChange({ ...value, mode: "past" })}
          className="h-4 w-4 accent-blue-600"
        />
        Vergangenen Zeitpunkt auswählen
      </label>
      {mode === "past" ? (
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          <label className="text-xs font-medium text-slate-600">
            Datum
            <input
              type="date"
              className={`${inputClass} mt-1`}
              value={value?.date || ""}
              onChange={(event) =>
                onChange({ ...value, mode: "past", date: event.target.value })
              }
            />
          </label>
          <label className="text-xs font-medium text-slate-600">
            Uhrzeit
            <input
              type="time"
              className={`${inputClass} mt-1`}
              value={value?.time || ""}
              onChange={(event) =>
                onChange({ ...value, mode: "past", time: event.target.value })
              }
            />
          </label>
        </div>
      ) : null}
    </div>
  );
}

export function DateTimeFlagsField({ field, value, onChange }) {
  const flags = field.flags || [];
  const activeFlag = flags.find((flag) => value?.[flag.id]);
  const disabled = Boolean(activeFlag);

  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        <label className="text-xs font-medium text-slate-600">
          Datum
          <input
            type="date"
            className={`${inputClass} mt-1`}
            disabled={disabled}
            value={value?.date || ""}
            onChange={(event) =>
              onChange({ ...value, date: event.target.value })
            }
          />
        </label>
        <label className="text-xs font-medium text-slate-600">
          Uhrzeit
          <input
            type="time"
            className={`${inputClass} mt-1`}
            disabled={disabled}
            value={value?.time || ""}
            onChange={(event) =>
              onChange({ ...value, time: event.target.value })
            }
          />
        </label>
      </div>
      {flags.map((flag) => (
        <label
          key={flag.id}
          className="inline-flex items-center gap-2 text-sm text-slate-800"
        >
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-slate-300 accent-blue-600"
            checked={Boolean(value?.[flag.id])}
            onChange={(event) => {
              const next = { ...(value || {}) };
              flags.forEach((item) => {
                if (item.id !== flag.id) delete next[item.id];
              });
              next[flag.id] = event.target.checked;
              if (event.target.checked) {
                next.date = "";
                next.time = "";
              }
              onChange(next);
            }}
          />
          {flag.label}
        </label>
      ))}
    </div>
  );
}

export function RadioField({ field, value, onChange }) {
  const selected = typeof value === "object" ? value?.value : value;
  const otherText = typeof value === "object" ? value?.other || "" : "";

  return (
    <div className="flex flex-col gap-3">
      <OptionList
        options={field.options || []}
        renderItem={(option) => (
          <label
            key={option.value}
            className="inline-flex items-start gap-2 text-sm text-slate-800"
          >
            <input
              type="radio"
              name={field.id}
              className="mt-0.5 h-4 w-4 accent-blue-600"
              checked={selected === option.value}
              onChange={() =>
                onChange(
                  field.otherTextKey
                    ? { value: option.value, other: otherText }
                    : option.value
                )
              }
            />
            <span>{option.label}</span>
          </label>
        )}
      />
      {field.otherTextKey && selected === "other" ? (
        <input
          type="text"
          className={inputClass}
          placeholder={field.otherPlaceholder || "Bitte beschreiben"}
          value={otherText}
          onChange={(event) =>
            onChange({ value: "other", other: event.target.value })
          }
        />
      ) : null}
    </div>
  );
}

export function CheckboxField({ field, value, onChange }) {
  const selected = Array.isArray(value?.values)
    ? value.values
    : Array.isArray(value)
      ? value
      : [];
  const otherText = value?.other || "";

  const toggle = (optionValue) => {
    const next = selected.includes(optionValue)
      ? selected.filter((item) => item !== optionValue)
      : [...selected, optionValue];
    onChange(
      field.otherTextKey
        ? { values: next, other: otherText }
        : next
    );
  };

  return (
    <div className="flex flex-col gap-3">
      <OptionList
        options={field.options || []}
        renderItem={(option) => (
          <label
            key={option.value}
            className="inline-flex items-start gap-2 text-sm text-slate-800"
          >
            <input
              type="checkbox"
              className="mt-0.5 h-4 w-4 rounded border-slate-300 accent-blue-600"
              checked={selected.includes(option.value)}
              onChange={() => toggle(option.value)}
            />
            <span>{option.label}</span>
          </label>
        )}
      />
      {field.otherTextKey && selected.includes("other") ? (
        <input
          type="text"
          className={inputClass}
          placeholder={field.otherPlaceholder || "Bitte beschreiben"}
          value={otherText}
          onChange={(event) =>
            onChange({ values: selected, other: event.target.value })
          }
        />
      ) : null}
    </div>
  );
}

export function SelectField({ field, value, onChange, options }) {
  const selected = typeof value === "object" ? value?.value : value;
  const otherText = typeof value === "object" ? value?.other || "" : "";
  const flags = field.flags || [];
  const unknown = Boolean(value?.unknown);

  return (
    <div className="flex flex-col gap-3">
      <select
        className={inputClass}
        disabled={unknown}
        value={selected ?? ""}
        onChange={(event) =>
          onChange(
            field.allowOther || field.otherTextKey
              ? { value: event.target.value, other: otherText }
              : event.target.value
          )
        }
      >
        <option value="">{field.placeholder || "Bitte auswählen"}</option>
        {(options || field.options || []).map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {flags.map((flag) => (
        <label
          key={flag.id}
          className="inline-flex items-center gap-2 text-sm text-slate-800"
        >
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-slate-300 accent-blue-600"
            checked={Boolean(value?.[flag.id])}
            onChange={(event) =>
              onChange({
                ...(typeof value === "object" ? value : { value: selected }),
                [flag.id]: event.target.checked,
              })
            }
          />
          {flag.label}
        </label>
      ))}
      {(field.allowOther || field.otherTextKey) && (
        <label className="inline-flex items-center gap-2 text-sm text-slate-800">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-slate-300 accent-blue-600"
            checked={selected === "other"}
            onChange={(event) =>
              onChange({
                value: event.target.checked ? "other" : "",
                other: otherText,
              })
            }
          />
          Sonstiges
        </label>
      )}
      {selected === "other" ? (
        <input
          type="text"
          className={inputClass}
          placeholder="Bitte beschreiben"
          value={otherText}
          onChange={(event) =>
            onChange({ value: "other", other: event.target.value })
          }
        />
      ) : null}
    </div>
  );
}

export function TextField({ field, value, onChange }) {
  return (
    <input
      type="text"
      className={inputClass}
      placeholder={field.placeholder || ""}
      value={value || ""}
      onChange={(event) => onChange(event.target.value)}
    />
  );
}

export function TextareaField({ field, value, onChange }) {
  return (
    <textarea
      className={`${inputClass} min-h-[140px] resize-y`}
      placeholder={field.placeholder || "Hier Ihren Kommentar eingeben…"}
      value={value || ""}
      onChange={(event) => onChange(event.target.value)}
      rows={field.rows || 5}
    />
  );
}

export { QuestionShell };
