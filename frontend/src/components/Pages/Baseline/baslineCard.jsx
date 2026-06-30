import { useTranslation } from "react-i18next";


const BaselineCard = ({
    baseline,
    onEdit,
    deleteMutation
}) => {

    const { t } = useTranslation();

    return (
        <div className="bg-slate-900 p-4 rounded-xl border border-slate-700 flex justify-between items-center">
            
            <div>
                <h3 className="text-lg font-semibold text-white">
                    {baseline.baseline_name}
                </h3>
                <p className="text-sm text-slate-400">
                    {t("baseline.id")}: {baseline.id}
                </p>
            </div>

            <div className="flex gap-2">
                <button
                    onClick={() => onEdit(baseline)}
                    className="px-3 py-1 bg-blue-600 hover:bg-blue-500 rounded text-white text-sm"
                >
                    {t("common.edit")}
                </button>

                <button
                    onClick={() => deleteMutation.mutate(baseline.id)}
                    className="px-3 py-1 bg-red-600 hover:bg-red-500 rounded text-white text-sm"
                >
                    {t("common.delete")}
                </button>
            </div>
        </div>
    );
};

export default BaselineCard;