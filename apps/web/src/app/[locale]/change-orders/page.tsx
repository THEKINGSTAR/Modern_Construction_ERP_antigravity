"use client";

import React, { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import {
  ClientChangeOrder,
  SubcontractChangeOrder,
  getClientChangeOrders,
  getSubcontractChangeOrders,
  createClientChangeOrder,
  createSubcontractChangeOrder,
  approveClientChangeOrder,
  approveSubcontractChangeOrder,
  Contract,
  getContracts,
  Subcontract,
  getSubcontracts,
  getCommercialSummary,
  CommercialSummary
} from "@/lib/api";

export default function ChangeOrdersPage() {
  const [activeTab, setActiveTab] = useState<"CLIENT" | "SUBCONTRACT">("CLIENT");
  const [clientOrders, setClientOrders] = useState<ClientChangeOrder[]>([]);
  const [subOrders, setSubOrders] = useState<SubcontractChangeOrder[]>([]);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [subcontracts, setSubcontracts] = useState<Subcontract[]>([]);
  const [summary, setSummary] = useState<CommercialSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [orderNumber, setOrderNumber] = useState("");
  const [orderTitle, setOrderTitle] = useState("");
  const [orderDesc, setOrderDesc] = useState("");
  const [orderAmount, setOrderAmount] = useState("100000");
  const [targetParentId, setTargetParentId] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [ccoList, scoList, cList, scList, sumData] = await Promise.all([
        getClientChangeOrders(),
        getSubcontractChangeOrders(),
        getContracts(),
        getSubcontracts(),
        getCommercialSummary().catch(() => null),
      ]);
      setClientOrders(ccoList);
      setSubOrders(scoList);
      setContracts(cList);
      setSubcontracts(scList);
      setSummary(sumData);
      if (cList.length > 0 && !targetParentId) setTargetParentId(cList[0].id);
    } catch (err: any) {
      console.error("Failed to load change orders", err);
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
        await approveClientChangeOrder(id);
      } else {
        await approveSubcontractChangeOrder(id);
      }
      await fetchData();
    } catch (err: any) {
      alert("Failed to approve change order: " + err.message);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsSubmitting(true);
      if (activeTab === "CLIENT") {
        await createClientChangeOrder({
          contract_id: targetParentId || (contracts[0]?.id ?? ""),
          number: orderNumber || `CCO-2026-${Math.floor(100 + Math.random() * 900)}`,
          title: orderTitle,
          description: orderDesc,
          amount: Number(orderAmount),
        });
      } else {
        await createSubcontractChangeOrder({
          subcontract_id: targetParentId || (subcontracts[0]?.id ?? ""),
          number: orderNumber || `SCO-2026-${Math.floor(100 + Math.random() * 900)}`,
          title: orderTitle,
          description: orderDesc,
          amount: Number(orderAmount),
        });
      }
      setIsModalOpen(false);
      setOrderNumber("");
      setOrderTitle("");
      setOrderDesc("");
      await fetchData();
    } catch (err: any) {
      alert("Failed to create change order: " + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const currentList = activeTab === "CLIENT" ? clientOrders : subOrders;
  const filteredList = currentList.filter(
    (item) => statusFilter === "ALL" || item.status === statusFilter
  );

  return (
    <AppLayout
      title="Variation & Change Orders"
      subtitle="Contractual scope adjustments, client variations (CCO) and subcontractor variations (SCO)"
      actions={
        <button
          onClick={() => {
            setTargetParentId(activeTab === "CLIENT" ? (contracts[0]?.id || "") : (subcontracts[0]?.id || ""));
            setIsModalOpen(true);
          }}
          className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold rounded-lg shadow-lg shadow-amber-500/20 transition flex items-center gap-2"
        >
          <span>➕</span> New {activeTab === "CLIENT" ? "Client Variation (CCO)" : "Subcontract Variation (SCO)"}
        </button>
      }
    >
      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Approved Client Additions</div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
            ${summary ? Number(summary.total_client_change_orders_approved).toLocaleString(undefined, { minimumFractionDigits: 2 }) : "0.00"}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Direct Contract Value Expansion</div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Pending Client Variations</div>
          <div className="text-2xl font-bold font-mono text-amber-400 mt-1">
            ${summary ? Number(summary.total_client_change_orders_pending).toLocaleString(undefined, { minimumFractionDigits: 2 }) : "0.00"}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Under Review or In Draft</div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Approved Subcontract Additions</div>
          <div className="text-2xl font-bold font-mono text-cyan-400 mt-1">
            ${summary ? Number(summary.total_subcontract_change_orders_approved).toLocaleString(undefined, { minimumFractionDigits: 2 }) : "0.00"}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Trade Commitment Additions</div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Change Orders</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">
            {clientOrders.length + subOrders.length}
          </div>
          <div className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1">
            <span>●</span> Live PostgreSQL Register
          </div>
        </div>
      </div>

      {/* Tabs & Filters */}
      <div className="flex flex-col sm:flex-row justify-between items-center gap-4 bg-slate-900/40 border border-slate-800/80 rounded-xl p-3">
        {/* Tab switcher */}
        <div className="flex items-center gap-2 bg-slate-950 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setActiveTab("CLIENT")}
            className={`px-4 py-1.5 rounded-md text-xs font-bold transition ${
              activeTab === "CLIENT"
                ? "bg-amber-500 text-slate-950 shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Client Variations (CCO) ({clientOrders.length})
          </button>
          <button
            onClick={() => setActiveTab("SUBCONTRACT")}
            className={`px-4 py-1.5 rounded-md text-xs font-bold transition ${
              activeTab === "SUBCONTRACT"
                ? "bg-amber-500 text-slate-950 shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Subcontractor Variations (SCO) ({subOrders.length})
          </button>
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-400 font-medium">Status Filter:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-amber-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="APPROVED">APPROVED</option>
            <option value="UNDER_REVIEW">UNDER_REVIEW</option>
            <option value="DRAFT">DRAFT</option>
          </select>
        </div>
      </div>

      {/* Change Orders Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden backdrop-blur">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 uppercase tracking-wider text-[11px] text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4 font-semibold">VO Number</th>
                <th className="py-3.5 px-4 font-semibold">
                  {activeTab === "CLIENT" ? "Parent Contract" : "Subcontract Package"}
                </th>
                <th className="py-3.5 px-4 font-semibold">Variation Title & Scope</th>
                <th className="py-3.5 px-4 font-semibold text-right">Adjustment Amount</th>
                <th className="py-3.5 px-4 font-semibold text-center">Status</th>
                <th className="py-3.5 px-4 font-semibold">Approved Date</th>
                <th className="py-3.5 px-4 font-semibold text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-slate-400">
                    Loading variation orders from PostgreSQL...
                  </td>
                </tr>
              ) : filteredList.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-slate-500">
                    No variation orders found for selected criteria.
                  </td>
                </tr>
              ) : (
                filteredList.map((item: any) => {
                  const isApproved = item.status === "APPROVED";
                  const isLoadingAction = actionLoadingId === item.id;
                  return (
                    <tr key={item.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-3 px-4 font-mono font-bold text-amber-400">
                        {item.number}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-200">
                        {activeTab === "CLIENT"
                          ? item.contract_number || "CTR-2026-001"
                          : item.subcontract_number || "SC-2026-PKG"}
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-white">{item.title}</div>
                        {item.description && (
                          <div className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">
                            {item.description}
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-white text-sm">
                        +${Number(item.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                            isApproved
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                              : item.status === "UNDER_REVIEW"
                              ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                              : "bg-slate-800 text-slate-400 border-slate-700"
                          }`}
                        >
                          {item.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">
                        {item.approved_date || "Pending Review"}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {!isApproved ? (
                          <button
                            onClick={() => handleApprove(item.id, activeTab)}
                            disabled={isLoadingAction}
                            className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[11px] font-bold shadow transition disabled:opacity-50"
                          >
                            {isLoadingAction ? "Approving..." : "✓ Approve & Apply"}
                          </button>
                        ) : (
                          <span className="text-emerald-400 text-xs font-semibold">✓ Applied to Value</span>
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

      {/* New Change Order Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>🔄</span> New {activeTab === "CLIENT" ? "Client Change Order" : "Subcontract Change Order"}
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 font-medium mb-1">
                  {activeTab === "CLIENT" ? "Target Prime Contract" : "Target Subcontract"}
                </label>
                <select
                  value={targetParentId}
                  onChange={(e) => setTargetParentId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500"
                >
                  {activeTab === "CLIENT"
                    ? contracts.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.contract_number} (Current: ${Number(c.current_value).toLocaleString()})
                        </option>
                      ))
                    : subcontracts.map((sc) => (
                        <option key={sc.id} value={sc.id}>
                          {sc.subcontract_number} - {sc.supplier_name} (${Number(sc.current_value).toLocaleString()})
                        </option>
                      ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Change Order Number</label>
                <input
                  type="text"
                  required
                  placeholder={activeTab === "CLIENT" ? "e.g. CCO-2026-005" : "e.g. SCO-MEP-02"}
                  value={orderNumber}
                  onChange={(e) => setOrderNumber(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Variation Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Acoustic Treatment Specification Upgrade"
                  value={orderTitle}
                  onChange={(e) => setOrderTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Scope Description / Justification</label>
                <textarea
                  rows={3}
                  placeholder="Detailed rationale, structural necessity, or client instructions..."
                  value={orderDesc}
                  onChange={(e) => setOrderDesc(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Cost Impact Amount ($ USD)</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={orderAmount}
                  onChange={(e) => setOrderAmount(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500 font-mono text-sm font-bold"
                />
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
                  {isSubmitting ? "Submitting..." : "Submit Variation Order"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
