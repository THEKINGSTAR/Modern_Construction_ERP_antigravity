"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import {
  getPayments,
  getPayment,
  createPayment,
  getAPInvoices,
  getBankAccounts,
  getSuppliers,
  Payment,
  APInvoice,
  BankAccount,
  Supplier,
} from "@/lib/api";

export default function APPaymentsPage({ params }: { params: { locale: string } }) {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [invoices, setInvoices] = useState<APInvoice[]>([]);
  const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [selectedPayment, setSelectedPayment] = useState<Payment | null>(null);

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    reference: `VCH-${new Date().getFullYear()}-${Math.floor(1000 + Math.random() * 9000)}`,
    payment_type: "AP_PAYMENT",
    date: new Date().toISOString().split("T")[0],
    amount: 0,
    currency: "USD",
    supplier_id: "",
    bank_account_id: "",
    selected_invoice_id: "",
  });

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [payData, invData, bankData, supData] = await Promise.all([
        getPayments(),
        getAPInvoices(),
        getBankAccounts().catch(() => []),
        getSuppliers().catch(() => []),
      ]);
      setPayments(payData);
      setInvoices(invData);
      setBankAccounts(bankData);
      setSuppliers(supData);
    } catch (err: any) {
      setError(err.message || "Failed to load payment disbursements");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const totalDisbursed = payments.reduce((acc, p) => acc + Number(p.amount || 0), 0);

  const handleSupplierChange = (supId: string) => {
    setForm((prev) => ({
      ...prev,
      supplier_id: supId,
      selected_invoice_id: "",
      amount: 0,
    }));
  };

  const handleInvoiceSelect = (invId: string) => {
    const inv = invoices.find((i) => i.id === invId);
    if (!inv) return;
    const outstanding = Number(inv.outstanding_amount || inv.total_amount || 0);
    setForm((prev) => ({
      ...prev,
      selected_invoice_id: invId,
      amount: outstanding,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.reference || !form.bank_account_id || form.amount <= 0) {
      alert("Please provide payment reference, source bank account, and a positive disbursement amount.");
      return;
    }

    try {
      setSubmitting(true);
      await createPayment({
        reference: form.reference,
        payment_type: form.payment_type,
        date: form.date,
        amount: Number(form.amount),
        currency: form.currency,
        supplier_id: form.supplier_id || undefined,
        bank_account_id: form.bank_account_id,
        allocations: form.selected_invoice_id
          ? [
              {
                ap_invoice_id: form.selected_invoice_id,
                amount: Number(form.amount),
              },
            ]
          : [],
      });

      setShowModal(false);
      setForm({
        reference: `VCH-${new Date().getFullYear()}-${Math.floor(1000 + Math.random() * 9000)}`,
        payment_type: "AP_PAYMENT",
        date: new Date().toISOString().split("T")[0],
        amount: 0,
        currency: "USD",
        supplier_id: "",
        bank_account_id: "",
        selected_invoice_id: "",
      });
      await fetchData();
    } catch (err: any) {
      alert(err.message || "Failed to process disbursement voucher");
    } finally {
      setSubmitting(false);
    }
  };

  const filteredPayments = payments.filter((p) => {
    const term = search.toLowerCase();
    return (
      p.reference.toLowerCase().includes(term) ||
      (p.supplier_name && p.supplier_name.toLowerCase().includes(term)) ||
      (p.bank_name && p.bank_name.toLowerCase().includes(term))
    );
  });

  const unpaidInvoices = invoices.filter(
    (inv) =>
      inv.status !== "PAID" &&
      (!form.supplier_id || inv.supplier_id === form.supplier_id)
  );

  return (
    <AppLayout locale={params.locale}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Vendor Payments & Disbursements</h1>
            <p className="text-sm text-slate-400">
              Treasury cash disbursement vouchers, general ledger settlement, and AP invoice allocation
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-lg shadow-sm transition-colors"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Issue Payment Voucher
          </button>
        </div>

        {/* KPI Strip */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs font-medium text-slate-400">Total Disbursed</span>
            <div className="text-xl font-bold text-emerald-400 mt-1 font-mono">
              ${totalDisbursed.toLocaleString("en-US", { minimumFractionDigits: 2 })}
            </div>
            <span className="text-xs text-slate-500 mt-1 block">Cleared Treasury Disbursals</span>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs font-medium text-blue-400">Active Bank Accounts</span>
            <div className="text-xl font-bold text-blue-400 mt-1 font-mono">
              {bankAccounts.length} <span className="text-sm text-slate-400">Treasury Accounts</span>
            </div>
            <span className="text-xs text-slate-500 mt-1 block">Connected GL Cash Accounts</span>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs font-medium text-purple-400">Vouchers Posted</span>
            <div className="text-xl font-bold text-purple-400 mt-1 font-mono">
              {payments.length} <span className="text-sm text-slate-400">Transactions</span>
            </div>
            <span className="text-xs text-purple-400/80 mt-1 block">General Ledger Balanced</span>
          </div>
        </div>

        {/* Search */}
        <div className="flex gap-4">
          <div className="relative flex-1">
            <svg
              className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search by voucher reference, supplier, bank..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-900/60 border border-slate-800 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {/* Data Table */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
          {loading ? (
            <div className="p-8 text-center text-slate-400">Loading payment records...</div>
          ) : error ? (
            <div className="p-8 text-center text-rose-400">{error}</div>
          ) : filteredPayments.length === 0 ? (
            <div className="p-8 text-center text-slate-500">No payment records found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-950/40 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                    <th className="px-6 py-3">Voucher Ref</th>
                    <th className="px-6 py-3">Date</th>
                    <th className="px-6 py-3">Beneficiary Supplier</th>
                    <th className="px-6 py-3">Source Treasury Bank</th>
                    <th className="px-6 py-3 text-right">Disbursed Amount</th>
                    <th className="px-6 py-3">GL Status</th>
                    <th className="px-6 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredPayments.map((pay) => (
                    <tr key={pay.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-6 py-4 font-mono font-medium text-white">{pay.reference}</td>
                      <td className="px-6 py-4 text-slate-400 text-xs">{pay.date}</td>
                      <td className="px-6 py-4 font-medium text-slate-200">{pay.supplier_name || "Direct Vendor"}</td>
                      <td className="px-6 py-4 text-slate-400 text-xs">
                        <div className="font-medium text-slate-300">{pay.bank_name || "Main Treasury"}</div>
                        <div className="text-[11px] text-slate-500">{pay.bank_account_name}</div>
                      </td>
                      <td className="px-6 py-4 text-right font-mono font-bold text-emerald-400">
                        ${Number(pay.amount).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-6 py-4">
                        <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20">
                          {pay.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => setSelectedPayment(pay)}
                          className="px-3 py-1 text-xs font-medium text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 rounded transition-colors"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Payment Detail Modal */}
        {selectedPayment && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-lg font-bold text-white">Payment Voucher {selectedPayment.reference}</h3>
                <button onClick={() => setSelectedPayment(null)} className="text-slate-400 hover:text-white">
                  ✕
                </button>
              </div>
              <div className="space-y-2 text-sm text-slate-300">
                <div className="flex justify-between">
                  <span className="text-slate-500">Beneficiary:</span>
                  <span className="font-semibold text-white">{selectedPayment.supplier_name || "Vendor"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Date Disbursed:</span>
                  <span>{selectedPayment.date}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Disbursed From:</span>
                  <span>{selectedPayment.bank_name || "Main Treasury Bank"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Total Disbursed:</span>
                  <span className="font-mono font-bold text-emerald-400 text-base">
                    ${Number(selectedPayment.amount).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                  </span>
                </div>
                {selectedPayment.journal_id && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">GL Journal ID:</span>
                    <span className="font-mono text-xs text-purple-400">{selectedPayment.journal_id}</span>
                  </div>
                )}
              </div>

              {selectedPayment.allocations && selectedPayment.allocations.length > 0 && (
                <div className="pt-2">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                    Settled Invoice Allocations
                  </span>
                  <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800 space-y-2">
                    {selectedPayment.allocations.map((alloc, i) => (
                      <div key={i} className="flex justify-between text-xs font-mono">
                        <span className="text-slate-400">AP Invoice {alloc.ap_invoice_id?.slice(0, 8)}...</span>
                        <span className="text-emerald-400 font-bold">${Number(alloc.amount).toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="pt-4 border-t border-slate-800 flex justify-end">
                <button
                  onClick={() => setSelectedPayment(null)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Issue Payment Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                <h3 className="text-lg font-bold text-white">Issue Vendor Payment Voucher</h3>
                <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-white">
                  ✕
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Voucher Reference *</label>
                  <input
                    type="text"
                    required
                    value={form.reference}
                    onChange={(e) => setForm({ ...form, reference: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500 font-mono"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">Payment Date</label>
                    <input
                      type="date"
                      required
                      value={form.date}
                      onChange={(e) => setForm({ ...form, date: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">Source Bank Account *</label>
                    <select
                      required
                      value={form.bank_account_id}
                      onChange={(e) => setForm({ ...form, bank_account_id: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                    >
                      <option value="">Select Treasury Bank</option>
                      {bankAccounts.map((b) => (
                        <option key={b.id} value={b.id}>
                          {b.name} ({b.account_number})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Beneficiary Supplier *</label>
                  <select
                    required
                    value={form.supplier_id}
                    onChange={(e) => handleSupplierChange(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="">Select Supplier</option>
                    {suppliers.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Outstanding Invoice Selection */}
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Allocate to Unpaid Invoice</label>
                  <select
                    value={form.selected_invoice_id}
                    onChange={(e) => handleInvoiceSelect(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="">-- Direct Advance / General Allocation --</option>
                    {unpaidInvoices.map((inv) => (
                      <option key={inv.id} value={inv.id}>
                        {inv.number} — Total: ${Number(inv.total_amount).toLocaleString()} (Bal: $
                        {Number(inv.outstanding_amount || inv.total_amount).toLocaleString()})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Disbursement Amount ($ USD) *</label>
                  <input
                    type="number"
                    step="any"
                    required
                    min="0.01"
                    value={form.amount}
                    onChange={(e) => setForm({ ...form, amount: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-emerald-400 font-mono font-bold focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div className="pt-4 border-t border-slate-800 flex justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 text-sm text-slate-400 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium transition-colors"
                  >
                    {submitting ? "Processing Settlement..." : "Post Disbursement Voucher"}
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
