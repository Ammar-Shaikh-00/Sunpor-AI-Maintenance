import { useMemo, useState } from "react";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import api from "../../../api";
import { ENDPOINTS } from "../../../api/sunpor";
import { useAuth } from "../../../context/authContext";
import {
  useOperatorContext,
  useOperatorSuggestions,
} from "../../../hooks/useOperatorAssist";
import OperatorAlertCard from "./OperatorAlertCard";
import OperatorCaptureHub from "./OperatorCaptureHub";
import OperatorTopBar from "./OperatorTopBar";

export default function OperatorHomePage({
  operatorTheme = "dark",
  onToggleOperatorTheme,
}) {
  const { t } = useTranslation();
  const { logout } = useAuth();
  const { context, loading: contextLoading } = useOperatorContext();
  const {
    data: suggestionData,
    loading: suggestionLoading,
    refresh,
  } = useOperatorSuggestions();
  const [busyId, setBusyId] = useState(null);

  const suggestion = useMemo(
    () => suggestionData?.suggestions?.[0] || null,
    [suggestionData]
  );
  const metrics = suggestionData?.metrics || null;
  const runId = context?.production_run?.id || suggestionData?.production_run_id;

  const confirmSuggestion = async (item, action) => {
    if (!runId && action !== "dismiss") {
      toast.error(t("operatorAssist.suggestions.needRun"));
      return;
    }

    setBusyId(`${item.id}-${action}`);
    try {
      await api.post(ENDPOINTS.operatorSuggestionConfirm, {
        suggestion_id: item.id,
        production_run_id: runId,
        action,
        level_1: item.suggested_event?.level_1,
        level_2: item.suggested_event?.level_2,
        level_3: item.suggested_event?.level_3,
        comment: item.message,
      });
      toast.success(
        action === "dismiss"
          ? t("operatorAssist.suggestions.dismissed")
          : t("operatorAssist.suggestions.confirmed")
      );
      refresh();
    } catch {
      toast.error(t("operatorAssist.suggestions.error"));
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="flex w-full flex-col gap-4 sm:gap-5">
      <OperatorTopBar
        context={context}
        loading={contextLoading}
        notifications={suggestionData?.notifications || []}
        onLogout={logout}
        operatorTheme={operatorTheme}
        onToggleOperatorTheme={onToggleOperatorTheme}
      />

      <OperatorAlertCard
        suggestion={suggestion}
        metrics={metrics}
        loading={suggestionLoading}
        busyId={busyId}
        onConfirm={(item) => confirmSuggestion(item, "confirm")}
        onDismiss={(item) => confirmSuggestion(item, "dismiss")}
      />

      <OperatorCaptureHub />
    </div>
  );
}
