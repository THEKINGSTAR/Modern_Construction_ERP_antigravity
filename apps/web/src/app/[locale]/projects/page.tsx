"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import { getProjects, createProject, updateProject, deleteProject, Project } from "@/lib/api";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [showModal, setShowModal] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);

  // Form State
  const [formData, setFormData] = useState({
    project_number: "",
    name: "",
    project_type: "Commercial High-Rise",
    location: "",
    start_date: "",
    planned_end_date: "",
    description: "",
    status: "ACTIVE",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await getProjects();
      setProjects(data);
    } catch (err) {
      console.error("Failed to load projects", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleOpenCreate = () => {
    setEditingProject(null);
    const randCode = Math.floor(1000 + Math.random() * 9000);
    setFormData({
      project_number: `PRJ-2026-${randCode}`,
      name: "",
      project_type: "Commercial High-Rise",
      location: "Metropolis Sector 4",
      start_date: new Date().toISOString().split("T")[0],
      planned_end_date: "2027-12-31",
      description: "",
      status: "ACTIVE",
    });
    setShowModal(true);
  };

  const handleOpenEdit = (proj: Project) => {
    setEditingProject(proj);
    setFormData({
      project_number: proj.project_number,
      name: proj.name,
      project_type: proj.project_type || "Commercial",
      location: proj.location || "",
      start_date: proj.start_date || "",
      planned_end_date: proj.planned_end_date || "",
      description: proj.description || "",
      status: proj.status || "ACTIVE",
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingProject) {
        await updateProject(editingProject.id, formData);
      } else {
        await createProject(formData);
      }
      setShowModal(false);
      await loadData();
    } catch (err: any) {
      alert("Error saving project: " + err.message);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this project?")) return;
    try {
      await deleteProject(id);
      await loadData();
    } catch (err: any) {
      alert("Error deleting project: " + err.message);
    }
  };

  const filtered = projects.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.project_number.toLowerCase().includes(search.toLowerCase()) ||
      (p.location && p.location.toLowerCase().includes(search.toLowerCase()));
    const matchesStatus = statusFilter === "ALL" || p.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <AppLayout
      title="Projects Directory"
      subtitle="Comprehensive multi-tenant capital project lifecycle and delivery tracking"
      actions={
        <button
          onClick={handleOpenCreate}
          className="px-3.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 shadow-md shadow-amber-500/20 transition"
        >
          <span>➕</span> New Project
        </button>
      }
    >
      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Total Projects</div>
          <div className="text-2xl font-black text-white mt-1">{projects.length}</div>
          <div className="text-[11px] text-emerald-400 mt-1">Live PostgreSQL Records</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Active Construction</div>
          <div className="text-2xl font-black text-amber-400 mt-1">
            {projects.filter((p) => p.status === "ACTIVE").length}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">In Execution Phase</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Planning & Pre-Con</div>
          <div className="text-2xl font-black text-sky-400 mt-1">
            {projects.filter((p) => p.status === "PLANNING").length}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Engineering / Bidding</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Base Currency</div>
          <div className="text-2xl font-black text-indigo-400 mt-1">USD ($)</div>
          <div className="text-[11px] text-slate-400 mt-1">Multi-Currency Enabled</div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row gap-4 items-center justify-between shadow-sm">
        <div className="w-full md:w-80 relative">
          <input
            type="text"
            placeholder="Search by project code, name, location..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500"
          />
        </div>
        <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto">
          {["ALL", "ACTIVE", "PLANNING", "ON_HOLD", "COMPLETED"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                statusFilter === st
                  ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                  : "bg-slate-950 text-slate-400 border border-slate-800 hover:text-slate-200"
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Projects Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/50 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="py-3.5 px-4">Project Code</th>
                <th className="py-3.5 px-4">Name & Type</th>
                <th className="py-3.5 px-4">Location</th>
                <th className="py-3.5 px-4">Schedule</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4">Linked Modules</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-500">
                    Loading project records from PostgreSQL...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-500">
                    No projects found matching current filters.
                  </td>
                </tr>
              ) : (
                filtered.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3.5 px-4 font-mono font-bold text-amber-400">
                      {p.project_number}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-white">{p.name}</div>
                      <div className="text-[11px] text-slate-400">{p.project_type || "Commercial"}</div>
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">{p.location || "Not specified"}</td>
                    <td className="py-3.5 px-4">
                      <div className="text-[11px]">Start: {p.start_date || "N/A"}</div>
                      <div className="text-[11px] text-slate-400">Target: {p.planned_end_date || "N/A"}</div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold border ${
                          p.status === "ACTIVE"
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                            : p.status === "PLANNING"
                            ? "bg-sky-500/10 text-sky-400 border-sky-500/30"
                            : "bg-slate-800 text-slate-400 border-slate-700"
                        }`}
                      >
                        {p.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-1.5">
                        <Link
                          href={`/en/wbs?project_id=${p.id}`}
                          className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-slate-300 font-medium"
                        >
                          WBS
                        </Link>
                        <Link
                          href={`/en/boq?project_id=${p.id}`}
                          className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-slate-300 font-medium"
                        >
                          BOQ
                        </Link>
                        <Link
                          href={`/en/budgets?project_id=${p.id}`}
                          className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-slate-300 font-medium"
                        >
                          Budget
                        </Link>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-2">
                      <button
                        onClick={() => handleOpenEdit(p)}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-[11px]"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(p.id)}
                        className="px-2.5 py-1 rounded bg-red-950/40 hover:bg-red-900/60 text-red-400 border border-red-800/40 text-[11px]"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create / Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <h2 className="text-base font-bold text-white flex items-center justify-between">
              <span>{editingProject ? "Edit Project Details" : "Register New Capital Project"}</span>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-200 text-lg"
              >
                ✕
              </button>
            </h2>

            <form onSubmit={handleSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Project Code / Number *</label>
                <input
                  type="text"
                  required
                  value={formData.project_number}
                  onChange={(e) => setFormData({ ...formData, project_number: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white font-mono focus:border-amber-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Project Title / Name *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:border-amber-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Project Type</label>
                  <input
                    type="text"
                    value={formData.project_type}
                    onChange={(e) => setFormData({ ...formData, project_type: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Location / Site</label>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Start Date</label>
                  <input
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Planned End Date</label>
                  <input
                    type="date"
                    value={formData.planned_end_date}
                    onChange={(e) => setFormData({ ...formData, planned_end_date: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Status</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:border-amber-500 focus:outline-none"
                >
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="PLANNING">PLANNING</option>
                  <option value="ON_HOLD">ON_HOLD</option>
                  <option value="COMPLETED">COMPLETED</option>
                  <option value="CANCELLED">CANCELLED</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Project Scope & Description</label>
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
                  {editingProject ? "Save Changes" : "Create Project"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
