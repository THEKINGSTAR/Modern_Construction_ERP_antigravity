"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import {
  getProjects,
  getPortfolioCostSummary,
  getProjectCostKPIs,
  getProjectCostSummary,
  getProjectCostTransactions,
  createProjectForecast,
  Project,
  PortfolioCostSummary,
  ProjectCostKPISummary,
  CostCodeSummary,
  CostTransaction,
} from "@/lib/api";

export default function CostControlPage({ params }: { params: { locale: string } }) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("88888888-8888-4888-8888-888888888888");
  const [portfolioSummary, setPortfolioSummary] = useState<PortfolioCostSummary | null>(null);
  const [projectKPI, setProjectKPI] = useState<ProjectCostKPISummary | null>(null);
  const [costSummaries, setCostSummaries] = useState<CostCodeSummary[]>([]);
  const [transactions, setTransactions] = useState<CostTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");

  // Modals & Drawers
  const [showForecastModal, setShowForecastModal] = useState(false);
  const [showTxnModal, setShowTxnModal] = useState(false);
  const [selectedTxnSource, setSelectedTxnSource] = useState("ALL");
  const [txnSearch, setTxnSearch] = useState("");
  const [submittingForecast, setSubmittingForecast] = useState(false);

  // Forecast form state
  const [forecastForm, setForecastForm] = useState<{
    forecastNumber: string;
    date: string;
    notes: string;
    lines: { [costCodeId: string]: string };
  }>({
    forecastNumber: `FC-${new Date().toISOString().slice(0, 10).replace(/-/g, "")}-01`,
    date: new Date().toISOString().slice(0, 10),
    notes: "Executive Cost Review & ETC Adjustment",
    lines: {},
  });

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Load projects
      const projs = await getProjects();
      setProjects(projs);

      let targetId = selectedProjectId;
      if (selectedProjectId !== "PORTFOLIO") {
        const found = projs.find((p) => p.id === selectedProjectId);
        if (!found && projs.length > 0) {
          targetId = projs[0].id;
          setSelectedProjectId(targetId);
        }
      }

      // 2. Load portfolio summary
      const portSummary = await getPortfolioCostSummary();
      setPortfolioSummary(portSummary);

      // 3. Load project-specific data if not PORTFOLIO
      if (targetId && targetId !== "PORTFOLIO") {
        const [kpi, summaries, txns] = await Promise.all([
          getProjectCostKPIs(targetId),
          getProjectCostSummary(targetId),
          getProjectCostTransactions(targetId),
        ]);
        setProjectKPI(kpi);
        setCostSummaries(summaries);
        setTransactions(txns);

        // Pre-fill forecast lines
        const initialLines: { [id: string]: string } = {};
        summaries.forEach((s) => {
          initialLines[s.cost_code_id] = String(s.estimate_to_complete || "0.00");
        });
        setForecastForm((prev) => ({ ...prev, lines: initialLines }));
      }
    } catch (err: any) {
      console.error("Failed to load cost control data:", err);
      setError(err.message || "Failed to load cost control data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedProjectId]);

  const handleOpenForecastModal = (specificCostCodeId?: string) => {
    const initialLines: { [id: string]: string } = {};
    costSummaries.forEach((s) => {
      initialLines[s.cost_code_id] = String(s.estimate_to_complete || "0.00");
    });
    setForecastForm({
      forecastNumber: `FC-${new Date().toISOString().slice(0, 10).replace(/-/g, "")}-${Math.floor(100 + Math.random() * 900)}`,
      date: new Date().toISOString().slice(0, 10),
      notes: "Updated Cost to Complete (ETC) baseline",
      lines: initialLines,
    });
    setShowForecastModal(true);
  };

  const handleForecastSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProjectId || selectedProjectId === "PORTFOLIO") return;

    setSubmittingForecast(true);
    try {
      const payload = {
        forecast_number: forecastForm.forecastNumber,
        date: forecastForm.date,
        notes: forecastForm.notes,
        lines: costSummaries.map((s) => ({
          cost_code_id: s.cost_code_id,
          etc_amount: Number(forecastForm.lines[s.cost_code_id] || 0),
          notes: `ETC update for ${s.cost_code_code || ""}`,
        })),
      };
      await createProjectForecast(selectedProjectId, payload);
      setShowForecastModal(false);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to submit project forecast");
    } finally {
      setSubmittingForecast(false);
    }
  };

  const formatCurrency = (val: number | string | undefined | null) => {
    const num = Number(val || 0);
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(num);
  };

  const formatCompactCurrency = (val: number | string | undefined | null) => {
    const num = Number(val || 0);
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      notation: "compact",
      maximumFractionDigits: 1,
    }).format(num);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "UNDER_BUDGET":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            Under Budget
          </span>
        );
      case "ON_TRACK":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 border border-blue-200">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
            On Track
          </span>
        );
      case "AT_RISK":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-100 text-amber-800 border border-amber-200">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
            At Risk
          </span>
        );
      case "OVER_BUDGET":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-full bg-rose-100 text-rose-800 border border-rose-200">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
            Over Budget
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800 border border-gray-200">
            {status}
          </span>
        );
    }
  };

  const getCategoryBadge = (category: string | undefined) => {
    const cat = (category || "GENERAL").toUpperCase();
    switch (cat) {
      case "MATERIAL":
        return <span className="px-2 py-0.5 text-xs font-medium rounded-md bg-cyan-100 text-cyan-800 border border-cyan-200">Material</span>;
      case "SUBCONTRACT":
        return <span className="px-2 py-0.5 text-xs font-medium rounded-md bg-purple-100 text-purple-800 border border-purple-200">Subcontract</span>;
      case "EQUIPMENT":
        return <span className="px-2 py-0.5 text-xs font-medium rounded-md bg-amber-100 text-amber-800 border border-amber-200">Equipment</span>;
      case "LABOR":
        return <span className="px-2 py-0.5 text-xs font-medium rounded-md bg-blue-100 text-blue-800 border border-blue-200">Labor</span>;
      case "OVERHEAD":
        return <span className="px-2 py-0.5 text-xs font-medium rounded-md bg-slate-100 text-slate-800 border border-slate-200">Overhead</span>;
      default:
        return <span className="px-2 py-0.5 text-xs font-medium rounded-md bg-gray-100 text-gray-700">{cat}</span>;
    }
  };

  const getCPIBadge = (cpi: number | string | undefined) => {
    const val = Number(cpi || 1.0);
    if (val >= 1.0) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-bold rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200">
          <svg className="w-3.5 h-3.5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 10l7-7m0 0l7 7m-7-7v18" />
          </svg>
          CPI {val.toFixed(2)} (Favorable)
        </span>
      );
    } else if (val >= 0.9) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-bold rounded-md bg-amber-50 text-amber-700 border border-amber-200">
          <svg className="w-3.5 h-3.5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          CPI {val.toFixed(2)} (Caution)
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-bold rounded-md bg-rose-50 text-rose-700 border border-rose-200">
          <svg className="w-3.5 h-3.5 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
          CPI {val.toFixed(2)} (Overrun)
        </span>
      );
    }
  };

  // Filtered summaries
  const filteredSummaries = costSummaries.filter((s) => {
    const matchSearch =
      (s.cost_code_code && s.cost_code_code.toLowerCase().includes(search.toLowerCase())) ||
      (s.cost_code_name && s.cost_code_name.toLowerCase().includes(search.toLowerCase()));
    const matchCat = categoryFilter === "ALL" || (s.cost_category && s.cost_category.toUpperCase() === categoryFilter);
    const matchStatus = statusFilter === "ALL" || s.status === statusFilter;
    return matchSearch && matchCat && matchStatus;
  });

  // Filtered transactions
  const filteredTransactions = transactions.filter((t) => {
    const matchSource = selectedTxnSource === "ALL" || t.source_type === selectedTxnSource;
    const matchSearch =
      !txnSearch ||
      (t.cost_code_code && t.cost_code_code.toLowerCase().includes(txnSearch.toLowerCase())) ||
      (t.cost_code_name && t.cost_code_name.toLowerCase().includes(txnSearch.toLowerCase())) ||
      (t.source_reference && t.source_reference.toLowerCase().includes(txnSearch.toLowerCase())) ||
      t.source_type.toLowerCase().includes(txnSearch.toLowerCase());
    return matchSource && matchSearch;
  });

  // Calculate totals
  const totalBudget = filteredSummaries.reduce((a, b) => a + Number(b.current_budget || 0), 0);
  const totalCommitted = filteredSummaries.reduce((a, b) => a + Number(b.committed_cost || 0), 0);
  const totalActual = filteredSummaries.reduce((a, b) => a + Number(b.actual_cost || 0), 0);
  const totalETC = filteredSummaries.reduce((a, b) => a + Number(b.estimate_to_complete || 0), 0);
  const totalEAC = filteredSummaries.reduce((a, b) => a + Number(b.estimate_at_completion || 0), 0);
  const totalVariance = filteredSummaries.reduce((a, b) => a + Number(b.variance || 0), 0);

  const activeProject = projects.find((p) => p.id === selectedProjectId);

  return (
    <AppLayout locale={params.locale}>
      <div className="p-6 space-y-6 max-w-[1700px] mx-auto">
        {/* Header & Controls */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 bg-white p-6 rounded-2xl border border-gray-200 shadow-sm">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Project Cost Control & EVM</h1>
              <span className="bg-indigo-50 text-indigo-700 text-xs font-semibold px-3 py-1 rounded-full border border-indigo-200">
                Earned Value & Budget Variance
              </span>
              {projectKPI && getCPIBadge(projectKPI.cost_performance_index)}
            </div>
            <p className="text-sm text-gray-500 mt-1">
              Real-time synchronization of budgets, committed subcontracts/POs, actual incurred costs (WAC material issues, AP invoices, timesheets), and Estimate-to-Complete (ETC).
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Project Switcher */}
            <div className="flex items-center gap-2">
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Project:</label>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="px-3.5 py-2 text-sm font-medium bg-gray-50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all min-w-[240px]"
              >
                <option value="PORTFOLIO">🌐 Portfolio Overview (All Projects)</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.project_number})
                  </option>
                ))}
              </select>
            </div>

            {selectedProjectId !== "PORTFOLIO" && (
              <button
                onClick={() => handleOpenForecastModal()}
                className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-xl shadow-sm transition-all"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Update ETC Forecast
              </button>
            )}

            {selectedProjectId !== "PORTFOLIO" && (
              <button
                onClick={() => setShowTxnModal(true)}
                className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white text-sm font-semibold rounded-xl shadow-sm transition-all"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                </svg>
                Audit Transactions ({transactions.length})
              </button>
            )}

            <button
              onClick={loadData}
              className="p-2 text-gray-500 hover:text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl transition-all"
              title="Refresh Data"
            >
              <svg className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-xl text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{error}</span>
            </div>
            <button onClick={loadData} className="text-xs underline font-semibold">Retry</button>
          </div>
        )}

        {/* Live KPI Metric Cards */}
        {selectedProjectId !== "PORTFOLIO" && projectKPI ? (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
              <div className="flex items-center justify-between text-xs font-semibold text-gray-500 uppercase tracking-wider">
                <span>Current Budget</span>
                <span className="p-1 rounded-lg bg-blue-50 text-blue-600">🏛️</span>
              </div>
              <div className="text-xl font-bold text-gray-900 mt-2">
                {formatCurrency(projectKPI.total_current_budget)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Orig: {formatCompactCurrency(projectKPI.total_original_budget)} | Chg: {formatCompactCurrency(projectKPI.total_approved_changes)}
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
              <div className="flex items-center justify-between text-xs font-semibold text-gray-500 uppercase tracking-wider">
                <span>Committed Cost</span>
                <span className="p-1 rounded-lg bg-purple-50 text-purple-600">📑</span>
              </div>
              <div className="text-xl font-bold text-purple-900 mt-2">
                {formatCurrency(projectKPI.total_committed)}
              </div>
              <div className="text-xs text-purple-600 mt-1 font-medium">
                POs & Trade Subcontracts
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
              <div className="flex items-center justify-between text-xs font-semibold text-gray-500 uppercase tracking-wider">
                <span>Actual Incurred</span>
                <span className="p-1 rounded-lg bg-amber-50 text-amber-600">💳</span>
              </div>
              <div className="text-xl font-bold text-amber-900 mt-2">
                {formatCurrency(projectKPI.total_actual)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Material, AP, Timesheets, Eq
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
              <div className="flex items-center justify-between text-xs font-semibold text-gray-500 uppercase tracking-wider">
                <span>Estimate To Complete</span>
                <span className="p-1 rounded-lg bg-indigo-50 text-indigo-600">🎯</span>
              </div>
              <div className="text-xl font-bold text-indigo-900 mt-2">
                {formatCurrency(projectKPI.total_estimate_to_complete)}
              </div>
              <div className="text-xs text-indigo-600 mt-1 font-medium">
                Active Approved Forecast (ETC)
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
              <div className="flex items-center justify-between text-xs font-semibold text-gray-500 uppercase tracking-wider">
                <span>Estimate at Completion</span>
                <span className="p-1 rounded-lg bg-slate-50 text-slate-600">📊</span>
              </div>
              <div className="text-xl font-bold text-slate-900 mt-2">
                {formatCurrency(projectKPI.total_estimate_at_completion)}
              </div>
              <div className="text-xs text-gray-500 mt-1 font-medium">
                EAC = Actual + ETC
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
              <div className="flex items-center justify-between text-xs font-semibold text-gray-500 uppercase tracking-wider">
                <span>Variance (VAC)</span>
                <span className="p-1 rounded-lg bg-emerald-50 text-emerald-600">⚖️</span>
              </div>
              <div className={`text-xl font-bold mt-2 ${Number(projectKPI.total_variance) >= 0 ? "text-emerald-700" : "text-rose-700"}`}>
                {formatCurrency(projectKPI.total_variance)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Budget − EAC
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
              <div className="flex items-center justify-between text-xs font-semibold text-gray-500 uppercase tracking-wider">
                <span>Performance & Status</span>
                <span className="p-1 rounded-lg bg-teal-50 text-teal-600">⚡</span>
              </div>
              <div className="mt-2">
                {getStatusBadge(projectKPI.status)}
              </div>
              <div className="text-xs text-gray-500 mt-1 font-semibold">
                CPI: {Number(projectKPI.cost_performance_index).toFixed(2)}
              </div>
            </div>
          </div>
        ) : portfolioSummary ? (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Total Projects</div>
              <div className="text-2xl font-bold text-gray-900 mt-2">{portfolioSummary.total_projects}</div>
              <div className="text-xs text-gray-500 mt-1">Active Portfolio</div>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Portfolio Budget</div>
              <div className="text-2xl font-bold text-blue-900 mt-2">{formatCompactCurrency(portfolioSummary.total_budget)}</div>
              <div className="text-xs text-gray-500 mt-1">{formatCurrency(portfolioSummary.total_budget)}</div>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Committed Total</div>
              <div className="text-2xl font-bold text-purple-900 mt-2">{formatCompactCurrency(portfolioSummary.total_committed)}</div>
              <div className="text-xs text-purple-600 mt-1 font-medium">All Open Commitments</div>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Incurred Actuals</div>
              <div className="text-2xl font-bold text-amber-900 mt-2">{formatCompactCurrency(portfolioSummary.total_actual)}</div>
              <div className="text-xs text-gray-500 mt-1">{formatCurrency(portfolioSummary.total_actual)}</div>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Estimate at Compl.</div>
              <div className="text-2xl font-bold text-slate-900 mt-2">{formatCompactCurrency(portfolioSummary.total_eac)}</div>
              <div className="text-xs text-gray-500 mt-1">AC + ETC Rollup</div>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Portfolio Variance</div>
              <div className={`text-2xl font-bold mt-2 ${Number(portfolioSummary.total_variance) >= 0 ? "text-emerald-700" : "text-rose-700"}`}>
                {formatCompactCurrency(portfolioSummary.total_variance)}
              </div>
              <div className="text-xs text-gray-500 mt-1">{formatCurrency(portfolioSummary.total_variance)}</div>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Overall CPI</div>
              <div className="mt-2">{getCPIBadge(portfolioSummary.overall_cpi)}</div>
              <div className="text-xs text-gray-500 mt-1">Portfolio Weighted</div>
            </div>
          </div>
        ) : null}

        {/* View Mode: Portfolio Multi-Project Comparison Matrix */}
        {selectedProjectId === "PORTFOLIO" && portfolioSummary && (
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="p-5 border-b border-gray-200 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-gray-900">Portfolio Projects Cost Matrix</h2>
                <p className="text-xs text-gray-500 mt-0.5">Click on any project to drill down into its detailed cost code matrix and source transactions.</p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 bg-gray-100 rounded-lg text-gray-700">
                {portfolioSummary.projects.length} Projects Tracked
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="bg-gray-50/80 text-gray-600 text-xs font-semibold border-b border-gray-200 uppercase tracking-wider">
                    <th className="py-3.5 px-4">Project</th>
                    <th className="py-3.5 px-4 text-right">Current Budget</th>
                    <th className="py-3.5 px-4 text-right">Committed</th>
                    <th className="py-3.5 px-4 text-right">Actual Incurred</th>
                    <th className="py-3.5 px-4 text-right">ETC</th>
                    <th className="py-3.5 px-4 text-right">EAC</th>
                    <th className="py-3.5 px-4 text-right">Variance (VAC)</th>
                    <th className="py-3.5 px-4 text-center">CPI</th>
                    <th className="py-3.5 px-4 text-center">Status</th>
                    <th className="py-3.5 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {portfolioSummary.projects.map((p) => (
                    <tr
                      key={p.project_id}
                      onClick={() => setSelectedProjectId(p.project_id)}
                      className="hover:bg-indigo-50/50 cursor-pointer transition-colors"
                    >
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-gray-900">{p.project_name}</div>
                        <div className="text-xs text-gray-500">{p.project_number || "No number"}</div>
                      </td>
                      <td className="py-3.5 px-4 text-right font-medium text-gray-900">{formatCurrency(p.total_current_budget)}</td>
                      <td className="py-3.5 px-4 text-right text-purple-900 font-medium">{formatCurrency(p.total_committed)}</td>
                      <td className="py-3.5 px-4 text-right text-amber-900 font-medium">{formatCurrency(p.total_actual)}</td>
                      <td className="py-3.5 px-4 text-right text-indigo-900 font-medium">{formatCurrency(p.total_estimate_to_complete)}</td>
                      <td className="py-3.5 px-4 text-right text-slate-900 font-medium">{formatCurrency(p.total_estimate_at_completion)}</td>
                      <td className={`py-3.5 px-4 text-right font-bold ${Number(p.total_variance) >= 0 ? "text-emerald-700" : "text-rose-700"}`}>
                        {formatCurrency(p.total_variance)}
                      </td>
                      <td className="py-3.5 px-4 text-center">{getCPIBadge(p.cost_performance_index)}</td>
                      <td className="py-3.5 px-4 text-center">{getStatusBadge(p.status)}</td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedProjectId(p.project_id);
                          }}
                          className="px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-semibold rounded-lg transition-all"
                        >
                          View Matrix →
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* View Mode: Single Project Cost Code Matrix */}
        {selectedProjectId !== "PORTFOLIO" && (
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
            {/* Table Filters Header */}
            <div className="p-5 border-b border-gray-200 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <h2 className="text-lg font-bold text-gray-900">
                  {activeProject ? activeProject.name : "Project"} — CSI Cost Code Breakdown
                </h2>
                <p className="text-xs text-gray-500 mt-0.5">
                  Line-by-line breakdown of current approved budget baseline against commitments, incurred costs, and forecast ETC.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                {/* Search */}
                <div className="relative min-w-[220px]">
                  <input
                    type="text"
                    placeholder="Search code or name..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full pl-9 pr-3.5 py-1.5 text-xs bg-gray-50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all"
                  />
                  <svg className="w-4 h-4 text-gray-400 absolute left-3 top-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>

                {/* Category Filter */}
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="px-3 py-1.5 text-xs bg-gray-50 border border-gray-300 rounded-xl font-medium text-gray-700"
                >
                  <option value="ALL">All Categories</option>
                  <option value="MATERIAL">Materials</option>
                  <option value="SUBCONTRACT">Subcontracts</option>
                  <option value="EQUIPMENT">Equipment</option>
                  <option value="LABOR">Labor</option>
                  <option value="OVERHEAD">Overhead</option>
                </select>

                {/* Status Filter */}
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-3 py-1.5 text-xs bg-gray-50 border border-gray-300 rounded-xl font-medium text-gray-700"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="UNDER_BUDGET">Under Budget</option>
                  <option value="ON_TRACK">On Track</option>
                  <option value="AT_RISK">At Risk</option>
                  <option value="OVER_BUDGET">Over Budget</option>
                </select>
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-gray-50/80 text-gray-600 font-semibold border-b border-gray-200 uppercase tracking-wider">
                    <th className="py-3 px-4">Cost Code</th>
                    <th className="py-3 px-4">Description</th>
                    <th className="py-3 px-3">Category</th>
                    <th className="py-3 px-3 text-right">Orig. Budget</th>
                    <th className="py-3 px-3 text-right">Approved Changes</th>
                    <th className="py-3 px-3 text-right font-bold text-gray-900">Current Budget</th>
                    <th className="py-3 px-3 text-right text-purple-900 font-bold">Committed</th>
                    <th className="py-3 px-3 text-right text-amber-900 font-bold">Actual Incurred</th>
                    <th className="py-3 px-3 text-right text-indigo-900 font-bold">ETC</th>
                    <th className="py-3 px-3 text-right text-slate-900 font-bold">EAC</th>
                    <th className="py-3 px-3 text-right font-bold">Variance</th>
                    <th className="py-3 px-3 text-center">Status</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredSummaries.length === 0 ? (
                    <tr>
                      <td colSpan={13} className="py-8 text-center text-gray-500">
                        No cost codes matching your filter criteria.
                      </td>
                    </tr>
                  ) : (
                    filteredSummaries.map((s) => {
                      const varNum = Number(s.variance || 0);
                      const varPct = Number(s.variance_percentage || 0);
                      return (
                        <tr key={s.cost_code_id} className="hover:bg-gray-50/60 transition-colors">
                          <td className="py-3 px-4 font-mono font-bold text-gray-900">
                            {s.cost_code_code || "N/A"}
                          </td>
                          <td className="py-3 px-4 font-medium text-gray-800">
                            {s.cost_code_name || "Uncategorized Line"}
                          </td>
                          <td className="py-3 px-3">
                            {getCategoryBadge(s.cost_category)}
                          </td>
                          <td className="py-3 px-3 text-right text-gray-600">
                            {formatCurrency(s.original_budget)}
                          </td>
                          <td className="py-3 px-3 text-right text-gray-600">
                            {formatCurrency(s.approved_changes)}
                          </td>
                          <td className="py-3 px-3 text-right font-bold text-gray-900">
                            {formatCurrency(s.current_budget)}
                          </td>
                          <td className="py-3 px-3 text-right font-semibold text-purple-800">
                            {formatCurrency(s.committed_cost)}
                          </td>
                          <td className="py-3 px-3 text-right font-semibold text-amber-800">
                            {formatCurrency(s.actual_cost)}
                          </td>
                          <td className="py-3 px-3 text-right font-semibold text-indigo-800">
                            {formatCurrency(s.estimate_to_complete)}
                          </td>
                          <td className="py-3 px-3 text-right font-bold text-slate-800">
                            {formatCurrency(s.estimate_at_completion)}
                          </td>
                          <td className={`py-3 px-3 text-right font-bold ${varNum >= 0 ? "text-emerald-700" : "text-rose-700"}`}>
                            <div>{formatCurrency(s.variance)}</div>
                            <div className="text-[10px] font-medium opacity-80">{varPct > 0 ? `+${varPct}%` : `${varPct}%`}</div>
                          </td>
                          <td className="py-3 px-3 text-center">
                            {getStatusBadge(s.status)}
                          </td>
                          <td className="py-3 px-4 text-right">
                            <button
                              onClick={() => handleOpenForecastModal(s.cost_code_id)}
                              className="px-2.5 py-1 text-xs font-semibold bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg transition-all"
                            >
                              Adjust ETC
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
                {filteredSummaries.length > 0 && (
                  <tfoot>
                    <tr className="bg-gray-100/80 font-bold text-gray-900 border-t-2 border-gray-300">
                      <td colSpan={3} className="py-3.5 px-4 text-left uppercase tracking-wider text-xs">
                        Totals ({filteredSummaries.length} Cost Codes)
                      </td>
                      <td className="py-3.5 px-3 text-right"></td>
                      <td className="py-3.5 px-3 text-right"></td>
                      <td className="py-3.5 px-3 text-right font-bold text-gray-900">{formatCurrency(totalBudget)}</td>
                      <td className="py-3.5 px-3 text-right text-purple-900">{formatCurrency(totalCommitted)}</td>
                      <td className="py-3.5 px-3 text-right text-amber-900">{formatCurrency(totalActual)}</td>
                      <td className="py-3.5 px-3 text-right text-indigo-900">{formatCurrency(totalETC)}</td>
                      <td className="py-3.5 px-3 text-right text-slate-900">{formatCurrency(totalEAC)}</td>
                      <td className={`py-3.5 px-3 text-right font-extrabold ${totalVariance >= 0 ? "text-emerald-700" : "text-rose-700"}`}>
                        {formatCurrency(totalVariance)}
                      </td>
                      <td colSpan={2} className="py-3.5 px-4"></td>
                    </tr>
                  </tfoot>
                )}
              </table>
            </div>
          </div>
        )}

        {/* Modal: Adjust Project Forecast (ETC) */}
        {showForecastModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-gray-200">
              <div className="p-6 border-b border-gray-200 flex items-center justify-between sticky top-0 bg-white z-10">
                <div>
                  <h3 className="text-xl font-bold text-gray-900">Update Cost to Complete (ETC) Forecast</h3>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Adjust remaining estimated costs per CSI Cost Code. Submitting will create an approved ProjectForecast document and re-calculate project EAC and variance.
                  </p>
                </div>
                <button
                  onClick={() => setShowForecastModal(false)}
                  className="p-1 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <form onSubmit={handleForecastSubmit} className="p-6 space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">Forecast Reference #</label>
                    <input
                      type="text"
                      required
                      value={forecastForm.forecastNumber}
                      onChange={(e) => setForecastForm({ ...forecastForm, forecastNumber: e.target.value })}
                      className="w-full px-3.5 py-2 text-sm bg-gray-50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">Forecast Effective Date</label>
                    <input
                      type="date"
                      required
                      value={forecastForm.date}
                      onChange={(e) => setForecastForm({ ...forecastForm, date: e.target.value })}
                      className="w-full px-3.5 py-2 text-sm bg-gray-50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">Notes / Justification</label>
                    <input
                      type="text"
                      value={forecastForm.notes}
                      onChange={(e) => setForecastForm({ ...forecastForm, notes: e.target.value })}
                      className="w-full px-3.5 py-2 text-sm bg-gray-50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:bg-white"
                    />
                  </div>
                </div>

                <div className="border border-gray-200 rounded-xl overflow-hidden">
                  <div className="bg-gray-50 px-4 py-2.5 border-b border-gray-200 text-xs font-bold text-gray-600 uppercase tracking-wider">
                    Cost Codes ETC Input Matrix
                  </div>
                  <div className="max-h-72 overflow-y-auto divide-y divide-gray-100">
                    {costSummaries.map((s) => {
                      const curVal = Number(forecastForm.lines[s.cost_code_id] || 0);
                      const actVal = Number(s.actual_cost || 0);
                      const projEAC = actVal + curVal;
                      const projVar = Number(s.current_budget || 0) - projEAC;

                      return (
                        <div key={s.cost_code_id} className="p-3.5 flex items-center justify-between gap-4 hover:bg-gray-50/70">
                          <div className="min-w-[200px]">
                            <div className="font-mono text-xs font-bold text-gray-900">{s.cost_code_code}</div>
                            <div className="text-xs text-gray-500 truncate max-w-[240px]">{s.cost_code_name}</div>
                            <div className="text-[11px] text-gray-400 mt-0.5">Budget: {formatCurrency(s.current_budget)} | Actual: {formatCurrency(s.actual_cost)}</div>
                          </div>

                          <div className="flex items-center gap-4">
                            <div>
                              <label className="block text-[10px] font-bold text-gray-500 uppercase">New ETC ($)</label>
                              <input
                                type="number"
                                min="0"
                                step="0.01"
                                value={forecastForm.lines[s.cost_code_id] || ""}
                                onChange={(e) =>
                                  setForecastForm({
                                    ...forecastForm,
                                    lines: { ...forecastForm.lines, [s.cost_code_id]: e.target.value },
                                  })
                                }
                                className="w-32 px-3 py-1.5 text-xs text-right font-mono bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                              />
                            </div>
                            <div className="w-28 text-right">
                              <div className="text-[10px] font-bold text-gray-500 uppercase">Projected EAC</div>
                              <div className="text-xs font-semibold text-gray-900">{formatCurrency(projEAC)}</div>
                            </div>
                            <div className="w-28 text-right">
                              <div className="text-[10px] font-bold text-gray-500 uppercase">Projected Var</div>
                              <div className={`text-xs font-bold ${projVar >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
                                {formatCurrency(projVar)}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
                  <button
                    type="button"
                    onClick={() => setShowForecastModal(false)}
                    className="px-4 py-2 text-sm font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingForecast}
                    className="inline-flex items-center gap-2 px-5 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-sm transition-all disabled:opacity-50"
                  >
                    {submittingForecast ? "Saving Forecast..." : "Commit & Apply Forecast"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Source Transactions Audit */}
        {showTxnModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden shadow-2xl border border-gray-200 flex flex-col">
              <div className="p-6 border-b border-gray-200 flex items-center justify-between bg-white">
                <div>
                  <h3 className="text-xl font-bold text-gray-900">Cost Transactions Audit Ledger</h3>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Underlying live transactional records from Purchase Orders, Trade Subcontracts, WAC Material Issues, AP Invoices, Timesheets, and Equipment usage.
                  </p>
                </div>
                <button
                  onClick={() => setShowTxnModal(false)}
                  className="p-1 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Filters */}
              <div className="p-4 bg-gray-50 border-b border-gray-200 flex flex-wrap items-center justify-between gap-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-semibold text-gray-500 uppercase">Source:</span>
                  {[
                    "ALL",
                    "PURCHASE_ORDER",
                    "SUBCONTRACT",
                    "MATERIAL_ISSUE",
                    "AP_INVOICE",
                    "TIMESHEET",
                    "EQUIPMENT_USAGE",
                  ].map((src) => (
                    <button
                      key={src}
                      onClick={() => setSelectedTxnSource(src)}
                      className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                        selectedTxnSource === src
                          ? "bg-slate-900 text-white shadow-sm"
                          : "bg-white text-gray-700 hover:bg-gray-200 border border-gray-300"
                      }`}
                    >
                      {src.replace("_", " ")}
                    </button>
                  ))}
                </div>

                <input
                  type="text"
                  placeholder="Filter transactions..."
                  value={txnSearch}
                  onChange={(e) => setTxnSearch(e.target.value)}
                  className="px-3.5 py-1 text-xs bg-white border border-gray-300 rounded-lg w-56"
                />
              </div>

              {/* Transactions Table */}
              <div className="overflow-y-auto flex-1 p-0">
                <table className="w-full text-left border-collapse text-xs">
                  <thead className="sticky top-0 bg-gray-100 text-gray-600 font-semibold border-b border-gray-200 uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4">Date</th>
                      <th className="py-3 px-3">Type</th>
                      <th className="py-3 px-3">Source</th>
                      <th className="py-3 px-4">Reference</th>
                      <th className="py-3 px-4">Cost Code</th>
                      <th className="py-3 px-4 text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {filteredTransactions.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-8 text-center text-gray-500">
                          No transactions found matching criteria.
                        </td>
                      </tr>
                    ) : (
                      filteredTransactions.map((t, idx) => (
                        <tr key={idx} className="hover:bg-gray-50 transition-colors">
                          <td className="py-3 px-4 text-gray-600 font-mono">{t.date}</td>
                          <td className="py-3 px-3">
                            <span
                              className={`px-2 py-0.5 text-[11px] font-bold rounded-md ${
                                t.cost_type === "COMMITTED"
                                  ? "bg-purple-100 text-purple-800 border border-purple-200"
                                  : "bg-amber-100 text-amber-800 border border-amber-200"
                              }`}
                            >
                              {t.cost_type}
                            </span>
                          </td>
                          <td className="py-3 px-3 font-medium text-gray-700">
                            {t.source_type.replace("_", " ")}
                          </td>
                          <td className="py-3 px-4 font-mono font-semibold text-gray-900">
                            {t.source_reference || "N/A"}
                          </td>
                          <td className="py-3 px-4">
                            <span className="font-mono font-bold text-gray-900">{t.cost_code_code || "General"}</span>
                            {t.cost_code_name && (
                              <span className="text-gray-500 ml-1.5 text-[11px]">{t.cost_code_name}</span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-right font-mono font-bold text-gray-900">
                            {formatCurrency(t.amount)}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              <div className="p-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between text-xs text-gray-600">
                <span>Showing {filteredTransactions.length} of {transactions.length} total source transactions</span>
                <button
                  onClick={() => setShowTxnModal(false)}
                  className="px-4 py-1.5 text-xs font-semibold bg-white border border-gray-300 hover:bg-gray-100 text-gray-700 rounded-lg transition-all"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
