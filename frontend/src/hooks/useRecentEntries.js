import { useCallback, useEffect, useRef, useState } from "react";
import safeApi, { ENDPOINTS } from "../api/safeApi";
import { sortEntriesByKeys } from "../utils/formEntryUtils";

const DEFAULT_SORT_KEYS = [
  "created_at",
  "event_time",
  "input_time",
  "start_time",
  "from_time",
];

export function useRecentEntries(
  endpoint,
  { limit = 10, filter, sortKeys, refreshKey = 0 } = {}
) {
  const [entries, setEntries] = useState([]);
  const [runsById, setRunsById] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const filterRef = useRef(filter);
  const sortKeysRef = useRef(sortKeys ?? DEFAULT_SORT_KEYS);
  const hasLoadedRef = useRef(false);

  filterRef.current = filter;
  sortKeysRef.current = sortKeys ?? DEFAULT_SORT_KEYS;

  const reload = useCallback(async () => {
    if (!hasLoadedRef.current) {
      setLoading(true);
    }

    const fetchLimit = Math.max(limit * 3, 30);
    const [entriesRes, runsRes] = await Promise.all([
      safeApi.get(`${endpoint}?limit=${fetchLimit}`),
      safeApi.get(`${ENDPOINTS.productionRuns}?limit=200`),
    ]);

    if (entriesRes.fallback) {
      setError(typeof entriesRes.error === "string" ? entriesRes.error : null);
      setEntries([]);
    } else {
      let items = entriesRes.data || [];
      if (filterRef.current) {
        items = items.filter(filterRef.current);
      }
      setEntries(sortEntriesByKeys(items, sortKeysRef.current).slice(0, limit));
      setError(null);
    }

    if (!runsRes.fallback) {
      const map = {};
      for (const run of runsRes.data || []) {
        map[run.id] = run;
      }
      setRunsById(map);
    }

    hasLoadedRef.current = true;
    setLoading(false);
  }, [endpoint, limit, refreshKey]);

  useEffect(() => {
    reload();
  }, [reload]);

  return { entries, runsById, loading, error, reload };
}
