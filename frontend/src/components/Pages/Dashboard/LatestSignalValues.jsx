import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import safeApi, { ENDPOINTS } from "../../../api/safeApi";

export default function LatestSignalValues() {
  const { t } = useTranslation();
  const [signals, setSignals] = useState([]);
  const [catalog, setCatalog] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showMore, setShowMore] = useState(false);
  const [snapshotTime, setSnapshotTime] = useState(null);
  const prevValuesRef = useRef({});
  const [changedIds, setChangedIds] = useState([]);

  const fetchValues = async () => {
    try {
      const [latestRes, catalogRes] = await Promise.all([
        safeApi.get(ENDPOINTS.signalLatest),
        safeApi.get(`${ENDPOINTS.signalCatalog}?limit=500`),
      ]);

      if (latestRes.fallback) {
        throw new Error(latestRes.error || t("dashboard.latestSignals.loadFailed"));
      }

      const catalogMap = {};
      (catalogRes.data || []).forEach((signal) => {
        catalogMap[signal.id] = signal;
      });

      const latest = latestRes.data || [];
      const changed = [];

      latest.forEach((row) => {
        const previous = prevValuesRef.current[row.signal_id];
        if (previous !== undefined && previous !== row.value_scaled) {
          changed.push(row.signal_id);
        }
        prevValuesRef.current[row.signal_id] = row.value_scaled;
      });

      setSignals(latest);
      setCatalog(catalogMap);
      setSnapshotTime(latest[0]?.timestamp || null);
      setChangedIds(changed);
      setError(null);

      if (changed.length > 0) {
        setTimeout(() => setChangedIds([]), 800);
      }
    } catch (err) {
      setError(err.message || t("dashboard.latestSignals.loadFailed"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchValues();
    const interval = setInterval(fetchValues, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="p-4 text-center text-gray-500">
        {t("dashboard.latestSignals.loading")}
      </div>
    );
  }

  if (error) {
    return <div className="p-4 text-center text-red-500 font-medium">{error}</div>;
  }

  const formattedDate = snapshotTime
    ? new Date(snapshotTime).toLocaleString("de-DE")
    : "—";

  const sortedSignals = [...signals].sort((a, b) => {
    const nameA = catalog[a.signal_id]?.display_name || "";
    const nameB = catalog[b.signal_id]?.display_name || "";
    return nameA.localeCompare(nameB);
  });

  const primarySignals = sortedSignals.slice(0, 12);
  const otherSignals = sortedSignals.slice(12);

  const renderCard = (row) => {
    const meta = catalog[row.signal_id] || {};
    const isChanged = changedIds.includes(row.signal_id);

    return (
      <div
        key={`${row.signal_id}-${row.timestamp}`}
        className={`rounded-2xl border p-4 transition-all duration-500 ${
          isChanged
            ? "scale-105 border-green-400 bg-green-100"
            : "border-gray-200 bg-white"
        }`}
      >
        <p className="text-xs text-gray-500">{meta.display_name || row.wincc_tag}</p>
        <p className="text-lg font-semibold text-gray-800">
          {Number(row.value_scaled).toFixed(2)}
          {meta.unit ? ` ${meta.unit}` : ""}
        </p>
        <p className="mt-1 text-[11px] text-gray-400">{meta.signal_group || "signal"}</p>
      </div>
    );
  };

  return (
    <div className="mb-8 space-y-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">
            {t("dashboard.latestSignals.title")}
          </h2>
          <p className="text-sm text-slate-500">
            {t("dashboard.latestSignals.subtitle")}
          </p>
        </div>
        <span className="text-sm text-gray-500">
          {t("dashboard.latestSignals.snapshot", { time: formattedDate })}
        </span>
      </div>

      <div>
        <h3 className="mb-2 text-md font-semibold text-gray-700">
          {t("dashboard.latestSignals.mainSignals")}
        </h3>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-6">
          {primarySignals.map((row) => renderCard(row))}
        </div>
      </div>

      {otherSignals.length > 0 ? (
        <div className="text-center">
          <button
            onClick={() => setShowMore(!showMore)}
            className="rounded-lg bg-violet-600 px-4 py-2 text-sm text-white hover:bg-violet-700"
          >
            {showMore
              ? t("dashboard.latestSignals.hideValues")
              : t("dashboard.latestSignals.moreValues")}
          </button>
        </div>
      ) : null}

      {showMore ? (
        <div>
          <h3 className="mb-2 text-md font-semibold text-gray-700">
            {t("dashboard.latestSignals.allSignals")}
          </h3>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-6">
            {otherSignals.map((row) => renderCard(row))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
