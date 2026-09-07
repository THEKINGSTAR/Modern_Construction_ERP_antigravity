"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import { getClients, createClient, updateClient, deleteClient, Client } from "@/lib/api";

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [editingClient, setEditingClient] = useState<Client | null>(null);

  const [formData, setFormData] = useState({
    name: "",
    legal_name: "",
    contact_information: "",
    billing_address: "",
    tax_identifier: "",
    status: "ACTIVE",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await getClients();
      setClients(data);
    } catch (err) {
      console.error("Failed to load clients", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleOpenCreate = () => {
    setEditingClient(null);
    setFormData({
      name: "",
      legal_name: "",
      contact_information: "",
      billing_address: "",
      tax_identifier: "",
      status: "ACTIVE",
    });
    setShowModal(true);
  };

  const handleOpenEdit = (c: Client) => {
    setEditingClient(c);
    setFormData({
      name: c.name,
      legal_name: c.legal_name || "",
      contact_information: c.contact_information || "",
      billing_address: c.billing_address || "",
      tax_identifier: c.tax_identifier || "",
      status: c.status || "ACTIVE",
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingClient) {
        await updateClient(editingClient.id, formData);
      } else {
        await createClient(formData);
      }
      setShowModal(false);
      await loadData();
    } catch (err: any) {
      alert("Error saving client: " + err.message);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this client?")) return;
    try {
      await deleteClient(id);
      await loadData();
    } catch (err: any) {
      alert("Error deleting client: " + err.message);
    }
  };

  const filtered = clients.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      (c.legal_name && c.legal_name.toLowerCase().includes(search.toLowerCase())) ||
      (c.contact_information && c.contact_information.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <AppLayout
      title="Client Registry"
      subtitle="Owner organizations, developers, and commercial client accounts management"
      actions={
        <button
          onClick={handleOpenCreate}
          className="px-3.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 shadow-md shadow-amber-500/20 transition"
        >
          <span>➕</span> Register Client
        </button>
      }
    >
      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Total Client Accounts</div>
          <div className="text-2xl font-black text-white mt-1">{clients.length}</div>
          <div className="text-[11px] text-emerald-400 mt-1">Verified In PostgreSQL Database</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Active Corporate Accounts</div>
          <div className="text-2xl font-black text-amber-400 mt-1">
            {clients.filter((c) => c.status === "ACTIVE").length}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">In Good Commercial Standing</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-slate-400 font-medium">Billing Jurisdiction</div>
          <div className="text-2xl font-black text-indigo-400 mt-1">Standard Tax Compliant</div>
          <div className="text-[11px] text-slate-400 mt-1">Automated AP/AR Reconciliation</div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 flex justify-between items-center">
          <input
            type="text"
            placeholder="Search clients by name, contact, or legal entity..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-80 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500"
          />
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/50 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="py-3.5 px-4">Client Name</th>
                <th className="py-3.5 px-4">Legal Name</th>
                <th className="py-3.5 px-4">Contact Details</th>
                <th className="py-3.5 px-4">Tax Identifier</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-slate-500">
                    Loading client records from PostgreSQL...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-slate-500">
                    No client records found.
                  </td>
                </tr>
              ) : (
                filtered.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3.5 px-4 font-bold text-white">{c.name}</td>
                    <td className="py-3.5 px-4 text-slate-400">{c.legal_name || "Same as trade name"}</td>
                    <td className="py-3.5 px-4">{c.contact_information || "None on file"}</td>
                    <td className="py-3.5 px-4 font-mono text-slate-400">{c.tax_identifier || "Pending"}</td>
                    <td className="py-3.5 px-4">
                      <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        {c.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-2">
                      <button
                        onClick={() => handleOpenEdit(c)}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-[11px]"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(c.id)}
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

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <h2 className="text-base font-bold text-white flex items-center justify-between">
              <span>{editingClient ? "Edit Client Profile" : "Register Client Organization"}</span>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-200 text-lg"
              >
                ✕
              </button>
            </h2>

            <form onSubmit={handleSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Client Commercial Name *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:border-amber-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Legal Entity Name</label>
                <input
                  type="text"
                  value={formData.legal_name}
                  onChange={(e) => setFormData({ ...formData, legal_name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:border-amber-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Contact (Phone / Email)</label>
                  <input
                    type="text"
                    value={formData.contact_information}
                    onChange={(e) => setFormData({ ...formData, contact_information: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Tax / Business ID</label>
                  <input
                    type="text"
                    value={formData.tax_identifier}
                    onChange={(e) => setFormData({ ...formData, tax_identifier: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white font-mono focus:border-amber-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Billing Address</label>
                <textarea
                  rows={2}
                  value={formData.billing_address}
                  onChange={(e) => setFormData({ ...formData, billing_address: e.target.value })}
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
                  Save Client
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
