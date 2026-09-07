"use client";

import React, { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import {
  Subcontract,
  getSubcontracts,
  createSubcontract,
  Project,
  getProjects,
  Supplier,
  getSuppliers,
  getCommercialSummary,
  CommercialSummary
} from "@/lib/api";

export default function SubcontractsPage() {
  const [subcontracts, setSubcontracts] = useState<Subcontract[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [summary, setSummary] = useState<CommercialSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter
  const [selectedProject, setSelectedProject] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [subNumber, setSubNumber] = useState("");
  const [subProjectId, setSubProjectId] = useState("");
  const [subSupplierId, setSubSupplierId] = useState("");
  const [subOriginalValue, setSubOriginalValue] = useState("500000");
  const [subRetentionRate, setSubRetentionRate] = useState("10.0");
  const [subStartDate, setSubStartDate] = useState("2026-03-01");
  const [subEndDate, setSubEndDate] = useState("2026-11-30");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [scList, projList, suppList, sumData] = await Promise.all([
        getSubcontracts(),
        getProjects(),
        getSuppliers(),
        getCommercialSummary().catch(() => null),
      ]);
      setSubcontracts(scList);
      setProjects(projList);
      setSuppliers(suppList);
      setSummary(sumData);
      if (projList.length > 0 && !subProjectId) setSubProjectId(projList[0].id);
      if (suppList.length > 0 && !subSupplierId) setSubSupplierId(suppList[0].id);
    } catch (err: any) {
      setError(err.message || "Failed to load subcontracts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsSubmitting(true);
      await createSubcontract({
        project_id: subProjectId,
        supplier_id: subSupplierId,
        subcontract_number: subNumber || `SC-2026-${Math.floor(1000 + Math.random() * 9000)}`,
        original_value: Number(subOriginalValue),
        currency_code: "USD",
        retention_rate: Number(subRetentionRate),
        start_date: subStartDate || undefined,
        end_date: subEndDate || undefined,
      });
      setIsModalOpen(false);
      setSubNumber("");
      await fetchData();
    } catch (err: any) {
      alert("Failed to award subcontract: " + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const filtered = subcontracts.filter((sc) => {
    const matchProj = selectedProject === "ALL" || sc.project_id === selectedProject;
    const matchSearch =
      sc.subcontract_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (sc.supplier_name && sc.supplier_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (sc.project_name && sc.project_name.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchProj && matchSearch;
  });

  const totalCommitted = subcontracts.reduce((acc, s) => acc + Number(s.current_value || s.original_value), 0);

  return (
    <AppLayout
      title="Trade Subcontracts"
      subtitle="Specialized trade packages, subcontractors directory, and retention commitments"
      actions={
        <button
          onClick={() => setIsModalOpen(true)}
          className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold rounded-lg shadow-lg shadow-amber-500/20 transition flex items-center gap-2"
        >
          <span>➕</span> Award Subcontract
        </button>
      }
    >
      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Subcontracts Value</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">
            ${totalCommitted.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1">
            <span>●</span> Live PostgreSQL Commitment
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Active Trade Packages</div>
          <div className="text-2xl font-bold font-mono text-amber-400 mt-1">
            {subcontracts.length}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Across Active Projects</div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Standard Retention Rate</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">10.0%</div>
          <div className="text-[11px] text-slate-400 mt-1">Withheld per Interim Certificate</div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Subcontractor Billings</div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
            ${summary ? Number(summary.total_subcontractor_billed).toLocaleString(undefined, { minimumFractionDigits: 2 }) : "0.00"}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Retention Held: ${summary ? Number(summary.total_subcontractor_retention).toLocaleString() : "0"}
          </div>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="flex items-center gap-3 w-full md:w-auto">
          <input
            type="text"
            placeholder="Search package # or subcontractor..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500 w-full md:w-64"
          />
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-amber-500"
          >
            <option value="ALL">All Projects ({projects.length})</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
        <div className="text-xs text-slate-400">
          Showing <span className="text-slate-200 font-bold">{filtered.length}</span> of {subcontracts.length} packages
        </div>
      </div>

      {/* Subcontracts Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden backdrop-blur">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 uppercase tracking-wider text-[11px] text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4 font-semibold">Subcontract #</th>
                <th className="py-3.5 px-4 font-semibold">Project</th>
                <th className="py-3.5 px-4 font-semibold">Subcontractor Trade Partner</th>
                <th className="py-3.5 px-4 font-semibold text-right">Original Value</th>
                <th className="py-3.5 px-4 font-semibold text-right">Current Value</th>
                <th className="py-3.5 px-4 font-semibold text-center">Retention</th>
                <th className="py-3.5 px-4 font-semibold">Period</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-slate-400">
                    Loading subcontracts from PostgreSQL...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-slate-500">
                    No subcontract packages match criteria.
                  </td>
                </tr>
              ) : (
                filtered.map((sc) => (
                  <tr key={sc.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-4 font-mono font-semibold text-amber-400">
                      {sc.subcontract_number}
                    </td>
                    <td className="py-3 px-4 text-slate-200 font-medium">
                      {sc.project_name || "Skyline Commercial Tower"}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-white">{sc.supplier_name || "Specialized Contractor"}</div>
                      <div className="text-[10px] text-slate-500 font-mono">ID: {sc.supplier_id.slice(0, 8)}...</div>
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-slate-300">
                      ${Number(sc.original_value).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-bold text-white">
                      ${Number(sc.current_value).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded text-[10px] font-mono font-semibold">
                        {Number(sc.retention_rate).toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">
                      {sc.start_date || "—"} to {sc.end_date || "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Award Subcontract Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>🤝</span> Award Trade Subcontract
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 font-medium mb-1">Subcontract Number</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. SC-2026-HVAC01"
                  value={subNumber}
                  onChange={(e) => setSubNumber(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Target Project</label>
                  <select
                    value={subProjectId}
                    onChange={(e) => setSubProjectId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500"
                  >
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Trade Subcontractor</label>
                  <select
                    value={subSupplierId}
                    onChange={(e) => setSubSupplierId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500"
                  >
                    {suppliers.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Original Package Value ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={subOriginalValue}
                    onChange={(e) => setSubOriginalValue(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Retention Rate (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    required
                    value={subRetentionRate}
                    onChange={(e) => setSubRetentionRate(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500 font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Start Date</label>
                  <input
                    type="date"
                    value={subStartDate}
                    onChange={(e) => setSubStartDate(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Expected Completion</label>
                  <input
                    type="date"
                    value={subEndDate}
                    onChange={(e) => setSubEndDate(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-lg transition disabled:opacity-50"
                >
                  {isSubmitting ? "Awarding..." : "Award Subcontract"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
