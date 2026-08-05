import { useMemo, useState } from "react";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import { displayInputToUtcIso, toDisplayInputValue } from "../../../utils/datetime";
import { translateDropdownValue } from "../../../utils/dropdownLabels";
import { X } from "lucide-react";
import api from "../../../api";
import { ENDPOINTS } from "../../../api/sunpor";
import { useAuth } from "../../../context/authContext";
import { useFormOptions } from "../../../hooks/useSunporData";
import { useNavigate } from "react-router-dom";

const ISSUE_CATEGORIES = [
  {
    id: "mechanical",
    labelKey: "operatorAssist.wizard.categories.mechanical",
    level1: "Malfunctions",
    level2: "Mechanical Malfunction",
    level3Key: "fault_mechanical_level_3",
  },
  {
    id: "electrical",
    labelKey: "operatorAssist.wizard.categories.electrical",
    level1: "Malfunctions",
    level2: "Electrical Malfunction",
    level3Key: "fault_electrical_level_3",
  },
  {
    id: "temperature",
    labelKey: "operatorAssist.wizard.categories.temperature",
    level1: "Extruder",
    level2: "Heating Up",
    level3Key: "extruder_heating_level_3",
  },
  {
    id: "material",
    labelKey: "operatorAssist.wizard.categories.material",
    level1: null,
    to: "/forms/material-behavior",
  },
];

export default function ReportIssueWizard({ productionRunId, onClose }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { options } = useFormOptions();
  const [step, setStep] = useState(1);
  const [category, setCategory] = useState(null);
  const [level3, setLevel3] = useState("");
  const [comment, setComment] = useState("");
  const [saving, setSaving] = useState(false);

  const level3Options = useMemo(() => {
    if (!category?.level3Key || !options?.dropdowns) {
      return [];
    }
    return options.dropdowns[category.level3Key] || [];
  }, [category, options]);

  const selectCategory = (item) => {
    if (item.to) {
      onClose();
      navigate(item.to);
      return;
    }
    setCategory(item);
    setLevel3("");
    setStep(2);
  };

  const submit = async () => {
    if (!productionRunId) {
      toast.error(t("operatorAssist.wizard.needRun"));
      return;
    }
    if (!category || !level3) {
      toast.error(t("operatorAssist.wizard.needDetail"));
      return;
    }

    setSaving(true);
    try {
      await api.post(ENDPOINTS.productionEvents, {
        production_run_id: productionRunId,
        event_time: displayInputToUtcIso(toDisplayInputValue(new Date())),
        level_1: category.level1,
        level_2: category.level2,
        level_3: level3,
        reason: "Operator report issue wizard",
        comment: comment || null,
        operator_id: user?.id || options?.current_user_id,
      });
      toast.success(t("operatorAssist.wizard.success"));
      onClose();
    } catch {
      toast.error(t("operatorAssist.wizard.error"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-3 sm:items-center">
      <div className="flex max-h-[min(92vh,40rem)] w-full max-w-lg flex-col overflow-hidden rounded-2xl bg-[#C5C8CF] shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-100 px-4 py-4 sm:px-5">
          <div className="min-w-0 pr-2">
            <h2 className="text-base font-semibold text-slate-900 sm:text-lg">
              {t("operatorAssist.wizard.title")}
            </h2>
            <p className="text-sm text-slate-500">
              {t("operatorAssist.wizard.step", { step })}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 rounded-lg p-2 text-slate-500 hover:bg-slate-100"
            aria-label={t("common.close")}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="overflow-y-auto px-4 py-4 sm:px-5">
          {step === 1 ? (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {ISSUE_CATEGORIES.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => selectCategory(item)}
                  className="min-h-16 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-left text-base font-semibold text-slate-800 transition hover:border-blue-300 hover:bg-blue-50"
                >
                  {t(item.labelKey)}
                </button>
              ))}
            </div>
          ) : null}

          {step === 2 ? (
            <div className="space-y-4">
              <p className="text-sm text-slate-600">
                {t("operatorAssist.wizard.pickDetail", {
                  category: t(category.labelKey),
                })}
              </p>
              <div className="grid gap-2">
                {level3Options.map((option) => (
                  <button
                    key={option.id}
                    type="button"
                    onClick={() => setLevel3(option.value)}
                    className={`min-h-12 rounded-xl border px-4 text-left text-sm font-medium ${
                      level3 === option.value
                        ? "border-blue-500 bg-blue-50 text-blue-900"
                        : "border-slate-200 bg-[#C5C8CF] text-slate-700"
                    }`}
                  >
                    {translateDropdownValue(t, option.value)}
                  </button>
                ))}
              </div>
              <textarea
                value={comment}
                onChange={(event) => setComment(event.target.value)}
                rows={3}
                placeholder={t("operatorAssist.wizard.commentPlaceholder")}
                className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="min-h-11 flex-1 rounded-xl border border-slate-300 px-4 text-sm font-semibold"
                >
                  {t("operatorAssist.wizard.back")}
                </button>
                <button
                  type="button"
                  disabled={saving}
                  onClick={submit}
                  className="min-h-11 flex-1 rounded-xl bg-blue-600 px-4 text-sm font-semibold text-white disabled:opacity-60"
                >
                  {saving
                    ? t("operatorAssist.wizard.saving")
                    : t("operatorAssist.wizard.submit")}
                </button>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
