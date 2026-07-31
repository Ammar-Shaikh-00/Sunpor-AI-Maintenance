import { useTranslation } from "react-i18next";
import { useFormOptions, useProductionRuns } from "../../../hooks/useSunporData";
import { formatApiDateTime } from "../../../utils/datetime";
import { FormCard, getShiftName } from "../OperatorForms/formUi";

function getMaterialTypeName(options, materialTypeId) {
  const material = (options?.material_types || []).find(
    (item) => item.id === materialTypeId
  );
  return material?.code || material?.description || "—";
}

export default function ProductionRunsPage() {
  const { t } = useTranslation();
  const { options, loading: optionsLoading } = useFormOptions();
  const { runs, loading: runsLoading } = useProductionRuns(50);

  const loading = optionsLoading || runsLoading;

  return (
    <FormCard
      title={t("productionRuns.title")}
      description={t("productionRuns.description")}
    >
      {loading ? (
        <div className="text-slate-500">{t("productionRuns.loading")}</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b text-slate-500">
              <tr>
                <th className="px-3 py-2">{t("productionRuns.columns.id")}</th>
                <th className="px-3 py-2">{t("productionRuns.columns.status")}</th>
                <th className="px-3 py-2">{t("productionRuns.columns.materialType")}</th>
                <th className="px-3 py-2">{t("productionRuns.columns.shift")}</th>
                <th className="px-3 py-2">{t("productionRuns.columns.start")}</th>
                <th className="px-3 py-2">{t("productionRuns.columns.trial")}</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.id} className="border-b border-slate-100">
                  <td className="px-3 py-3 font-medium">#{run.id}</td>
                  <td className="px-3 py-3">{run.status}</td>
                  <td className="px-3 py-3">{getMaterialTypeName(options, run.material_type_id)}</td>
                  <td className="px-3 py-3">{getShiftName(options, run.shift_id)}</td>
                  <td className="px-3 py-3">
                    {run.start_time ? formatApiDateTime(run.start_time) : "—"}
                  </td>
                  <td className="px-3 py-3">
                    {run.is_trial ? t("common.yes") : t("common.no")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </FormCard>
  );
}
