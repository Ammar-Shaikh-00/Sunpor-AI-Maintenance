import api from "./index";
import { ENDPOINTS } from "./sunpor";

export const safeApi = {
  get: async (url, config = {}) => {
    try {
      const response = await api.get(url, config);
      return { fallback: false, data: response.data };
    } catch (error) {
      return {
        fallback: true,
        data: null,
        error: error?.response?.data?.detail || error?.message || "Request failed",
      };
    }
  },

  post: async (url, data = {}, config = {}) => {
    const response = await api.post(url, data, config);
    return { fallback: false, data: response.data };
  },

  put: async (url, data = {}, config = {}) => {
    const response = await api.put(url, data, config);
    return { fallback: false, data: response.data };
  },

  delete: async (url, config = {}) => {
    const response = await api.delete(url, config);
    return { fallback: false, data: response.data };
  },
};

export { ENDPOINTS };

export default safeApi;
