import { ArrowLeft } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link, useLocation } from "react-router-dom";

export default function OperatorNavStrip() {
  const { t } = useTranslation();
  const location = useLocation();

  if (location.pathname === "/operator" || location.pathname === "/") {
    return null;
  }

  return (
    <div className="mb-4 flex items-center">
      <Link
        to="/operator"
        className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-slate-400/30 bg-[#C5C8CF] px-4 text-sm font-semibold text-blue-700"
      >
        <ArrowLeft className="h-4 w-4" />
        {t("operatorAssist.shell.backHome")}
      </Link>
    </div>
  );
}
