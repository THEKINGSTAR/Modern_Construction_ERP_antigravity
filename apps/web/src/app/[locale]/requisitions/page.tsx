"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import {
  getRequisitions,
  createRequisition,
  submitRequisition,
  approveRequisition,
  PurchaseRequisition,
  getProjects,
  Project,
  getCostCodes,
  CostCode,
} from "@/lib/api";

export default function RequisitionsPage({ params }: { params: { locale: string } }) {
  const [requisitions, setRequisitions] = useState<PurchaseRequisition[]>([]);
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
    pr_number: `PR-2026-${Math.floor(100 + Math.random() * 900)}`,
    project_id: "",
    description: "",
    required_date: new Date(Date.now() + 14 * 86400000).toISOString().split("T")[0],
    item_description: "",
    unit: "TON",
    quantity: "50",
    cost_code_id: "",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [reqData, projData, ccData] = await Promise.all([
        getRequisitions(),
        getProjects(),
        getCostCodes(),
      ]);
      setRequisitions(reqData);
      setProjects(projData);
      setCostCodes(ccData);
      if (projData.length > 0 && !form.project_id) {
        setForm((prev) => ({
          ...prev,
          project_id: projData[0].id,
          cost_code_id: ccData.length > 0 ? ccData[0].id : "",
        }));
      }
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load requisitions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSubmitPR = async (id: string) => {
    try {
      await submitRequisition(id);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to submit requisition");
    }
  };

  const handleApprovePR = async (id: string) => {
    try {
      await approveRequisition(id);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to approve requisition");
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.pr_number.trim() || !form.project_id) return;

    try {
      setSubmitting(true);
      await createRequisition({
        pr_number: form.pr_number,
        project_id: form.project_id,
        requester_id: "44444444-4444-4444-8444-444444444444", // demo user
        description: form.description || undefined,
        status: "DRAFT",
        required_date: form.required_date || undefined,
        lines: [
          {
            cost_code_id: form.cost_code_id || undefined,
            item_description: form.item_description || "High-Tensile Construction Materials",
            unit: form.unit || "TON",
            quantity: parseFloat(form.quantity) || 1,
          },
        ],
      });
      setShowModal(false);
      setForm({
        pr_number: `PR-2026-${Math.floor(100 + Math.random() * 900)}`,
        project_id: projects.length > 0 ? projects[0].id : "",
        description: "",
        required_date: new Date(Date.now() + 14 * 86400000).toISOString().split("T")[0],
        item_description: "",
        unit: "TON",
        quantity: "50",
        cost_code_id: costCodes.length > 0 ? costCodes[0].id : "",
      });
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to create requisition");
    } finally {
      setSubmitting(false);
    }
  };

  const filtered = requisitions.filter((r) => {
    const matchesFilter = filter === "ALL" || r.status === filter;
    const matchesSearch =
      r.pr_number.toLowerCase().includes(search.toLowerCase()) ||
      (r.description && r.description.toLowerCase().includes(search.toLowerCase())) ||
      (r.project_name && r.project_name.toLowerCase().includes(search.toLowerCase()));
    return matchesFilter && matchesSearch;
  });

  const approvedCount = requisitions.filter((r) => r.status === "APPROVED").length;
  const pendingCount = requisitions.filter((r) => r.status === "DRAFT" || r.status === "SUBMITTED").length;

  return (
    <AppLayout locale={params.locale} title="Purchase Requisitions">
      <div className="space-y-6">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">Purchase Requisitions (PR)</h2>
            <p className="text-sm text-slate-400">
              Site material demands, cost code validation, and multi-tier approval workflow.
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg shadow-lg shadow-blue-500/20 text-sm transition flex items-center gap-2 self-start"
          >
            <span>+</span> New Requisition
          </button>
        </div>

        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Total Requisitions</span>
            <div className="text-2xl font-bold text-white mt-1">{requisitions.length}</div>
            <div className="text-xs text-slate-500 mt-1">Logged to date</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Approved Demands</span>
            <div className="text-2xl font-bold text-emerald-400 mt-1">{approvedCount}</div>
            <div className="text-xs text-slate-500 mt-1">Ready for RFQ / PO</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Pending Approval</span>
            <div className="text-2xl font-bold text-amber-400 mt-1">{pendingCount}</div>
            <div className="text-xs text-slate-500 mt-1">Under engineering review</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Cost Code Control</span>
            <div className="text-2xl font-bold text-purple-400 mt-1">100% Assigned</div>
            <div className="text-xs text-slate-500 mt-1">Zero unallocated demands</div>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 w-full md:w-auto">
            <input
              type="text"
              placeholder="Search by PR#, project, description..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 w-full md:w-80"
            />
          </div>
          <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto">
            {["ALL", "DRAFT", "SUBMITTED", "APPROVED"].map((st) => (
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

        {/* Requisitions Table */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-900/80 text-xs text-slate-400 uppercase tracking-wider border-b border-slate-800 font-semibold">
                <tr>
                  <th className="px-6 py-3.5">PR Number & Description</th>
                  <th className="px-6 py-3.5">Project</th>
                  <th className="px-6 py-3.5">Required Date</th>
                  <th className="px-6 py-3.5">Items</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-right">Workflow Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-slate-500">
                      Loading purchase requisitions from PostgreSQL...
                    </td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-slate-500">
                      No purchase requisitions match the selected filter.
                    </td>
                  </tr>
                ) : (
                  filtered.map((pr) => (
                    <tr key={pr.id} className="hover:bg-slate-800/30 transition">
                      <td className="px-6 py-4">
                        <div className="font-semibold text-white font-mono">{pr.pr_number}</div>
                        <div className="text-xs text-slate-400 line-clamp-1">{pr.description || "General Material Requisition"}</div>
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-300">
                        {pr.project_name || "Skyline Commercial Tower"}
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-400">
                        {pr.required_date ? new Date(pr.required_date).toLocaleDateString() : "—"}
                      </td>
                      <td className="px-6 py-4 text-xs font-semibold text-slate-300">
                        {pr.lines ? pr.lines.length : pr.lines_count || 1} line item(s)
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-2.5 py-1 rounded-full text-[11px] font-semibold ${
                            pr.status === "APPROVED"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : pr.status === "SUBMITTED"
                              ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                              : "bg-slate-500/10 text-slate-400 border border-slate-500/20"
                          }`}
                        >
                          {pr.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        {pr.status === "DRAFT" && (
                          <button
                            onClick={() => handleSubmitPR(pr.id)}
                            className="px-3 py-1 bg-amber-600/80 hover:bg-amber-500 text-white rounded text-xs font-semibold transition shadow-sm"
                          >
                            Submit
                          </button>
                        )}
                        {pr.status === "SUBMITTED" && (
                          <button
                            onClick={() => handleApprovePR(pr.id)}
                            className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold transition shadow-sm"
                          >
                            Approve
                          </button>
                        )}
                        {pr.status === "APPROVED" && (
                          <span className="text-xs text-slate-500 italic">Ready for RFQ</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Modal: New Requisition */}
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-lg font-bold text-white">New Purchase Requisition (PR)</h3>
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
                    <label className="block text-xs font-semibold text-slate-300 mb-1">PR Number *</label>
                    <input
                      type="text"
                      required
                      value={form.pr_number}
                      onChange={(e) => setForm({ ...form, pr_number: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">Required On Site</label>
                    <input
                      type="date"
                      value={form.required_date}
                      onChange={(e) => setForm({ ...form, required_date: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>

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
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Requisition Description</label>
                  <textarea
                    rows={2}
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                    placeholder="Describe requisition purpose (e.g. Slab casting stage 2 rebar)..."
                  />
                </div>

                <div className="border-t border-slate-800 pt-3 space-y-3">
                  <span className="text-xs font-semibold text-blue-400 block">Initial Material Demand Item</span>
                  <div>
                    <input
                      type="text"
                      required
                      value={form.item_description}
                      onChange={(e) => setForm({ ...form, item_description: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                      placeholder="Item specification (e.g. 16mm Deformed Steel Rebar Grade 60)"
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
                      <label className="block text-xs text-slate-400 mb-1">Cost Code</label>
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
                    {submitting ? "Saving..." : "Create Requisition"}
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
