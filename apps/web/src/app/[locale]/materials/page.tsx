"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import { getMaterials, createMaterial, getDetailedBalances, Material, InventoryBalanceDetail } from "@/lib/api";

export default function MaterialsPage({ params }: { params: { locale: string } }) {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [balances, setBalances] = useState<InventoryBalanceDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("ALL");

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    material_code: "",
    name: "",
    description: "",
    category: "Metals & Rebar",
    base_unit: "TON",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [matsData, balsData] = await Promise.all([
        getMaterials(),
        getDetailedBalances().catch(() => [])
      ]);
      setMaterials(matsData);
      setBalances(balsData);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load materials catalog");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.material_code.trim() || !form.name.trim()) return;

    try {
      setSubmitting(true);
      await createMaterial({
        material_code: form.material_code.trim().toUpperCase(),
        name: form.name.trim(),
        description: form.description.trim() || undefined,
        category: form.category,
        base_unit: form.base_unit,
      });
      setShowModal(false);
      setForm({
        material_code: "",
        name: "",
        description: "",
        category: "Metals & Rebar",
        base_unit: "TON",
      });
      await loadData();
    } catch (err: any) {
      alert("Error creating material: " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  // Aggregations
  const categories = Array.from(new Set(materials.map((m) => m.category).filter(Boolean))) as string[];
  const filteredMaterials = materials.filter((m) => {
    const matchesCat = selectedCategory === "ALL" || m.category === selectedCategory;
    const matchesSearch =
      m.name.toLowerCase().includes(search.toLowerCase()) ||
      m.material_code.toLowerCase().includes(search.toLowerCase()) ||
      (m.description && m.description.toLowerCase().includes(search.toLowerCase()));
    return matchesCat && matchesSearch;
  });

  // Calculate stock on hand per material
  const stockMap: Record<string, { qty: number; val: number }> = {};
  balances.forEach((b) => {
    if (!stockMap[b.material_id]) {
      stockMap[b.material_id] = { qty: 0, val: 0 };
    }
    stockMap[b.material_id].qty += parseFloat(b.quantity as any) || 0;
    stockMap[b.material_id].val += parseFloat(b.total_cost as any) || 0;
  });

  const totalCatalogValuation = Object.values(stockMap).reduce((acc, s) => acc + s.val, 0);

  return (
    <AppLayout locale={params.locale}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-gray-200 pb-5">
          <div>
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
              <span>Inventory & Site Logistics</span>
              <span>/</span>
              <span className="text-gray-900 font-medium">Materials Master</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Materials Master Catalog</h1>
            <p className="text-sm text-gray-500 mt-1">
              Standardized item catalog, technical specifications, units of measure, and active inventory valuations
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center justify-center px-4 py-2.5 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 transition-colors gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add New Material
          </button>
        </div>

        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="text-sm font-medium text-gray-500">Catalog Items</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{materials.length}</div>
            <div className="text-xs text-green-600 mt-1">✓ Active in ERP database</div>
          </div>
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="text-sm font-medium text-gray-500">Trade Categories</div>
            <div className="text-2xl font-bold text-blue-600 mt-1">{categories.length || 1}</div>
            <div className="text-xs text-gray-500 mt-1">Concrete, Steel, Sand, etc.</div>
          </div>
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="text-sm font-medium text-gray-500">Total In-Stock Valuation</div>
            <div className="text-2xl font-bold text-emerald-600 mt-1">
              ${totalCatalogValuation.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-gray-500 mt-1">Real-time WAC across all yards</div>
          </div>
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="text-sm font-medium text-gray-500">Warehouses Storing Stock</div>
            <div className="text-2xl font-bold text-indigo-600 mt-1">
              {Array.from(new Set(balances.map((b) => b.warehouse_id))).length}
            </div>
            <div className="text-xs text-gray-500 mt-1">Active site laydowns & depots</div>
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
                placeholder="Search by code, material description..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              />
            </div>
          </div>
          <div className="flex items-center gap-2 overflow-x-auto pb-1 md:pb-0">
            <button
              onClick={() => setSelectedCategory("ALL")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                selectedCategory === "ALL" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              All Categories
            </button>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                  selectedCategory === cat ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Materials Table */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-gray-500">Loading materials catalog from PostgreSQL...</div>
          ) : error ? (
            <div className="p-12 text-center text-red-500">{error}</div>
          ) : filteredMaterials.length === 0 ? (
            <div className="p-12 text-center text-gray-500">No materials matching your criteria.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50/70 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    <th className="py-3.5 px-4">Material Code</th>
                    <th className="py-3.5 px-4">Material Description</th>
                    <th className="py-3.5 px-4">Category</th>
                    <th className="py-3.5 px-4">Base UOM</th>
                    <th className="py-3.5 px-4 text-right">Current Stock</th>
                    <th className="py-3.5 px-4 text-right">Total Valuation</th>
                    <th className="py-3.5 px-4 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 text-sm">
                  {filteredMaterials.map((mat) => {
                    const st = stockMap[mat.id] || { qty: 0, val: 0 };
                    return (
                      <tr key={mat.id} className="hover:bg-gray-50/80 transition-colors">
                        <td className="py-3.5 px-4 font-mono font-medium text-blue-700">{mat.material_code}</td>
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-gray-900">{mat.name}</div>
                          {mat.description && <div className="text-xs text-gray-500 mt-0.5 line-clamp-1">{mat.description}</div>}
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-800 border border-blue-200">
                            {mat.category || "General"}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 font-mono text-gray-600">{mat.base_unit}</td>
                        <td className="py-3.5 px-4 text-right font-medium text-gray-900">
                          {st.qty > 0 ? (
                            <span className="text-emerald-700 font-semibold">
                              {st.qty.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 2 })} {mat.base_unit}
                            </span>
                          ) : (
                            <span className="text-gray-400">0.0 {mat.base_unit}</span>
                          )}
                        </td>
                        <td className="py-3.5 px-4 text-right font-medium text-gray-900">
                          ${st.val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td className="py-3.5 px-4 text-center">
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                            ACTIVE
                          </span>
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
                <h3 className="text-lg font-bold text-gray-900">Add New Material to Catalog</h3>
                <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 transition-colors">
                  ✕
                </button>
              </div>
              <form onSubmit={handleCreate} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Material Code *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. MAT-STEEL-12"
                      value={form.material_code}
                      onChange={(e) => setForm({ ...form, material_code: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Base Unit (UOM) *</label>
                    <select
                      value={form.base_unit}
                      onChange={(e) => setForm({ ...form, base_unit: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                    >
                      <option value="TON">TON (Metric Ton)</option>
                      <option value="M3">M3 (Cubic Meter)</option>
                      <option value="BAG">BAG (50kg Bag)</option>
                      <option value="PCS">PCS (Pieces)</option>
                      <option value="SHT">SHT (Sheets)</option>
                      <option value="LM">LM (Linear Meter)</option>
                      <option value="M2">M2 (Square Meter)</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Material Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. High-Tensile Deformed Rebar 12mm"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Category *</label>
                  <select
                    value={form.category}
                    onChange={(e) => setForm({ ...form, category: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                  >
                    <option value="Metals & Rebar">Metals & Rebar</option>
                    <option value="Concrete & Cement">Concrete & Cement</option>
                    <option value="Aggregates & Sand">Aggregates & Sand</option>
                    <option value="Scaffolding & Formwork">Scaffolding & Formwork</option>
                    <option value="Masonry & Blocks">Masonry & Blocks</option>
                    <option value="MEP & Piping">MEP & Piping</option>
                    <option value="Safety & Consumables">Safety & Consumables</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Technical Specification / Notes</label>
                  <textarea
                    rows={2}
                    placeholder="Grade, standard specifications, storage requirements..."
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
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
                    {submitting ? "Saving..." : "Save Material"}
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
