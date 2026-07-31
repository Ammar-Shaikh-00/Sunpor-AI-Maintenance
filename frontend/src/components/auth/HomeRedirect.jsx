import { Navigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../context/authContext";
import { getHomePath } from "../../utils/permissions";
import Dashboard from "../Pages/Dashboard/dashboard";

export default function HomeRedirect({ backendStatus }) {
  const { t } = useTranslation();
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-[#C5C8CF] p-8 text-slate-500">
        {t("common.loading")}
      </div>
    );
  }

  const homePath = getHomePath(user);
  if (homePath !== "/") {
    return <Navigate to={homePath} replace />;
  }

  return <Dashboard backendStatus={backendStatus} />;
}
