import { useTranslation } from "react-i18next";

const DemoCredentials = ({ companyName }) => {
  const { t } = useTranslation();
  const adminLabel = companyName
    ? t("login.adminForCompany", { company: companyName })
    : t("login.roles.admin");

  return (
    <div className="mt-6 pt-6 border-t border-slate-200 space-y-3">
      <p className="text-xs text-slate-500 text-center">
        {t("login.demoCredentials")}:
      </p>

      <div className="flex flex-col gap-1 text-xs">
        <div className="flex justify-between items-center p-2 bg-slate-50 rounded border border-slate-200 gap-3">
          <span className="text-slate-500 shrink-0">{adminLabel}:</span>
          <span className="text-slate-700 font-mono text-right">
            admin@sunpor.local / Admin@123456
          </span>
        </div>
      </div>
    </div>
  );
};

export default DemoCredentials;
