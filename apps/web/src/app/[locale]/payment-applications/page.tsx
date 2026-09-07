"use client";

import React, { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import {
  ClientPaymentApplication,
  SubcontractPaymentApplication,
  getClientPaymentApplications,
  getSubcontractPaymentApplications,
  createClientPaymentApplication,
  createSubcontractPaymentApplication,
  approveClientPaymentApplication,
  approveSubcontractPaymentApplication,
  postClientPaymentApplication,
  postSubcontractPaymentApplication,
  Contract,
  getContracts,
  Subcontract,
  getSubcontracts,
  AccountingPeriod,
  getAccountingPeriods,
  getCommercialSummary,
  CommercialSummary
} from "@/lib/api";

export default function PaymentApplicationsPage() {
  const [activeTab, setActiveTab] = useState<"CLIENT" | "SUBCONTRACT">("CLIENT");
  const [clientApps, setClientApps] = useState<ClientPaymentApplication[]>([]);
  const [subApps, setSubApps] = useState<SubcontractPaymentApplication[]>([]);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [subcontracts, setSubcontracts] = useState<Subcontract[]>([]);
  const [periods, setPeriods] = useState<AccountingPeriod[]>([]);
  const [summary, setSummary] = useState<CommercialSummary | null>(null);
  const [loading, setLoading] = useState(true);

  // Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [appNumber, setAppNumber] = useState("");
  const [targetParentId, setTargetParentId] = useState("");
  const [periodId, setPeriodId] = useState("");
  const [appDate, setAppDate] = useState("2026-09-30");
  const [grossWork, setGrossWork] = useState("3500000");
  const [prevWork, setPrevWork] = useState("2100000");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  // Calculation previews
  const grossNum = Number(grossWork) || 0;
  const prevNum = Number(prevWork) || 0;
  const currentWork = Math.max(0, grossNum - prevNum);
  const retentionAmt = currentWork * 0.10;
  const netDue = currentWork - retentionAmt;

  const fetchData = async () => {
    try {
      setLoading(true);
      const [cApps, sApps, cList, scList, pList, sumData] = await Promise.all([
        getClientPaymentApplications(),
        getSubcontractPaymentApplications(),
        getContracts(),
        getSubcontracts(),
        getAccountingPeriods(),
        getCommercialSummary().catch(() => null),
      ]);
      setClientApps(cApps);
      setSubApps(sApps);
      setContracts(cList);
      setSubcontracts(scList);
      setPeriods(pList);
      setSummary(sumData);
      if (pList.length > 0 && !periodId) setPeriodId(pList[0].id);
      if (cList.length > 0 && !targetParentId) setTargetParentId(cList[0].id);
    } catch (err: any) {
      console.error("Failed to load payment applications", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleApprove = async (id: string, type: "CLIENT" | "SUBCONTRACT") => {
    try {
      setActionLoadingId(id);
      if (type === "CLIENT") {
        await approveClientPaymentApplication(id);
      } else {
        await approveSubcontractPaymentApplication(id);
      }
      await fetchData();
    } catch (err: any) {
      alert("Approval failed: " + err.message);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handlePostGL = async (id: string, type: "CLIENT" | "SUBCONTRACT") => {
    try {
      setActionLoadingId(id);
      if (type === "CLIENT") {
        // Accounts: AR (1200), Revenue (4010), Retention (Asset/Liability)
        await postClientPaymentApplication(
          id,
          "b5f14e0b-bc59-48b5-9180-91c223e63ecf", // AR (1200)
          "9c7ed362-278c-4b69-bfcd-79fd970bd898", // Revenue (4010)
          "b5f14e0b-bc59-48b5-9180-91c223e63ecf"  // Retention Receivable
        );
      } else {
        // Accounts: WIP (5010), AP (2010), Retention
        await postSubcontractPaymentApplication(
          id,
          "8285f01c-cb29-4849-b07e-ae5a640e3dfe", // WIP / Materials Expense (5010)
          "04b32a89-808e-4e37-b1b6-24845b99befc", // AP Trade (2010)
          "04b32a89-808e-4e37-b1b6-24845b99befc"  // Retention Payable
        );
      }
      alert("Successfully posted to General Ledger!");
      await fetchData();
    } catch (err: any) {
      alert("GL Posting failed: " + err.message);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsSubmitting(true);
      if (activeTab === "CLIENT") {
        await createClientPaymentApplication({
          contract_id: targetParentId || (contracts[0]?.id ?? ""),
          accounting_period_id: periodId || (periods[0]?.id ?? ""),
          number: appNumber || `IPC-${Math.floor(100 + Math.random() * 900)}`,
          date: appDate,
          gross_work: grossNum,
          previous_certified_work: prevNum,
          retention_amount: retentionAmt,
          advance_recovery_amount: 0,
          deductions_amount: 0,
          adjustments_amount: 0,
        });
      } else {
        await createSubcontractPaymentApplication({
          subcontract_id: targetParentId || (subcontracts[0]?.id ?? ""),
          accounting_period_id: periodId || (periods[0]?.id ?? ""),
          number: appNumber || `SC-APP-${Math.floor(100 + Math.random() * 900)}`,
          date: appDate,
          gross_work: grossNum,
          previous_certified_work: prevNum,
          retention_amount: retentionAmt,
          advance_recovery_amount: 0,
          deductions_amount: 0,
          adjustments_amount: 0,
        });
      }
      setIsModalOpen(false);
      setAppNumber("");
      await fetchData();
    } catch (err: any) {
      alert("Failed to submit payment application: " + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const currentList = activeTab === "CLIENT" ? clientApps : subApps;

  return (
    <AppLayout
      title="Progress Billings & Claims"
      subtitle="Interim Payment Certificates (IPC), Subcontractor Claims, 10% retention, and GL posting"
      actions={
        <button
          onClick={() => {
            setTargetParentId(activeTab === "CLIENT" ? (contracts[0]?.id || "") : (subcontracts[0]?.id || ""));
            setIsModalOpen(true);
          }}
          className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold rounded-lg shadow-lg shadow-amber-500/20 transition flex items-center gap-2"
        >
          <span>➕</span> New {activeTab === "CLIENT" ? "Client Billing (IPC)" : "Subcontract Claim"}
        </button>
      }
    >
      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Client Gross Billed</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">
            ${summary ? Number(summary.total_client_billed).toLocaleString(undefined, { minimumFractionDigits: 2 }) : "0.00"}
          </div>
          <div className="text-[11px] text-emerald-400 mt-1">Cumulative Completed Work</div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Client Retention Held</div>
          <div className="text-2xl font-bold font-mono text-amber-400 mt-1">
            ${summary ? Number(summary.total_client_retention).toLocaleString(undefined, { minimumFractionDigits: 2 }) : "0.00"}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">10% Statutory Withholding</div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Subcontractor Work Certified</div>
          <div className="text-2xl font-bold font-mono text-cyan-400 mt-1">
            ${summary ? Number(summary.total_subcontractor_billed).toLocaleString(undefined, { minimumFractionDigits: 2 }) : "0.00"}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Subcontract Retention: ${summary ? Number(summary.total_subcontractor_retention).toLocaleString() : "0"}
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Payment Applications</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">
            {clientApps.length + subApps.length}
          </div>
          <div className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1">
            <span>●</span> PostgreSQL Ledger Linked
          </div>
        </div>
      </div>

      {/* Tab Switcher */}
      <div className="flex items-center gap-2 bg-slate-950 p-1.5 rounded-xl border border-slate-800 w-fit">
        <button
          onClick={() => setActiveTab("CLIENT")}
          className={`px-5 py-2 rounded-lg text-xs font-bold transition ${
            activeTab === "CLIENT"
              ? "bg-amber-500 text-slate-950 shadow-md"
              : "text-slate-400 hover:text-white"
          }`}
        >
          Client Interim Payment Certificates (AR) ({clientApps.length})
        </button>
        <button
          onClick={() => setActiveTab("SUBCONTRACT")}
          className={`px-5 py-2 rounded-lg text-xs font-bold transition ${
            activeTab === "SUBCONTRACT"
              ? "bg-amber-500 text-slate-950 shadow-md"
              : "text-slate-400 hover:text-white"
          }`}
        >
          Subcontractor Payment Claims (AP) ({subApps.length})
        </button>
      </div>

      {/* Payment Applications Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden backdrop-blur">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 uppercase tracking-wider text-[11px] text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4 font-semibold">App / IPC #</th>
                <th className="py-3.5 px-4 font-semibold">
                  {activeTab === "CLIENT" ? "Prime Contract" : "Subcontract"}
                </th>
                <th className="py-3.5 px-4 font-semibold">Financial Period</th>
                <th className="py-3.5 px-4 font-semibold text-right">Gross Work</th>
                <th className="py-3.5 px-4 font-semibold text-right">Prev Certified</th>
                <th className="py-3.5 px-4 font-semibold text-right">Current Work</th>
                <th className="py-3.5 px-4 font-semibold text-right">Retention (10%)</th>
                <th className="py-3.5 px-4 font-semibold text-right">Net Due</th>
                <th className="py-3.5 px-4 font-semibold text-center">Status</th>
                <th className="py-3.5 px-4 font-semibold text-center">GL Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={10} className="text-center py-8 text-slate-400">
                    Loading payment applications from PostgreSQL...
                  </td>
                </tr>
              ) : currentList.length === 0 ? (
                <tr>
                  <td colSpan={10} className="text-center py-8 text-slate-500">
                    No payment applications found.
                  </td>
                </tr>
              ) : (
                currentList.map((app: any) => {
                  const gross = Number(app.gross_work);
                  const prev = Number(app.previous_certified_work);
                  const curr = gross - prev;
                  const ret = Number(app.retention_amount);
                  const net = Number(app.net_amount_due);
                  const isDraft = app.status === "DRAFT";
                  const isApproved = app.status === "APPROVED";
                  const isPosted = app.status === "POSTED";
                  const isLoading = actionLoadingId === app.id;

                  return (
                    <tr key={app.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-3 px-4 font-mono font-bold text-amber-400">
                        {app.number}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-200">
                        {activeTab === "CLIENT"
                          ? app.contract_number || "CTR-2026-001"
                          : app.subcontract_number || "SC-2026-PKG"}
                      </td>
                      <td className="py-3 px-4 text-slate-300">
                        {app.period_name || "Period 2026-08"}
                        <div className="text-[10px] text-slate-500 font-mono">{app.date}</div>
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-slate-300">
                        ${gross.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-slate-500">
                        ${prev.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-semibold text-slate-100">
                        ${curr.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-amber-400">
                        -${ret.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-white text-sm">
                        ${net.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                            isPosted
                              ? "bg-purple-500/10 text-purple-400 border-purple-500/20"
                              : isApproved
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                              : "bg-slate-800 text-slate-400 border-slate-700"
                          }`}
                        >
                          {app.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        {isDraft ? (
                          <button
                            onClick={() => handleApprove(app.id, activeTab)}
                            disabled={isLoading}
                            className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[11px] font-bold shadow transition disabled:opacity-50"
                          >
                            {isLoading ? "..." : "Approve"}
                          </button>
                        ) : isApproved ? (
                          <button
                            onClick={() => handlePostGL(app.id, activeTab)}
                            disabled={isLoading}
                            className="px-2.5 py-1 bg-purple-600 hover:bg-purple-500 text-white rounded text-[11px] font-bold shadow transition disabled:opacity-50"
                          >
                            {isLoading ? "Posting..." : "⚡ Post to GL"}
                          </button>
                        ) : (
                          <span className="text-purple-400 text-xs font-mono">
                            Journal Posted
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* New Payment App Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>📑</span> New {activeTab === "CLIENT" ? "Client Billing (IPC)" : "Subcontractor Claim"}
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-medium mb-1">
                    {activeTab === "CLIENT" ? "Prime Contract" : "Subcontract"}
                  </label>
                  <select
                    value={targetParentId}
                    onChange={(e) => setTargetParentId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500"
                  >
                    {activeTab === "CLIENT"
                      ? contracts.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.contract_number} (${Number(c.current_value).toLocaleString()})
                          </option>
                        ))
                      : subcontracts.map((sc) => (
                          <option key={sc.id} value={sc.id}>
                            {sc.subcontract_number} - {sc.supplier_name}
                          </option>
                        ))}
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 font-medium mb-1">Accounting Period</label>
                  <select
                    value={periodId}
                    onChange={(e) => setPeriodId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500"
                  >
                    {periods.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Application Number</label>
                  <input
                    type="text"
                    required
                    placeholder={activeTab === "CLIENT" ? "e.g. IPC-004" : "e.g. SC-APP-03"}
                    value={appNumber}
                    onChange={(e) => setAppNumber(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Certificate Date</label>
                  <input
                    type="date"
                    required
                    value={appDate}
                    onChange={(e) => setAppDate(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Cumulative Gross Work ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={grossWork}
                    onChange={(e) => setGrossWork(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Previous Certified Work ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={prevWork}
                    onChange={(e) => setPrevWork(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500 font-mono"
                  />
                </div>
              </div>

              {/* Real-time Calculation Breakdown Box */}
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 space-y-1.5 font-mono text-[11px]">
                <div className="text-slate-400 uppercase tracking-wider text-[10px] font-sans font-bold">
                  Calculation Engine Preview (10% Retention)
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>Current Period Work (Gross - Prev):</span>
                  <span className="font-bold">${currentWork.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between text-amber-400">
                  <span>Less Retention Deducted (10.0%):</span>
                  <span>-${retentionAmt.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between text-white font-bold border-t border-slate-800 pt-1.5 text-xs">
                  <span>Net Amount Due:</span>
                  <span className="text-emerald-400 font-bold">${netDue.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-lg transition disabled:opacity-50"
                >
                  {isSubmitting ? "Submitting..." : "Submit Application"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
