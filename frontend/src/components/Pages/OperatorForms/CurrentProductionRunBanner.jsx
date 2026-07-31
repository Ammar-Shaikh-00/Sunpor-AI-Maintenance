import { Calendar, ClipboardList, Clock, Hash, Layers, MessageSquare, Sun } from "lucide-react";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { PRODUCTION_RUN_STATUS } from "../../../constants/productionRun";
import { useFormOptions, useProductionRuns } from "../../../hooks/useSunporData";
import { formatApiDate, formatApiTime } from "../../../utils/datetime";
import { getLineName, getShiftName } from "./formUi";

function formatRunDate(value) {
  if (!value) {
    return "—";
  }
  return formatApiDate(value);
}

function formatRunTime(value) {
  if (!value) {
    return "—";
  }
  return formatApiTime(value, { withSeconds: false });
}

function displayValue(value) {
  if (value === null || value === undefined || String(value).trim() === "") {
    return "—";
  }
  return String(value);
}

function RunStatusBadge({ status }) {
  const { t } = useTranslation();
  const normalized = status || PRODUCTION_RUN_STATUS.RUNNING;
  const isRunning = normalized === PRODUCTION_RUN_STATUS.RUNNING;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold uppercase tracking-wide ${
        isRunning
          ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200"
          : "bg-slate-100 text-slate-600 ring-1 ring-slate-200"
      }`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${isRunning ? "bg-emerald-500" : "bg-slate-400"}`}
        aria-hidden="true"
      />
      {t(`allForms.runBanner.status.${normalized}`, { defaultValue: normalized })}
    </span>
  );
}

function MetaItem({ icon: Icon, label, value }) {
  return (
    <div className="flex min-w-0 items-center gap-2 text-sm text-slate-500">
      <Icon className="h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
      <span className="min-w-0 break-words">
        <span className="text-slate-400">{label}:</span>{" "}
        <span className="font-medium text-slate-700">{value}</span>
      </span>
    </div>
  );
}

export default function CurrentProductionRunBanner() {
  const { t } = useTranslation();
  const { options, loading: optionsLoading } = useFormOptions();
  const { runs, loading: runsLoading } = useProductionRuns(20, { runningOnly: true });

  const currentRun = useMemo(() => runs[0] || null, [runs]);
  const loading = optionsLoading || runsLoading;

  if (loading) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-[#C5C8CF] px-4 py-4 shadow-sm sm:px-6 sm:py-5">
        <div className="h-6 w-48 max-w-full animate-pulse rounded bg-slate-100" />
        <div className="mt-4 flex flex-wrap gap-4">
          <div className="h-4 w-32 animate-pulse rounded bg-slate-100" />
          <div className="h-4 w-28 animate-pulse rounded bg-slate-100" />
          <div className="h-4 w-24 animate-pulse rounded bg-slate-100" />
        </div>
      </section>
    );
  }

  if (!currentRun) {
    return (
      <section className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4 shadow-sm sm:px-6 sm:py-5">
        <p className="text-sm font-medium text-amber-900">{t("allForms.runBanner.noActiveRun")}</p>
        <Link
          to="/forms/production-start"
          className="mt-2 inline-flex min-h-11 items-center text-sm font-semibold text-blue-700 hover:text-blue-800"
        >
          {t("allForms.runBanner.startRun")}
        </Link>
      </section>
    );
  }

  const lineName = getLineName(options, currentRun.production_line_id);
  const shiftName = getShiftName(options, currentRun.shift_id);

  return (
    <section className="rounded-2xl border border-slate-200 bg-[#C5C8CF] px-4 py-4 shadow-sm sm:px-6 sm:py-5">
      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
        <h2 className="min-w-0 text-base font-semibold text-slate-900 sm:text-xl">
          {t("allForms.runBanner.title", { id: currentRun.id })}
        </h2>
        <RunStatusBadge status={currentRun.status} />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-x-6 lg:grid-cols-3 xl:grid-cols-4">
        <MetaItem icon={Layers} label={t("allForms.runBanner.line")} value={lineName} />
        <MetaItem icon={Sun} label={t("allForms.runBanner.shift")} value={shiftName} />
        <MetaItem
          icon={Calendar}
          label={t("allForms.runBanner.date")}
          value={formatRunDate(currentRun.start_time)}
        />
        <MetaItem
          icon={Clock}
          label={t("allForms.runBanner.time")}
          value={formatRunTime(currentRun.start_time)}
        />
        <MetaItem
          icon={Hash}
          label={t("allForms.runBanner.recipeNumber")}
          value={displayValue(currentRun.recipe_number)}
        />
        <MetaItem
          icon={ClipboardList}
          label={t("allForms.runBanner.productionOrder")}
          value={displayValue(currentRun.production_order)}
        />
        <MetaItem
          icon={MessageSquare}
          label={t("allForms.runBanner.comment")}
          value={displayValue(currentRun.comment)}
        />
      </div>
    </section>
  );
}
