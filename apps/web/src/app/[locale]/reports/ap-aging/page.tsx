"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import { getAPAging, AgingReport } from "@/lib/api";

export default function APAgingReportPage() {
  const [report, setReport] = useState<AgingReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await getAPAging();
        setReport(data);
      } catch (err) {
        console.error("Failed to load AP aging report", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <AppLayout title="Accounts Payable Aging" subtitle="Open vendor liabilities by age">
      <div className="p-6">
        {loading ? (
          <div className="flex h-32 items-center justify-center text-slate-400">Loading aging data...</div>
        ) : !report ? (
          <div className="text-red-400">Failed to load data.</div>
        ) : (
          <div className="space-y-6">
            
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
              <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
                <h2 className="text-sm font-semibold text-white">
                  AP Aging Summary as of {new Date(report.as_of_date).toLocaleDateString()}
                </h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="bg-slate-800/50 text-xs uppercase text-slate-400">
                    <tr>
                      <th className="px-4 py-3 font-medium">Vendor</th>
                      <th className="px-4 py-3 font-medium text-right">Current</th>
                      <th className="px-4 py-3 font-medium text-right">1-30 Days</th>
                      <th className="px-4 py-3 font-medium text-right">31-60 Days</th>
                      <th className="px-4 py-3 font-medium text-right">61-90 Days</th>
                      <th className="px-4 py-3 font-medium text-right">Over 90 Days</th>
                      <th className="px-4 py-3 font-medium text-right font-bold text-white">Total Balance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {report.details.map((detail) => (
                      <tr key={detail.party_id} className="hover:bg-slate-800/20 transition-colors">
                        <td className="px-4 py-3 font-medium text-white">{detail.party_name}</td>
                        <td className="px-4 py-3 text-right font-mono">${Number(detail.buckets.current).toLocaleString()}</td>
                        <td className="px-4 py-3 text-right font-mono">${Number(detail.buckets.days_1_30).toLocaleString()}</td>
                        <td className="px-4 py-3 text-right font-mono">${Number(detail.buckets.days_31_60).toLocaleString()}</td>
                        <td className="px-4 py-3 text-right font-mono">${Number(detail.buckets.days_61_90).toLocaleString()}</td>
                        <td className="px-4 py-3 text-right font-mono text-rose-400">${Number(detail.buckets.over_90).toLocaleString()}</td>
                        <td className="px-4 py-3 text-right font-mono font-bold text-white">${Number(detail.buckets.total).toLocaleString()}</td>
                      </tr>
                    ))}
                    {report.details.length === 0 && (
                      <tr>
                        <td colSpan={7} className="px-4 py-8 text-center text-slate-500">
                          No open payables found.
                        </td>
                      </tr>
                    )}
                  </tbody>
                  <tfoot className="bg-slate-900 font-semibold text-white border-t border-slate-700">
                    <tr>
                      <td className="px-4 py-3">Total Open Payables</td>
                      <td className="px-4 py-3 text-right font-mono">${Number(report.totals.current).toLocaleString()}</td>
                      <td className="px-4 py-3 text-right font-mono">${Number(report.totals.days_1_30).toLocaleString()}</td>
                      <td className="px-4 py-3 text-right font-mono">${Number(report.totals.days_31_60).toLocaleString()}</td>
                      <td className="px-4 py-3 text-right font-mono">${Number(report.totals.days_61_90).toLocaleString()}</td>
                      <td className="px-4 py-3 text-right font-mono text-rose-400">${Number(report.totals.over_90).toLocaleString()}</td>
                      <td className="px-4 py-3 text-right font-mono font-bold text-emerald-400">${Number(report.totals.total).toLocaleString()}</td>
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
