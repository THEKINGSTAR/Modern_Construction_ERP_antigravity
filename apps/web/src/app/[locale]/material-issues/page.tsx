"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import {
  getMaterialIssues,
  createMaterialIssue,
  getWarehouses,
  getProjects,
  getCostCodes,
  getMaterials,
  getDetailedBalances,
  MaterialIssue,
  Warehouse,
  Project,
  CostCode,
  Material,
  InventoryBalanceDetail,
} from "@/lib/api";

export default function MaterialIssuesPage({ params }: { params: { locale: string } }) {
  const [issues, setIssues] = useState<MaterialIssue[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [costCodes, setCostCodes] = useState<CostCode[]>([]);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [balances, setBalances] = useState<InventoryBalanceDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [selectedIssue, setSelectedIssue] = useState<MaterialIssue | null>(null);

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    issue_number: "",
    warehouse_id: "",
    project_id: "",
    cost_code_id: "",
    date: new Date().toISOString().split("T")[0],
    purpose: "",
    material_id: "",
    quantity: 10,
    line_notes: "",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [issData, whData, prjData, ccData, matData, balData] = await Promise.all([
        getMaterialIssues(),
        getWarehouses().catch(() => []),
        getProjects().catch(() => []),
        getCostCodes().catch(() => []),
        getMaterials().catch(() => []),
        getDetailedBalances().catch(() => []),
      ]);
      setIssues(issData);
      setWarehouses(whData);
      setProjects(prjData);
      setCostCodes(ccData);
      setMaterials(matData);
      setBalances(balData);

      if (!form.warehouse_id && whData.length > 0) {
        setForm((prev) => ({
          ...prev,
          warehouse_id: whData[0].id,
          project_id: prjData[0]?.id ?? "",
          cost_code_id: ccData[0]?.id ?? "",
          material_id: matData[0]?.id ?? "",
          issue_number: `ISS-2026-${String(issData.length + 1).padStart(3, "0")}`,
        }));
      }
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load material issue records");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.warehouse_id || !form.project_id || !form.cost_code_id || !form.material_id) {
      alert("Please complete all required fields (Warehouse, Project, Cost Code, Material).");
      return;
    }

    try {
      setSubmitting(true);
      await createMaterialIssue({
        issue_number: form.issue_number || `ISS-2026-${Date.now().toString().slice(-4)}`,
        warehouse_id: form.warehouse_id,
        project_id: form.project_id,
        cost_code_id: form.cost_code_id,
        date: form.date,
        purpose: form.purpose || undefined,
        lines: [
          {
            material_id: form.material_id,
            quantity: Number(form.quantity),
            notes: form.line_notes || undefined,
          },
        ],
      });
      setShowModal(false);
      await loadData();
    } catch (err: any) {
      alert("Error posting Material Issue: " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  // Metrics
  const totalIssuedValue = issues.reduce((acc, i) => acc + (parseFloat(i.total_amount as any) || 0), 0);
  const totalProjectsServed = Array.from(new Set(issues.map((i) => i.project_id))).length;
  const totalCostCodes = Array.from(new Set(issues.map((i) => i.cost_code_id))).length;

  const filteredIssues = issues.filter((i) => {
    const s = search.toLowerCase();
    return (
      i.issue_number.toLowerCase().includes(s) ||
      (i.project_name && i.project_name.toLowerCase().includes(s)) ||
      (i.warehouse_name && i.warehouse_name.toLowerCase().includes(s)) ||
      (i.cost_code_code && i.cost_code_code.toLowerCase().includes(s)) ||
      (i.purpose && i.purpose.toLowerCase().includes(s))
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
              <span className="text-gray-900 font-medium">Material Issues</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Material Issues to Project Sites</h1>
            <p className="text-sm text-gray-500 mt-1">
              Store requisition slips, site material dispatches, work package allocation, and project cost code charging
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center justify-center px-4 py-2.5 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 transition-colors gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Issue Materials to Site
          </button>
        </div>

        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="text-sm font-medium text-gray-500">Material Dispatches</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{issues.length}</div>
            <div className="text-xs text-green-600 mt-1">✓ WAC cost posted to WBS</div>
          </div>
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="text-sm font-medium text-gray-500">Dispatched Material Value</div>
            <div className="text-2xl font-bold text-amber-600 mt-1">
              ${totalIssuedValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-gray-500 mt-1">Direct construction consumption</div>
          </div>
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="text-sm font-medium text-gray-500">Project Sites Served</div>
            <div className="text-2xl font-bold text-blue-600 mt-1">{totalProjectsServed}</div>
            <div className="text-xs text-gray-500 mt-1">Active site delivery locations</div>
          </div>
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="text-sm font-medium text-gray-500">Cost Codes Charged</div>
            <div className="text-2xl font-bold text-indigo-600 mt-1">{totalCostCodes}</div>
            <div className="text-xs text-gray-500 mt-1">Concrete, structural, MEP</div>
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
              placeholder="Search by issue #, project, warehouse, or purpose..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
          </div>
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-gray-500">Loading material issues from PostgreSQL...</div>
          ) : error ? (
            <div className="p-12 text-center text-red-500">{error}</div>
          ) : filteredIssues.length === 0 ? (
            <div className="p-12 text-center text-gray-500">No material issue slips found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50/70 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    <th className="py-3.5 px-4">Issue Slip #</th>
                    <th className="py-3.5 px-4">Date</th>
                    <th className="py-3.5 px-4">Source Warehouse</th>
                    <th className="py-3.5 px-4">Target Project</th>
                    <th className="py-3.5 px-4">Cost Code</th>
                    <th className="py-3.5 px-4">Purpose / Work Area</th>
                    <th className="py-3.5 px-4 text-right">Dispatched Value</th>
                    <th className="py-3.5 px-4 text-center">Status</th>
                    <th className="py-3.5 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 text-sm">
                  {filteredIssues.map((iss) => (
                    <tr key={iss.id} className="hover:bg-gray-50/80 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-bold text-blue-700">{iss.issue_number}</td>
                      <td className="py-3.5 px-4 text-gray-600">{iss.date}</td>
                      <td className="py-3.5 px-4 text-gray-700">{iss.warehouse_name || "Central Laydown"}</td>
                      <td className="py-3.5 px-4 font-semibold text-gray-900">{iss.project_name || "Project Site"}</td>
                      <td className="py-3.5 px-4 font-mono text-xs text-gray-600">
                        {iss.cost_code_code || "03-100"}
                      </td>
                      <td className="py-3.5 px-4 text-xs text-gray-500 max-w-xs truncate">{iss.purpose || "Site Works"}</td>
                      <td className="py-3.5 px-4 text-right font-semibold text-amber-700">
                        ${(parseFloat(iss.total_amount as any) || 0).toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
                          {iss.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => setSelectedIssue(iss)}
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

        {/* Breakdown Drawer / Modal */}
        {selectedIssue && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-gray-100 animate-in fade-in zoom-in duration-200">
              <div className="flex items-center justify-between border-b border-gray-100 pb-4 mb-4">
                <div>
                  <h3 className="text-lg font-bold text-gray-900">
                    Material Issue Breakdown: {selectedIssue.issue_number}
                  </h3>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Target: {selectedIssue.project_name} | Cost Code: {selectedIssue.cost_code_code}
                  </p>
                </div>
                <button onClick={() => setSelectedIssue(null)} className="text-gray-400 hover:text-gray-600">
                  ✕
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-gray-200 bg-gray-50 text-gray-500 uppercase font-semibold">
                      <th className="py-2.5 px-3">Material Code</th>
                      <th className="py-2.5 px-3">Description</th>
                      <th className="py-2.5 px-3 text-right">Quantity</th>
                      <th className="py-2.5 px-3 text-right">WAC Unit Cost</th>
                      <th className="py-2.5 px-3 text-right">Line Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {selectedIssue.lines && selectedIssue.lines.length > 0 ? (
                      selectedIssue.lines.map((ln) => (
                        <tr key={ln.id}>
                          <td className="py-2.5 px-3 font-mono text-blue-700 font-medium">{ln.material_code || "MAT"}</td>
                          <td className="py-2.5 px-3 font-medium text-gray-800">{ln.material_name || "Material item"}</td>
                          <td className="py-2.5 px-3 text-right font-semibold text-gray-900">
                            {Number(ln.quantity).toFixed(2)}
                          </td>
                          <td className="py-2.5 px-3 text-right">${Number(ln.unit_cost || 0).toFixed(2)}</td>
                          <td className="py-2.5 px-3 text-right font-semibold text-amber-700">
                            ${(Number(ln.quantity) * Number(ln.unit_cost || 0)).toLocaleString(undefined, {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={5} className="py-4 text-center text-gray-500">
                          1 summary line item dispatched.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {selectedIssue.purpose && (
                <div className="mt-4 p-3 bg-gray-50 rounded-lg text-xs text-gray-600">
                  <span className="font-semibold text-gray-700">Work Area / Requisition Purpose: </span>
                  {selectedIssue.purpose}
                </div>
              )}

              <div className="mt-5 flex justify-end">
                <button
                  onClick={() => setSelectedIssue(null)}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-lg text-xs font-semibold"
                >
                  Close Breakdown
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal */}
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-gray-100 animate-in fade-in zoom-in duration-200">
              <div className="flex items-center justify-between border-b border-gray-100 pb-4 mb-5">
                <h3 className="text-lg font-bold text-gray-900">Issue Materials to Job Site</h3>
                <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 transition-colors">
                  ✕
                </button>
              </div>
              <form onSubmit={handleCreate} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Issue Number *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. ISS-2026-003"
                      value={form.issue_number}
                      onChange={(e) => setForm({ ...form, issue_number: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Issue Date *</label>
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
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Source Warehouse / Laydown *</label>
                    <select
                      value={form.warehouse_id}
                      onChange={(e) => setForm({ ...form, warehouse_id: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                    >
                      <option value="">-- Select Source Yard --</option>
                      {warehouses.map((wh) => (
                        <option key={wh.id} value={wh.id}>
                          {wh.code} - {wh.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Destination Project *</label>
                    <select
                      value={form.project_id}
                      onChange={(e) => setForm({ ...form, project_id: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                    >
                      <option value="">-- Select Project --</option>
                      {projects.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.project_number} - {p.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Charging Cost Code *</label>
                  <select
                    value={form.cost_code_id}
                    onChange={(e) => setForm({ ...form, cost_code_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                  >
                    <option value="">-- Select Cost Code --</option>
                    {costCodes.map((cc) => (
                      <option key={cc.id} value={cc.id}>
                        {cc.code} - {cc.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="p-4 bg-gray-50/70 rounded-xl border border-gray-200/80 space-y-3">
                  <div className="text-xs font-bold text-gray-800 uppercase tracking-wider">Material Requisition Details</div>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="col-span-2">
                      <label className="block text-xs font-medium text-gray-700 mb-1">Material Item *</label>
                      <select
                        value={form.material_id}
                        onChange={(e) => setForm({ ...form, material_id: e.target.value })}
                        className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm bg-white"
                      >
                        <option value="">-- Select Material --</option>
                        {materials.map((m) => (
                          <option key={m.id} value={m.id}>
                            {m.material_code} - {m.name} ({m.base_unit})
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Quantity *</label>
                      <input
                        type="number"
                        step="0.01"
                        required
                        value={form.quantity}
                        onChange={(e) => setForm({ ...form, quantity: parseFloat(e.target.value) || 0 })}
                        className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm bg-white font-semibold text-gray-900"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Work Area / Requisition Purpose</label>
                  <textarea
                    rows={2}
                    placeholder="Floor 2 columns pour, perimeter slab shoring..."
                    value={form.purpose}
                    onChange={(e) => setForm({ ...form, purpose: e.target.value })}
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
                    {submitting ? "Posting..." : "Confirm & Issue to Site"}
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
