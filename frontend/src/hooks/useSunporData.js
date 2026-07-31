import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import safeApi, { ENDPOINTS } from "../api/safeApi";
import { PRODUCTION_RUN_STATUS } from "../constants/productionRun";

const EMPTY_OPTIONS = {
  companies: [],
  shifts: [],
  material_types: [],
  production_lines: [],
  dropdowns: {},
  current_user_id: null,
};

export function useFormOptions() {
  const { t } = useTranslation();
  const [options, setOptions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      const res = await safeApi.get(ENDPOINTS.formOptions);

      if (res.fallback) {
        const message =
          typeof res.error === "string"
            ? res.error
            : t("forms.common.loadOptionsFailed");
        setError(message);
        setOptions(EMPTY_OPTIONS);
        toast.error(message);
      } else {
        setOptions(res.data);
        setError(null);
      }

      setLoading(false);
    };

    load();
  }, [t]);

  return { options, loading, error };
}

export function useProductionRuns(limit = 50, { runningOnly = false } = {}) {
  const { t } = useTranslation();
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const reload = async () => {
    const res = await safeApi.get(`${ENDPOINTS.productionRuns}?limit=${limit}`);

    if (res.fallback) {
      const message =
        typeof res.error === "string"
          ? res.error
          : t("forms.common.loadRunsFailed");
      setError(message);
      setRuns([]);
    } else {
      const items = res.data || [];
      setRuns(
        runningOnly
          ? items.filter((run) => run.status === PRODUCTION_RUN_STATUS.RUNNING)
          : items
      );
      setError(null);
    }

    setLoading(false);
  };

  useEffect(() => {
    reload();
  }, [limit]);

  return { runs, loading, error, reload };
}
