"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import { getCostCodes, createCostCode, CostCode } from "@/lib/api";

export default function CostCodesPage() {
  const [codes, setCodes] = useState<CostCode[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);

  const [formData, setFormData] = useState({
    code: "",
    name: "",
    category: "MATERIAL",
    parent_id: null as string | null,
    is_active: true,
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await getCostCodes();
      setCodes(data);
    } catch (err) {
      console.error("Failed to load cost codes", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleOpenCreate = () => {
    setFormData({
      code: "03-3100",
      name: "",
      category: "MATERIAL",
      parent_id: null,
      is_active: true,
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createCostCode(formData);
      setShowModal(false);
      await loadData();
    } catch (err: any) {
      alert("Error creating Cost Code: " + err.message);
    }
  };

  const filtered = codes.filter(
    (c) =>
      c.code.toLowerCase().includes(search.toLowerCase()) ||
      c.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <AppLayout
      title="Standard Cost Codes (CSI MasterFormat)"
      subtitle="Construction Specification Institute uniform cost accounting codes for materials, labor, equipment, and subcontracts"
      actions={
        <button
          onClick={handleOpenCreate}
          className="px-3.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 shadow-md shadow-amber-500/20 transition"
        >
          <span>➕</span> Add Cost Code
        </button>
      }
    >
      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Total Cost Codes</div>
          <div className="text-2xl font-black text-white mt-1">{codes.length}</div>
          <div className="text-[11px] text-emerald-400 mt-1">Standard Active Codes</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Specification Standard</div>
          <div className="text-2xl font-black text-amber-400 mt-1">CSI MasterFormat</div>
          <div className="text-[11px] text-slate-400 mt-1">50 Standard Divisions</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Ledger Integration</div>
          <div className="text-2xl font-black text-sky-400 mt-1">Automated GL</div>
          <div className="text-[11px] text-slate-400 mt-1">WIP & Expense Accounts</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Cost Variances</div>
          <div className="text-2xl font-black text-indigo-400 mt-1">Real-Time</div>
          <div className="text-[11px] text-slate-400 mt-1">Actual vs Budget Tracking</div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 flex justify-between items-center">
          <input
            type="text"
            placeholder="Search cost codes by number or description..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-80 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500"
          />
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/50 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="py-3.5 px-4">Cost Code</th>
                <th className="py-3.5 px-4">Description / Scope</th>
                <th className="py-3.5 px-4">Category</th>
                <th className="py-3.5 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={4} className="text-center py-12 text-slate-500">
                    Loading cost code directory from database...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-center py-12 text-slate-500">
                    No cost codes found. Click "Add Cost Code" to register one.
                  </td>
                </tr>
              ) : (
                filtered.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3.5 px-4 font-mono font-bold text-amber-400">
                      {c.code}
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-white">{c.name}</td>
                    <td className="py-3.5 px-4">
                      <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                        {c.category || "MATERIAL"}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        ACTIVE
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <h2 className="text-base font-bold text-white flex items-center justify-between">
              <span>Register Cost Code</span>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-200 text-lg"
              >
                ✕
              </button>
            </h2>

            <form onSubmit={handleSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Cost Code (CSI format) *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 03-3000"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white font-mono focus:border-amber-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Code Name / Description *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Cast-in-Place Structural Concrete"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:border-amber-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Cost Category</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:border-amber-500 focus:outline-none"
                >
                  <option value="MATERIAL">MATERIAL</option>
                  <option value="LABOR">LABOR</option>
                  <option value="EQUIPMENT">EQUIPMENT</option>
                  <option value="SUBCONTRACT">SUBCONTRACT</option>
                  <option value="OVERHEAD">OVERHEAD</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold"
                >
                  Save Cost Code
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
