import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import safeApi, { ENDPOINTS } from "../api/safeApi";

export const SIGNAL_CHART_RANGES = {
  "1h": { hours: 1 },
  "1d": { hours: 24 },
  "1w": { hours: 24 * 7 },
  "1m": { hours: 24 * 30 },
};

export function getRangeWindow(rangeKey, now = new Date()) {
  const config = SIGNAL_CHART_RANGES[rangeKey] || SIGNAL_CHART_RANGES["1h"];
  const end = now;
  const start = new Date(end.getTime() - config.hours * 60 * 60 * 1000);
  return { start, end };
}

export function useSignalCatalogForCharts() {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      const res = await safeApi.get(`${ENDPOINTS.signalCatalog}?limit=500`);
      if (cancelled) {
        return;
      }

      if (res.fallback) {
        setError(
          typeof res.error === "string"
            ? res.error
            : "Failed to load signal catalog"
        );
        setSignals([]);
      } else {
        const rows = Array.isArray(res.data) ? res.data : [];
        setSignals(
          rows
            .filter((item) => item?.active !== false)
            .sort((a, b) =>
              String(a.display_name || a.wincc_tag || "").localeCompare(
                String(b.display_name || b.wincc_tag || ""),
                "de"
              )
            )
        );
        setError(null);
      }
      setLoading(false);
    };

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const groups = useMemo(() => {
    const values = new Set();
    signals.forEach((signal) => {
      if (signal.signal_group) {
        values.add(signal.signal_group);
      }
    });
    return [...values].sort((a, b) => a.localeCompare(b, "de"));
  }, [signals]);

  return { signals, groups, loading, error };
}

export function useSignalChartSeries(signalId, rangeKey, enabled) {
  const [points, setPoints] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const requestIdRef = useRef(0);

  const fetchSeries = useCallback(async () => {
    if (!signalId || !enabled) {
      return;
    }

    const requestId = ++requestIdRef.current;
    setLoading(true);
    setError(null);

    const { start, end } = getRangeWindow(rangeKey);
    const params = new URLSearchParams({
      signal_id: String(signalId),
      start_time: start.toISOString(),
      end_time: end.toISOString(),
      max_points: "400",
    });

    const res = await safeApi.get(`${ENDPOINTS.signalChart}?${params.toString()}`);
    if (requestId !== requestIdRef.current) {
      return;
    }

    if (res.fallback) {
      setPoints([]);
      setError(
        typeof res.error === "string" ? res.error : "Failed to load chart data"
      );
    } else {
      const series = (res.data?.points || []).map((point) => ({
        timestamp: point.timestamp,
        value: point.value,
      }));
      setPoints(series);
      setError(null);
    }
    setLoading(false);
  }, [signalId, rangeKey, enabled]);

  useEffect(() => {
    if (!enabled) {
      return undefined;
    }

    fetchSeries();
    return () => {
      requestIdRef.current += 1;
    };
  }, [enabled, fetchSeries]);

  return { points, loading, error, refetch: fetchSeries };
}
