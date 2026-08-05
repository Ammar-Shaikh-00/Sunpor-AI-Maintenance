import {
  Info,
  CircleDot,
  Grid3X3,
  Droplets,
  Minus,
  Plus,
  Smile,
  Meh,
  Frown,
} from "lucide-react";
import { useTranslation } from "react-i18next";
import { translateDropdownValue } from "../../../utils/dropdownLabels";

const FOAMING_UI = {
  OK: {
    icon: Smile,
    selectedClass: "border-emerald-500 bg-emerald-50 text-emerald-800",
    idleClass: "border-slate-200 bg-white text-slate-700 hover:border-emerald-300",
    badgeClass: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  },
  "Not OK": {
    icon: Meh,
    selectedClass: "border-blue-500 bg-blue-50 text-blue-900",
    idleClass: "border-slate-200 bg-white text-slate-700 hover:border-amber-300",
    badgeClass: "bg-amber-50 text-amber-800 ring-amber-200",
  },
  Bad: {
    icon: Frown,
    selectedClass: "border-rose-500 bg-rose-50 text-rose-800",
    idleClass: "border-slate-200 bg-white text-slate-700 hover:border-rose-300",
    badgeClass: "bg-rose-50 text-rose-700 ring-rose-200",
  },
};

export function clampNumber(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

export function PercentMetricCard({
  label,
  value,
  onChange,
  min = 0,
  max = 100,
  typicalMax,
  infoText,
  icon: Icon = CircleDot,
}) {
  const { t } = useTranslation();
  const numeric = Number(value);
  const safeValue = Number.isFinite(numeric) ? numeric : 0;
  const guideMax = typicalMax ?? max;
  const percentOnGuide = clampNumber((safeValue / guideMax) * 100, 0, 100);

  const step = (delta) => {
    const next = clampNumber(Math.round(safeValue + delta), min, max);
    onChange(next);
  };

  return (
    <article className="flex h-full min-w-0 flex-col rounded-3xl border border-slate-200 bg-[#C5C8CF] p-4 sm:p-5">
      <div className="mb-4 flex items-start justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 sm:h-10 sm:w-10">
            <Icon className="h-5 w-5" aria-hidden="true" />
          </div>
          <h3 className="truncate text-sm font-semibold text-slate-900 sm:text-base">{label}</h3>
        </div>
        {infoText ? (
          <span
            title={infoText}
            className="rounded-full p-1 text-slate-400 hover:bg-slate-50 hover:text-slate-600"
          >
            <Info className="h-4 w-4" aria-hidden="true" />
          </span>
        ) : null}
      </div>

      <div className="flex items-center justify-between gap-3">
        <button
          type="button"
          onClick={() => step(-1)}
          className="flex h-12 w-12 items-center justify-center rounded-2xl border border-slate-200 bg-slate-50 text-slate-700 transition hover:bg-slate-100 active:scale-95"
          aria-label={t("forms.dailyQuality.decrease")}
        >
          <Minus className="h-5 w-5" />
        </button>

        <div className="min-w-0 flex-1 text-center">
          <input
            type="number"
            inputMode="decimal"
            min={min}
            max={max}
            step="1"
            value={Number.isFinite(numeric) ? numeric : ""}
            onChange={(event) => {
              const next = event.target.value;
              if (next === "") {
                onChange("");
                return;
              }
              const parsed = Number(next);
              if (!Number.isFinite(parsed)) {
                return;
              }
              onChange(clampNumber(parsed, min, max));
            }}
            className="w-full appearance-none border-0 bg-transparent text-center text-4xl font-bold text-slate-900 outline-none"
          />
          <div className="text-sm font-medium text-slate-400">%</div>
        </div>

        <button
          type="button"
          onClick={() => step(1)}
          className="flex h-12 w-12 items-center justify-center rounded-2xl border border-slate-200 bg-slate-50 text-slate-700 transition hover:bg-slate-100 active:scale-95"
          aria-label={t("forms.dailyQuality.increase")}
        >
          <Plus className="h-5 w-5" />
        </button>
      </div>

      <div className="mt-6">
        <p className="mb-2 text-xs font-medium text-slate-500">
          {t("forms.dailyQuality.typicalRange", { min, max: guideMax })}
        </p>
        <div className="relative h-3 rounded-full bg-gradient-to-r from-emerald-400 via-amber-300 to-rose-500">
          <span
            className="absolute top-1/2 h-5 w-5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-sky-500 shadow"
            style={{ left: `${percentOnGuide}%` }}
            aria-hidden="true"
          />
          <input
            type="range"
            min={min}
            max={guideMax}
            step="1"
            value={clampNumber(safeValue, min, guideMax)}
            onChange={(event) => onChange(Number(event.target.value))}
            className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
            aria-label={label}
          />
        </div>
      </div>
    </article>
  );
}

export function FoamingBehaviorCard({ value, options, onChange }) {
  const { t } = useTranslation();
  const selected = FOAMING_UI[value] || FOAMING_UI["Not OK"];
  const SelectedIcon = selected.icon;

  return (
    <article className="flex h-full min-w-0 flex-col rounded-3xl border border-slate-200 bg-[#C5C8CF] p-4 sm:p-5">
      <div className="mb-4 flex items-center gap-2">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 sm:h-10 sm:w-10">
          <Droplets className="h-5 w-5" aria-hidden="true" />
        </div>
        <h3 className="text-sm font-semibold text-slate-900 sm:text-base">
          {t("forms.dailyQuality.foamingBehavior")}
        </h3>
      </div>

      <div className="mb-5 flex items-center gap-3 rounded-2xl bg-slate-50 px-4 py-3">
        <SelectedIcon
          className={`h-7 w-7 ${
            value === "OK"
              ? "text-emerald-600"
              : value === "Bad"
                ? "text-rose-600"
                : "text-amber-500"
          }`}
        />
        <div>
          <div className="text-xs font-medium uppercase tracking-wide text-slate-400">
            {t("forms.dailyQuality.currentSelection")}
          </div>
          <div className="text-lg font-semibold text-slate-900">
            {value
              ? translateDropdownValue(t, value)
              : t("common.select")}
          </div>
        </div>
      </div>

      <div className="mt-auto grid grid-cols-3 gap-2">
        {options.map((option) => {
          const meta = FOAMING_UI[option] || FOAMING_UI["Not OK"];
          const OptionIcon = meta.icon;
          const isSelected = value === option;
          return (
            <button
              key={option}
              type="button"
              onClick={() => onChange(option)}
              className={`flex min-h-14 flex-col items-center justify-center gap-1 rounded-2xl border px-1.5 py-2.5 text-[11px] font-semibold transition sm:min-h-16 sm:px-2 sm:py-3 sm:text-sm ${
                isSelected ? meta.selectedClass : meta.idleClass
              }`}
            >
              <OptionIcon className="h-4 w-4 sm:h-5 sm:w-5" />
              <span className="max-w-full truncate">
                {translateDropdownValue(t, option)}
              </span>
            </button>
          );
        })}
      </div>
    </article>
  );
}

export function foamingBadgeClass(value) {
  return FOAMING_UI[value]?.badgeClass || "bg-slate-100 text-slate-700 ring-slate-200";
}

export function FoamingBadge({ value }) {
  const { t } = useTranslation();
  const meta = FOAMING_UI[value] || FOAMING_UI["Not OK"];
  const Icon = meta.icon;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${foamingBadgeClass(value)}`}
    >
      <Icon className="h-3.5 w-3.5" />
      {translateDropdownValue(t, value)}
    </span>
  );
}

export function percentBadgeClass(value, typicalMax) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return "bg-slate-100 text-slate-700 ring-slate-200";
  }
  const ratio = numeric / (typicalMax || 100);
  if (ratio <= 0.35) {
    return "bg-emerald-50 text-emerald-700 ring-emerald-200";
  }
  if (ratio <= 0.7) {
    return "bg-amber-50 text-amber-800 ring-amber-200";
  }
  return "bg-rose-50 text-rose-700 ring-rose-200";
}

export function PercentBadge({ value, typicalMax = 100 }) {
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${percentBadgeClass(value, typicalMax)}`}
    >
      {value}%
    </span>
  );
}

export { CircleDot, Grid3X3 };
