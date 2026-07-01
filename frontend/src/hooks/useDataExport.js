import { useCallback, useEffect, useState } from "react";
import safeApi, { ENDPOINTS } from "../api/safeApi";

export function useDataExportCatalog() {
  const [catalog, setCatalog] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      const res = await safeApi.get(ENDPOINTS.dataExportCatalog);
      if (res.fallback) {
        setError(res.error || "Failed to load export catalog");
        setCatalog([]);
      } else {
        setCatalog(res.data?.datasets || []);
        setError(null);
      }
      setLoading(false);
    };

    load();
  }, []);

  return { catalog, loading, error };
}

export function useDataExportQuery() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async (params) => {
    setLoading(true);
    setError(null);

    const search = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        search.set(key, String(value));
      }
    });

    const res = await safeApi.get(`${ENDPOINTS.dataExportQuery}?${search.toString()}`);

    if (res.fallback) {
      setError(typeof res.error === "string" ? res.error : "Query failed");
      setData(null);
    } else {
      setData(res.data);
      setError(null);
    }

    setLoading(false);
    return res.fallback ? null : res.data;
  }, []);

  return { data, loading, error, fetchData };
}
