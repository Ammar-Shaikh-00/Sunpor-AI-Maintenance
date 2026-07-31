import { AlertTriangle, CheckCircle2, X } from "lucide-react";
import { useTranslation } from "react-i18next";

const ACCENT_BLUE = "#2563EB";
const ACCENT_BLUE_SOFT = "#BFDBFE";

function Sparkline({ values = [] }) {
  if (!values.length) {
    return (
      <div className="mt-2 h-9 w-full rounded-md bg-[#B1B8C2]/40" aria-hidden="true" />
    );
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const width = 100;
  const height = 36;
  const points = values
    .map((value, index) => {
      const x = values.length === 1 ? width / 2 : (index / (values.length - 1)) * width;
      const y = height - ((value - min) / span) * (height - 6) - 3;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="mt-2 h-9 w-full" aria-hidden="true">
      <polyline
        fill="none"
        stroke={ACCENT_BLUE}
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
}

function ProbabilityGauge({ value }) {
  const percent = Math.max(0, Math.min(100, value ?? 0));
  const radius = 42;
  const circumference = Math.PI * radius;
  const offset = circumference - (percent / 100) * circumference;

  return (
    <div className="relative mx-auto flex h-28 w-40 items-end justify-center">
      <svg viewBox="0 0 120 70" className="h-full w-full overflow-visible">
        <path
          d="M 18 60 A 42 42 0 0 1 102 60"
          fill="none"
          stroke={ACCENT_BLUE_SOFT}
          strokeWidth="10"
          strokeLinecap="round"
        />
        <path
          d="M 18 60 A 42 42 0 0 1 102 60"
          fill="none"
          stroke={ACCENT_BLUE}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute bottom-1 text-center">
        <div className="text-3xl font-bold tabular-nums text-blue-600">{percent}%</div>
      </div>
    </div>
  );
}

function MetricCell({ label, value, unit, delta, rising, trend }) {
  const { t } = useTranslation();
  const hasValue = value != null && value !== "";
  const isRising = rising == null ? (delta != null ? delta > 0 : true) : rising;

  return (
    <div className="min-w-0 border-t border-slate-400/25 pt-3 first:border-t-0 first:pt-0 sm:border-l sm:border-t-0 sm:pl-5 sm:pt-0 sm:first:border-l-0 sm:first:pl-0">
      <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="mt-1 flex items-baseline gap-1.5">
        <span className="text-xl font-bold tabular-nums text-slate-900 sm:text-2xl">
          {hasValue ? value : "—"}
        </span>
        {unit ? <span className="text-sm text-slate-500">{unit}</span> : null}
      </div>
      {delta != null ? (
        <div className="mt-1 text-xs font-semibold text-blue-600">
          {isRising ? "↑" : "↓"} {isRising ? "+" : "−"}
          {Math.abs(delta)}%
        </div>
      ) : (
        <div className="mt-1 text-[11px] text-slate-400">
          {t("operatorAssist.alert.deltaUnavailable")}
        </div>
      )}
      <Sparkline values={trend || []} />
    </div>
  );
}

const PHASE_TITLE_KEYS = {
  fault_disturbance: "operatorAssist.phases.fault_disturbance",
  heating_up: "operatorAssist.phases.heating_up",
  startup: "operatorAssist.phases.startup",
  stable_production: "operatorAssist.phases.stable_production",
  low_production: "operatorAssist.phases.low_production",
  cleaning_run: "operatorAssist.phases.cleaning_run",
  empty_run: "operatorAssist.phases.empty_run",
  cooling_down: "operatorAssist.phases.cooling_down",
  shutdown: "operatorAssist.phases.shutdown",
};

export default function OperatorAlertCard({
  suggestion,
  metrics,
  loading,
  busyId,
  onConfirm,
  onDismiss,
}) {
  const { t } = useTranslation();

  if (loading && !suggestion) {
    return (
      <section className="h-48 animate-pulse rounded-3xl bg-[#C5C8CF] ring-1 ring-slate-400/25" />
    );
  }

  if (!suggestion) {
    return (
      <section className="rounded-3xl bg-[#C5C8CF] px-5 py-8 text-center text-sm text-slate-600 ring-1 ring-slate-400/25">
        {t("operatorAssist.suggestions.empty")}
      </section>
    );
  }

  const severity = suggestion.severity || "info";
  const isAlert = severity === "critical" || severity === "warning";
  const titleKey = suggestion.phase ? PHASE_TITLE_KEYS[suggestion.phase] : null;
  const isScreenBlockage = /screen|blockage|siebverstopfung/i.test(
    `${suggestion.title || ""} ${suggestion.message || ""}`
  );
  const title = isScreenBlockage
    ? t("operatorAssist.phases.screen_blockage")
    : titleKey
      ? t(titleKey, { defaultValue: suggestion.title })
      : suggestion.title;
  const message = isScreenBlockage
    ? t("operatorAssist.phases.screen_blockage_message", {
        defaultValue: suggestion.message,
      })
    : suggestion.message;
  const rawConfidence = Number(suggestion.confidence);
  const confidencePercent = Number.isFinite(rawConfidence)
    ? Math.round(rawConfidence > 1 ? rawConfidence : rawConfidence * 100)
    : null;
  const horizon = suggestion.horizon_minutes;

  const pressure = metrics?.pressure;
  const torque = metrics?.torque;
  const throughput = metrics?.throughput;

  return (
    <section className="rounded-3xl bg-[#C5C8CF] p-4 ring-1 ring-slate-400/25 sm:p-5">
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,1.35fr)_minmax(11rem,0.7fr)]">
        <div className="flex gap-3">
          <div className="mt-0.5 flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-blue-600/10 text-blue-600">
            <AlertTriangle className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <h2 className="text-lg font-bold leading-snug text-slate-900 sm:text-xl">
              {title}
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">
              {message}
            </p>
            {isAlert ? (
              <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
                <button
                  type="button"
                  disabled={busyId === `${suggestion.id}-confirm`}
                  onClick={() => onConfirm(suggestion)}
                  className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-60 sm:w-auto"
                >
                  <CheckCircle2 className="h-4 w-4" />
                  {t("operatorAssist.suggestions.confirm")}
                </button>
                <button
                  type="button"
                  disabled={busyId === `${suggestion.id}-dismiss`}
                  onClick={() => onDismiss(suggestion)}
                  className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-xl border border-slate-400/40 px-4 text-sm font-semibold text-slate-800 transition hover:bg-white disabled:opacity-60 sm:w-auto"
                >
                  <X className="h-4 w-4" />
                  {t("operatorAssist.suggestions.dismiss")}
                </button>
              </div>
            ) : null}
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <MetricCell
            label={t("operatorAssist.alert.pressure")}
            value={pressure?.value}
            unit={pressure?.unit || "bar"}
            delta={pressure?.delta_percent}
            rising={pressure?.rising}
            trend={pressure?.trend}
          />
          <MetricCell
            label={t("operatorAssist.alert.torque")}
            value={torque?.value}
            unit={torque?.unit || "%"}
            delta={torque?.delta_percent}
            rising={torque?.rising}
            trend={torque?.trend}
          />
          <MetricCell
            label={t("operatorAssist.alert.throughput")}
            value={throughput?.value}
            unit={throughput?.unit || "t/h"}
            delta={throughput?.delta_percent}
            rising={throughput?.rising}
            trend={throughput?.trend}
          />
        </div>

        <div className="flex flex-col items-center justify-center rounded-2xl bg-[#B1B8C2]/55 px-3 py-4 ring-1 ring-slate-400/20">
          <div className="text-center text-sm font-bold text-slate-900">
            {suggestion.recommended_action ||
              t("operatorAssist.alert.checkScreenNow")}
          </div>
          <ProbabilityGauge value={confidencePercent ?? 0} />
          <p className="mt-1 max-w-[12rem] text-center text-[11px] leading-snug text-slate-600">
            <span className="block font-medium">
              {t("operatorAssist.alert.blockageProbability")}
            </span>
            {horizon ? (
              <span className="mt-0.5 block font-bold text-slate-900">
                {t("operatorAssist.alert.probabilityHorizon", {
                  minutes: horizon,
                })}
              </span>
            ) : (
              <span className="mt-0.5 block text-slate-500">
                {t("operatorAssist.alert.probabilityHint")}
              </span>
            )}
          </p>
        </div>
      </div>
    </section>
  );
}
