import { useEffect, useState } from "react";
import safeApi, { ENDPOINTS } from "../api/safeApi";

export function useFormOptions() {
  const [options, setOptions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      const res = await safeApi.get(ENDPOINTS.formOptions);
      if (res.fallback) {
        setError(res.error || "Failed to load form options");
      } else {
        setOptions(res.data);
      }
      setLoading(false);
    };

    load();
  }, []);

  return { options, loading, error };
}

export function useProductionRuns(limit = 20) {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);

  const reload = async () => {
    const res = await safeApi.get(`${ENDPOINTS.productionRuns}?limit=${limit}`);
    if (!res.fallback) {
      setRuns(res.data || []);
    }
    setLoading(false);
  };

  useEffect(() => {
    reload();
  }, [limit]);

  return { runs, loading, reload };
}
