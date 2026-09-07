"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import { getEstimates, createEstimate, getProjects, Estimate, Project } from "@/lib/api";

export default function EstimatesPage() {
  const [estimates, setEstimates] = useState<Estimate[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  const [formData, setFormData] = useState({
    project_id: "",
    name: "",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [eData, pData] = await Promise.all([getEstimates(), getProjects()]);
      setEstimates(eData);
      setProjects(pData);
      if (pData.length > 0 && !formData.project_id) {
        setFormData((prev) => ({ ...prev, project_id: pData[0].id }));
      }
    } catch (err) {
      console.error("Failed to load estimates", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleOpenCreate = () => {
    setFormData({
      project_id: projects[0]?.id || "",
      name: "Baseline Detailed Cost Estimate (Rev 1)",
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createEstimate(formData);
      setShowModal(false);
      await loadData();
    } catch (err: any) {
      alert("Error creating Estimate: " + err.message);
    }
  };

  return (
    <AppLayout
      title="Cost Estimating & Markups"
      subtitle="Direct costs, labor hours, material rates, subcontractor allowances, overhead, and profit margin estimation"
      actions={
        <button
          onClick={handleOpenCreate}
          className="px-3.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 shadow-md shadow-amber-500/20 transition"
        >
          <span>➕</span> New Estimate
        </button>
      }
    >
      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Active Cost Estimates</div>
          <div className="text-2xl font-black text-white mt-1">{estimates.length}</div>
          <div className="text-[11px] text-emerald-400 mt-1">In Database</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Estimation Method</div>
          <div className="text-2xl font-black text-amber-400 mt-1">Parametric & First-Principles</div>
          <div className="text-[11px] text-slate-400 mt-1">Unit Rate Build-Up</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Markups & Overheads</div>
          <div className="text-2xl font-black text-indigo-400 mt-1">Configurable</div>
          <div className="text-[11px] text-slate-400 mt-1">General Conditions + Margin</div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/50 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="py-3.5 px-4">Estimate Title</th>
                <th className="py-3.5 px-4">Project Reference</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4">Created Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={4} className="text-center py-12 text-slate-500">
                    Loading estimates from PostgreSQL...
                  </td>
                </tr>
              ) : estimates.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-center py-12 text-slate-500">
                    No cost estimates found. Click "New Estimate" to begin tender estimation.
                  </td>
                </tr>
              ) : (
                estimates.map((e) => {
                  const proj = projects.find((p) => p.id === e.project_id);
                  return (
                    <tr key={e.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3.5 px-4 font-bold text-white">{e.name}</td>
                      <td className="py-3.5 px-4 text-slate-300">
                        {proj ? proj.name : e.project_id.slice(0, 8)}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                          {e.status || "DRAFT"}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-400 font-mono">
                        {e.created_at ? new Date(e.created_at).toLocaleDateString() : "Recent"}
                      </td>
                    </tr>
                  );
                })
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
              <span>Create Cost Estimate</span>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-200 text-lg"
              >
                ✕
              </button>
            </h2>

            <form onSubmit={handleSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Project *</label>
                <select
                  required
                  value={formData.project_id}
                  onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:border-amber-500 focus:outline-none"
                >
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.project_number})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Estimate Name *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:border-amber-500 focus:outline-none"
                />
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
                  Create Estimate
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
