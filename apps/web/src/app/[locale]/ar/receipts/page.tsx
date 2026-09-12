"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import {
  getCustomerReceipts,
  getCustomerReceipt,
  createCustomerReceipt,
  getARInvoices,
  getClients,
  getBankAccounts,
  CustomerReceipt,
  ARInvoice,
  Client,
  BankAccount,
} from "@/lib/api";

export default function ARReceiptsPage({ params }: { params: { locale: string } }) {
  const [receipts, setReceipts] = useState<CustomerReceipt[]>([]);
  const [invoices, setInvoices] = useState<ARInvoice[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [clientFilter, setClientFilter] = useState("ALL");

  // Selection & Details Drawer
  const [selectedReceipt, setSelectedReceipt] = useState<CustomerReceipt | null>(null);

  // New Receipt Modal
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    payment_number: "",
    client_id: "",
    bank_account_id: "",
    payment_date: new Date().toISOString().split("T")[0],
    amount: 0,
    reference: "",
    invoice_id: "",
  });

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [receiptData, invoiceData, clientData, bankData] = await Promise.all([
        getCustomerReceipts(),
        getARInvoices(),
        getClients().catch(() => []),
        getBankAccounts().catch(() => []),
      ]);
      setReceipts(receiptData);
      setInvoices(invoiceData);
      setClients(clientData);
      setBankAccounts(bankData);
    } catch (err: any) {
      setError(err.message || "Failed to load customer collections data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateReceipt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.client_id || !form.bank_account_id || Number(form.amount) <= 0) {
      alert("Please fill in client, bank account, and a positive amount.");
      return;
    }
    setSubmitting(true);
    try {
      await createCustomerReceipt({
        payment_number: form.payment_number,
        client_id: form.client_id,
        bank_account_id: form.bank_account_id,
        payment_date: form.payment_date,
        amount: Number(form.amount),
        reference: form.reference || undefined,
        invoice_id: form.invoice_id || undefined,
      });
      setShowModal(false);
      setForm({
        payment_number: "",
        client_id: "",
        bank_account_id: "",
        payment_date: new Date().toISOString().split("T")[0],
        amount: 0,
        reference: "",
        invoice_id: "",
      });
      await fetchData();
    } catch (err: any) {
      alert(err.message || "Failed to record customer collection");
    } finally {
      setSubmitting(false);
    }
  };

  const filteredReceipts = receipts.filter((rec) => {
    const matchSearch =
      rec.payment_number.toLowerCase().includes(search.toLowerCase()) ||
      (rec.client_name && rec.client_name.toLowerCase().includes(search.toLowerCase())) ||
      (rec.reference && rec.reference.toLowerCase().includes(search.toLowerCase())) ||
      (rec.bank_name && rec.bank_name.toLowerCase().includes(search.toLowerCase()));

    const matchClient = clientFilter === "ALL" || rec.client_id === clientFilter;
    return matchSearch && matchClient;
  });

  const totalCollected = receipts.reduce((acc, r) => acc + Number(r.amount || 0), 0);
  const openInvoicesForClient = form.client_id
    ? invoices.filter(
        (inv) =>
          inv.client_id === form.client_id &&
          (inv.status === "POSTED" || inv.status === "PARTIAL" || inv.status === "APPROVED")
      )
    : [];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "POSTED":
      case "CLEARED":
      case "RECONCILED":
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">Received & Settled</span>;
      case "APPROVED":
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 border border-blue-200">Approved</span>;
      case "DRAFT":
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-700 border border-gray-300">Draft</span>;
      default:
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">{status}</span>;
    }
  };

  return (
    <AppLayout locale={params.locale}>
      <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-white p-6 rounded-2xl border border-gray-200 shadow-sm">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Customer Collections & Receipts</h1>
              <span className="bg-emerald-50 text-emerald-700 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-200">
                Treasury Settlement
              </span>
            </div>
            <p className="text-sm text-gray-500 mt-1">
              Record cash receipts from clients, deposit into operating treasury accounts, and settle open progress invoices.
            </p>
          </div>
          <button
            onClick={() => {
              setForm({
                ...form,
                payment_number: `REC-${new Date().getFullYear()}-${String(receipts.length + 1).padStart(3, "0")}`,
              });
              setShowModal(true);
            }}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-xl shadow-sm transition-all"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Record New Collection
          </button>
        </div>

        {/* Live KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Total Collections</span>
            <div className="text-2xl font-bold text-emerald-600 mt-1">
              ${totalCollected.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <span className="text-xs text-emerald-600 font-medium mt-1 inline-block">Realized cash in bank</span>
          </div>
          <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Total Receipt Transactions</span>
            <div className="text-2xl font-bold text-gray-900 mt-1">{receipts.length}</div>
            <span className="text-xs text-gray-500 font-medium mt-1 inline-block">Vouchers settled</span>
          </div>
          <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Active Treasury Accounts</span>
            <div className="text-2xl font-bold text-blue-600 mt-1">{bankAccounts.length}</div>
            <span className="text-xs text-blue-600 font-medium mt-1 inline-block">Deposit bank accounts (GL 1010)</span>
          </div>
          <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Outstanding Invoices</span>
            <div className="text-2xl font-bold text-rose-600 mt-1">
              {invoices.filter((i) => i.status === "POSTED" || i.status === "PARTIAL").length}
            </div>
            <span className="text-xs text-rose-500 font-medium mt-1 inline-block">Awaiting full collection</span>
          </div>
        </div>

        {/* Search & Filter Bar */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
          <div className="relative w-full md:w-96">
            <input
              type="text"
              placeholder="Search receipt #, reference, client, bank..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all"
            />
            <svg className="w-4 h-4 text-gray-400 absolute left-3.5 top-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>

          <div className="flex items-center gap-3 w-full md:w-auto">
            <label className="text-xs font-medium text-gray-500">Client:</label>
            <select
              value={clientFilter}
              onChange={(e) => setClientFilter(e.target.value)}
              className="px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-lg text-xs font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="ALL">All Clients</option>
              {clients.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Collections Table & Details */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className={`bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden ${selectedReceipt ? "lg:col-span-2" : "lg:col-span-3"}`}>
            {loading ? (
              <div className="p-12 text-center text-gray-500">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mx-auto mb-3"></div>
                Loading customer collections...
              </div>
            ) : error ? (
              <div className="p-8 text-center text-rose-600 bg-rose-50 rounded-xl m-4 border border-rose-200">
                <p className="font-semibold">{error}</p>
                <button onClick={fetchData} className="mt-2 text-xs text-rose-700 underline">Try again</button>
              </div>
            ) : filteredReceipts.length === 0 ? (
              <div className="p-12 text-center text-gray-500">
                <svg className="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                <p className="font-medium text-gray-700">No collections found</p>
                <p className="text-xs text-gray-400 mt-1">Record your first customer receipt to deposit cash and settle client invoices.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 bg-gray-50/75 text-gray-600 font-semibold text-xs uppercase tracking-wider">
                      <th className="p-3.5">Receipt #</th>
                      <th className="p-3.5">Client</th>
                      <th className="p-3.5">Deposit Bank Account</th>
                      <th className="p-3.5">Date</th>
                      <th className="p-3.5 text-right">Amount</th>
                      <th className="p-3.5">Reference</th>
                      <th className="p-3.5 text-center">Status</th>
                      <th className="p-3.5 text-center">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {filteredReceipts.map((rec) => (
                      <tr
                        key={rec.id}
                        className={`hover:bg-emerald-50/30 transition-colors cursor-pointer ${selectedReceipt?.id === rec.id ? "bg-emerald-50/60" : ""}`}
                        onClick={() => setSelectedReceipt(rec)}
                      >
                        <td className="p-3.5 font-semibold text-emerald-700">{rec.payment_number}</td>
                        <td className="p-3.5 font-medium text-gray-900">{rec.client_name || "Unknown Client"}</td>
                        <td className="p-3.5 text-xs text-gray-600">
                          <span className="font-semibold text-gray-800 block">{rec.bank_name || "Treasury Account"}</span>
                          <span className="text-gray-400">{rec.bank_account_name || ""}</span>
                        </td>
                        <td className="p-3.5 text-xs text-gray-600">{rec.payment_date}</td>
                        <td className="p-3.5 text-right font-bold text-emerald-600">
                          ${Number(rec.amount || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="p-3.5 text-xs text-gray-500">{rec.reference || "N/A"}</td>
                        <td className="p-3.5 text-center">{getStatusBadge(rec.status)}</td>
                        <td className="p-3.5 text-center" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={() => setSelectedReceipt(rec)}
                            className="px-2.5 py-1 text-xs text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded-lg border border-emerald-200"
                          >
                            Details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Details Drawer */}
          {selectedReceipt && (
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 space-y-4">
              <div className="flex items-center justify-between border-b pb-3">
                <div>
                  <h3 className="text-lg font-bold text-gray-900">{selectedReceipt.payment_number}</h3>
                  <span className="text-xs text-gray-500">Collection Voucher Details</span>
                </div>
                <button
                  onClick={() => setSelectedReceipt(null)}
                  className="text-gray-400 hover:text-gray-600 p-1"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4 text-xs">
                <div className="bg-gray-50 p-3.5 rounded-xl space-y-2 border border-gray-200">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Client:</span>
                    <span className="font-semibold text-gray-900">{selectedReceipt.client_name || "N/A"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Bank Account:</span>
                    <span className="font-semibold text-gray-900">{selectedReceipt.bank_name || "N/A"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Payment Date:</span>
                    <span className="font-medium text-gray-900">{selectedReceipt.payment_date}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Reference:</span>
                    <span className="font-medium text-gray-900">{selectedReceipt.reference || "None"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Status:</span>
                    <span>{getStatusBadge(selectedReceipt.status)}</span>
                  </div>
                  {selectedReceipt.journal_id && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">GL Journal Entry:</span>
                      <span className="font-mono text-purple-700 font-semibold">{selectedReceipt.journal_id.slice(0, 8)}...</span>
                    </div>
                  )}
                </div>

                <div className="bg-emerald-50 p-4 rounded-xl border border-emerald-200 space-y-2">
                  <div className="flex justify-between text-xs text-emerald-800">
                    <span>Total Deposited:</span>
                    <span className="text-lg font-bold text-emerald-700">
                      ${Number(selectedReceipt.amount || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                  <div className="text-[11px] text-emerald-700 font-medium">
                    Posted to General Ledger: Debit Cash (1010), Credit Accounts Receivable (1200).
                  </div>
                </div>

                {/* Allocations Breakdown */}
                <div>
                  <h4 className="font-semibold text-gray-800 uppercase tracking-wider text-[11px] mb-2">Invoice Settlement Allocations</h4>
                  {selectedReceipt.allocations && selectedReceipt.allocations.length > 0 ? (
                    <div className="space-y-2">
                      {selectedReceipt.allocations.map((alloc) => (
                        <div key={alloc.id} className="p-3 bg-gray-50 rounded-xl border border-gray-200 flex justify-between items-center text-xs">
                          <div>
                            <span className="font-bold text-gray-900 block">{alloc.invoice_number || "Invoice"}</span>
                            <span className="text-[10px] text-gray-500">ID: {alloc.invoice_id.slice(0, 8)}...</span>
                          </div>
                          <span className="font-bold text-emerald-700">
                            ${Number(alloc.allocated_amount).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-400 italic text-xs">Direct deposit with automatic balance settlement.</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal: New Customer Collection */}
        {showModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl border border-gray-200">
              <div className="flex items-center justify-between border-b pb-3">
                <h3 className="text-lg font-bold text-gray-900">Record Customer Collection</h3>
                <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600">✕</button>
              </div>

              <form onSubmit={handleCreateReceipt} className="space-y-4 text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-semibold text-gray-700 mb-1">Receipt Number</label>
                    <input
                      type="text"
                      value={form.payment_number}
                      onChange={(e) => setForm({ ...form, payment_number: e.target.value })}
                      required
                      placeholder="e.g. REC-2026-003"
                      className="w-full p-2.5 bg-gray-50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-gray-700 mb-1">Receipt Date</label>
                    <input
                      type="date"
                      value={form.payment_date}
                      onChange={(e) => setForm({ ...form, payment_date: e.target.value })}
                      required
                      className="w-full p-2.5 bg-gray-50 border border-gray-300 rounded-xl"
                    />
                  </div>
                </div>

                <div>
                  <label className="block font-semibold text-gray-700 mb-1">Client</label>
                  <select
                    value={form.client_id}
                    onChange={(e) => setForm({ ...form, client_id: e.target.value, invoice_id: "" })}
                    required
                    className="w-full p-2.5 bg-gray-50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="">-- Choose Client --</option>
                    {clients.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-gray-700 mb-1">Deposit Treasury Bank Account (GL 1010)</label>
                  <select
                    value={form.bank_account_id}
                    onChange={(e) => setForm({ ...form, bank_account_id: e.target.value })}
                    required
                    className="w-full p-2.5 bg-gray-50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="">-- Choose Bank Account --</option>
                    {bankAccounts.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.name} - {b.bank_name} ({b.currency || "USD"})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Settle Invoice Selector */}
                {form.client_id && (
                  <div>
                    <label className="block font-semibold text-gray-700 mb-1">
                      Allocate to Open Invoice (Optional)
                    </label>
                    <select
                      value={form.invoice_id}
                      onChange={(e) => {
                        const invId = e.target.value;
                        const targetInv = invoices.find((i) => i.id === invId);
                        setForm({
                          ...form,
                          invoice_id: invId,
                          amount: targetInv ? Number(targetInv.outstanding_amount ?? targetInv.total_amount) : form.amount,
                        });
                      }}
                      className="w-full p-2.5 bg-gray-50 border border-gray-300 rounded-xl text-xs"
                    >
                      <option value="">-- Unallocated / General Collection --</option>
                      {openInvoicesForClient.map((inv) => (
                        <option key={inv.id} value={inv.id}>
                          {inv.number} - Balance Due: ${Number(inv.outstanding_amount ?? inv.total_amount).toLocaleString()} ({inv.status})
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-semibold text-gray-700 mb-1">Amount Collected ($)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0.01"
                      value={form.amount}
                      onChange={(e) => setForm({ ...form, amount: parseFloat(e.target.value) || 0 })}
                      required
                      className="w-full p-2.5 bg-gray-50 border border-gray-300 rounded-xl font-bold text-emerald-700 text-sm"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-gray-700 mb-1">Check / Wire Reference</label>
                    <input
                      type="text"
                      placeholder="e.g. WIRE-884210"
                      value={form.reference}
                      onChange={(e) => setForm({ ...form, reference: e.target.value })}
                      className="w-full p-2.5 bg-gray-50 border border-gray-300 rounded-xl"
                    />
                  </div>
                </div>

                <div className="bg-gray-50 p-3 rounded-xl border border-gray-200 text-[11px] text-gray-600 space-y-1">
                  <p className="font-semibold text-gray-800">Automatic Double-Entry Posting:</p>
                  <p>• Debits the selected Treasury Bank Account (Asset 1010).</p>
                  <p>• Credits Accounts Receivable (Asset 1200) reducing client balance.</p>
                  <p>• Updates invoice paid amount and transitions status automatically.</p>
                </div>

                <div className="flex justify-end gap-3 pt-3 border-t">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-semibold transition-all disabled:opacity-50 shadow-sm"
                  >
                    {submitting ? "Processing..." : "Record Collection"}
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
