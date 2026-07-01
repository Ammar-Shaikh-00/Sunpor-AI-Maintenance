import { useState } from "react";
import { useTranslation } from "react-i18next";

/* ---------------- Status Chip ---------------- */
function StatusChip({ status, label }) {
  const map = {
    available: "text-green-700 bg-green-50 ring-green-600/20",
    unavailable: "text-amber-700 bg-amber-50 ring-amber-600/20",
    error: "text-red-700 bg-red-50 ring-red-600/20",
  };

  const icon =
    status === "available" ? (
      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M20 6L9 17l-5-5" />
      </svg>
    ) : status === "error" ? (
      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
        <path d="M12 9v4" />
        <path d="M12 17h.01" />
      </svg>
    ) : (
      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="3" />
      </svg>
    );

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ring-1 ${map[status]}`}
    >
      {icon}
      {label}
    </span>
  );
}

/* ---------------- Alert Toggle ---------------- */
function AlertToggle({ status, onToggle, loading }) {
  const { t } = useTranslation();

  return (
    <div className="flex gap-2 items-center">
      <span className="text-xs">{t("header.alertService")}</span>
      <button
        onClick={onToggle}
        disabled={loading}
        className={`flex items-center gap-2 px-1 py-1 rounded-xl border text-sm font-medium transition ${
          status
            ? "bg-green-50 text-green-700 border-green-200"
            : "bg-red-50 text-red-700 border-red-200"
        } ${loading ? "opacity-50 cursor-not-allowed" : "hover:scale-105"}`}
      >
        <div
          className={`w-7 h-3 flex items-center rounded-full p-1 transition ${
            status ? "bg-green-500" : "bg-gray-300"
          }`}
        >
          <div
            className={`bg-white w-3 h-3 rounded-full shadow transform transition ${
              status ? "translate-x-3" : ""
            }`}
          />
        </div>

        <span className="text-xs">
          {status ? t("common.active") : t("common.inactive")}
        </span>
      </button>
    </div>
  );
}

/* ---------------- User Menu ---------------- */
function UserMenu({ user, role, onLogout }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);

  const name = user?.name || user?.email || t("header.user");

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 rounded-full shadow-md px-3 py-1.5 bg-white hover:bg-gray-50"
      >
        <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
          <span className="text-sm font-medium text-purple-700">
            {name.charAt(0).toUpperCase()}
          </span>
        </div>

        <span className="hidden sm:inline text-sm">{role}</span>

        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-48 bg-white  rounded-lg shadow z-50">
          <div className="px-4 py-3 border-b">
            <div className="text-sm font-medium">
              {t("header.role")}: {role}
            </div>
            <div className="text-xs text-gray-500 truncate">{user?.email}</div>
          </div>

          <button
            onClick={() => {
              onLogout();
              setOpen(false);
            }}
            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50"
          >
            {t("header.logout")}
          </button>
        </div>
      )}
    </div>
  );
}

/* ---------------- Main Topbar ---------------- */
export default function Header({
  appName = "My App",
  tagline = "Tagline here",
  user = {},
  role = "ADMIN",
  aiStatus = null,
  aiLoading = false,
  onLogout = () => {},
  onMenuClick,
  backendStatus,
}) {
  const { t } = useTranslation();

  /* --------- Status Logic --------- */
  const getStatus = () => {
    if (aiLoading) return "unavailable";
    if (!aiStatus) return "unavailable";

    if (aiStatus === "healthy" || aiStatus === "operational")
      return "available";

    if (aiStatus === "error" || aiStatus === "degraded")
      return "error";

    return "unavailable";
  };

  // const backendStatus = useBackendStore((state) => state.status);

  // Dynamic KI Status Label
  const statusLabel = aiLoading
    ? t("header.loading")
    : t("header.kiStatus", { status: aiStatus || t("header.unknown") });

  return (
    <header className="mb-6">
      <div className="flex flex-col lg:flex-row lg:justify-between gap-4 p-6 m-2 mt-6 rounded-xl bg-white shadow-sm">

        {/* Left */}
        <div>
          <h1 className="text-2xl font-semibold bg-gradient-to-r from-purple-700 to-purple-500 bg-clip-text text-transparent">
            {appName}
          </h1>

          <div className="text-xs uppercase text-gray-500 mt-1">
            {tagline}
          </div>
        </div>

        {/* Right */}
        <div className="flex items-center gap-3">

          {/* Mobile menu */}
          {onMenuClick && (
            <button
              onClick={onMenuClick}
              className="lg:hidden w-10 h-10 shadow-md rounded-xl hover:scale-105 flex items-center justify-center"
            >
              ☰
            </button>
          )}

          {/* Status Chip */}
          <StatusChip status={getStatus()} label={statusLabel} />

          {/* User Menu */}
          <UserMenu user={user} role={role} onLogout={onLogout} />
        </div>
      </div>
    </header>
  );
}