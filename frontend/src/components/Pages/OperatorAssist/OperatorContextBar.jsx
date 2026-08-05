import { AlertTriangle, Clock3, Layers, Package, Sun, UserRound } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { translateDropdownValue } from "../../../utils/dropdownLabels";

function formatRunningTime(minutes) {
  if (minutes == null) {
    return "—";
  }
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours <= 0) {
    return `${mins} min`;
  }
  return `${hours}h ${mins}m`;
}

function MetaChip({ icon: Icon, label, value }) {
  return (
    <div className="flex min-w-0 items-center gap-2 rounded-xl bg-[#C5C8CF] px-3 py-2 ring-1 ring-slate-400/30">
      <Icon className="h-4 w-4 shrink-0 text-blue-600" aria-hidden="true" />
      <div className="min-w-0">
        <div className="text-[11px] uppercase tracking-wide text-slate-400">{label}</div>
        <div className="truncate text-sm font-semibold text-slate-800">{value || "—"}</div>
      </div>
    </div>
  );
}

export default function OperatorContextBar({ context, loading }) {
  const { t } = useTranslation();

  if (loading && !context) {
    return (
      <section className="rounded-2xl border border-slate-400/30 bg-[#C5C8CF] p-4">
        <div className="h-5 w-40 animate-pulse rounded bg-slate-100" />
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
          {Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className="h-14 animate-pulse rounded-xl bg-slate-100" />
          ))}
        </div>
      </section>
    );
  }

  const run = context?.production_run;

  if (!run) {
    return (
      <section className="rounded-2xl border border-amber-200 bg-amber-50 p-4 shadow-sm">
        <div className="flex items-start gap-3">
          <AlertTriangle className="mt-0.5 h-5 w-5 text-amber-600" />
          <div>
            <p className="font-semibold text-amber-900">
              {t("operatorAssist.context.noActiveRun")}
            </p>
            <Link
              to="/forms/production-start"
              className="mt-1 inline-flex text-sm font-semibold text-blue-700"
            >
              {t("operatorAssist.context.startRun")}
            </Link>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-blue-100 bg-gradient-to-br from-blue-50 via-white to-slate-50 p-4 shadow-sm">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <h2 className="text-base font-semibold text-slate-900 sm:text-lg">
          {t("operatorAssist.context.title", { id: run.id })}
        </h2>
        <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-700 ring-1 ring-emerald-200">
          {run.status}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
        <MetaChip
          icon={Layers}
          label={t("operatorAssist.context.line")}
          value={run.line?.name}
        />
        <MetaChip
          icon={Package}
          label={t("operatorAssist.context.material")}
          value={run.material?.code || run.material?.description}
        />
        <MetaChip
          icon={Sun}
          label={t("operatorAssist.context.shift")}
          value={translateDropdownValue(
            t,
            run.shift?.name || context?.resolved_shift?.name
          ) || "—"}
        />
        <MetaChip
          icon={UserRound}
          label={t("operatorAssist.context.operator")}
          value={
            context?.operator?.name || run.run_operator?.name || "—"
          }
        />
        <MetaChip
          icon={Clock3}
          label={t("operatorAssist.context.runningTime")}
          value={formatRunningTime(run.running_minutes)}
        />
        <MetaChip
          icon={AlertTriangle}
          label={t("operatorAssist.context.status")}
          value={run.status}
        />
      </div>
    </section>
  );
}
