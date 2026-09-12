"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import {
  getARInvoices,
  getARInvoice,
  createARInvoice,
  createARInvoiceFromPaymentApp,
  approveARInvoice,
  postARInvoice,
  getARSummary,
  getClients,
  getProjects,
  getClientPaymentApplications,
  ARInvoice,
  ARSummary,
  Client,
  Project,
  ClientPaymentApplication,
} from "@/lib/api";

export default function ARInvoicesPage({ params }: { params: { locale: string } }) {
  const [invoices, setInvoices] = useState<ARInvoice[]>([]);
  const [summary, setSummary] = useState<ARSummary | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [payApps, setPayApps] = useState<ClientPaymentApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  // Drawer / Selection State
  const [selectedInvoice, setSelectedInvoice] = useState<ARInvoice | null>(null);
  const [drawerLoading, setDrawerLoading] = useState(false);

  // Modals
  const [showManualModal, setShowManualModal] = useState(false);
  const [showIpcModal, setShowIpcModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  // Manual Form
  const [form, setForm] = useState({
    number: "",
    client_id: "",
    contract_id: "",
    date: new Date().toISOString().split("T")[0],
    due_date: new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0],
    description: "",
    retention_amount: 0,
    lines: [
      {
        project_id: "",
        cost_code_id: "",
        description: "",
        quantity: 1,
        unit_price: 0,
        tax_rate: 0,
      },
    ],
  });

  // Selected IPC for IPC Generation
  const [selectedPayAppId, setSelectedPayAppId] = useState("");

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [invData, sumData, clientData, projData, payAppData] = await Promise.all([
        getARInvoices(),
        getARSummary().catch(() => null),
        getClients().catch(() => []),
        getProjects().catch(() => []),
        getClientPaymentApplications().catch(() => []),
      ]);
      setInvoices(invData);
      setSummary(sumData);
      setClients(clientData);
      setProjects(projData);
      setPayApps(payAppData);
    } catch (err: any) {
      setError(err.message || "Failed to load accounts receivable data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleApprove = async (id: string) => {
    setActionLoadingId(id);
    try {
      await approveARInvoice(id);
      await fetchData();
      if (selectedInvoice && selectedInvoice.id === id) {
        const updated = await getARInvoice(id);
        setSelectedInvoice(updated);
      }
    } catch (err: any) {
      alert(err.message || "Failed to approve invoice");
    } finally {
      setActionLoadingId(null);
    }
  };

  const handlePost = async (id: string) => {
    setActionLoadingId(id);
    try {
      await postARInvoice(id);
      await fetchData();
      if (selectedInvoice && selectedInvoice.id === id) {
        const updated = await getARInvoice(id);
        setSelectedInvoice(updated);
      }
    } catch (err: any) {
      alert(err.message || "Failed to post invoice to General Ledger");
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleSelectInvoice = async (inv: ARInvoice) => {
    setSelectedInvoice(inv);
    setDrawerLoading(true);
    try {
      const detailed = await getARInvoice(inv.id);
      setSelectedInvoice(detailed);
    } catch (err) {
      // Keep basic invoice
    } finally {
      setDrawerLoading(false);
    }
  };

  const handleCreateFromIpc = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPayAppId) return;
    setSubmitting(true);
    try {
      await createARInvoiceFromPaymentApp(selectedPayAppId);
      setShowIpcModal(false);
      setSelectedPayAppId("");
      await fetchData();
    } catch (err: any) {
      alert(err.message || "Failed to generate invoice from Client Payment Application");
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddLine = () => {
    setForm({
      ...form,
      lines: [
        ...form.lines,
        {
          project_id: "",
          cost_code_id: "",
          description: "",
          quantity: 1,
          unit_price: 0,
          tax_rate: 0,
        },
      ],
    });
  };

  const handleRemoveLine = (index: number) => {
    if (form.lines.length <= 1) return;
    const nextLines = form.lines.filter((_, i) => i !== index);
    setForm({ ...form, lines: nextLines });
  };

  const handleLineChange = (index: number, field: string, value: any) => {
    const nextLines = [...form.lines];
    (nextLines[index] as any)[field] = value;
    setForm({ ...form, lines: nextLines });
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await createARInvoice({
        number: form.number,
        client_id: form.client_id,
        contract_id: form.contract_id || undefined,
        date: form.date,
        due_date: form.due_date,
        description: form.description || undefined,
        retention_amount: Number(form.retention_amount) || 0,
        lines: form.lines.map((l) => ({
          project_id: l.project_id || undefined,
          cost_code_id: l.cost_code_id || undefined,
          description: l.description,
          quantity: Number(l.quantity),
          unit_price: Number(l.unit_price),
          tax_rate: Number(l.tax_rate) || 0,
        })),
      });
      setShowManualModal(false);
      setForm({
        number: "",
        client_id: "",
        contract_id: "",
        date: new Date().toISOString().split("T")[0],
        due_date: new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0],
        description: "",
        retention_amount: 0,
        lines: [
          {
            project_id: "",
            cost_code_id: "",
            description: "",
            quantity: 1,
            unit_price: 0,
            tax_rate: 0,
          },
        ],
      });
      await fetchData();
    } catch (err: any) {
      alert(err.message || "Failed to create client invoice");
    } finally {
      setSubmitting(false);
    }
  };

  const filteredInvoices = invoices.filter((inv) => {
    const matchSearch =
      inv.number.toLowerCase().includes(search.toLowerCase()) ||
      (inv.client_name && inv.client_name.toLowerCase().includes(search.toLowerCase())) ||
      (inv.contract_number && inv.contract_number.toLowerCase().includes(search.toLowerCase())) ||
      (inv.payment_application_number &&
        inv.payment_application_number.toLowerCase().includes(search.toLowerCase()));

    const matchStatus = statusFilter === "ALL" || inv.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "DRAFT":
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-700 border border-gray-300">Draft</span>;
      case "APPROVED":
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 border border-blue-200">Approved</span>;
      case "POSTED":
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800 border border-purple-200">GL Posted</span>;
      case "PARTIAL":
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-100 text-amber-800 border border-amber-200">Partially Paid</span>;
      case "PAID":
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">Paid in Full</span>;
      case "CANCELLED":
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-rose-100 text-rose-800 border border-rose-200">Cancelled</span>;
      default:
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">{status}</span>;
    }
  };

  const manualSubtotal = form.lines.reduce((acc, l) => acc + (Number(l.quantity) * Number(l.unit_price)), 0);
  const manualTax = form.lines.reduce((acc, l) => acc + (Number(l.quantity) * Number(l.unit_price) * (Number(l.tax_rate) / 100)), 0);
  const manualNet = manualSubtotal + manualTax - Number(form.retention_amount || 0);

  return (
    <AppLayout locale={params.locale}>
      <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-white p-6 rounded-2xl border border-gray-200 shadow-sm">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Client Invoices & Progress Billing</h1>
              <span className="bg-blue-50 text-blue-700 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-blue-200">
                AIA G702/G703 Studio
              </span>
            </div>
            <p className="text-sm text-gray-500 mt-1">
              Issue progress billing applications, retainage withholding, customer claims, and double-entry GL postings.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowIpcModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-xl shadow-sm transition-all"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              Generate from IPC
            </button>
            <button
              onClick={() => setShowManualModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl shadow-sm transition-all"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New Client Invoice
            </button>
          </div>
        </div>

        {/* Live Executive Summary KPI Cards */}
        {summary && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
              <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Total Invoiced</span>
              <div className="text-2xl font-bold text-gray-900 mt-1">
                ${Number(summary.total_invoiced || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <span className="text-xs text-blue-600 font-medium mt-1 inline-block">Gross progress billings</span>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
              <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Total Receivables</span>
              <div className="text-2xl font-bold text-rose-600 mt-1">
                ${Number(summary.total_receivables || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <span className="text-xs text-rose-500 font-medium mt-1 inline-block">Uncollected customer balance</span>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
              <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Retainage Withheld</span>
              <div className="text-2xl font-bold text-amber-600 mt-1">
                ${Number(summary.total_retention_held || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <span className="text-xs text-amber-600 font-medium mt-1 inline-block">Contract retainage asset (GL 1210)</span>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
              <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Total Collections</span>
              <div className="text-2xl font-bold text-emerald-600 mt-1">
                ${Number(summary.total_received || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <span className="text-xs text-emerald-600 font-medium mt-1 inline-block">Settled into Treasury accounts</span>
            </div>
          </div>
        )}

        {/* Filters & Search */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
          <div className="relative w-full md:w-96">
            <input
              type="text"
              placeholder="Search invoice #, client, contract, IPC..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
            />
            <svg className="w-4 h-4 text-gray-400 absolute left-3.5 top-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>

          <div className="flex flex-wrap items-center gap-1.5 w-full md:w-auto">
            {["ALL", "DRAFT", "APPROVED", "POSTED", "PARTIAL", "PAID"].map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  statusFilter === status
                    ? "bg-blue-600 text-white shadow-sm"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {status}
              </button>
            ))}
          </div>
        </div>

        {/* Invoices Table & Detail Drawer */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className={`bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden ${selectedInvoice ? "lg:col-span-2" : "lg:col-span-3"}`}>
            {loading ? (
              <div className="p-12 text-center text-gray-500">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
                Loading client invoices...
              </div>
            ) : error ? (
              <div className="p-8 text-center text-rose-600 bg-rose-50 rounded-xl m-4 border border-rose-200">
                <p className="font-semibold">{error}</p>
                <button onClick={fetchData} className="mt-2 text-xs text-rose-700 underline">Try again</button>
              </div>
            ) : filteredInvoices.length === 0 ? (
              <div className="p-12 text-center text-gray-500">
                <svg className="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="font-medium text-gray-700">No client invoices found</p>
                <p className="text-xs text-gray-400 mt-1">Generate an invoice from an approved IPC or create a new invoice manually.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 bg-gray-50/75 text-gray-600 font-semibold text-xs uppercase tracking-wider">
                      <th className="p-3.5">Invoice #</th>
                      <th className="p-3.5">Client & Contract</th>
                      <th className="p-3.5">Date / Due</th>
                      <th className="p-3.5 text-right">Subtotal</th>
                      <th className="p-3.5 text-right">Retainage</th>
                      <th className="p-3.5 text-right">Net Due</th>
                      <th className="p-3.5 text-right">Balance</th>
                      <th className="p-3.5 text-center">Status</th>
                      <th className="p-3.5 text-center">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {filteredInvoices.map((inv) => (
                      <tr
                        key={inv.id}
                        className={`hover:bg-blue-50/40 transition-colors cursor-pointer ${selectedInvoice?.id === inv.id ? "bg-blue-50/70" : ""}`}
                        onClick={() => handleSelectInvoice(inv)}
                      >
                        <td className="p-3.5 font-semibold text-blue-600">
                          {inv.number}
                          {inv.payment_application_number && (
                            <span className="block text-[11px] font-normal text-gray-400">
                              IPC: {inv.payment_application_number}
                            </span>
                          )}
                        </td>
                        <td className="p-3.5">
                          <span className="font-medium text-gray-900 block">{inv.client_name || "Unknown Client"}</span>
                          <span className="text-xs text-gray-400">{inv.contract_number || "No Contract Linked"}</span>
                        </td>
                        <td className="p-3.5 text-xs text-gray-600">
                          <div>{inv.date}</div>
                          <div className="text-gray-400">Due: {inv.due_date}</div>
                        </td>
                        <td className="p-3.5 text-right font-medium text-gray-900">
                          ${Number(inv.subtotal || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="p-3.5 text-right font-medium text-amber-600">
                          ${Number(inv.retention_amount || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="p-3.5 text-right font-bold text-gray-900">
                          ${Number(inv.total_amount || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="p-3.5 text-right font-bold text-rose-600">
                          ${Number(inv.outstanding_amount ?? inv.total_amount).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="p-3.5 text-center">{getStatusBadge(inv.status)}</td>
                        <td className="p-3.5 text-center" onClick={(e) => e.stopPropagation()}>
                          <div className="flex items-center justify-center gap-1.5">
                            {inv.status === "DRAFT" && (
                              <button
                                onClick={() => handleApprove(inv.id)}
                                disabled={actionLoadingId === inv.id}
                                className="px-2.5 py-1 text-xs font-semibold bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg transition-all border border-blue-200"
                              >
                                Approve
                              </button>
                            )}
                            {(inv.status === "DRAFT" || inv.status === "APPROVED") && (
                              <button
                                onClick={() => handlePost(inv.id)}
                                disabled={actionLoadingId === inv.id}
                                className="px-2.5 py-1 text-xs font-semibold bg-purple-50 text-purple-700 hover:bg-purple-100 rounded-lg transition-all border border-purple-200"
                              >
                                Post GL
                              </button>
                            )}
                            <button
                              onClick={() => handleSelectInvoice(inv)}
                              className="px-2 py-1 text-xs text-gray-500 hover:text-gray-900"
                            >
                              Details
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Details Drawer */}
          {selectedInvoice && (
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 space-y-4">
              <div className="flex items-center justify-between border-b pb-3">
                <div>
                  <h3 className="text-lg font-bold text-gray-900">{selectedInvoice.number}</h3>
                  <span className="text-xs text-gray-500">Progress Billing Details</span>
                </div>
                <button
                  onClick={() => setSelectedInvoice(null)}
                  className="text-gray-400 hover:text-gray-600 p-1"
                >
                  ✕
                </button>
              </div>

              {drawerLoading ? (
                <div className="p-6 text-center text-gray-400 text-sm">Loading line details...</div>
              ) : (
                <div className="space-y-4 text-xs">
                  <div className="bg-gray-50 p-3.5 rounded-xl space-y-2 border border-gray-200">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Client:</span>
                      <span className="font-semibold text-gray-900">{selectedInvoice.client_name || "N/A"}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Contract:</span>
                      <span className="font-semibold text-gray-900">{selectedInvoice.contract_number || "N/A"}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Status:</span>
                      <span>{getStatusBadge(selectedInvoice.status)}</span>
                    </div>
                    {selectedInvoice.journal_id && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">GL Journal Ref:</span>
                        <span className="font-mono text-purple-700 font-semibold">{selectedInvoice.journal_id.slice(0, 8)}...</span>
                      </div>
                    )}
                  </div>

                  {/* Financial Breakdown */}
                  <div className="bg-blue-50/50 p-3.5 rounded-xl space-y-2 border border-blue-100">
                    <div className="flex justify-between text-gray-600">
                      <span>Work Certified (Subtotal):</span>
                      <span className="font-semibold text-gray-900">${Number(selectedInvoice.subtotal || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}</span>
                    </div>
                    <div className="flex justify-between text-amber-700">
                      <span>Retainage Withheld (-):</span>
                      <span className="font-semibold">-${Number(selectedInvoice.retention_amount || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}</span>
                    </div>
                    <div className="flex justify-between text-gray-600">
                      <span>Taxes (+):</span>
                      <span className="font-semibold">${Number(selectedInvoice.tax_amount || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}</span>
                    </div>
                    <div className="border-t border-blue-200 pt-1.5 flex justify-between text-sm font-bold text-gray-900">
                      <span>Net Invoiced:</span>
                      <span>${Number(selectedInvoice.total_amount || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}</span>
                    </div>
                    <div className="flex justify-between text-emerald-700 font-semibold">
                      <span>Collections Received:</span>
                      <span>${Number(selectedInvoice.paid_amount || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}</span>
                    </div>
                    <div className="flex justify-between text-rose-700 font-bold">
                      <span>Outstanding Balance:</span>
                      <span>${Number(selectedInvoice.outstanding_amount ?? selectedInvoice.total_amount).toLocaleString("en-US", { minimumFractionDigits: 2 })}</span>
                    </div>
                  </div>

                  {/* Line Items */}
                  <div>
                    <h4 className="font-semibold text-gray-800 uppercase tracking-wider text-[11px] mb-2">Schedule of Values / Lines</h4>
                    <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                      {selectedInvoice.lines && selectedInvoice.lines.length > 0 ? (
                        selectedInvoice.lines.map((l, i) => (
                          <div key={l.id || i} className="p-2.5 bg-gray-50 rounded-lg border border-gray-200 text-[11px] space-y-1">
                            <div className="font-semibold text-gray-900">{l.description}</div>
                            <div className="flex justify-between text-gray-500">
                              <span>Qty: {l.quantity} × ${Number(l.unit_price).toLocaleString()}</span>
                              <span className="font-bold text-gray-900">${Number(l.line_total).toLocaleString()}</span>
                            </div>
                            {l.project_name && (
                              <div className="text-gray-400">Project: {l.project_name}</div>
                            )}
                          </div>
                        ))
                      ) : (
                        <p className="text-gray-400 italic">No line items breakdown available.</p>
                      )}
                    </div>
                  </div>

                  {/* Action Bar */}
                  <div className="pt-2 flex gap-2">
                    {selectedInvoice.status === "DRAFT" && (
                      <button
                        onClick={() => handleApprove(selectedInvoice.id)}
                        disabled={actionLoadingId === selectedInvoice.id}
                        className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-xs transition-all shadow-sm"
                      >
                        Approve Invoice
                      </button>
                    )}
                    {(selectedInvoice.status === "DRAFT" || selectedInvoice.status === "APPROVED") && (
                      <button
                        onClick={() => handlePost(selectedInvoice.id)}
                        disabled={actionLoadingId === selectedInvoice.id}
                        className="w-full py-2 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-xl text-xs transition-all shadow-sm"
                      >
                        Post to GL
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal: Generate from IPC */}
        {showIpcModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl border border-gray-200">
              <div className="flex items-center justify-between border-b pb-3">
                <h3 className="text-lg font-bold text-gray-900">Generate Client Invoice from IPC</h3>
                <button onClick={() => setShowIpcModal(false)} className="text-gray-400 hover:text-gray-600">✕</button>
              </div>

              <form onSubmit={handleCreateFromIpc} className="space-y-4 text-sm">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Select Approved Client Payment Application (IPC)</label>
                  <select
                    value={selectedPayAppId}
                    onChange={(e) => setSelectedPayAppId(e.target.value)}
                    required
                    className="w-full p-2.5 bg-gray-50 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">-- Choose Payment Application --</option>
                    {payApps.map((pa) => (
                      <option key={pa.id} value={pa.id}>
                        {pa.number} - {pa.period_name || pa.date} (${Number(pa.net_amount_due).toLocaleString()})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="bg-emerald-50 p-4 rounded-xl border border-emerald-200 text-xs text-emerald-800 space-y-1">
                  <p className="font-semibold">Automated Progress Billing Rules:</p>
                  <p>• Certified gross work will be recognized as progress revenue (Account 4010).</p>
                  <p>• Retainage (usually 5-10%) will be withheld into Retainage Receivable (Account 1210).</p>
                  <p>• Net amount due will populate Accounts Receivable (Account 1200).</p>
                </div>

                <div className="flex justify-end gap-3 pt-3 border-t">
                  <button
                    type="button"
                    onClick={() => setShowIpcModal(false)}
                    className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-medium text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting || !selectedPayAppId}
                    className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-semibold text-xs transition-all disabled:opacity-50"
                  >
                    {submitting ? "Generating..." : "Generate Invoice"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: New Client Invoice Manual */}
        {showManualModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-2xl w-full p-6 space-y-5 shadow-2xl border border-gray-200 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between border-b pb-3">
                <h3 className="text-lg font-bold text-gray-900">Create Client Invoice</h3>
                <button onClick={() => setShowManualModal(false)} className="text-gray-400 hover:text-gray-600">✕</button>
              </div>

              <form onSubmit={handleManualSubmit} className="space-y-4 text-xs">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block font-semibold text-gray-700 mb-1">Invoice Number</label>
                    <input
                      type="text"
                      placeholder="e.g. INV-METRO-005"
                      value={form.number}
                      onChange={(e) => setForm({ ...form, number: e.target.value })}
                      required
                      className="w-full p-2.5 bg-gray-50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-gray-700 mb-1">Client</label>
                    <select
                      value={form.client_id}
                      onChange={(e) => setForm({ ...form, client_id: e.target.value })}
                      required
                      className="w-full p-2.5 bg-gray-50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">-- Select Client --</option>
                      {clients.map((c) => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block font-semibold text-gray-700 mb-1">Invoice Date</label>
                    <input
                      type="date"
                      value={form.date}
                      onChange={(e) => setForm({ ...form, date: e.target.value })}
                      required
                      className="w-full p-2.5 bg-gray-50 border border-gray-300 rounded-xl"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-gray-700 mb-1">Due Date</label>
                    <input
                      type="date"
                      value={form.due_date}
                      onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                      required
                      className="w-full p-2.5 bg-gray-50 border border-gray-300 rounded-xl"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-gray-700 mb-1">Retainage Withheld ($)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={form.retention_amount}
                      onChange={(e) => setForm({ ...form, retention_amount: parseFloat(e.target.value) || 0 })}
                      className="w-full p-2.5 bg-gray-50 border border-gray-300 rounded-xl font-medium text-amber-700"
                    />
                  </div>
                </div>

                <div>
                  <label className="block font-semibold text-gray-700 mb-1">Description / Memo</label>
                  <input
                    type="text"
                    placeholder="e.g. Monthly progress billing for structural milestones"
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    className="w-full p-2.5 bg-gray-50 border border-gray-300 rounded-xl"
                  />
                </div>

                {/* Line Items */}
                <div className="border-t pt-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-gray-800 uppercase tracking-wider text-[11px]">Invoice Items</span>
                    <button
                      type="button"
                      onClick={handleAddLine}
                      className="text-xs text-blue-600 font-semibold hover:text-blue-800"
                    >
                      + Add Item
                    </button>
                  </div>

                  {form.lines.map((line, idx) => (
                    <div key={idx} className="p-3 bg-gray-50 rounded-xl border border-gray-200 space-y-2">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        <div>
                          <label className="block text-[10px] text-gray-500">Project</label>
                          <select
                            value={line.project_id}
                            onChange={(e) => handleLineChange(idx, "project_id", e.target.value)}
                            className="w-full p-1.5 bg-white border border-gray-300 rounded-lg text-xs"
                          >
                            <option value="">-- None / General --</option>
                            {projects.map((p) => (
                              <option key={p.id} value={p.id}>{p.name}</option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <label className="block text-[10px] text-gray-500">Description</label>
                          <input
                            type="text"
                            placeholder="e.g. Milestone 3 Concrete Pouring"
                            value={line.description}
                            onChange={(e) => handleLineChange(idx, "description", e.target.value)}
                            required
                            className="w-full p-1.5 bg-white border border-gray-300 rounded-lg text-xs"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-3 sm:grid-cols-4 gap-2 items-center">
                        <div>
                          <label className="block text-[10px] text-gray-500">Quantity</label>
                          <input
                            type="number"
                            min="0.01"
                            step="0.01"
                            value={line.quantity}
                            onChange={(e) => handleLineChange(idx, "quantity", parseFloat(e.target.value) || 0)}
                            required
                            className="w-full p-1.5 bg-white border border-gray-300 rounded-lg text-xs"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-gray-500">Unit Price ($)</label>
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            value={line.unit_price}
                            onChange={(e) => handleLineChange(idx, "unit_price", parseFloat(e.target.value) || 0)}
                            required
                            className="w-full p-1.5 bg-white border border-gray-300 rounded-lg text-xs"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-gray-500">Tax Rate (%)</label>
                          <input
                            type="number"
                            min="0"
                            step="0.1"
                            value={line.tax_rate}
                            onChange={(e) => handleLineChange(idx, "tax_rate", parseFloat(e.target.value) || 0)}
                            className="w-full p-1.5 bg-white border border-gray-300 rounded-lg text-xs"
                          />
                        </div>
                        <div className="flex items-center justify-between sm:justify-end gap-2 pt-3">
                          <span className="font-bold text-gray-900 text-xs">
                            ${(Number(line.quantity) * Number(line.unit_price)).toLocaleString()}
                          </span>
                          {form.lines.length > 1 && (
                            <button
                              type="button"
                              onClick={() => handleRemoveLine(idx)}
                              className="text-rose-500 hover:text-rose-700 text-xs font-bold"
                            >
                              ✕
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Calculation Summary */}
                <div className="bg-blue-50/70 p-3.5 rounded-xl border border-blue-100 space-y-1.5 text-right">
                  <div className="flex justify-between text-gray-600">
                    <span>Subtotal:</span>
                    <span className="font-semibold text-gray-900">${manualSubtotal.toLocaleString("en-US", { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between text-gray-600">
                    <span>Estimated Taxes:</span>
                    <span className="font-semibold text-gray-900">${manualTax.toLocaleString("en-US", { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between text-amber-700">
                    <span>Retainage Withheld (-):</span>
                    <span className="font-semibold">-${Number(form.retention_amount || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="border-t border-blue-200 pt-1 flex justify-between text-sm font-bold text-gray-900">
                    <span>Total Net Invoice Due:</span>
                    <span>${manualNet.toLocaleString("en-US", { minimumFractionDigits: 2 })}</span>
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-3 border-t">
                  <button
                    type="button"
                    onClick={() => setShowManualModal(false)}
                    className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-medium text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold text-xs transition-all disabled:opacity-50"
                  >
                    {submitting ? "Saving..." : "Create Client Invoice"}
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
