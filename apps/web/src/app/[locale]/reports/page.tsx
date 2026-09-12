"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import { getExecutiveDashboard, ExecutiveDashboard } from "@/lib/api";

export default function ReportsDashboardPage() {
  const [data, setData] = useState<ExecutiveDashboard | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const dashboardData = await getExecutiveDashboard();
        setData(dashboardData);
      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <AppLayout title="Executive Analytics Hub" subtitle="Real-time portfolio and financial metrics">
      <div className="p-6">
        {loading ? (
          <div className="flex h-32 items-center justify-center text-slate-400">Loading metrics...</div>
        ) : !data ? (
          <div className="text-red-400">Failed to load data.</div>
        ) : (
          <div className="space-y-6">
            {/* Top KPIs */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div className="text-xs text-slate-400 font-medium mb-1">Total Contract Value</div>
                <div className="text-2xl font-bold text-white">
                  ${Number(data.total_contract_value).toLocaleString()}
                </div>
                <div className="text-[10px] text-emerald-400 mt-1 flex items-center gap-1">
                  <span>Across {data.total_active_contracts} Active Contracts</span>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div className="text-xs text-slate-400 font-medium mb-1">Open AP Liabilities</div>
                <div className="text-2xl font-bold text-rose-400">
                  ${Number(data.total_open_payables).toLocaleString()}
                </div>
                <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-1">
                  <span>From {data.total_ap_invoices} Invoices</span>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div className="text-xs text-slate-400 font-medium mb-1">Inventory Valuation</div>
                <div className="text-2xl font-bold text-white">
                  ${Number(data.total_inventory_valuation).toLocaleString()}
                </div>
                <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-1">
                  <span>In {data.warehouse_count} Warehouses</span>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div className="text-xs text-slate-400 font-medium mb-1">Ledger Status</div>
                <div className="text-2xl font-bold text-white">
                  {data.is_ledger_balanced ? (
                    <span className="text-emerald-400">Balanced</span>
                  ) : (
                    <span className="text-rose-400">Out of Balance</span>
                  )}
                </div>
                <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-1">
                  <span>{data.total_journal_entries} Journal Entries</span>
                </div>
              </div>
            </div>

            {/* Financial Overview */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
              <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
                <h2 className="text-sm font-semibold text-white">Accounting Overview</h2>
              </div>
              <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">Debits & Credits</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center p-3 bg-slate-800/50 rounded-lg">
                      <span className="text-sm font-medium text-slate-300">Total Debits</span>
                      <span className="font-mono text-emerald-400">${Number(data.total_debits).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-slate-800/50 rounded-lg">
                      <span className="text-sm font-medium text-slate-300">Total Credits</span>
                      <span className="font-mono text-emerald-400">${Number(data.total_credits).toLocaleString()}</span>
                    </div>
                  </div>
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">Operations</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center p-3 bg-slate-800/50 rounded-lg">
                      <span className="text-sm font-medium text-slate-300">Active Projects</span>
                      <span className="font-mono text-white">{data.active_projects} / {data.total_projects}</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-slate-800/50 rounded-lg">
                      <span className="text-sm font-medium text-slate-300">Client Accounts</span>
                      <span className="font-mono text-white">{data.total_clients}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        )}
      </div>
    </AppLayout>
  );
}
