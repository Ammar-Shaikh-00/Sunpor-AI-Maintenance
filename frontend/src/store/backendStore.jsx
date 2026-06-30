import { create } from "zustand";
import api from "../api";
import { ENDPOINTS } from "../api/sunpor";

const defaultAppConfig = {
  appName: "",
  companyName: "",
  displayTitle: "",
  tagline: "",
};

export const useBackendStore = create((set, get) => ({
  status: "checking",
  lastCheck: null,
  healthCheckInterval: null,
  appConfig: defaultAppConfig,

  setStatus: (status) => set({ status }),
  setLastCheck: (date) => set({ lastCheck: date }),

  startHealthCheck: () => {
    const checkHealth = async () => {
      try {
        const response = await api.get(ENDPOINTS.appInfo);
        const data = response.data || {};

        set({
          status: "online",
          lastCheck: new Date(),
          appConfig: {
            appName: data.app_name || "",
            companyName: data.company_name || "",
            displayTitle: data.display_title || data.app_name || "",
            tagline: data.tagline || "",
          },
        });
      } catch {
        set({
          status: "offline",
          lastCheck: new Date(),
        });
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    set({ healthCheckInterval: interval });
  },

  stopHealthCheck: () => {
    const interval = get().healthCheckInterval;
    if (interval) {
      clearInterval(interval);
      set({ healthCheckInterval: null });
    }
  },
}));

export function useAppBranding() {
  const appConfig = useBackendStore((state) => state.appConfig);
  const status = useBackendStore((state) => state.status);

  return {
    appName: appConfig.displayTitle || appConfig.appName || "Predictive Maintenance",
    companyName: appConfig.companyName || "",
    tagline: appConfig.tagline || "",
    backendOnline: status === "online",
    backendStatus: status,
  };
}
