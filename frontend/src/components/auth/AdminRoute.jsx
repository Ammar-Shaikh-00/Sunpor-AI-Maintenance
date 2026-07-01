import { Navigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../context/authContext";

export default function PermissionGate({
  permission,
  anyOf = [],
  children,
  fallback = null,
}) {
  const { hasPermission, hasAnyPermission, isLoading } = useAuth();

  if (isLoading) {
    return fallback;
  }

  const allowed = permission
    ? hasPermission(permission)
    : hasAnyPermission(anyOf);

  if (!allowed) {
    return fallback;
  }

  return children;
}

export function AdminRoute({ permission, anyOf = [], children }) {
  const { t } = useTranslation();
  const { hasPermission, hasAnyPermission, isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-8 text-slate-500">
        {t("common.loading")}
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const allowed = permission
    ? hasPermission(permission)
    : hasAnyPermission(anyOf);

  if (!allowed) {
    return (
      <div className="rounded-2xl border border-rose-200 bg-rose-50 p-8 text-rose-700">
        {t("admin.accessDenied")}
      </div>
    );
  }

  return children;
}
