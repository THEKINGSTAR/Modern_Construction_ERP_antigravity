"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import { getContracts, createContract, getProjects, getContractTypes, Contract, Project, ContractType } from "@/lib/api";

export default function ContractsPage() {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [contractTypes, setContractTypes] = useState<ContractType[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    contract_number: "",
    project_id: "",
    contract_type_id: "",
    original_value: 1000000,
    current_value: 1000000,
    currency_code: "USD",
    retention_rate: 10.0,
    payment_terms: "Net 30",
    start_date: new Date().toISOString().split("T")[0],
    end_date: "2027-12-31",
    status: "ACTIVE",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [cData, pData, tData] = await Promise.all([
        getContracts(),
        getProjects(),
        getContractTypes().catch(() => []),
      ]);
      setContracts(cData);
      setProjects(pData);
      setContractTypes(tData);
      if (pData.length > 0 && !formData.project_id) {
        setFormData((prev) => ({ ...prev, project_id: pData[0].id }));
      }
      if (tData.length > 0 && !formData.contract_type_id) {
        setFormData((prev) => ({ ...prev, contract_type_id: tData[0].id }));
      }
    } catch (err) {
      console.error("Failed to load contracts", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleOpenCreate = () => {
    const rand = Math.floor(100 + Math.random() * 900);
    setFormData({
      contract_number: `CTR-2026-${rand}`,
      project_id: projects[0]?.id || "",
      contract_type_id: contractTypes[0]?.id || "",
      original_value: 2500000,
      current_value: 2500000,
      currency_code: "USD",
      retention_rate: 10.0,
      payment_terms: "Net 30",
      start_date: new Date().toISOString().split("T")[0],
      end_date: "2027-12-31",
      status: "ACTIVE",
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createContract({
        ...formData,
        original_value: Number(formData.original_value),
        current_value: Number(formData.original_value),
        retention_rate: Number(formData.retention_rate),
      });
      setShowModal(false);
      await loadData();
    } catch (err: any) {
      alert("Error creating contract: " + err.message);
    }
  };

  const totalContractVal = contracts.reduce((acc, c) => acc + (Number(c.current_value) || 0), 0);

  return (
    <AppLayout
      title="Prime Contracts"
      subtitle="Commercial contract administration, change management, retention, and progress billing baselines"
      actions={
        <button
          onClick={handleOpenCreate}
          className="px-3.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 shadow-md shadow-amber-500/20 transition"
        >
          <span>➕</span> New Contract
        </button>
      }
    >
      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Total Contract Commitments</div>
          <div className="text-2xl font-black text-amber-400 mt-1">
            ${totalContractVal.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[11px] text-emerald-400 mt-1">Live SQL Contract Aggregation</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Total Contracts On File</div>
          <div className="text-2xl font-black text-white mt-1">{contracts.length}</div>
          <div className="text-[11px] text-slate-400 mt-1">Across Active Projects</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Average Retention Reserve</div>
          <div className="text-2xl font-black text-sky-400 mt-1">10.00%</div>
          <div className="text-[11px] text-slate-400 mt-1">Security Withholding</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Contract Type Standard</div>
          <div className="text-2xl font-black text-indigo-400 mt-1">Lump Sum / GMP</div>
          <div className="text-[11px] text-slate-400 mt-1">Fixed Commercial Terms</div>
        </div>
      </div>

      {/* Contracts Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/50 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="py-3.5 px-4">Contract #</th>
                <th className="py-3.5 px-4">Project Linked</th>
                <th className="py-3.5 px-4">Original Value</th>
                <th className="py-3.5 px-4">Current Value</th>
                <th className="py-3.5 px-4">Retention %</th>
                <th className="py-3.5 px-4">Payment Terms</th>
                <th className="py-3.5 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-500">
                    Loading contract ledger from PostgreSQL...
                  </td>
                </tr>
              ) : contracts.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-500">
                    No contracts found in database.
                  </td>
                </tr>
              ) : (
                contracts.map((c) => {
                  const proj = projects.find((p) => p.id === c.project_id);
                  return (
                    <tr key={c.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3.5 px-4 font-mono font-bold text-amber-400">
                        {c.contract_number}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-white">
                          {proj ? proj.name : c.project_id.slice(0, 8)}
                        </div>
                        <div className="text-[11px] text-slate-400 font-mono">
                          {proj?.project_number}
                        </div>
                      </td>
                      <td className="py-3.5 px-4 font-mono">
                        ${Number(c.original_value).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3.5 px-4 font-mono font-bold text-emerald-400">
                        ${Number(c.current_value).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3.5 px-4 font-mono">{Number(c.retention_rate).toFixed(1)}%</td>
                      <td className="py-3.5 px-4 text-slate-300">{c.payment_terms || "Net 30"}</td>
                      <td className="py-3.5 px-4">
                        <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                          {c.status}
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

      {/* Create Contract Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <h2 className="text-base font-bold text-white flex items-center justify-between">
              <span>Execute Prime Contract</span>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-200 text-lg"
              >
                ✕
              </button>
            </h2>

            <form onSubmit={handleSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Contract Number *</label>
                <input
                  type="text"
                  required
                  value={formData.contract_number}
                  onChange={(e) => setFormData({ ...formData, contract_number: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white font-mono focus:border-amber-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Assign to Project *</label>
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
                  <label className="block text-slate-400 mb-1">Original Value ($) *</label>
                  <input
                    type="number"
                    required
                    step="0.01"
                    value={formData.original_value}
                    onChange={(e) => setFormData({ ...formData, original_value: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white font-mono focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Retention Rate (%) *</label>
                  <input
                    type="number"
                    required
                    step="0.5"
                    value={formData.retention_rate}
                    onChange={(e) => setFormData({ ...formData, retention_rate: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white font-mono focus:border-amber-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Payment Terms</label>
                  <input
                    type="text"
                    value={formData.payment_terms}
                    onChange={(e) => setFormData({ ...formData, payment_terms: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Currency Code</label>
                  <input
                    type="text"
                    value={formData.currency_code}
                    onChange={(e) => setFormData({ ...formData, currency_code: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white font-mono focus:border-amber-500 focus:outline-none"
                  />
                </div>
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
                  Execute Contract
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
