"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import { getWarehouses, createWarehouse, getProjects, getDetailedBalances, Warehouse, Project, InventoryBalanceDetail } from "@/lib/api";

export default function WarehousesPage({ params }: { params: { locale: string } }) {
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [balances, setBalances] = useState<InventoryBalanceDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [search, setSearch] = useState("");

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    code: "",
    name: "",
    location: "",
    type: "PROJECT",
    project_id: "",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [whData, prjData, balData] = await Promise.all([
        getWarehouses(),
        getProjects(),
        getDetailedBalances().catch(() => [])
      ]);
      setWarehouses(whData);
      setProjects(prjData);
      setBalances(balData);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load warehouses");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.code.trim() || !form.name.trim()) return;

    try {
      setSubmitting(true);
      await createWarehouse({
        code: form.code.trim().toUpperCase(),
        name: form.name.trim(),
        location: form.location.trim() || undefined,
        type: form.type,
        project_id: form.project_id || undefined,
      });
      setShowModal(false);
      setForm({
        code: "",
        name: "",
        location: "",
        type: "PROJECT",
        project_id: "",
      });
      await loadData();
    } catch (err: any) {
      alert("Error adding warehouse: " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  // Aggregations per warehouse
  const whStockMap: Record<string, { itemsCount: number; totalVal: number }> = {};
  balances.forEach((b) => {
    if (!whStockMap[b.warehouse_id]) {
      whStockMap[b.warehouse_id] = { itemsCount: 0, totalVal: 0 };
    }
    whStockMap[b.warehouse_id].itemsCount += 1;
    whStockMap[b.warehouse_id].totalVal += parseFloat(b.total_cost as any) || 0;
  });

  const filteredWarehouses = warehouses.filter((wh) => {
    const matchesType = typeFilter === "ALL" || wh.type === typeFilter;
    const matchesSearch =
      wh.code.toLowerCase().includes(search.toLowerCase()) ||
      wh.name.toLowerCase().includes(search.toLowerCase()) ||
      (wh.location && wh.location.toLowerCase().includes(search.toLowerCase())) ||
      (wh.project_name && wh.project_name.toLowerCase().includes(search.toLowerCase()));
    return matchesType && matchesSearch;
  });

  const centralCount = warehouses.filter((w) => w.type === "CENTRAL").length;
  const projectCount = warehouses.filter((w) => w.type === "PROJECT").length;
  const transitCount = warehouses.filter((w) => w.type === "TRANSIT").length;

  return (
    <AppLayout locale={params.locale}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-gray-200 pb-5">
          <div>
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
              <span>Inventory & Site Logistics</span>
              <span>/</span>
              <span className="text-gray-900 font-medium">Warehouses & Yards</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Storage Yards & Site Warehouses</h1>
            <p className="text-sm text-gray-500 mt-1">
              Central logistics bases, on-site staging yards, laydown areas, and inter-site transit buffers
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center justify-center px-4 py-2.5 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 transition-colors gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Warehouse / Yard
          </button>
        </div>

        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="text-sm font-medium text-gray-500">Total Storage Facilities</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{warehouses.length}</div>
            <div className="text-xs text-green-600 mt-1">✓ Active in logistics grid</div>
          </div>
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="text-sm font-medium text-gray-500">Central Logistics Depots</div>
            <div className="text-2xl font-bold text-blue-600 mt-1">{centralCount}</div>
            <div className="text-xs text-gray-500 mt-1">Main fabrication & stock yards</div>
          </div>
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="text-sm font-medium text-gray-500">Project Site Laydowns</div>
            <div className="text-2xl font-bold text-emerald-600 mt-1">{projectCount}</div>
            <div className="text-xs text-gray-500 mt-1">Dedicated jobsite staging areas</div>
          </div>
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="text-sm font-medium text-gray-500">Transit & Transfer Hubs</div>
            <div className="text-2xl font-bold text-indigo-600 mt-1">{transitCount}</div>
            <div className="text-xs text-gray-500 mt-1">In-transit material checkpoints</div>
          </div>
        </div>

        {/* Filters & Search */}
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3 w-full md:w-96">
            <div className="relative w-full">
              <svg className="w-5 h-5 absolute left-3 top-2.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by code, facility name, location..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              />
            </div>
          </div>
          <div className="flex items-center gap-2 overflow-x-auto pb-1 md:pb-0">
            {["ALL", "CENTRAL", "PROJECT", "TRANSIT"].map((t) => (
              <button
                key={t}
                onClick={() => setTypeFilter(t)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                  typeFilter === t ? "bg-blue-600 text-white font-semibold" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {t === "ALL" ? "All Facility Types" : t}
              </button>
            ))}
          </div>
        </div>

        {/* Warehouses Table */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-gray-500">Loading warehouses from PostgreSQL...</div>
          ) : error ? (
            <div className="p-12 text-center text-red-500">{error}</div>
          ) : filteredWarehouses.length === 0 ? (
            <div className="p-12 text-center text-gray-500">No storage facilities found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50/70 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    <th className="py-3.5 px-4">Warehouse Code</th>
                    <th className="py-3.5 px-4">Facility Name</th>
                    <th className="py-3.5 px-4">Type</th>
                    <th className="py-3.5 px-4">Associated Project</th>
                    <th className="py-3.5 px-4">Location / Address</th>
                    <th className="py-3.5 px-4 text-center">Stock Items</th>
                    <th className="py-3.5 px-4 text-right">Stored Valuation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 text-sm">
                  {filteredWarehouses.map((wh) => {
                    const st = whStockMap[wh.id] || { itemsCount: 0, totalVal: 0 };
                    return (
                      <tr key={wh.id} className="hover:bg-gray-50/80 transition-colors">
                        <td className="py-3.5 px-4 font-mono font-medium text-blue-700">{wh.code}</td>
                        <td className="py-3.5 px-4 font-semibold text-gray-900">{wh.name}</td>
                        <td className="py-3.5 px-4">
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                              wh.type === "CENTRAL"
                                ? "bg-purple-50 text-purple-700 border-purple-200"
                                : wh.type === "PROJECT"
                                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                : "bg-amber-50 text-amber-700 border-amber-200"
                            }`}
                          >
                            {wh.type}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-gray-700">
                          {wh.project_name || "Central / All Projects"}
                        </td>
                        <td className="py-3.5 px-4 text-gray-500 text-xs">{wh.location || "N/A"}</td>
                        <td className="py-3.5 px-4 text-center">
                          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold bg-gray-100 text-gray-800">
                            {st.itemsCount} SKUs
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-right font-medium text-gray-900">
                          ${st.totalVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal */}
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-gray-100 animate-in fade-in zoom-in duration-200">
              <div className="flex items-center justify-between border-b border-gray-100 pb-4 mb-5">
                <h3 className="text-lg font-bold text-gray-900">Add Storage Facility / Laydown</h3>
                <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 transition-colors">
                  ✕
                </button>
              </div>
              <form onSubmit={handleCreate} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Facility Code *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. WH-NORTH-01"
                      value={form.code}
                      onChange={(e) => setForm({ ...form, code: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Facility Type *</label>
                    <select
                      value={form.type}
                      onChange={(e) => setForm({ ...form, type: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                    >
                      <option value="PROJECT">PROJECT (Site Laydown Yard)</option>
                      <option value="CENTRAL">CENTRAL (Central Depot / Base)</option>
                      <option value="TRANSIT">TRANSIT (In-Transit Hub)</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Facility Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Marina Tower On-Site Staging Yard"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Associated Project (Optional)</label>
                  <select
                    value={form.project_id}
                    onChange={(e) => setForm({ ...form, project_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                  >
                    <option value="">-- Central / Non-Project Facility --</option>
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.project_number} - {p.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Physical Location / Gate</label>
                  <textarea
                    rows={2}
                    placeholder="Plot number, gate coordinates, access notes..."
                    value={form.location}
                    onChange={(e) => setForm({ ...form, location: e.target.value })}
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
                    {submitting ? "Saving..." : "Save Facility"}
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
