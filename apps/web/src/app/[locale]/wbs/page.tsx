"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import { getWBSNodes, createWBSNode, getProjects, WBSNode, Project } from "@/lib/api";

export default function WBSPage() {
  const [nodes, setNodes] = useState<WBSNode[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  const [formData, setFormData] = useState({
    project_id: "",
    parent_id: null as string | null,
    code: "",
    name: "",
    description: "",
    is_active: true,
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [projData, wbsData] = await Promise.all([
        getProjects(),
        getWBSNodes(selectedProjectId || undefined),
      ]);
      setProjects(projData);
      setNodes(wbsData);
      if (projData.length > 0 && !formData.project_id) {
        setFormData((prev) => ({ ...prev, project_id: projData[0].id }));
      }
    } catch (err) {
      console.error("Failed to load WBS nodes", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedProjectId]);

  const handleOpenCreate = () => {
    const nextIdx = nodes.length + 1;
    setFormData({
      project_id: selectedProjectId || projects[0]?.id || "",
      parent_id: null,
      code: `WBS-0${nextIdx}`,
      name: "",
      description: "",
      is_active: true,
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createWBSNode(formData);
      setShowModal(false);
      await loadData();
    } catch (err: any) {
      alert("Error creating WBS Node: " + err.message);
    }
  };

  return (
    <AppLayout
      title="Work Breakdown Structure (WBS)"
      subtitle="Hierarchical project deliverables, work packages, phases, and schedule scope breakdown"
      actions={
        <button
          onClick={handleOpenCreate}
          className="px-3.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 shadow-md shadow-amber-500/20 transition"
        >
          <span>➕</span> Add WBS Element
        </button>
      }
    >
      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Total WBS Elements</div>
          <div className="text-2xl font-black text-white mt-1">{nodes.length}</div>
          <div className="text-[11px] text-emerald-400 mt-1">Scoped In Database</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Level 1 Milestones / Phases</div>
          <div className="text-2xl font-black text-amber-400 mt-1">
            {nodes.filter((n) => !n.parent_id).length}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Primary Deliverables</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Work Packages (Level 2+)</div>
          <div className="text-2xl font-black text-sky-400 mt-1">
            {nodes.filter((n) => n.parent_id).length}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Detailed Construction Scope</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Active Scope Tracking</div>
          <div className="text-2xl font-black text-indigo-400 mt-1">100%</div>
          <div className="text-[11px] text-slate-400 mt-1">Linked to Cost Engine</div>
        </div>
      </div>

      {/* Project Selector Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row gap-4 items-center justify-between shadow-sm">
        <div className="flex items-center gap-3 w-full md:w-auto">
          <span className="text-xs text-slate-400 font-semibold whitespace-nowrap">Filter by Project:</span>
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
          >
            <option value="">All Active Projects</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.project_number})
              </option>
            ))}
          </select>
        </div>
        <div className="text-xs text-slate-400">
          Showing <strong className="text-white">{nodes.length}</strong> WBS element(s)
        </div>
      </div>

      {/* WBS Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/50 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="py-3.5 px-4">WBS Code</th>
                <th className="py-3.5 px-4">Deliverable / Work Package Name</th>
                <th className="py-3.5 px-4">Description / Scope</th>
                <th className="py-3.5 px-4">Project Reference</th>
                <th className="py-3.5 px-4">Hierarchy Level</th>
                <th className="py-3.5 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-slate-500">
                    Loading Work Breakdown Structure from database...
                  </td>
                </tr>
              ) : nodes.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-slate-500">
                    No WBS elements found for this selection. Click "Add WBS Element" to create one.
                  </td>
                </tr>
              ) : (
                nodes.map((n) => {
                  const proj = projects.find((p) => p.id === n.project_id);
                  const isRoot = !n.parent_id;
                  return (
                    <tr key={n.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3.5 px-4 font-mono font-bold text-amber-400">
                        {n.code}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className={`font-semibold ${isRoot ? "text-white text-sm" : "text-slate-200 pl-4"}`}>
                          {!isRoot && "↳ "}
                          {n.name}
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-slate-400 max-w-xs truncate">
                        {n.description || "No additional scope details"}
                      </td>
                      <td className="py-3.5 px-4 text-slate-300">
                        {proj ? proj.name : n.project_id.slice(0, 8)}
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold border ${
                            isRoot
                              ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                              : "bg-slate-800 text-slate-400 border-slate-700"
                          }`}
                        >
                          {isRoot ? "Level 1: Milestone" : "Level 2: Work Package"}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                          ACTIVE
                        </span>
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
              <span>Add WBS Work Package</span>
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

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">WBS Code *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. WBS-01 or 01.02"
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white font-mono focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Parent WBS (Optional)</label>
                  <select
                    value={formData.parent_id || ""}
                    onChange={(e) => setFormData({ ...formData, parent_id: e.target.value || null })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:border-amber-500 focus:outline-none"
                  >
                    <option value="">None (Root Milestone)</option>
                    {nodes
                      .filter((n) => !n.parent_id)
                      .map((n) => (
                        <option key={n.id} value={n.id}>
                          {n.code} — {n.name}
                        </option>
                      ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Deliverable / Work Package Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Substructure & Foundation Excavation"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:border-amber-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Scope Description</label>
                <textarea
                  rows={2}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
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
                  Save WBS Element
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
