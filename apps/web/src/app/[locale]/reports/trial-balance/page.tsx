"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import { getTrialBalance, TrialBalanceReport } from "@/lib/api";

export default function TrialBalanceReportPage() {
  const [report, setReport] = useState<TrialBalanceReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await getTrialBalance();
        setReport(data);
      } catch (err) {
        console.error("Failed to load trial balance report", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <AppLayout title="Trial Balance" subtitle="General Ledger account balances">
      <div className="p-6">
        {loading ? (
          <div className="flex h-32 items-center justify-center text-slate-400">Loading trial balance...</div>
        ) : !report ? (
          <div className="text-red-400">Failed to load data.</div>
        ) : (
          <div className="space-y-6">
            
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
              <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
                <h2 className="text-sm font-semibold text-white">
                  Trial Balance as of {new Date(report.as_of_date).toLocaleDateString()}
                </h2>
                <div>
                  {Number(report.total_debit) === Number(report.total_credit) ? (
                    <span className="text-xs font-medium px-2 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-md">
                      ✓ Ledger Balanced
                    </span>
                  ) : (
                    <span className="text-xs font-medium px-2 py-1 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-md">
                      ⚠️ Out of Balance
                    </span>
                  )}
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="bg-slate-800/50 text-xs uppercase text-slate-400">
                    <tr>
                      <th className="px-4 py-3 font-medium">Account Code</th>
                      <th className="px-4 py-3 font-medium">Account Name</th>
                      <th className="px-4 py-3 font-medium text-right">Debit</th>
                      <th className="px-4 py-3 font-medium text-right">Credit</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {report.lines.map((line) => (
                      <tr key={line.account_id} className="hover:bg-slate-800/20 transition-colors">
                        <td className="px-4 py-3 font-medium text-slate-400 font-mono">{line.account_code}</td>
                        <td className="px-4 py-3 font-medium text-white">{line.account_name}</td>
                        <td className="px-4 py-3 text-right font-mono">
                          {Number(line.debit) > 0 ? `$${Number(line.debit).toLocaleString()}` : "-"}
                        </td>
                        <td className="px-4 py-3 text-right font-mono">
                          {Number(line.credit) > 0 ? `$${Number(line.credit).toLocaleString()}` : "-"}
                        </td>
                      </tr>
                    ))}
                    {report.lines.length === 0 && (
                      <tr>
                        <td colSpan={4} className="px-4 py-8 text-center text-slate-500">
                          No accounting data found.
                        </td>
                      </tr>
                    )}
                  </tbody>
                  <tfoot className="bg-slate-900 font-semibold text-white border-t border-slate-700">
                    <tr>
                      <td colSpan={2} className="px-4 py-3 text-right">Totals</td>
                      <td className="px-4 py-3 text-right font-mono border-double border-b-4 border-slate-700">
                        ${Number(report.total_debit).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-right font-mono border-double border-b-4 border-slate-700">
                        ${Number(report.total_credit).toLocaleString()}
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
