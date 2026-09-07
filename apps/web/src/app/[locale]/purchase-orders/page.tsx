"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import {
  getPurchaseOrders,
  createPurchaseOrder,
  issuePurchaseOrder,
  cancelPurchaseOrder,
  PurchaseOrder,
  getSuppliers,
  Supplier,
  getProjects,
  Project,
  getCostCodes,
  CostCode,
} from "@/lib/api";

export default function PurchaseOrdersPage({ params }: { params: { locale: string } }) {
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrder[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [costCodes, setCostCodes] = useState<CostCode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("ALL");
  const [search, setSearch] = useState<string>("");

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    po_number: `PO-2026-${Math.floor(100 + Math.random() * 900)}`,
    project_id: "",
    supplier_id: "",
    delivery_date: new Date(Date.now() + 14 * 86400000).toISOString().split("T")[0],
    notes: "",
    item_description: "",
    unit: "TON",
    quantity: "50",
    unit_price: "850",
    cost_code_id: "",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [poData, supData, projData, ccData] = await Promise.all([
        getPurchaseOrders(),
        getSuppliers(),
        getProjects(),
        getCostCodes(),
      ]);
      setPurchaseOrders(poData);
      setSuppliers(supData);
      setProjects(projData);
      setCostCodes(ccData);

      if (projData.length > 0 && supData.length > 0 && !form.project_id) {
        setForm((prev) => ({
          ...prev,
          project_id: projData[0].id,
          supplier_id: supData[0].id,
          cost_code_id: ccData.length > 0 ? ccData[0].id : "",
        }));
      }
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load purchase orders");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleIssue = async (id: string) => {
    try {
      await issuePurchaseOrder(id);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to issue purchase order");
    }
  };

  const handleCancel = async (id: string) => {
    if (!confirm("Are you sure you want to cancel this purchase order?")) return;
    try {
      await cancelPurchaseOrder(id);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to cancel purchase order");
    }
  };

  const calcAmount = () => {
    const q = parseFloat(form.quantity) || 0;
    const p = parseFloat(form.unit_price) || 0;
    return q * p;
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.po_number.trim() || !form.project_id || !form.supplier_id) return;

    const amount = calcAmount();
    try {
      setSubmitting(true);
      await createPurchaseOrder({
        po_number: form.po_number,
        project_id: form.project_id,
        supplier_id: form.supplier_id,
        issue_date: new Date().toISOString().split("T")[0],
        delivery_date: form.delivery_date || undefined,
        currency: "USD",
        notes: form.notes || undefined,
        lines: [
          {
            cost_code_id: form.cost_code_id || undefined,
            item_description: form.item_description || "Commercial Material Procurement Package",
            unit: form.unit || "TON",
            quantity: parseFloat(form.quantity) || 1,
            unit_price: parseFloat(form.unit_price) || 0,
            amount: amount,
          },
        ],
      });
      setShowModal(false);
      setForm({
        po_number: `PO-2026-${Math.floor(100 + Math.random() * 900)}`,
        project_id: projects.length > 0 ? projects[0].id : "",
        supplier_id: suppliers.length > 0 ? suppliers[0].id : "",
        delivery_date: new Date(Date.now() + 14 * 86400000).toISOString().split("T")[0],
        notes: "",
        item_description: "",
        unit: "TON",
        quantity: "50",
        unit_price: "850",
        cost_code_id: costCodes.length > 0 ? costCodes[0].id : "",
      });
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to create purchase order");
    } finally {
      setSubmitting(false);
    }
  };

  const filtered = purchaseOrders.filter((po) => {
    const matchesFilter = filter === "ALL" || po.status === filter;
    const matchesSearch =
      po.po_number.toLowerCase().includes(search.toLowerCase()) ||
      (po.supplier_name && po.supplier_name.toLowerCase().includes(search.toLowerCase())) ||
      (po.project_name && po.project_name.toLowerCase().includes(search.toLowerCase())) ||
      (po.notes && po.notes.toLowerCase().includes(search.toLowerCase()));
    return matchesFilter && matchesSearch;
  });

  const totalCommitted = purchaseOrders
    .filter((p) => p.status !== "CANCELLED")
    .reduce((sum, p) => sum + (parseFloat(p.total_amount) || 0), 0);

  const activeCount = purchaseOrders.filter((p) => p.status === "ISSUED" || p.status === "DRAFT").length;
  const issuedCount = purchaseOrders.filter((p) => p.status === "ISSUED").length;

  return (
    <AppLayout locale={params.locale} title="Purchase Orders">
      <div className="space-y-6">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">Purchase Orders (PO)</h2>
            <p className="text-sm text-slate-400">
              Procurement commitments, supplier order issuance, and delivery schedule control.
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg shadow-lg shadow-blue-500/20 text-sm transition flex items-center gap-2 self-start"
          >
            <span>+</span> Create Purchase Order
          </button>
        </div>

        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Total Committed POs</span>
            <div className="text-2xl font-bold text-emerald-400 mt-1">
              ${totalCommitted.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-slate-500 mt-1">Active procurement commitments</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Active Orders</span>
            <div className="text-2xl font-bold text-white mt-1">{activeCount}</div>
            <div className="text-xs text-slate-500 mt-1">In progress & issued</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Issued to Vendors</span>
            <div className="text-2xl font-bold text-blue-400 mt-1">{issuedCount}</div>
            <div className="text-xs text-slate-500 mt-1">Awaiting delivery & GRN</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Suppliers Engaged</span>
            <div className="text-2xl font-bold text-purple-400 mt-1">{suppliers.length}</div>
            <div className="text-xs text-slate-500 mt-1">Active trade suppliers</div>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 w-full md:w-auto">
            <input
              type="text"
              placeholder="Search by PO#, supplier, project, notes..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 w-full md:w-80"
            />
          </div>
          <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto">
            {["ALL", "DRAFT", "ISSUED", "CANCELLED"].map((st) => (
              <button
                key={st}
                onClick={() => setFilter(st)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition whitespace-nowrap ${
                  filter === st
                    ? "bg-blue-600 text-white"
                    : "bg-slate-800/80 text-slate-400 hover:text-white"
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>

        {/* POs Table */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-900/80 text-xs text-slate-400 uppercase tracking-wider border-b border-slate-800 font-semibold">
                <tr>
                  <th className="px-6 py-3.5">PO Number & Notes</th>
                  <th className="px-6 py-3.5">Project</th>
                  <th className="px-6 py-3.5">Supplier</th>
                  <th className="px-6 py-3.5">Delivery Date</th>
                  <th className="px-6 py-3.5 text-right">Order Amount</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-8 text-center text-slate-500">
                      Loading purchase orders from PostgreSQL...
                    </td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-8 text-center text-slate-500">
                      No purchase orders match the selected filter.
                    </td>
                  </tr>
                ) : (
                  filtered.map((po) => {
                    const amt = parseFloat(po.total_amount) || 0;
                    return (
                      <tr key={po.id} className="hover:bg-slate-800/30 transition">
                        <td className="px-6 py-4">
                          <div className="font-semibold text-white font-mono">{po.po_number}</div>
                          {po.notes && <div className="text-xs text-slate-400 line-clamp-1">{po.notes}</div>}
                        </td>
                        <td className="px-6 py-4 text-xs text-slate-300">
                          {po.project_name || "Skyline Commercial Tower"}
                        </td>
                        <td className="px-6 py-4 text-xs font-semibold text-slate-200">
                          {po.supplier_name || "Vulcan Steel & Materials"}
                        </td>
                        <td className="px-6 py-4 text-xs text-slate-400">
                          {po.delivery_date ? new Date(po.delivery_date).toLocaleDateString() : "—"}
                        </td>
                        <td className="px-6 py-4 text-right font-mono font-bold text-white">
                          ${amt.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-6 py-4">
                          <span
                            className={`px-2.5 py-1 rounded-full text-[11px] font-semibold ${
                              po.status === "ISSUED"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : po.status === "DRAFT"
                                ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                : "bg-red-500/10 text-red-400 border border-red-500/20"
                            }`}
                          >
                            {po.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right space-x-2">
                          {po.status === "DRAFT" && (
                            <button
                              onClick={() => handleIssue(po.id)}
                              className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold transition shadow-sm"
                            >
                              Issue PO
                            </button>
                          )}
                          {po.status !== "CANCELLED" && (
                            <button
                              onClick={() => handleCancel(po.id)}
                              className="px-2.5 py-1 bg-slate-800 hover:bg-red-950/60 hover:text-red-400 text-slate-400 rounded text-xs transition"
                            >
                              Cancel
                            </button>
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

        {/* Modal: Create Purchase Order */}
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-lg font-bold text-white">Create Purchase Order (PO)</h3>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-slate-400 hover:text-white text-lg font-bold"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleCreate} className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">PO Number *</label>
                    <input
                      type="text"
                      required
                      value={form.po_number}
                      onChange={(e) => setForm({ ...form, po_number: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">Expected Delivery Date</label>
                    <input
                      type="date"
                      value={form.delivery_date}
                      onChange={(e) => setForm({ ...form, delivery_date: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">Target Project *</label>
                    <select
                      value={form.project_id}
                      onChange={(e) => setForm({ ...form, project_id: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                    >
                      {projects.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.project_number} — {p.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">Supplier / Vendor *</label>
                    <select
                      value={form.supplier_id}
                      onChange={(e) => setForm({ ...form, supplier_id: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                    >
                      {suppliers.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Order Notes / Delivery Terms</label>
                  <textarea
                    rows={2}
                    value={form.notes}
                    onChange={(e) => setForm({ ...form, notes: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                    placeholder="Delivery to site gate 3, quality mill test certificates required..."
                  />
                </div>

                <div className="border-t border-slate-800 pt-3 space-y-3">
                  <span className="text-xs font-semibold text-blue-400 block">Purchase Order Line Item</span>
                  <div>
                    <input
                      type="text"
                      required
                      value={form.item_description}
                      onChange={(e) => setForm({ ...form, item_description: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                      placeholder="Item description (e.g. 16mm Deformed Steel Rebar Grade 60)"
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Unit</label>
                      <input
                        type="text"
                        value={form.unit}
                        onChange={(e) => setForm({ ...form, unit: e.target.value })}
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Quantity</label>
                      <input
                        type="number"
                        step="any"
                        value={form.quantity}
                        onChange={(e) => setForm({ ...form, quantity: e.target.value })}
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Unit Price ($)</label>
                      <input
                        type="number"
                        step="any"
                        value={form.unit_price}
                        onChange={(e) => setForm({ ...form, unit_price: e.target.value })}
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs text-slate-400 mb-1">Cost Code Allocation</label>
                    <select
                      value={form.cost_code_id}
                      onChange={(e) => setForm({ ...form, cost_code_id: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500"
                    >
                      {costCodes.map((cc) => (
                        <option key={cc.id} value={cc.id}>
                          {cc.code} ({cc.name})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="bg-slate-950/80 border border-slate-800/80 rounded-lg p-3 flex items-center justify-between">
                    <span className="text-xs text-slate-400">Total Order Amount (USD):</span>
                    <span className="text-base font-bold font-mono text-emerald-400">
                      ${calcAmount().toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-3 border-t border-slate-800 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg text-sm transition shadow-lg shadow-blue-500/20 disabled:opacity-50"
                  >
                    {submitting ? "Saving..." : "Create Purchase Order"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
