import { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import api from "../../../../api";
import { ENDPOINTS } from "../../../../api/sunpor";
import { useFormOptions, useProductionRuns } from "../../../../hooks/useSunporData";
import { getFormDefinition } from "../spec";
import OperatorFormFooter from "./OperatorFormFooter";
import OperatorFormHeader from "./OperatorFormHeader";
import {
  CheckboxField,
  DateTimeFlagsField,
  EventTimeField,
  QuestionShell,
  RadioField,
  RunSelectField,
  SelectField,
  TextareaField,
  TextField,
} from "./OperatorFormFields";
import {
  buildInitialValues,
  buildSubmitPayload,
  fieldIndexMap,
  validateFormValues,
} from "./formHelpers";

function materialLabel(item) {
  const code = item.code || item.name || item.label;
  const description = item.description;
  if (code && description && description !== code) {
    return `${code} — ${description}`;
  }
  return code || description || String(item.id ?? item.value ?? "");
}

function resolveSelectOptions(field, formOptions) {
  if (field.options?.length) return field.options;
  const source = field.optionsSource;
  if (!source || !formOptions) return [];

  if (source === "materials") {
    return (formOptions.materials || formOptions.material_types || []).map(
      (item) => ({
        value: String(item.id ?? item.value ?? item.code ?? item.name),
        label: materialLabel(item),
      })
    );
  }
  if (source === "batches") {
    return (formOptions.batches || []).map((item) => ({
      value: String(item.id ?? item.value ?? item.name),
      label: item.name || item.label || item.code || String(item.id),
    }));
  }
  if (source === "machines" || source === "production_lines") {
    return (formOptions.production_lines || formOptions.lines || []).map(
      (item) => ({
        value: String(item.id ?? item.value ?? item.name),
        label: item.name || item.label || String(item.id),
      })
    );
  }
  return [];
}

function FieldRenderer({ field, value, onChange, runs, formOptions, error, index }) {
  let control = null;

  switch (field.type) {
    case "run_select":
      control = (
        <RunSelectField
          field={field}
          value={value}
          onChange={onChange}
          runs={runs}
        />
      );
      break;
    case "event_time":
      control = <EventTimeField value={value} onChange={onChange} />;
      break;
    case "datetime_flags":
      control = (
        <DateTimeFlagsField field={field} value={value} onChange={onChange} />
      );
      break;
    case "radio":
      control = <RadioField field={field} value={value} onChange={onChange} />;
      break;
    case "checkbox":
      control = (
        <CheckboxField field={field} value={value} onChange={onChange} />
      );
      break;
    case "select":
      control = (
        <SelectField
          field={field}
          value={value}
          onChange={onChange}
          options={resolveSelectOptions(field, formOptions)}
        />
      );
      break;
    case "textarea":
      control = (
        <TextareaField field={field} value={value} onChange={onChange} />
      );
      break;
    case "text":
      control = <TextField field={field} value={value} onChange={onChange} />;
      break;
    case "quality_link":
      control = (
        <p className="text-sm text-slate-500">
          Verknüpfte Ereignisse können nach dem Speichern unter „Letzte
          Einträge“ gepflegt werden.
        </p>
      );
      break;
    case "file":
      control = (
        <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-3 py-4 text-sm text-slate-500">
          Dateianhänge folgen in einem späteren Schritt. Bitte relevante Hinweise
          im Kommentar vermerken.
        </div>
      );
      break;
    default:
      control = (
        <TextField field={field} value={value} onChange={onChange} />
      );
  }

  return (
    <QuestionShell
      index={index}
      label={field.label}
      required={field.required}
      hint={field.hint}
      error={error}
    >
      {control}
    </QuestionShell>
  );
}

export default function OperatorInputFormPage({ categoryId: categoryProp }) {
  const params = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const categoryId = categoryProp || params.categoryId;

  const definition = useMemo(
    () => getFormDefinition(categoryId),
    [categoryId]
  );

  const { options: formOptions } = useFormOptions();
  const { runs = [] } = useProductionRuns(100);
  const editId = searchParams.get("edit");

  const [values, setValues] = useState(() =>
    definition ? buildInitialValues(definition) : {}
  );
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!editId) return undefined;
    let cancelled = false;
    (async () => {
      try {
        const { data } = await api.get(`${ENDPOINTS.operatorEntries}/${editId}`);
        if (cancelled || !data?.payload) return;
        setValues((prev) => ({ ...prev, ...data.payload }));
      } catch {
        toast.error("Eintrag konnte nicht geladen werden.");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [editId]);

  const indexes = useMemo(
    () => (definition ? fieldIndexMap(definition) : {}),
    [definition]
  );
  const fieldMap = useMemo(() => {
    if (!definition) return {};
    return Object.fromEntries(
      definition.fields.map((field) => [field.id, field])
    );
  }, [definition]);

  if (!definition) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6 text-slate-700">
        Unbekanntes Formular: {categoryId}
      </div>
    );
  }

  const setFieldValue = (fieldId, next) => {
    setValues((prev) => ({ ...prev, [fieldId]: next }));
    setErrors((prev) => {
      if (!prev[fieldId]) return prev;
      const copy = { ...prev };
      delete copy[fieldId];
      return copy;
    });
  };

  const handleCancel = () => navigate("/operator");

  const handleSubmit = async (event) => {
    event?.preventDefault?.();
    const nextErrors = validateFormValues(definition, values);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) {
      toast.error("Bitte Pflichtfelder ausfüllen.");
      return;
    }

    const body = buildSubmitPayload(definition, values, runs, formOptions);
    if (!body.event_time) {
      toast.error("Ungültige Ereigniszeit.");
      return;
    }

    setSubmitting(true);
    try {
      if (editId) {
        const { category: _category, ...updateBody } = body;
        await api.put(`${ENDPOINTS.operatorEntries}/${editId}`, updateBody);
        toast.success("Eintrag aktualisiert.");
      } else {
        await api.post(ENDPOINTS.operatorEntries, body);
        toast.success("Eintrag erfasst.");
      }
      navigate("/forms/recent-entries");
    } catch (error) {
      const detail =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        error?.message;
      const message =
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail.map((item) => item.msg || JSON.stringify(item)).join("; ")
            : "Speichern fehlgeschlagen.";
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  const accent = definition.accent || "#1E3A8A";

  return (
    <div className="operator-input-form -mx-3 flex min-h-[70vh] flex-col bg-[#F3F5F8] sm:-mx-4 lg:-mx-6">
      <OperatorFormHeader
        title={definition.title}
        description={definition.description}
        accent={accent}
        backTo="/operator"
        onClose={handleCancel}
      />

      <form
        className="mx-auto flex w-full max-w-[1600px] flex-1 flex-col"
        onSubmit={handleSubmit}
      >
        <div className="flex-1 px-3 py-4 sm:px-5 sm:py-5">
          {definition.plantValues?.length ? (
            <div className="mb-4 rounded-xl border border-slate-200 bg-white p-4">
              <h2 className="mb-2 text-sm font-semibold text-[#1E3A8A]">
                Anlagenwerte (Anzeige)
              </h2>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                {definition.plantValues.map((item) => (
                  <div
                    key={item.id || item.label}
                    className="rounded-lg border border-slate-200 px-3 py-2"
                  >
                    <div className="text-xs text-slate-500">{item.label}</div>
                    <div className="text-sm font-semibold text-slate-800">
                      {item.placeholder || "—"}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            {(definition.layout || []).map((row, rowIndex) => {
              const colClass =
                row.length >= 4
                  ? "grid-cols-1 sm:grid-cols-2 xl:grid-cols-4"
                  : row.length === 3
                    ? "grid-cols-1 md:grid-cols-3"
                    : row.length === 2
                      ? "grid-cols-1 md:grid-cols-2"
                      : "grid-cols-1";

              return (
                <div
                  key={`row-${rowIndex}`}
                  className={`grid border-b border-slate-200 last:border-b-0 ${colClass}`}
                >
                  {row.map((fieldId) => {
                    const field = fieldMap[fieldId];
                    if (!field) return null;
                    return (
                      <div
                        key={fieldId}
                        className="min-w-0 border-b border-r border-slate-200 last:border-r-0 md:border-b-0"
                      >
                        <FieldRenderer
                          field={field}
                          index={indexes[fieldId]}
                          value={values[fieldId]}
                          onChange={(next) => setFieldValue(fieldId, next)}
                          runs={runs}
                          formOptions={formOptions}
                          error={errors[fieldId]}
                        />
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>

        <OperatorFormFooter
          onCancel={handleCancel}
          submitLabel={definition.submitLabel || "Jetzt erfassen"}
          submitting={submitting}
          accent="#1E4FD6"
        />
      </form>
    </div>
  );
}
