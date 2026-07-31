import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import SimpleLiveChart from "../../subComponents/simpleLiveChart";
import { useSignalChartSeries } from "../../../hooks/useSignalCharts";

const LINE_COLORS = [
  "#7c3aed",
  "#0891b2",
  "#059669",
  "#d97706",
  "#e11d48",
  "#2563eb",
];

function formatLastValue(value, unit) {
  if (value == null || Number.isNaN(Number(value))) {
    return "—";
  }
  const numeric = Number(value);
  const formatted =
    Math.abs(numeric) >= 100 ? numeric.toFixed(1) : numeric.toFixed(2);
  return unit ? `${formatted} ${unit}` : formatted;
}

export default function SignalChartCard({ signal, rangeKey, index = 0 }) {
  const { t } = useTranslation();
  const rootRef = useRef(null);
  const [visible, setVisible] = useState(false);
  const { points, loading, error } = useSignalChartSeries(
    signal.id,
    rangeKey,
    visible
  );

  useEffect(() => {
    const node = rootRef.current;
    if (!node) {
      return undefined;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "160px 0px", threshold: 0.01 }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  const title = signal.display_name || signal.wincc_tag || `#${signal.id}`;
  const unit = signal.unit || "";
  const lastValue = points.length ? points[points.length - 1].value : null;
  const timeFormat = rangeKey === "1h" ? "time" : "datetime";
  const lineColor = LINE_COLORS[index % LINE_COLORS.length];

  const legend = useMemo(() => {
    const parts = [];
    if (signal.signal_group) {
      parts.push(signal.signal_group);
    }
    if (unit) {
      parts.push(unit);
    }
    if (points.length) {
      parts.push(
        t("signalsCharts.pointCount", { count: points.length })
      );
    }
    return parts.join(" · ");
  }, [signal.signal_group, unit, points.length, t]);

  return (
    <article
      ref={rootRef}
      className="min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-[#C5C8CF] shadow-sm"
    >
      <div className="flex items-start justify-between gap-3 border-b border-slate-100 px-4 py-3">
        <div className="min-w-0">
          <h3 className="truncate text-sm font-semibold text-slate-900 sm:text-base">
            {title}
          </h3>
          {signal.wincc_tag && signal.wincc_tag !== title ? (
            <p className="mt-0.5 truncate text-xs text-slate-400">
              {signal.wincc_tag}
            </p>
          ) : null}
        </div>
        <div className="shrink-0 text-right">
          <div className="text-[10px] font-medium uppercase tracking-wide text-slate-400">
            {t("signalsCharts.lastValue")}
          </div>
          <div className="text-sm font-semibold text-blue-700">
            {loading && !points.length
              ? "…"
              : formatLastValue(lastValue, unit)}
          </div>
        </div>
      </div>

      <div className="p-2 sm:p-3">
        {!visible || (loading && !points.length) ? (
          <div className="flex h-[220px] items-center justify-center rounded-xl bg-slate-50 text-sm text-slate-400">
            {t("signalsCharts.loadingChart")}
          </div>
        ) : error ? (
          <div className="flex h-[220px] items-center justify-center rounded-xl border border-rose-100 bg-rose-50 px-4 text-center text-sm text-rose-700">
            {t("signalsCharts.chartError")}
          </div>
        ) : !points.length ? (
          <div className="flex h-[220px] items-center justify-center rounded-xl bg-slate-50 px-4 text-center text-sm text-slate-500">
            {t("signalsCharts.noData")}
          </div>
        ) : (
          <div className="-m-1 [&_.rounded-2xl]:rounded-xl [&_.rounded-2xl]:p-2 [&_.rounded-2xl]:shadow-none [&_h3]:hidden [&_p]:mb-1">
            <SimpleLiveChart
              title={title}
              legend={legend}
              data={points}
              unit={unit}
              lineColor={lineColor}
              height={200}
              timeFormat={timeFormat}
            />
          </div>
        )}
      </div>
    </article>
  );
}
