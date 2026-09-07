"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import {
  getGoodsReceipts,
  createGoodsReceipt,
  getPurchaseOrders,
  getSuppliers,
  getWarehouses,
  getMaterials,
  GoodsReceipt,
  PurchaseOrder,
  Supplier,
  Warehouse,
  Material,
} from "@/lib/api";

export default function GoodsReceiptsPage({ params }: { params: { locale: string } }) {
  const [receipts, setReceipts] = useState<GoodsReceipt[]>([]);
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrder[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [selectedReceipt, setSelectedReceipt] = useState<GoodsReceipt | null>(null);

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    receipt_number: "",
    purchase_order_id: "",
    supplier_id: "",
    warehouse_id: "",
    date: new Date().toISOString().split("T")[0],
    notes: "",
    material_id: "",
    received_quantity: 50,
    accepted_quantity: 50,
    rejected_quantity: 0,
    unit_cost: 750,
    line_notes: "",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [rcptData, poData, supData, whData, matData] = await Promise.all([
        getGoodsReceipts(),
        getPurchaseOrders().catch(() => []),
        getSuppliers().catch(() => []),
        getWarehouses().catch(() => []),
        getMaterials().catch(() => []),
      ]);
      setReceipts(rcptData);
      setPurchaseOrders(poData);
      setSuppliers(supData);
      setWarehouses(whData);
      setMaterials(matData);

      // Default form selections if available
      if (poData.length > 0 && !form.purchase_order_id) {
        const p0 = poData[0];
        setForm((prev) => ({
          ...prev,
          purchase_order_id: p0.id,
          supplier_id: p0.supplier_id || (supData[0]?.id ?? ""),
          warehouse_id: whData[0]?.id ?? "",
          material_id: matData[0]?.id ?? "",
          receipt_number: `GRN-2026-${String(rcptData.length + 1).padStart(3, "0")}`,
        }));
      }
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load goods receipt records");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handlePoChange = (poId: string) => {
    const selectedPo = purchaseOrders.find((p) => p.id === poId);
    setForm((prev) => ({
      ...prev,
      purchase_order_id: poId,
      supplier_id: selectedPo?.supplier_id || prev.supplier_id,
    }));
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.purchase_order_id || !form.warehouse_id || !form.material_id) {
      alert("Please select a Purchase Order, Warehouse, and Material.");
      return;
    }

    try {
      setSubmitting(true);
      await createGoodsReceipt({
        receipt_number: form.receipt_number || `GRN-2026-${Date.now().toString().slice(-4)}`,
        purchase_order_id: form.purchase_order_id,
        supplier_id: form.supplier_id,
        warehouse_id: form.warehouse_id,
        date: form.date,
        notes: form.notes || undefined,
        lines: [
          {
            material_id: form.material_id,
            received_quantity: Number(form.received_quantity),
            accepted_quantity: Number(form.accepted_quantity),
            rejected_quantity: Number(form.rejected_quantity),
            unit_cost: Number(form.unit_cost),
            notes: form.line_notes || undefined,
          },
        ],
      });
      setShowModal(false);
      await loadData();
    } catch (err: any) {
      alert("Error posting Goods Receipt: " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  // Metrics
  const totalReceivedValue = receipts.reduce(
    (acc, r) => acc + (parseFloat(r.total_received_amount as any) || 0),
    0
  );
  const totalWarehouses = Array.from(new Set(receipts.map((r) => r.warehouse_id))).length;
  const totalSuppliers = Array.from(new Set(receipts.map((r) => r.supplier_id))).length;

  const filteredReceipts = receipts.filter((r) => {
    const s = search.toLowerCase();
    return (
      r.receipt_number.toLowerCase().includes(s) ||
      (r.po_number && r.po_number.toLowerCase().includes(s)) ||
      (r.supplier_name && r.supplier_name.toLowerCase().includes(s)) ||
      (r.warehouse_name && r.warehouse_name.toLowerCase().includes(s))
    );
  });

  return (
    <AppLayout locale={params.locale}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-gray-200 pb-5">
          <div>
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
              <span>Inventory & Site Logistics</span>
              <span>/</span>
              <span className="text-gray-900 font-medium">Goods Receipts (GRN)</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Goods Receipt Notes (GRN)</h1>
            <p className="text-sm text-gray-500 mt-1">
              Material delivery intake inspection, purchase order matching, warehouse laydown intake, and WAC stock ledger posting
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center justify-center px-4 py-2.5 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 transition-colors gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Receive Goods (New GRN)
          </button>
        </div>

        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="text-sm font-medium text-gray-500">Total GRN Records</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{receipts.length}</div>
            <div className="text-xs text-green-600 mt-1">✓ Posted to inventory ledger</div>
          </div>
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="text-sm font-medium text-gray-500">Accepted Goods Value</div>
            <div className="text-2xl font-bold text-emerald-600 mt-1">
              ${totalReceivedValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-gray-500 mt-1">Cumulative material intake</div>
          </div>
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="text-sm font-medium text-gray-500">Receiving Warehouses</div>
            <div className="text-2xl font-bold text-blue-600 mt-1">{totalWarehouses}</div>
            <div className="text-xs text-gray-500 mt-1">Central & site laydowns</div>
          </div>
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="text-sm font-medium text-gray-500">Fulfilling Suppliers</div>
            <div className="text-2xl font-bold text-indigo-600 mt-1">{totalSuppliers}</div>
            <div className="text-xs text-gray-500 mt-1">Approved trade suppliers</div>
          </div>
        </div>

        {/* Search */}
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex items-center justify-between">
          <div className="relative w-full max-w-md">
            <svg className="w-5 h-5 absolute left-3 top-2.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by GRN #, PO #, vendor, or warehouse..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
          </div>
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-gray-500">Loading goods receipts from PostgreSQL...</div>
          ) : error ? (
            <div className="p-12 text-center text-red-500">{error}</div>
          ) : filteredReceipts.length === 0 ? (
            <div className="p-12 text-center text-gray-500">No goods receipts found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50/70 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    <th className="py-3.5 px-4">GRN #</th>
                    <th className="py-3.5 px-4">Date</th>
                    <th className="py-3.5 px-4">Purchase Order</th>
                    <th className="py-3.5 px-4">Vendor / Supplier</th>
                    <th className="py-3.5 px-4">Receiving Yard</th>
                    <th className="py-3.5 px-4 text-center">Items</th>
                    <th className="py-3.5 px-4 text-right">Received Amount</th>
                    <th className="py-3.5 px-4 text-center">Status</th>
                    <th className="py-3.5 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 text-sm">
                  {filteredReceipts.map((rcpt) => (
                    <tr key={rcpt.id} className="hover:bg-gray-50/80 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-bold text-blue-700">{rcpt.receipt_number}</td>
                      <td className="py-3.5 px-4 text-gray-600">{rcpt.date}</td>
                      <td className="py-3.5 px-4 font-mono font-medium text-gray-800">
                        {rcpt.po_number || "Direct PO"}
                      </td>
                      <td className="py-3.5 px-4 font-medium text-gray-900">{rcpt.supplier_name || "Trade Vendor"}</td>
                      <td className="py-3.5 px-4 text-gray-700">{rcpt.warehouse_name || "Central Laydown"}</td>
                      <td className="py-3.5 px-4 text-center">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-800">
                          {rcpt.lines_count || (rcpt.lines ? rcpt.lines.length : 1)} lines
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right font-semibold text-emerald-700">
                        ${(parseFloat(rcpt.total_received_amount as any) || 0).toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
                          {rcpt.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => setSelectedReceipt(rcpt)}
                          className="px-2.5 py-1 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-md transition-colors"
                        >
                          View Lines
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Lines Detail Drawer / Modal */}
        {selectedReceipt && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-gray-100 animate-in fade-in zoom-in duration-200">
              <div className="flex items-center justify-between border-b border-gray-100 pb-4 mb-4">
                <div>
                  <h3 className="text-lg font-bold text-gray-900">
                    Goods Receipt Breakdown: {selectedReceipt.receipt_number}
                  </h3>
                  <p className="text-xs text-gray-500 mt-0.5">
                    PO Ref: {selectedReceipt.po_number || "Direct"} | Warehouse: {selectedReceipt.warehouse_name}
                  </p>
                </div>
                <button onClick={() => setSelectedReceipt(null)} className="text-gray-400 hover:text-gray-600">
                  ✕
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-gray-200 bg-gray-50 text-gray-500 uppercase font-semibold">
                      <th className="py-2.5 px-3">Material Code</th>
                      <th className="py-2.5 px-3">Description</th>
                      <th className="py-2.5 px-3 text-right">Received</th>
                      <th className="py-2.5 px-3 text-right">Accepted</th>
                      <th className="py-2.5 px-3 text-right">Unit Cost</th>
                      <th className="py-2.5 px-3 text-right">Total Cost</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {selectedReceipt.lines && selectedReceipt.lines.length > 0 ? (
                      selectedReceipt.lines.map((ln) => (
                        <tr key={ln.id}>
                          <td className="py-2.5 px-3 font-mono text-blue-700 font-medium">{ln.material_code || "MAT"}</td>
                          <td className="py-2.5 px-3 font-medium text-gray-800">{ln.material_name || "Material item"}</td>
                          <td className="py-2.5 px-3 text-right">{Number(ln.received_quantity).toFixed(2)}</td>
                          <td className="py-2.5 px-3 text-right font-semibold text-emerald-700">
                            {Number(ln.accepted_quantity).toFixed(2)}
                          </td>
                          <td className="py-2.5 px-3 text-right">${Number(ln.unit_cost).toFixed(2)}</td>
                          <td className="py-2.5 px-3 text-right font-semibold text-gray-900">
                            ${(Number(ln.accepted_quantity) * Number(ln.unit_cost)).toLocaleString(undefined, {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="py-4 text-center text-gray-500">
                          1 summary item received for this receipt document.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {selectedReceipt.notes && (
                <div className="mt-4 p-3 bg-gray-50 rounded-lg text-xs text-gray-600">
                  <span className="font-semibold text-gray-700">Delivery Inspection Notes: </span>
                  {selectedReceipt.notes}
                </div>
              )}

              <div className="mt-5 flex justify-end">
                <button
                  onClick={() => setSelectedReceipt(null)}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-lg text-xs font-semibold"
                >
                  Close Breakdown
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Create Modal */}
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-gray-100 animate-in fade-in zoom-in duration-200">
              <div className="flex items-center justify-between border-b border-gray-100 pb-4 mb-5">
                <h3 className="text-lg font-bold text-gray-900">Receive Goods (Generate New GRN)</h3>
                <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 transition-colors">
                  ✕
                </button>
              </div>
              <form onSubmit={handleCreate} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">GRN Number *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. GRN-2026-005"
                      value={form.receipt_number}
                      onChange={(e) => setForm({ ...form, receipt_number: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Receipt Date *</label>
                    <input
                      type="date"
                      required
                      value={form.date}
                      onChange={(e) => setForm({ ...form, date: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Purchase Order *</label>
                    <select
                      value={form.purchase_order_id}
                      onChange={(e) => handlePoChange(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-blue-500 outline-none"
                    >
                      <option value="">-- Select PO --</option>
                      {purchaseOrders.map((po) => (
                        <option key={po.id} value={po.id}>
                          {po.po_number} ({po.supplier_name || "Vendor"})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Receiving Warehouse / Yard *</label>
                    <select
                      value={form.warehouse_id}
                      onChange={(e) => setForm({ ...form, warehouse_id: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                    >
                      <option value="">-- Select Yard --</option>
                      {warehouses.map((wh) => (
                        <option key={wh.id} value={wh.id}>
                          {wh.code} - {wh.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="p-4 bg-gray-50/70 rounded-xl border border-gray-200/80 space-y-3">
                  <div className="text-xs font-bold text-gray-800 uppercase tracking-wider">Line Item Delivery Details</div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">Material Item *</label>
                    <select
                      value={form.material_id}
                      onChange={(e) => setForm({ ...form, material_id: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none bg-white"
                    >
                      <option value="">-- Select Material --</option>
                      {materials.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.material_code} - {m.name} ({m.base_unit})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Received Qty</label>
                      <input
                        type="number"
                        step="0.01"
                        value={form.received_quantity}
                        onChange={(e) =>
                          setForm({
                            ...form,
                            received_quantity: parseFloat(e.target.value) || 0,
                            accepted_quantity: parseFloat(e.target.value) || 0,
                          })
                        }
                        className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm bg-white"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Accepted Qty</label>
                      <input
                        type="number"
                        step="0.01"
                        value={form.accepted_quantity}
                        onChange={(e) => setForm({ ...form, accepted_quantity: parseFloat(e.target.value) || 0 })}
                        className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm bg-white font-semibold text-emerald-700"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Unit Cost ($)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={form.unit_cost}
                        onChange={(e) => setForm({ ...form, unit_cost: parseFloat(e.target.value) || 0 })}
                        className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm bg-white font-mono"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Inspection Notes / Batch Ticket</label>
                  <textarea
                    rows={2}
                    placeholder="Mill test certificates verified, delivery vehicle number..."
                    value={form.notes}
                    onChange={(e) => setForm({ ...form, notes: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>

                <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-100">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-2 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                  >
                    {submitting ? "Posting..." : "Confirm & Post GRN"}
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
