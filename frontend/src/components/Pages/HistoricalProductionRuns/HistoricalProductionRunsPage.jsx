import { useEffect, useState } from "react";
import safeApi from "../../../api/safeApi";

import SidebarFilters from "./components/SidebarFilters";
import TopHeader from "./components/TopHeader";
import SummaryCards from "./components/SummaryCards";
import ProductionRunsTable from "./components/ProductionRunsTable";
import TrendChart from "./components/TrendChart";
import ScrapDistribution from "./components/ScrapDistribution";
import DeviationsTable from "./components/DeviationsTable";
import ProductionRunPage from "../ProductionRun/ProductionRun";

export default function HistoricalProductionRunsPage() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchRuns = async () => {
    try {
      const res = await safeApi.get("/production-run/?limit=10");

      setRuns(res.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  if (loading) {
    return <div className="p-10">Loading...</div>;
  }

  return (
    <div className="flex bg-slate-50 min-h-screen">

      {/* SIDEBAR */}
      {/* <SidebarFilters /> */}

      {/* MAIN */}
      <div className="flex-1 p-6 space-y-6 overflow-auto">

        <TopHeader />

        <SummaryCards runs={runs} />
        
        <ProductionRunsTable runs={runs} />
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

          {/* <div className="xl:col-span-2">
            <TrendChart runs={runs} />
          </div> */}

          <ScrapDistribution runs={runs} />

        </div>

        {/* <DeviationsTable /> */}

      </div>
    </div>
  );
}