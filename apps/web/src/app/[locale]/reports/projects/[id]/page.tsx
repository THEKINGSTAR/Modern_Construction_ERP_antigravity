"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import AppLayout from "@/components/AppLayout";
import { getProjectDashboard, getBudgetVsActual, ProjectDashboard, BudgetVsActualReport } from "@/lib/api";

export default function ProjectDashboardPage() {
  const params = useParams();
  const projectId = params.id as string;
  
  const [dashboard, setDashboard] = useState<ProjectDashboard | null>(null);
  const [budgetVsActual, setBudgetVsActual] = useState<BudgetVsActualReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [dashData, bvaData] = await Promise.all([
          getProjectDashboard(projectId),
          getBudgetVsActual(projectId)
        ]);
        setDashboard(dashData);
        setBudgetVsActual(bvaData);
      } catch (err) {
        console.error("Failed to load project dashboard data", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [projectId]);

  return (
    <AppLayout title="Project Analytics" subtitle="Financial performance and budget variance">
      <div className="p-6">
        {loading ? (
          <div className="flex h-32 items-center justify-center text-slate-400">Loading metrics...</div>
        ) : !dashboard || !budgetVsActual ? (
          <div className="text-red-400">Failed to load data.</div>
        ) : (
          <div className="space-y-6">
            
            {/* Top KPIs */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div className="text-xs text-slate-400 font-medium mb-1">Contract Value</div>
                <div className="text-2xl font-bold text-white">
                  ${Number(dashboard.current_contract_value).toLocaleString()}
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div className="text-xs text-slate-400 font-medium mb-1">Total Billed</div>
                <div className="text-2xl font-bold text-emerald-400">
                  ${Number(dashboard.billed).toLocaleString()}
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div className="text-xs text-slate-400 font-medium mb-1">Total Paid (Collections)</div>
                <div className="text-2xl font-bold text-emerald-400">
                  ${Number(dashboard.collected).toLocaleString()}
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div className="text-xs text-slate-400 font-medium mb-1">Gross Profit Margin</div>
                <div className="text-2xl font-bold text-white">
                  {Number(dashboard.margin_percentage).toFixed(2)}%
                </div>
              </div>
            </div>

            {/* Financial Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Cost Breakdown */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
                <div className="p-4 border-b border-slate-800 bg-slate-900/50">
                  <h2 className="text-sm font-semibold text-white">Cost Overview</h2>
                </div>
                <div className="p-4 space-y-4">
                  <div className="flex justify-between items-center p-3 bg-slate-800/50 rounded-lg">
                    <span className="text-sm font-medium text-slate-300">Original Budget</span>
                    <span className="font-mono text-white">${Number(dashboard.original_budget).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-slate-800/50 rounded-lg">
                    <span className="text-sm font-medium text-slate-300">Current Budget</span>
                    <span className="font-mono text-white">${Number(dashboard.current_budget).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-slate-800/50 rounded-lg">
                    <span className="text-sm font-medium text-slate-300">Committed Cost</span>
                    <span className="font-mono text-amber-400">${Number(dashboard.committed_cost).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-slate-800/50 rounded-lg">
                    <span className="text-sm font-medium text-slate-300">Actual Cost</span>
                    <span className="font-mono text-rose-400">${Number(dashboard.actual_cost).toLocaleString()}</span>
                  </div>
                </div>
              </div>

              {/* Forecast & Variance */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
                <div className="p-4 border-b border-slate-800 bg-slate-900/50">
                  <h2 className="text-sm font-semibold text-white">Forecast & Variance</h2>
                </div>
                <div className="p-4 space-y-4">
                  <div className="flex justify-between items-center p-3 bg-slate-800/50 rounded-lg">
                    <span className="text-sm font-medium text-slate-300">Forecast Cost (ETC)</span>
                    <span className="font-mono text-white">${Number(dashboard.forecast_cost).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-slate-800/50 rounded-lg">
                    <span className="text-sm font-medium text-slate-300">Estimate at Completion (EAC)</span>
                    <span className="font-mono text-white">${Number(dashboard.estimate_at_completion).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-slate-800/50 rounded-lg">
                    <span className="text-sm font-medium text-slate-300">Variance</span>
                    <span className={`font-mono ${Number(dashboard.variance) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      ${Number(dashboard.variance).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Budget vs Actual Details */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
              <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
                <h2 className="text-sm font-semibold text-white">Budget vs Actual by Cost Code</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="bg-slate-800/50 text-xs uppercase text-slate-400">
                    <tr>
                      <th className="px-4 py-3 font-medium">Cost Code</th>
                      <th className="px-4 py-3 font-medium text-right">Current Budget</th>
                      <th className="px-4 py-3 font-medium text-right">Actual Cost</th>
                      <th className="px-4 py-3 font-medium text-right">Variance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {budgetVsActual.details.map((cc) => (
                      <tr key={cc.cost_code_id} className="hover:bg-slate-800/20 transition-colors">
                        <td className="px-4 py-3 font-medium text-white">{cc.cost_code_name}</td>
                        <td className="px-4 py-3 text-right font-mono">${Number(cc.current_budget).toLocaleString()}</td>
                        <td className="px-4 py-3 text-right font-mono">${Number(cc.actual_cost).toLocaleString()}</td>
                        <td className={`px-4 py-3 text-right font-mono ${Number(cc.variance) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          ${Number(cc.variance).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                    {budgetVsActual.details.length === 0 && (
                      <tr>
                        <td colSpan={4} className="px-4 py-8 text-center text-slate-500">
                          No cost code data available.
                        </td>
                      </tr>
                    )}
                  </tbody>
                  <tfoot className="bg-slate-900 font-semibold text-white border-t border-slate-700">
                    <tr>
                      <td className="px-4 py-3">Total</td>
                      <td className="px-4 py-3 text-right font-mono">${Number(budgetVsActual.total_budget).toLocaleString()}</td>
                      <td className="px-4 py-3 text-right font-mono">${Number(budgetVsActual.total_actual).toLocaleString()}</td>
                      <td className={`px-4 py-3 text-right font-mono ${Number(budgetVsActual.total_variance) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                        ${Number(budgetVsActual.total_variance).toLocaleString()}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>

          </div>
        )}
      </div>
    </AppLayout>
  );
}
