import React, { useEffect, useState } from "react";
import TopSection from "./topSection";
import LatestSignalValues from "./LatestSignalValues";
import safeApi, { ENDPOINTS } from "../../../api/safeApi";
import { DashboardSkeleton } from "../../LoadingSkeleton/dashboardSkeleton";

export default function Dashboard({ backendStatus }) {
  const [summary, setSummary] = useState({
    signalCount: 0,
    productionRunCount: 0,
    backendStatus: "checking",
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const [signalsRes, runsRes] = await Promise.all([
          safeApi.get(ENDPOINTS.signalLatest),
          safeApi.get(`${ENDPOINTS.productionRuns}?limit=100`),
        ]);

        setSummary({
          signalCount: signalsRes.data?.length || 0,
          productionRunCount: runsRes.data?.length || 0,
          backendStatus: backendStatus || "online",
        });
      } catch (error) {
        console.error("Dashboard summary error:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSummary();
    const interval = setInterval(fetchSummary, 10000);
    return () => clearInterval(interval);
  }, [backendStatus]);

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  return (
    <>
      <TopSection summary={summary} />
      <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-sm text-slate-500">Active Signals</div>
          <div className="mt-2 text-4xl font-bold text-violet-700">{summary.signalCount}</div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-sm text-slate-500">Production Runs</div>
          <div className="mt-2 text-4xl font-bold text-violet-700">{summary.productionRunCount}</div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-sm text-slate-500">Backend Status</div>
          <div className="mt-2 text-2xl font-bold text-emerald-600 capitalize">
            {summary.backendStatus}
          </div>
        </div>
      </div>
      <LatestSignalValues />
    </>
  );
}
