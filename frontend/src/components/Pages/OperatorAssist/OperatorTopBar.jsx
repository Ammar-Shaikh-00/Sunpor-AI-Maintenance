import { Bell, Clock3, Layers, Package, Sun, UserRound, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import {
  formatDisplayClock,
  formatDisplayDate,
  formatDuration,
} from "../../../utils/datetime";
import { useAppBranding } from "../../../store/backendStore";
import { translateDropdownValue } from "../../../utils/dropdownLabels";
import BrandLogo from "./BrandLogo";
import OperatorThemeToggle from "./OperatorThemeToggle";

function formatRunningTimeFromStart(startTimeIso, tick) {
  if (!startTimeIso) {
    return "—";
  }
  const start = new Date(startTimeIso).getTime();
  if (Number.isNaN(start)) {
    return "—";
  }
  const totalSeconds = Math.max(0, Math.floor((tick.getTime() - start) / 1000));
  return formatDuration(totalSeconds);
}

function Chip({ label, value, icon: Icon, highlight = false }) {
  return (
    <div className="flex min-w-0 flex-col rounded-xl bg-[#C5C8CF] px-3 py-2.5 ring-1 ring-slate-400/25">
      <div className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
        {Icon ? (
          <Icon className="h-3.5 w-3.5 shrink-0 text-blue-600" aria-hidden="true" />
        ) : null}
        <span className="truncate">{label}</span>
      </div>
      <div
        className={`mt-1 truncate text-sm font-bold sm:text-[15px] ${
          highlight ? "text-blue-600" : "text-slate-900"
        }`}
      >
        {value || "—"}
      </div>
    </div>
  );
}

export default function OperatorTopBar({
  context,
  loading,
  notifications = [],
  onLogout,
  operatorTheme = "dark",
  onToggleOperatorTheme,
}) {
  const { t } = useTranslation();
  const { appName, companyName, displayTimezone } = useAppBranding();
  const [now, setNow] = useState(() => new Date());
  const [openNotifications, setOpenNotifications] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const run = context?.production_run;
  const brand = companyName ? `${companyName} AI` : appName || "SCLERA AI";
  const count = notifications.length;

  const timeLabel = formatDisplayClock(now, { timeZone: displayTimezone });
  const dateLabel = formatDisplayDate(now, { timeZone: displayTimezone });

  const chips = run ? (
    <div className="grid min-w-0 flex-1 grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-6">
      <Chip
        label={t("operatorAssist.context.line")}
        value={run.line?.name}
        icon={Layers}
        highlight
      />
      <Chip
        label={t("operatorAssist.context.material")}
        value={run.material?.code || run.material?.description}
        icon={Package}
      />
      <Chip
        label={t("operatorAssist.context.shift")}
        value={translateDropdownValue(
          t,
          run.shift?.name || context?.resolved_shift?.name
        )}
        icon={Sun}
      />
      <Chip
        label={t("operatorAssist.context.operator")}
        value={context?.operator?.name || run.run_operator?.name}
        icon={UserRound}
      />
      <Chip
        label={t("operatorAssist.context.runId")}
        value={run.id != null ? String(run.id) : "—"}
        highlight
      />
      <Chip
        label={t("operatorAssist.context.runningTime")}
        value={formatRunningTimeFromStart(run.start_time, now)}
        icon={Clock3}
      />
    </div>
  ) : null;

  return (
    <header className="flex flex-col gap-3 lg:flex-row lg:items-center lg:gap-3 xl:gap-4">
      <div className="flex min-w-0 items-center justify-between gap-3 lg:contents">
        <div className="min-w-0 shrink-0">
          <BrandLogo
            className="h-12 w-auto max-w-[12rem] sm:h-14 sm:max-w-[16rem] lg:h-[3.75rem] lg:max-w-[17rem]"
            alt={brand}
            theme={operatorTheme}
          />
        </div>

        <div className="relative flex shrink-0 items-center gap-2 sm:gap-3 lg:order-last">
          <OperatorThemeToggle
            theme={operatorTheme}
            onToggle={onToggleOperatorTheme}
          />
          <button
            type="button"
            className="relative rounded-full p-2.5 text-slate-700 transition hover:bg-[#C5C8CF]"
            aria-label={t("operatorAssist.shell.notifications")}
            onClick={() => setOpenNotifications((prev) => !prev)}
          >
            <Bell className="h-5 w-5" />
            {count > 0 ? (
              <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white">
                {count > 9 ? "9+" : count}
              </span>
            ) : null}
          </button>

          {openNotifications ? (
            <div className="absolute right-0 top-11 z-40 w-[min(22rem,calc(100vw-1.5rem))] rounded-2xl border border-slate-300/50 bg-[#C5C8CF] p-3 shadow-xl sm:w-96">
              <div className="mb-2 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-900">
                  {t("operatorAssist.shell.notifications")}
                </h3>
                <button
                  type="button"
                  onClick={() => setOpenNotifications(false)}
                  className="rounded-lg p-1 text-slate-500 hover:bg-white"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
              {count === 0 ? (
                <p className="rounded-xl bg-[#B1B8C2]/50 px-3 py-4 text-sm text-slate-600">
                  {t("operatorAssist.shell.noNotifications")}
                </p>
              ) : (
                <ul className="max-h-72 space-y-2 overflow-y-auto">
                  {notifications.map((item) => (
                    <li
                      key={item.id}
                      className="rounded-xl bg-[#B1B8C2]/35 px-3 py-2"
                    >
                      <div className="text-sm font-semibold text-slate-900">
                        {item.title}
                      </div>
                      <div className="mt-0.5 break-words text-xs text-slate-600">
                        {item.message}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ) : null}

          <div className="hidden text-right sm:block">
            <div className="text-base font-bold leading-none text-slate-900 sm:text-lg">
              {timeLabel}
            </div>
            <div className="mt-1 text-xs text-slate-500">{dateLabel}</div>
          </div>

          {onLogout ? (
            <button
              type="button"
              onClick={onLogout}
              className="rounded-xl border border-slate-400/30 bg-[#C5C8CF] px-3 py-2 text-xs font-semibold text-slate-800 transition hover:bg-white"
            >
              {t("header.logout", { defaultValue: "Abmelden" })}
            </button>
          ) : null}
        </div>
      </div>

      {loading && !context ? (
        <div className="grid min-w-0 flex-1 grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-6">
          {Array.from({ length: 6 }).map((_, index) => (
            <div
              key={index}
              className="h-14 animate-pulse rounded-xl bg-[#C5C8CF]/80"
            />
          ))}
        </div>
      ) : !run ? (
        <div className="min-w-0 flex-1 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-900 ring-1 ring-amber-200">
          {t("operatorAssist.context.noActiveRun")}{" "}
          <Link
            to="/forms/production-start"
            className="font-semibold text-blue-700"
          >
            {t("operatorAssist.context.startRun")}
          </Link>
        </div>
      ) : (
        chips
      )}
    </header>
  );
}
