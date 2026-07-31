import { useCallback, useState } from "react";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import safeApi from "../api/safeApi";
import { getApiErrorMessage } from "../utils/apiError";

/**
 * Shared delete handler for recent-entry lists. Deletion is restricted to
 * SuperAdmin users on the backend; this hook simply wires up the request,
 * confirmation, feedback, and a refresh callback.
 */
export function useDeleteEntry(endpoint, onDeleted) {
  const { t } = useTranslation();
  const [deletingId, setDeletingId] = useState(null);

  const onDelete = useCallback(
    async (entry) => {
      if (!entry?.id) {
        return;
      }

      const confirmed = window.confirm(
        t("forms.common.deleteConfirm", { id: entry.id })
      );
      if (!confirmed) {
        return;
      }

      setDeletingId(entry.id);
      try {
        await safeApi.delete(`${endpoint}/${entry.id}`);
        toast.success(t("forms.common.deleteSuccess"));
        onDeleted?.(entry);
      } catch (error) {
        toast.error(getApiErrorMessage(error, t("forms.common.deleteError")));
      } finally {
        setDeletingId(null);
      }
    },
    [endpoint, onDeleted, t]
  );

  return { onDelete, deletingId };
}
