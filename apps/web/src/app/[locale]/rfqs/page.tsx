"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import {
  getRFQs,
  createRFQ,
  publishRFQ,
  closeRFQ,
  RFQ,
  getRequisitions,
  PurchaseRequisition,
  getProjects,
  Project,
  getQuotations,
  SupplierQuotation,
} from "@/lib/api";

export default function RFQsPage({ params }: { params: { locale: string } }) {
  const [rfqs, setRFQs] = useState<RFQ[]>([]);
  const [requisitions, setRequisitions] = useState<PurchaseRequisition[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [quotations, setQuotations] = useState<SupplierQuotation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("ALL");
  const [search, setSearch] = useState<string>("");

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    rfq_number: `RFQ-2026-${Math.floor(100 + Math.random() * 900)}`,
    project_id: "",
    requisition_id: "",
    title: "",
    description: "",
    due_date: new Date(Date.now() + 10 * 86400000).toISOString().split("T")[0],
    item_description: "",
    unit: "TON",
    quantity: "100",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [rfqData, reqData, projData, quoteData] = await Promise.all([
        getRFQs(),
        getRequisitions(),
        getProjects(),
        getQuotations(),
      ]);
      setRFQs(rfqData);
      setRequisitions(reqData);
      setProjects(projData);
      setQuotations(quoteData);

      const approvedReqs = reqData.filter((r) => r.status === "APPROVED");
      if (projData.length > 0 && !form.project_id) {
        setForm((prev) => ({
          ...prev,
          project_id: projData[0].id,
          requisition_id: approvedReqs.length > 0 ? approvedReqs[0].id : "",
        }));
      }
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load RFQs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handlePublish = async (id: string) => {
    try {
      await publishRFQ(id);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to publish RFQ");
    }
  };

  const handleClose = async (id: string) => {
    try {
      await closeRFQ(id);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to close RFQ");
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.rfq_number.trim() || !form.project_id || !form.title.trim()) return;

    try {
      setSubmitting(true);
      await createRFQ({
        rfq_number: form.rfq_number,
        project_id: form.project_id,
        requisition_id: form.requisition_id || undefined,
        title: form.title,
        description: form.description || undefined,
        status: "DRAFT",
        due_date: form.due_date || undefined,
        lines: [
          {
            item_description: form.item_description || "Commercial Material Supply Package",
            unit: form.unit || "TON",
            quantity: parseFloat(form.quantity) || 1,
          },
        ],
      });
      setShowModal(false);
      setForm({
        rfq_number: `RFQ-2026-${Math.floor(100 + Math.random() * 900)}`,
        project_id: projects.length > 0 ? projects[0].id : "",
        requisition_id: "",
        title: "",
        description: "",
        due_date: new Date(Date.now() + 10 * 86400000).toISOString().split("T")[0],
        item_description: "",
        unit: "TON",
        quantity: "100",
      });
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to create RFQ");
    } finally {
      setSubmitting(false);
    }
  };

  const filtered = rfqs.filter((r) => {
    const matchesFilter = filter === "ALL" || r.status === filter;
    const matchesSearch =
      r.rfq_number.toLowerCase().includes(search.toLowerCase()) ||
      r.title.toLowerCase().includes(search.toLowerCase()) ||
      (r.project_name && r.project_name.toLowerCase().includes(search.toLowerCase()));
    return matchesFilter && matchesSearch;
  });

  const publishedCount = rfqs.filter((r) => r.status === "PUBLISHED").length;
  const closedCount = rfqs.filter((r) => r.status === "CLOSED").length;
  const approvedReqs = requisitions.filter((r) => r.status === "APPROVED");

  return (
    <AppLayout locale={params.locale} title="Requests for Quotation">
      <div className="space-y-6">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">RFQs & Tender Packages</h2>
            <p className="text-sm text-slate-400">
              Vendor tender publishing, competitive bid solicitation, and quotation evaluation.
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg shadow-lg shadow-blue-500/20 text-sm transition flex items-center gap-2 self-start"
          >
            <span>+</span> Create RFQ
          </button>
        </div>

        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Total RFQs</span>
            <div className="text-2xl font-bold text-white mt-1">{rfqs.length}</div>
            <div className="text-xs text-slate-500 mt-1">Tender packages created</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Active Tenders</span>
            <div className="text-2xl font-bold text-blue-400 mt-1">{publishedCount}</div>
            <div className="text-xs text-slate-500 mt-1">Open for vendor bids</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Bids Received</span>
            <div className="text-2xl font-bold text-emerald-400 mt-1">{quotations.length}</div>
            <div className="text-xs text-slate-500 mt-1">Supplier quotations logged</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Closed Packages</span>
            <div className="text-2xl font-bold text-purple-400 mt-1">{closedCount}</div>
            <div className="text-xs text-slate-500 mt-1">Ready for PO award</div>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 w-full md:w-auto">
            <input
              type="text"
              placeholder="Search by RFQ#, title, project..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 w-full md:w-80"
            />
          </div>
          <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto">
            {["ALL", "DRAFT", "PUBLISHED", "CLOSED"].map((st) => (
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

        {/* RFQs Table */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-900/80 text-xs text-slate-400 uppercase tracking-wider border-b border-slate-800 font-semibold">
                <tr>
                  <th className="px-6 py-3.5">RFQ Number & Title</th>
                  <th className="px-6 py-3.5">Project</th>
                  <th className="px-6 py-3.5">Linked PR</th>
                  <th className="px-6 py-3.5">Due Date</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-right">Tender Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-slate-500">
                      Loading RFQs from PostgreSQL...
                    </td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-slate-500">
                      No RFQ tender packages match the selected filter.
                    </td>
                  </tr>
                ) : (
                  filtered.map((rfq) => (
                    <tr key={rfq.id} className="hover:bg-slate-800/30 transition">
                      <td className="px-6 py-4">
                        <div className="font-semibold text-white font-mono">{rfq.rfq_number}</div>
                        <div className="text-xs text-slate-400 line-clamp-1">{rfq.title}</div>
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-300">
                        {rfq.project_name || "Skyline Commercial Tower"}
                      </td>
                      <td className="px-6 py-4 text-xs font-mono text-blue-400">
                        {rfq.requisition_number || "Direct Tender"}
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-400">
                        {rfq.due_date ? new Date(rfq.due_date).toLocaleDateString() : "—"}
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-2.5 py-1 rounded-full text-[11px] font-semibold ${
                            rfq.status === "PUBLISHED"
                              ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                              : rfq.status === "CLOSED"
                              ? "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                              : "bg-slate-500/10 text-slate-400 border border-slate-500/20"
                          }`}
                        >
                          {rfq.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        {rfq.status === "DRAFT" && (
                          <button
                            onClick={() => handlePublish(rfq.id)}
                            className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-semibold transition shadow-sm"
                          >
                            Publish
                          </button>
                        )}
                        {rfq.status === "PUBLISHED" && (
                          <button
                            onClick={() => handleClose(rfq.id)}
                            className="px-3 py-1 bg-purple-600 hover:bg-purple-500 text-white rounded text-xs font-semibold transition shadow-sm"
                          >
                            Close Bidding
                          </button>
                        )}
                        {rfq.status === "CLOSED" && (
                          <span className="text-xs text-slate-500 italic">Tender Closed</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Modal: Create RFQ */}
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-lg font-bold text-white">Create RFQ Tender Package</h3>
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
                    <label className="block text-xs font-semibold text-slate-300 mb-1">RFQ Number *</label>
                    <input
                      type="text"
                      required
                      value={form.rfq_number}
                      onChange={(e) => setForm({ ...form, rfq_number: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">Bidding Due Date</label>
                    <input
                      type="date"
                      value={form.due_date}
                      onChange={(e) => setForm({ ...form, due_date: e.target.value })}
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
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Linked Approved Requisition (Optional)</label>
                  <select
                    value={form.requisition_id}
                    onChange={(e) => setForm({ ...form, requisition_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="">-- Direct Tender (No Requisition Link) --</option>
                    {approvedReqs.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.pr_number} — {r.description}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Tender Package Title *</label>
                  <input
                    type="text"
                    required
                    value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                    placeholder="e.g. Supply of High-Tensile Deformed Steel Rebar 200 TON"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Scope & Notes</label>
                  <textarea
                    rows={2}
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                    placeholder="Delivery terms, site specifications, quality assurance certificates required..."
                  />
                </div>

                <div className="border-t border-slate-800 pt-3 space-y-3">
                  <span className="text-xs font-semibold text-blue-400 block">Tender Line Item Specification</span>
                  <div>
                    <input
                      type="text"
                      required
                      value={form.item_description}
                      onChange={(e) => setForm({ ...form, item_description: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                      placeholder="e.g. 16mm High-Tensile Deformed Rebar Grade 60"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
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
                    {submitting ? "Saving..." : "Create RFQ"}
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
