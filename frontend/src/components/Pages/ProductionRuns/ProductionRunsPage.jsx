import { useProductionRuns } from "../../../hooks/useSunporData";
import { FormCard } from "../OperatorForms/formUi";

export default function ProductionRunsPage() {
  const { runs, loading } = useProductionRuns(50);

  return (
    <FormCard
      title="Production Runs"
      description="Recent production runs recorded for this site."
    >
      {loading ? (
        <div className="text-slate-500">Loading production runs...</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b text-slate-500">
              <tr>
                <th className="px-3 py-2">ID</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Material Type</th>
                <th className="px-3 py-2">Shift</th>
                <th className="px-3 py-2">Start</th>
                <th className="px-3 py-2">Trial</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.id} className="border-b border-slate-100">
                  <td className="px-3 py-3 font-medium">#{run.id}</td>
                  <td className="px-3 py-3">{run.status}</td>
                  <td className="px-3 py-3">{run.material_type_id}</td>
                  <td className="px-3 py-3">{run.shift_id}</td>
                  <td className="px-3 py-3">
                    {run.start_time ? new Date(run.start_time).toLocaleString() : "--"}
                  </td>
                  <td className="px-3 py-3">{run.is_trial ? "Yes" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </FormCard>
  );
}
