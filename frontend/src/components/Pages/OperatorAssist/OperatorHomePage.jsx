import { ClipboardList } from "lucide-react";
import { useMemo, useState } from "react";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import cleaningIcon from "../../../assets/operator-form-icons-png/Cleaning.png";
import extruderIcon from "../../../assets/operator-form-icons-png/Extruder-events.png";
import materialBehaviorIcon from "../../../assets/operator-form-icons-png/Material-behaviour.png";
import materialBlockIcon from "../../../assets/operator-form-icons-png/Material-block.png";
import granulatorIcon from "../../../assets/operator-form-icons-png/Messer-Granulator.png";
import productionStartIcon from "../../../assets/operator-form-icons-png/Production-start.png";
import qualityIcon from "../../../assets/operator-form-icons-png/Quality.png";
import reportProblemIcon from "../../../assets/operator-form-icons-png/Report-problem.png";
import api from "../../../api";
import { ENDPOINTS } from "../../../api/sunpor";
import { useAuth } from "../../../context/authContext";
import {
  useOperatorContext,
  useOperatorSuggestions,
} from "../../../hooks/useOperatorAssist";
import OperatorAlertCard from "./OperatorAlertCard";
import OperatorTopBar from "./OperatorTopBar";
import ReportIssueWizard from "./ReportIssueWizard";

const ACTION_CARDS = [
  {
    id: "productionStart",
    path: "/forms/production-start",
    image: productionStartIcon,
    titleKey: "operatorAssist.cards.productionStart.title",
    descriptionKey: "operatorAssist.cards.productionStart.description",
  },
  {
    id: "extruderEvents",
    path: "/forms/extruder-events",
    image: extruderIcon,
    titleKey: "operatorAssist.cards.extruderEvents.title",
    descriptionKey: "operatorAssist.cards.extruderEvents.description",
  },
  {
    id: "granulatorEvents",
    path: "/forms/granulator-events",
    image: granulatorIcon,
    titleKey: "operatorAssist.cards.granulatorEvents.title",
    descriptionKey: "operatorAssist.cards.granulatorEvents.description",
  },
  {
    id: "cleaning",
    path: "/forms/cleaning",
    image: cleaningIcon,
    titleKey: "operatorAssist.cards.cleaning.title",
    descriptionKey: "operatorAssist.cards.cleaning.description",
  },
  {
    id: "faults",
    path: null,
    wizard: true,
    image: reportProblemIcon,
    titleKey: "operatorAssist.cards.faults.title",
    descriptionKey: "operatorAssist.cards.faults.description",
  },
  {
    id: "materialBehavior",
    path: "/forms/material-behavior",
    image: materialBehaviorIcon,
    titleKey: "operatorAssist.cards.materialBehavior.title",
    descriptionKey: "operatorAssist.cards.materialBehavior.description",
  },
  {
    id: "dailyQuality",
    path: "/forms/daily-quality",
    image: qualityIcon,
    titleKey: "operatorAssist.cards.dailyQuality.title",
    descriptionKey: "operatorAssist.cards.dailyQuality.description",
  },
  {
    id: "materialBlocking",
    path: "/forms/material-blocking",
    image: materialBlockIcon,
    titleKey: "operatorAssist.cards.materialBlocking.title",
    descriptionKey: "operatorAssist.cards.materialBlocking.description",
  },
];

export default function OperatorHomePage() {
  const { t } = useTranslation();
  const { logout } = useAuth();
  const { context, loading: contextLoading } = useOperatorContext();
  const {
    data: suggestionData,
    loading: suggestionLoading,
    refresh,
  } = useOperatorSuggestions();
  const [showWizard, setShowWizard] = useState(false);
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
      />

      <OperatorAlertCard
        suggestion={suggestion}
        metrics={metrics}
        loading={suggestionLoading}
        busyId={busyId}
        onConfirm={(item) => confirmSuggestion(item, "confirm")}
        onDismiss={(item) => confirmSuggestion(item, "dismiss")}
      />

      <section>
        <div className="mb-4 flex items-center gap-3 overflow-hidden rounded-2xl bg-gradient-to-r from-blue-700 via-blue-600 to-blue-500 px-4 py-3.5 shadow-sm ring-1 ring-blue-900/10 sm:mb-5 sm:gap-4 sm:px-5 sm:py-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white/15 text-white ring-1 ring-white/25 backdrop-blur sm:h-12 sm:w-12">
            <ClipboardList className="h-5 w-5 sm:h-6 sm:w-6" aria-hidden="true" />
          </div>
          <div className="min-w-0">
            <h2 className="text-lg font-bold leading-tight text-white sm:text-xl">
              {t("operatorAssist.captureTitle")}
            </h2>
            <p className="mt-0.5 text-xs text-blue-50/90 sm:text-sm">
              {t("operatorAssist.captureSubtitle")}
            </p>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:gap-3.5 md:grid-cols-4">
          {ACTION_CARDS.map((card) => {
            const content = (
              <>
                <div className="mb-2.5 flex h-14 w-full items-center justify-center sm:mb-3 sm:h-16 lg:h-20">
                  <img
                    src={card.image}
                    alt=""
                    aria-hidden="true"
                    loading="lazy"
                    draggable="false"
                    className="h-full w-auto max-w-full object-contain"
                  />
                </div>
                <div className="text-sm font-bold leading-snug text-slate-900 sm:text-base lg:text-lg">
                  {t(card.titleKey)}
                </div>
                <div className="mt-1 max-w-[14rem] text-[11px] leading-snug text-slate-500 sm:text-sm">
                  {t(card.descriptionKey)}
                </div>
              </>
            );

            const className =
              "flex min-h-[140px] flex-col items-center justify-center rounded-2xl bg-[#C5C8CF] px-3 py-5 text-center shadow-sm ring-1 ring-slate-400/20 transition hover:-translate-y-0.5 hover:bg-[#CDD0D6] hover:shadow-md active:scale-[0.99] sm:min-h-[160px] sm:rounded-3xl sm:px-4 sm:py-6";

            if (card.wizard) {
              return (
                <button
                  key={card.id}
                  type="button"
                  onClick={() => setShowWizard(true)}
                  className={className}
                >
                  {content}
                </button>
              );
            }

            return (
              <Link key={card.id} to={card.path} className={className}>
                {content}
              </Link>
            );
          })}
        </div>
      </section>

      {showWizard ? (
        <ReportIssueWizard
          productionRunId={runId}
          onClose={() => setShowWizard(false)}
        />
      ) : null}
    </div>
  );
}
