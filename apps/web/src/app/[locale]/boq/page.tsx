"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import { getBOQs, createBOQ, getProjects, BOQ, Project } from "@/lib/api";

export default function BOQPage() {
  const [boqs, setBoqs] = useState<BOQ[]>([]);
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
      const [bData, pData] = await Promise.all([getBOQs(), getProjects()]);
      setBoqs(bData);
      setProjects(pData);
      if (pData.length > 0 && !formData.project_id) {
        setFormData((prev) => ({ ...prev, project_id: pData[0].id }));
      }
    } catch (err) {
      console.error("Failed to load BOQs", err);
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
      name: "Master Tender Bill of Quantities (Rev 1)",
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createBOQ(formData);
      setShowModal(false);
      await loadData();
    } catch (err: any) {
      alert("Error creating BOQ: " + err.message);
    }
  };

  return (
    <AppLayout
      title="Bill of Quantities (BOQ)"
      subtitle="Itemized construction scope, measured quantities, tender rate baselines, and revision histories"
      actions={
        <button
          onClick={handleOpenCreate}
          className="px-3.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 shadow-md shadow-amber-500/20 transition"
        >
          <span>➕</span> New BOQ
        </button>
      }
    >
      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Active BOQ Documents</div>
          <div className="text-2xl font-black text-white mt-1">{boqs.length}</div>
          <div className="text-[11px] text-emerald-400 mt-1">PostgreSQL Version Controlled</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Tender Compliance</div>
          <div className="text-2xl font-black text-amber-400 mt-1">Standard SMM / CESMM</div>
          <div className="text-[11px] text-slate-400 mt-1">Standard Method of Measurement</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Rate Baselines</div>
          <div className="text-2xl font-black text-indigo-400 mt-1">Contract Linked</div>
          <div className="text-[11px] text-slate-400 mt-1">Automates Progress Valuation</div>
        </div>
      </div>

      {/* BOQ Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/50 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="py-3.5 px-4">BOQ Title</th>
                <th className="py-3.5 px-4">Project</th>
                <th className="py-3.5 px-4">Revision Status</th>
                <th className="py-3.5 px-4">Created Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={4} className="text-center py-12 text-slate-500">
                    Loading BOQs from PostgreSQL...
                  </td>
                </tr>
              ) : boqs.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-center py-12 text-slate-500">
                    No Bill of Quantities on file. Click "New BOQ" to initialize one.
                  </td>
                </tr>
              ) : (
                boqs.map((b) => {
                  const proj = projects.find((p) => p.id === b.project_id);
                  return (
                    <tr key={b.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3.5 px-4 font-bold text-white">{b.name}</td>
                      <td className="py-3.5 px-4 text-slate-300">
                        {proj ? proj.name : b.project_id.slice(0, 8)}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                          {b.status || "DRAFT"}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-400 font-mono">
                        {b.created_at ? new Date(b.created_at).toLocaleDateString() : "Recent"}
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
              <span>Create Bill of Quantities</span>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-200 text-lg"
              >
                ✕
              </button>
            </h2>

            <form onSubmit={handleSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Select Project *</label>
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
                <label className="block text-slate-400 mb-1">BOQ Title *</label>
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
                  Initialize BOQ
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
