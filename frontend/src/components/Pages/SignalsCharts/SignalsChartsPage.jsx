import { Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSignalCatalogForCharts } from "../../../hooks/useSignalCharts";
import SignalChartCard from "./SignalChartCard";

const RANGE_KEYS = ["1h", "1d", "1w", "1m"];

function useDebouncedValue(value, delayMs = 250) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
}

export default function SignalsChartsPage() {
  const { t } = useTranslation();
  const { signals, groups, loading, error } = useSignalCatalogForCharts();
  const [rangeKey, setRangeKey] = useState("1h");
  const [search, setSearch] = useState("");
  const [group, setGroup] = useState("");
  const debouncedSearch = useDebouncedValue(search);

  const filteredSignals = useMemo(() => {
    const query = debouncedSearch.trim().toLowerCase();
    return signals.filter((signal) => {
      if (group && signal.signal_group !== group) {
        return false;
      }
      if (!query) {
        return true;
      }
      const haystack = [
        signal.display_name,
        signal.wincc_tag,
        signal.signal_group,
        signal.signal_role,
        signal.description,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return haystack.includes(query);
    });
  }, [signals, debouncedSearch, group]);

  return (
    <div className="mx-auto w-full max-w-7xl space-y-5 px-1 sm:px-0">
      <header className="space-y-1">
        <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">
          {t("signalsCharts.title")}
        </h1>
        <p className="max-w-3xl text-sm text-slate-500 sm:text-base">
          {t("signalsCharts.description")}
        </p>
      </header>

      <section className="sticky top-0 z-20 rounded-2xl border border-slate-200 bg-[#C5C8CF]/95 p-3 shadow-sm backdrop-blur sm:p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div
            className="flex flex-wrap gap-2"
            role="group"
            aria-label={t("signalsCharts.rangeLabel")}
          >
            {RANGE_KEYS.map((key) => {
              const active = rangeKey === key;
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => setRangeKey(key)}
                  className={`inline-flex min-h-11 items-center justify-center rounded-xl px-4 text-sm font-semibold transition ${
                    active
                      ? "bg-blue-700 text-white shadow-sm"
                      : "border border-slate-200 bg-[#C5C8CF] text-slate-700 hover:border-blue-200 hover:bg-blue-50"
                  }`}
                >
                  {t(`signalsCharts.ranges.${key}`)}
                </button>
              );
            })}
          </div>

          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <label className="relative min-w-0 flex-1 sm:w-64">
              <span className="sr-only">{t("signalsCharts.searchLabel")}</span>
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder={t("signalsCharts.searchPlaceholder")}
                className="min-h-11 w-full rounded-xl border border-slate-200 bg-[#C5C8CF] py-2 pl-9 pr-3 text-sm outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
              />
            </label>

            <label className="min-w-0 sm:w-52">
              <span className="sr-only">{t("signalsCharts.groupLabel")}</span>
              <select
                value={group}
                onChange={(event) => setGroup(event.target.value)}
                className="min-h-11 w-full rounded-xl border border-slate-200 bg-[#C5C8CF] px-3 text-sm outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
              >
                <option value="">{t("signalsCharts.allGroups")}</option>
                {groups.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>

        <p className="mt-3 text-xs text-slate-500 sm:text-sm">
          {t("signalsCharts.resultSummary", {
            shown: filteredSignals.length,
            total: signals.length,
          })}
        </p>
      </section>

      {loading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <div
              key={index}
              className="h-72 animate-pulse rounded-2xl border border-slate-200 bg-slate-100"
            />
          ))}
        </div>
      ) : error ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-6 text-sm text-rose-700">
          {t("signalsCharts.loadError")}
        </div>
      ) : !filteredSignals.length ? (
        <div className="rounded-2xl border border-slate-200 bg-[#C5C8CF] px-4 py-10 text-center text-sm text-slate-500">
          {t("signalsCharts.emptyFilter")}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filteredSignals.map((signal, index) => (
            <SignalChartCard
              key={`${signal.id}-${rangeKey}`}
              signal={signal}
              rangeKey={rangeKey}
              index={index}
            />
          ))}
        </div>
      )}
    </div>
  );
}
