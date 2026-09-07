"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import {
  getAPInvoices,
  getAPInvoice,
  createAPInvoice,
  matchAPInvoice,
  approveAPInvoice,
  postAPInvoice,
  getAPSummary,
  getSuppliers,
  getPurchaseOrders,
  getGoodsReceipts,
  APInvoice,
  ThreeWayMatchReport,
  APSummary,
  Supplier,
  PurchaseOrder,
  GoodsReceipt,
} from "@/lib/api";

export default function APInvoicesPage({ params }: { params: { locale: string } }) {
  const [invoices, setInvoices] = useState<APInvoice[]>([]);
  const [summary, setSummary] = useState<APSummary | null>(null);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrder[]>([]);
  const [goodsReceipts, setGoodsReceipts] = useState<GoodsReceipt[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [matchingFilter, setMatchingFilter] = useState("ALL");

  // 3-Way Match Studio State
  const [matchReport, setMatchReport] = useState<ThreeWayMatchReport | null>(null);
  const [matchingLoading, setMatchingLoading] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState<APInvoice | null>(null);

  // New Invoice Modal
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  const [form, setForm] = useState({
    number: "",
    supplier_id: "",
    purchase_order_id: "",
    goods_receipt_id: "",
    date: new Date().toISOString().split("T")[0],
    due_date: new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0],
    description: "",
    tax_amount: 0,
    lines: [
      {
        description: "",
        quantity: 1,
        unit_price: 0,
        tax_rate: 0,
      },
    ],
  });

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [invData, sumData, supData, poData, grnData] = await Promise.all([
        getAPInvoices(),
        getAPSummary().catch(() => null),
        getSuppliers().catch(() => []),
        getPurchaseOrders().catch(() => []),
        getGoodsReceipts().catch(() => []),
      ]);
      setInvoices(invData);
      setSummary(sumData);
      setSuppliers(supData);
      setPurchaseOrders(poData);
      setGoodsReceipts(grnData);
    } catch (err: any) {
      setError(err.message || "Failed to load accounts payable invoices");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRunMatch = async (inv: APInvoice) => {
    try {
      setSelectedInvoice(inv);
      setMatchingLoading(true);
      const report = await matchAPInvoice(inv.id);
      setMatchReport(report);
      // Refresh list to update badge
      const updatedList = await getAPInvoices();
      setInvoices(updatedList);
    } catch (err: any) {
      alert(err.message || "Failed to execute 3-way match verification");
    } finally {
      setMatchingLoading(false);
    }
  };

  const handleApprove = async (id: string) => {
    try {
      setActionLoadingId(id);
      await approveAPInvoice(id);
      await fetchData();
      if (matchReport && matchReport.invoice_id === id) {
        setMatchReport(null);
      }
    } catch (err: any) {
      alert(err.message || "Approval failed");
    } finally {
      setActionLoadingId(null);
    }
  };

  const handlePostGL = async (id: string) => {
    try {
      setActionLoadingId(id);
      await postAPInvoice(id);
      await fetchData();
    } catch (err: any) {
      alert(err.message || "Posting to General Ledger failed");
    } finally {
      setActionLoadingId(null);
    }
  };

  const handlePoSelection = (poId: string) => {
    const selectedPo = purchaseOrders.find((p) => p.id === poId);
    if (!selectedPo) return;

    // Auto-resolve linked GRN if available
    const linkedGrn = goodsReceipts.find((g) => g.purchase_order_id === poId);

    setForm((prev) => ({
      ...prev,
      purchase_order_id: poId,
      goods_receipt_id: linkedGrn ? linkedGrn.id : prev.goods_receipt_id,
      supplier_id: selectedPo.supplier_id || prev.supplier_id,
      description: `Invoice for PO ${selectedPo.po_number}`,
      lines: selectedPo.lines && selectedPo.lines.length > 0
        ? selectedPo.lines.map((l: any) => ({
            description: l.item_description || "PO Line Item",
            quantity: Number(l.quantity) || 1,
            unit_price: Number(l.unit_price) || 0,
            tax_rate: 0,
          }))
        : [
            {
              description: `Materials delivery against PO ${selectedPo.po_number}`,
              quantity: 1,
              unit_price: Number(selectedPo.total_amount) || 0,
              tax_rate: 0,
            },
          ],
    }));
  };

  const handleAddLine = () => {
    setForm((prev) => ({
      ...prev,
      lines: [...prev.lines, { description: "", quantity: 1, unit_price: 0, tax_rate: 0 }],
    }));
  };

  const handleRemoveLine = (index: number) => {
    setForm((prev) => ({
      ...prev,
      lines: prev.lines.filter((_, i) => i !== index),
    }));
  };

  const handleLineChange = (index: number, field: string, value: any) => {
    setForm((prev) => {
      const updatedLines = [...prev.lines];
      updatedLines[index] = { ...updatedLines[index], [field]: value };
      return { ...prev, lines: updatedLines };
    });
  };

  const calculateSubtotal = () => {
    return form.lines.reduce((acc, l) => acc + (Number(l.quantity) || 0) * (Number(l.unit_price) || 0), 0);
  };

  const calculateTotal = () => {
    const sub = calculateSubtotal();
    const lineTaxes = form.lines.reduce(
      (acc, l) => acc + (Number(l.quantity) || 0) * (Number(l.unit_price) || 0) * ((Number(l.tax_rate) || 0) / 100),
      0
    );
    return sub + lineTaxes + (Number(form.tax_amount) || 0);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.number || !form.supplier_id || form.lines.length === 0) {
      alert("Please fill in invoice number, supplier, and at least one line item.");
      return;
    }

    try {
      setSubmitting(true);
      await createAPInvoice({
        number: form.number,
        supplier_id: form.supplier_id,
        purchase_order_id: form.purchase_order_id || undefined,
        goods_receipt_id: form.goods_receipt_id || undefined,
        date: form.date,
        due_date: form.due_date,
        description: form.description,
        tax_amount: Number(form.tax_amount) || 0,
        lines: form.lines.map((l) => ({
          description: l.description,
          quantity: Number(l.quantity),
          unit_price: Number(l.unit_price),
          tax_rate: Number(l.tax_rate) || 0,
        })),
      });

      setShowModal(false);
      setForm({
        number: "",
        supplier_id: "",
        purchase_order_id: "",
        goods_receipt_id: "",
        date: new Date().toISOString().split("T")[0],
        due_date: new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0],
        description: "",
        tax_amount: 0,
        lines: [{ description: "", quantity: 1, unit_price: 0, tax_rate: 0 }],
      });
      await fetchData();
    } catch (err: any) {
      alert(err.message || "Failed to create invoice");
    } finally {
      setSubmitting(false);
    }
  };

  const filteredInvoices = invoices.filter((inv) => {
    const term = search.toLowerCase();
    const matchTerm =
      inv.number.toLowerCase().includes(term) ||
      (inv.supplier_name && inv.supplier_name.toLowerCase().includes(term)) ||
      (inv.po_number && inv.po_number.toLowerCase().includes(term)) ||
      (inv.grn_number && inv.grn_number.toLowerCase().includes(term));

    const matchStatus = statusFilter === "ALL" || inv.status === statusFilter;
    const matchMatching = matchingFilter === "ALL" || inv.matching_status === matchingFilter;
    return matchTerm && matchStatus && matchMatching;
  });

  return (
    <AppLayout locale={params.locale}>
      <div className="space-y-6">
        {/* Header Title */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Accounts Payable & Invoicing</h1>
            <p className="text-sm text-slate-400">
              Contractor 3-way matching, variance detection, GL posting, and vendor disbursements
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-lg shadow-sm transition-colors"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Register Vendor Invoice
          </button>
        </div>

        {/* Executive KPI Strip */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs font-medium text-slate-400">Total Invoiced</span>
            <div className="text-xl font-bold text-white mt-1 font-mono">
              ${summary ? Number(summary.total_invoiced).toLocaleString("en-US", { minimumFractionDigits: 2 }) : "0.00"}
            </div>
            <span className="text-xs text-slate-500 mt-1 block">Gross billing to date</span>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs font-medium text-amber-400">Outstanding Payables</span>
            <div className="text-xl font-bold text-amber-400 mt-1 font-mono">
              ${summary ? Number(summary.total_payables).toLocaleString("en-US", { minimumFractionDigits: 2 }) : "0.00"}
            </div>
            <span className="text-xs text-slate-500 mt-1 block">Unsettled vendor liability</span>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs font-medium text-emerald-400">3-Way Matched</span>
            <div className="text-xl font-bold text-emerald-400 mt-1 font-mono">
              {summary ? summary.matched_count : 0} <span className="text-sm text-slate-400">Invoices</span>
            </div>
            <span className="text-xs text-emerald-500/80 mt-1 block">PO + GRN + Invoice verified</span>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <span className="text-xs font-medium text-rose-400">Variance Flags</span>
            <div className="text-xl font-bold text-rose-400 mt-1 font-mono">
              {summary ? summary.variance_count : 0} <span className="text-sm text-slate-400">Alerts</span>
            </div>
            <span className="text-xs text-rose-400/80 mt-1 block">Require approval or credit note</span>
          </div>
        </div>

        {/* Filter / Search Bar */}
        <div className="flex flex-col sm:flex-row gap-3">
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
              placeholder="Search by invoice number, supplier, PO#, GRN#..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-900/60 border border-slate-800 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div className="flex gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 bg-slate-900/60 border border-slate-800 rounded-lg text-sm text-slate-300 focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="DRAFT">Draft</option>
              <option value="APPROVED">Approved</option>
              <option value="POSTED">Posted</option>
              <option value="PARTIAL">Partial</option>
              <option value="PAID">Paid</option>
            </select>
            <select
              value={matchingFilter}
              onChange={(e) => setMatchingFilter(e.target.value)}
              className="px-3 py-2 bg-slate-900/60 border border-slate-800 rounded-lg text-sm text-slate-300 focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">All Matching</option>
              <option value="MATCHED">Matched</option>
              <option value="VARIANCE">Variance</option>
              <option value="UNMATCHED">Unmatched</option>
            </select>
          </div>
        </div>

        {/* Data Table */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
          {loading ? (
            <div className="p-8 text-center text-slate-400">Loading AP invoices from PostgreSQL...</div>
          ) : error ? (
            <div className="p-8 text-center text-rose-400">{error}</div>
          ) : filteredInvoices.length === 0 ? (
            <div className="p-8 text-center text-slate-500">No invoices match the selected criteria.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-950/40 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                    <th className="px-6 py-3">Invoice #</th>
                    <th className="px-6 py-3">Supplier</th>
                    <th className="px-6 py-3">PO / GRN Match</th>
                    <th className="px-6 py-3">Invoice Date</th>
                    <th className="px-6 py-3 text-right">Total Amount</th>
                    <th className="px-6 py-3 text-right">Outstanding</th>
                    <th className="px-6 py-3">3-Way Match</th>
                    <th className="px-6 py-3">Status</th>
                    <th className="px-6 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredInvoices.map((inv) => (
                    <tr key={inv.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-6 py-4 font-mono font-medium text-white">{inv.number}</td>
                      <td className="px-6 py-4 text-slate-300 font-medium">{inv.supplier_name || "Unknown Supplier"}</td>
                      <td className="px-6 py-4">
                        <div className="flex flex-col gap-1 text-xs font-mono">
                          {inv.po_number && (
                            <span className="text-blue-400 inline-flex items-center">
                              <span className="w-1.5 h-1.5 rounded-full bg-blue-400 mr-1.5"></span>
                              {inv.po_number}
                            </span>
                          )}
                          {inv.grn_number && (
                            <span className="text-emerald-400 inline-flex items-center">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5"></span>
                              {inv.grn_number}
                            </span>
                          )}
                          {!inv.po_number && !inv.grn_number && <span className="text-slate-500">Direct Expense</span>}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-slate-400 text-xs">
                        <div>{inv.date}</div>
                        <div className="text-[11px] text-slate-500">Due: {inv.due_date}</div>
                      </td>
                      <td className="px-6 py-4 text-right font-mono font-semibold text-white">
                        ${Number(inv.total_amount).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-6 py-4 text-right font-mono font-semibold">
                        <span
                          className={
                            Number(inv.outstanding_amount || 0) > 0 ? "text-amber-400" : "text-emerald-400"
                          }
                        >
                          ${Number(inv.outstanding_amount || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${
                            inv.matching_status === "MATCHED"
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                              : inv.matching_status === "VARIANCE"
                              ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                              : "bg-slate-800 text-slate-400 border-slate-700"
                          }`}
                        >
                          {inv.matching_status === "MATCHED" && (
                            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          )}
                          {inv.matching_status === "VARIANCE" && (
                            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                              />
                            </svg>
                          )}
                          {inv.matching_status}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${
                            inv.status === "PAID"
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                              : inv.status === "PARTIAL"
                              ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                              : inv.status === "POSTED"
                              ? "bg-purple-500/10 text-purple-400 border-purple-500/20"
                              : inv.status === "APPROVED"
                              ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
                              : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                          }`}
                        >
                          {inv.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => handleRunMatch(inv)}
                            className="px-2.5 py-1 text-xs font-medium text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 rounded transition-colors"
                            title="Verify 3-Way Match against PO & GRN"
                          >
                            3-Way Match
                          </button>
                          {inv.status === "DRAFT" && (
                            <button
                              onClick={() => handleApprove(inv.id)}
                              disabled={actionLoadingId === inv.id}
                              className="px-2.5 py-1 text-xs font-medium text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/10 rounded transition-colors"
                            >
                              Approve
                            </button>
                          )}
                          {(inv.status === "DRAFT" || inv.status === "APPROVED") && (
                            <button
                              onClick={() => handlePostGL(inv.id)}
                              disabled={actionLoadingId === inv.id}
                              className="px-2.5 py-1 text-xs font-medium text-purple-400 hover:text-purple-300 hover:bg-purple-500/10 rounded transition-colors"
                            >
                              Post GL
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* 3-Way Match Studio Modal / Drawer */}
        {matchReport && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl">
              {/* Header */}
              <div className="p-6 border-b border-slate-800 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-xl font-bold text-white">3-Way Match Studio</h2>
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${
                        matchReport.matching_status === "MATCHED"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                          : "bg-rose-500/10 text-rose-400 border-rose-500/30"
                      }`}
                    >
                      {matchReport.matching_status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1 font-mono">
                    Invoice: <span className="text-white">{matchReport.invoice_number}</span> | PO:{" "}
                    <span className="text-blue-400">{matchReport.po_number || "None"}</span> | GRN:{" "}
                    <span className="text-emerald-400">{matchReport.grn_number || "None"}</span>
                  </p>
                </div>
                <button onClick={() => setMatchReport(null)} className="text-slate-400 hover:text-white">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Status Banner */}
              <div className="px-6 pt-4">
                <div
                  className={`p-4 rounded-lg border flex items-center gap-3 text-sm ${
                    matchReport.is_matched
                      ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-300"
                      : "bg-rose-500/10 border-rose-500/20 text-rose-300"
                  }`}
                >
                  <div className="text-2xl">{matchReport.is_matched ? "✓" : "⚠️"}</div>
                  <div>
                    <div className="font-semibold">
                      {matchReport.is_matched
                        ? "3-Way Reconciliation Perfect: Quantities and unit rates match contract parameters."
                        : "Variance Detected: Discrepancy between vendor invoice and warehouse receiving slips."}
                    </div>
                    <div className="text-xs opacity-90 mt-0.5">
                      Variance Amount: ${Number(matchReport.variance_amount).toFixed(2)} USD across line items.
                    </div>
                  </div>
                </div>
              </div>

              {/* Comparative Lines Table */}
              <div className="p-6 overflow-y-auto flex-1">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
                      <th className="py-2.5">Item Description</th>
                      <th className="py-2.5 text-right">Inv Qty</th>
                      <th className="py-2.5 text-right">GRN Accepted</th>
                      <th className="py-2.5 text-right">Inv Rate</th>
                      <th className="py-2.5 text-right">PO Rate</th>
                      <th className="py-2.5 text-right">Inv Total</th>
                      <th className="py-2.5 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/40">
                    {matchReport.lines.map((l) => (
                      <tr key={l.invoice_line_id} className="hover:bg-slate-800/20">
                        <td className="py-3 pr-2">
                          <div className="font-medium text-white">{l.description}</div>
                          {l.notes && <div className="text-[11px] text-slate-400 mt-0.5">{l.notes}</div>}
                        </td>
                        <td className="py-3 text-right font-mono text-slate-200">{Number(l.invoice_qty).toFixed(2)}</td>
                        <td className="py-3 text-right font-mono">
                          <span
                            className={
                              Number(l.qty_variance) !== 0 ? "text-rose-400 font-bold" : "text-emerald-400"
                            }
                          >
                            {l.grn_accepted_qty !== null ? Number(l.grn_accepted_qty).toFixed(2) : "—"}
                          </span>
                        </td>
                        <td className="py-3 text-right font-mono text-slate-200">${Number(l.invoice_unit_price).toFixed(2)}</td>
                        <td className="py-3 text-right font-mono">
                          <span
                            className={
                              Number(l.price_variance) !== 0 ? "text-rose-400 font-bold" : "text-emerald-400"
                            }
                          >
                            {l.po_unit_price !== null ? `$${Number(l.po_unit_price).toFixed(2)}` : "—"}
                          </span>
                        </td>
                        <td className="py-3 text-right font-mono font-semibold text-white">
                          ${Number(l.invoice_line_total).toFixed(2)}
                        </td>
                        <td className="py-3 text-center">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                              l.line_status === "MATCHED"
                                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                            }`}
                          >
                            {l.line_status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Modal Footer Actions */}
              <div className="p-6 border-t border-slate-800 flex items-center justify-between bg-slate-950/40">
                <button
                  type="button"
                  onClick={() => setMatchReport(null)}
                  className="px-4 py-2 text-sm text-slate-400 hover:text-white"
                >
                  Close Studio
                </button>
                <div className="flex gap-2">
                  {selectedInvoice && selectedInvoice.status === "DRAFT" && (
                    <button
                      onClick={() => handleApprove(selectedInvoice.id)}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                      {matchReport.is_matched ? "Approve Verified Invoice" : "Override Variance & Approve"}
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Register Vendor Invoice Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-2xl w-full max-h-[90vh] flex flex-col shadow-2xl">
              <div className="p-6 border-b border-slate-800 flex items-center justify-between">
                <h2 className="text-xl font-bold text-white">Register Vendor Invoice</h2>
                <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-white">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-4">
                {/* PO Fast Link */}
                <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg p-3">
                  <label className="block text-xs font-semibold text-blue-300 uppercase tracking-wider mb-1">
                    Link Approved Purchase Order (Auto-fills lines)
                  </label>
                  <select
                    value={form.purchase_order_id}
                    onChange={(e) => handlePoSelection(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="">-- Optional: Select Purchase Order --</option>
                    {purchaseOrders.map((po) => (
                      <option key={po.id} value={po.id}>
                        {po.po_number} — ${Number(po.total_amount).toLocaleString()} ({po.supplier_id})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">Invoice Number *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. INV-2026-009"
                      value={form.number}
                      onChange={(e) => setForm({ ...form, number: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">Supplier *</label>
                    <select
                      required
                      value={form.supplier_id}
                      onChange={(e) => setForm({ ...form, supplier_id: e.target.value })}
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
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">Invoice Date</label>
                    <input
                      type="date"
                      required
                      value={form.date}
                      onChange={(e) => setForm({ ...form, date: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">Payment Due Date</label>
                    <input
                      type="date"
                      required
                      value={form.due_date}
                      onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Description</label>
                  <input
                    type="text"
                    placeholder="e.g. Supply of reinforcement steel bars"
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>

                {/* Line Items Section */}
                <div className="space-y-2 pt-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Line Items</span>
                    <button
                      type="button"
                      onClick={handleAddLine}
                      className="text-xs text-blue-400 hover:text-blue-300 font-medium"
                    >
                      + Add Item Line
                    </button>
                  </div>

                  {form.lines.map((line, idx) => (
                    <div key={idx} className="bg-slate-950/60 p-3 rounded-lg border border-slate-800 flex gap-2 items-center">
                      <div className="flex-1">
                        <input
                          type="text"
                          required
                          placeholder="Item Description"
                          value={line.description}
                          onChange={(e) => handleLineChange(idx, "description", e.target.value)}
                          className="w-full px-2 py-1.5 bg-slate-900 border border-slate-800 rounded text-xs text-white"
                        />
                      </div>
                      <div className="w-20">
                        <input
                          type="number"
                          step="any"
                          required
                          placeholder="Qty"
                          value={line.quantity}
                          onChange={(e) => handleLineChange(idx, "quantity", e.target.value)}
                          className="w-full px-2 py-1.5 bg-slate-900 border border-slate-800 rounded text-xs text-white text-right"
                        />
                      </div>
                      <div className="w-24">
                        <input
                          type="number"
                          step="any"
                          required
                          placeholder="Unit Price"
                          value={line.unit_price}
                          onChange={(e) => handleLineChange(idx, "unit_price", e.target.value)}
                          className="w-full px-2 py-1.5 bg-slate-900 border border-slate-800 rounded text-xs text-white text-right"
                        />
                      </div>
                      <div className="w-24 text-right font-mono text-xs text-slate-300">
                        ${((Number(line.quantity) || 0) * (Number(line.unit_price) || 0)).toFixed(2)}
                      </div>
                      {form.lines.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveLine(idx)}
                          className="text-slate-500 hover:text-rose-400 p-1"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  ))}
                </div>

                {/* Totals Breakdown */}
                <div className="bg-slate-950/40 p-4 rounded-lg border border-slate-800/80 space-y-2 text-sm">
                  <div className="flex justify-between text-slate-400">
                    <span>Subtotal</span>
                    <span className="font-mono text-white">${calculateSubtotal().toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-400">
                    <span>Freight / Tax Adjustment</span>
                    <input
                      type="number"
                      step="any"
                      value={form.tax_amount}
                      onChange={(e) => setForm({ ...form, tax_amount: Number(e.target.value) })}
                      className="w-28 px-2 py-1 bg-slate-900 border border-slate-800 rounded text-xs text-white text-right font-mono"
                    />
                  </div>
                  <div className="flex justify-between text-base font-bold text-white border-t border-slate-800 pt-2">
                    <span>Total Invoiced</span>
                    <span className="font-mono text-blue-400">${calculateTotal().toFixed(2)}</span>
                  </div>
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
                    className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors"
                  >
                    {submitting ? "Saving & Matching..." : "Post Invoice"}
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
