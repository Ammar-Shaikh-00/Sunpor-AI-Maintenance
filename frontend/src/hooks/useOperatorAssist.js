import { useCallback, useEffect, useState } from "react";
import api from "../api";
import { ENDPOINTS } from "../api/sunpor";

export function useOperatorContext(pollMs = 15000) {
  const [context, setContext] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const response = await api.get(ENDPOINTS.operatorContext);
      setContext(response.data);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    if (!pollMs) {
      return undefined;
    }
    const timer = setInterval(refresh, pollMs);
    return () => clearInterval(timer);
  }, [pollMs, refresh]);

  return { context, loading, error, refresh };
}

export function useOperatorSuggestions(pollMs = 20000) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const response = await api.get(ENDPOINTS.operatorSuggestions);
      setData(response.data);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    if (!pollMs) {
      return undefined;
    }
    const timer = setInterval(refresh, pollMs);
    return () => clearInterval(timer);
  }, [pollMs, refresh]);

  return { data, loading, error, refresh };
}
