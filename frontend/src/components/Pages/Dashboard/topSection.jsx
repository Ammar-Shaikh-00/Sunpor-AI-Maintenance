import React from "react";
import { useTranslation } from "react-i18next";
import { useAppBranding } from "../../../store/backendStore";

export default function TopSection({ summary }) {
  const { t } = useTranslation();
  const { companyName, tagline } = useAppBranding();
  const dashboardTitle = companyName
    ? t("dashboard.title", { company: companyName })
    : t("dashboard.titleFallback");

  return (
    <div className="mb-8">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="mb-2 text-3xl text-slate-900">{dashboardTitle}</h1>
          <p className="text-sm text-slate-600">
            {tagline || t("dashboard.subtitle")}
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-4">
        <div className="min-w-[180px] flex-1 rounded-xl border border-slate-200/80 bg-white/95 px-5 py-3 shadow-md backdrop-blur-sm">
          <div className="mb-1 flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-emerald-500" />
            <span className="text-xs text-slate-500">{t("dashboard.dataPipeline")}</span>
          </div>
          <div className="text-base text-emerald-600">{t("dashboard.mqttActive")}</div>
        </div>

        <div className="min-w-[180px] flex-1 rounded-xl border border-slate-200/80 bg-white/95 px-5 py-3 shadow-md backdrop-blur-sm">
          <div className="mb-1 flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-violet-500" />
            <span className="text-xs text-slate-500">
              {companyName
                ? t("dashboard.backendCompany", { company: companyName.toUpperCase() })
                : t("dashboard.backend")}
            </span>
          </div>
          <div className="text-base capitalize text-violet-700">
            {t(`login.status.${summary?.backendStatus || "online"}`, {
              defaultValue: summary?.backendStatus || "online",
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
