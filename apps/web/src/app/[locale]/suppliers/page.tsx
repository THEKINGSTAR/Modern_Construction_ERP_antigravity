"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import { getSuppliers, createSupplier, Supplier } from "@/lib/api";

export default function SuppliersPage({ params }: { params: { locale: string } }) {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("ALL");
  const [search, setSearch] = useState<string>("");

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    name: "",
    legal_name: "",
    tax_identifier: "",
    address: "",
    status: "ACTIVE",
    contact_name: "",
    contact_email: "",
    contact_phone: "",
    contact_role: "Sales Director",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await getSuppliers();
      setSuppliers(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load suppliers");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return;

    try {
      setSubmitting(true);
      await createSupplier({
        name: form.name,
        legal_name: form.legal_name || undefined,
        tax_identifier: form.tax_identifier || undefined,
        address: form.address || undefined,
        status: form.status,
        contacts: form.contact_name
          ? [
              {
                name: form.contact_name,
                email: form.contact_email || undefined,
                phone: form.contact_phone || undefined,
                role: form.contact_role || undefined,
              },
            ]
          : [],
      });
      setShowModal(false);
      setForm({
        name: "",
        legal_name: "",
        tax_identifier: "",
        address: "",
        status: "ACTIVE",
        contact_name: "",
        contact_email: "",
        contact_phone: "",
        contact_role: "Sales Director",
      });
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to register supplier");
    } finally {
      setSubmitting(false);
    }
  };

  const filteredSuppliers = suppliers.filter((s) => {
    const matchesFilter = filter === "ALL" || s.status === filter;
    const matchesSearch =
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      (s.tax_identifier && s.tax_identifier.toLowerCase().includes(search.toLowerCase())) ||
      (s.address && s.address.toLowerCase().includes(search.toLowerCase()));
    return matchesFilter && matchesSearch;
  });

  const activeCount = suppliers.filter((s) => s.status === "ACTIVE").length;

  return (
    <AppLayout locale={params.locale} title="Suppliers & Trade Directory">
      <div className="space-y-6">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">Suppliers & Trade Partners</h2>
            <p className="text-sm text-slate-400">
              Vendor directory, TRN tax identifiers, contacts, and qualification status.
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg shadow-lg shadow-blue-500/20 text-sm transition flex items-center gap-2 self-start"
          >
            <span>+</span> Register Supplier
          </button>
        </div>

        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Total Suppliers</span>
            <div className="text-2xl font-bold text-white mt-1">{suppliers.length}</div>
            <div className="text-xs text-slate-500 mt-1">Directory registered</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Active Vendors</span>
            <div className="text-2xl font-bold text-emerald-400 mt-1">{activeCount}</div>
            <div className="text-xs text-slate-500 mt-1">Pre-qualified for POs</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Compliance Status</span>
            <div className="text-2xl font-bold text-blue-400 mt-1">100%</div>
            <div className="text-xs text-slate-500 mt-1">TRN verified</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Trade Categories</span>
            <div className="text-2xl font-bold text-purple-400 mt-1">Steel, Concrete, MEP</div>
            <div className="text-xs text-slate-500 mt-1">Core disciplines</div>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 w-full md:w-auto">
            <input
              type="text"
              placeholder="Search by vendor name, TRN, or location..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 w-full md:w-80"
            />
          </div>
          <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto">
            {["ALL", "ACTIVE", "INACTIVE"].map((st) => (
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

        {/* Suppliers Table */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-900/80 text-xs text-slate-400 uppercase tracking-wider border-b border-slate-800 font-semibold">
                <tr>
                  <th className="px-6 py-3.5">Supplier / Company</th>
                  <th className="px-6 py-3.5">Tax ID (TRN)</th>
                  <th className="px-6 py-3.5">Operating Address</th>
                  <th className="px-6 py-3.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {loading ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-slate-500">
                      Loading suppliers directory from PostgreSQL...
                    </td>
                  </tr>
                ) : filteredSuppliers.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-slate-500">
                      No suppliers match the selected filter.
                    </td>
                  </tr>
                ) : (
                  filteredSuppliers.map((s) => (
                    <tr key={s.id} className="hover:bg-slate-800/30 transition">
                      <td className="px-6 py-4">
                        <div className="font-semibold text-white">{s.name}</div>
                        {s.legal_name && <div className="text-xs text-slate-400">{s.legal_name}</div>}
                      </td>
                      <td className="px-6 py-4 font-mono text-xs text-slate-300">
                        {s.tax_identifier || "—"}
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-400">
                        {s.address || "—"}
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-2.5 py-1 rounded-full text-[11px] font-semibold ${
                            s.status === "ACTIVE"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : "bg-slate-500/10 text-slate-400 border border-slate-500/20"
                          }`}
                        >
                          {s.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Modal: Register Supplier */}
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-lg font-bold text-white">Register Trade Supplier</h3>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-slate-400 hover:text-white text-lg font-bold"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleRegister} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Company Name *</label>
                  <input
                    type="text"
                    required
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                    placeholder="e.g. Gulf Structural Steel LLC"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">Legal Name</label>
                    <input
                      type="text"
                      value={form.legal_name}
                      onChange={(e) => setForm({ ...form, legal_name: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                      placeholder="e.g. Gulf Structural Steel LLC"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">Tax Identifier (TRN)</label>
                    <input
                      type="text"
                      value={form.tax_identifier}
                      onChange={(e) => setForm({ ...form, tax_identifier: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                      placeholder="e.g. TRN-100223344"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Operating Address</label>
                  <input
                    type="text"
                    value={form.address}
                    onChange={(e) => setForm({ ...form, address: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                    placeholder="e.g. Jebel Ali Industrial Zone 1, Dubai"
                  />
                </div>

                <div className="border-t border-slate-800 pt-3">
                  <span className="text-xs font-semibold text-blue-400 block mb-2">Primary Contact Person</span>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <input
                        type="text"
                        value={form.contact_name}
                        onChange={(e) => setForm({ ...form, contact_name: e.target.value })}
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                        placeholder="Contact Name"
                      />
                    </div>
                    <div>
                      <input
                        type="email"
                        value={form.contact_email}
                        onChange={(e) => setForm({ ...form, contact_email: e.target.value })}
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                        placeholder="Contact Email"
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
                    {submitting ? "Saving..." : "Save Supplier"}
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
