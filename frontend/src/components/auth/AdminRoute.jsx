import { Navigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../context/authContext";
import { isOperatorOnlyUser } from "../../utils/permissions";

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
      <div className="rounded-2xl border border-slate-200 bg-[#C5C8CF] p-8 text-slate-500">
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

/** Operator home shell — only users with the Operator role (not Admin/SuperAdmin). */
export function OperatorRoute({ children }) {
  const { t } = useTranslation();
  const { user, isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-[#C5C8CF] p-8 text-slate-500">
        {t("common.loading")}
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!isOperatorOnlyUser(user)) {
    return <Navigate to="/" replace />;
  }

  return children;
}
