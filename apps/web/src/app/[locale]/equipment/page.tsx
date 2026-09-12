"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import {
  getProjects,
  getCostCodes,
  getEquipmentSummary,
  getEquipmentList,
  createEquipment,
  updateEquipment,
  getEquipmentAssignments,
  createEquipmentAssignment,
  getEquipmentUsageLogs,
  createEquipmentUsageLog,
  submitEquipmentUsageLog,
  approveEquipmentUsageLog,
  getFuelTransactions,
  createFuelTransaction,
  getMaintenanceRecords,
  createMaintenanceRecord,
  Project,
  CostCode,
  Equipment,
  EquipmentSummary,
  EquipmentAssignment,
  EquipmentUsageLog,
  FuelTransaction,
  MaintenanceRecord,
} from "@/lib/api";

export default function EquipmentPage({ params }: { params: { locale: string } }) {
  const [activeTab, setActiveTab] = useState<"FLEET" | "ASSIGNMENTS" | "USAGE" | "FUEL" | "MAINTENANCE">("FLEET");
  const [summary, setSummary] = useState<EquipmentSummary | null>(null);
  const [equipmentList, setEquipmentList] = useState<Equipment[]>([]);
  const [assignments, setAssignments] = useState<EquipmentAssignment[]>([]);
  const [usageLogs, setUsageLogs] = useState<EquipmentUsageLog[]>([]);
  const [fuelTxns, setFuelTxns] = useState<FuelTransaction[]>([]);
  const [maintenanceRecords, setMaintenanceRecords] = useState<MaintenanceRecord[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [costCodes, setCostCodes] = useState<CostCode[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  // Modals
  const [showCreateEqModal, setShowCreateEqModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [showUsageModal, setShowUsageModal] = useState(false);
  const [showFuelModal, setShowFuelModal] = useState(false);
  const [showMaintModal, setShowMaintModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Selected Log for detail drawer
  const [selectedLog, setSelectedLog] = useState<EquipmentUsageLog | null>(null);

  // Form states
  const [eqForm, setEqForm] = useState({
    name: "",
    make: "",
    model: "",
    year: "2024",
    serial_number: "",
    internal_id: "",
    base_hourly_cost: "150.00",
  });

  const [assignForm, setAssignForm] = useState({
    equipment_id: "",
    project_id: "",
    start_date: new Date().toISOString().slice(0, 10),
    end_date: "",
    hourly_cost_override: "",
  });

  const [usageForm, setUsageForm] = useState({
    equipment_id: "",
    period_start: new Date().toISOString().slice(0, 10),
    period_end: new Date(Date.now() + 6 * 86400000).toISOString().slice(0, 10),
    project_id: "",
    cost_code_id: "",
    date: new Date().toISOString().slice(0, 10),
    hours: "8.0",
  });

  const [fuelForm, setFuelForm] = useState({
    equipment_id: "",
    project_id: "",
    cost_code_id: "",
    date: new Date().toISOString().slice(0, 10),
    volume: "100.0",
    unit_cost: "3.85",
  });

  const [maintForm, setMaintForm] = useState({
    equipment_id: "",
    project_id: "",
    cost_code_id: "",
    type: "PREVENTIVE",
    date: new Date().toISOString().slice(0, 10),
    description: "",
    duration_hours: "4.0",
    cost: "500.00",
  });

  const loadAll = async () => {
    setLoading(true);
    setError(null);
    try {
      const [sum, eqs, asgns, logs, fuels, maints, projs, codes] = await Promise.all([
        getEquipmentSummary(),
        getEquipmentList(),
        getEquipmentAssignments(),
        getEquipmentUsageLogs(),
        getFuelTransactions(),
        getMaintenanceRecords(),
        getProjects(),
        getCostCodes(),
      ]);
      setSummary(sum);
      setEquipmentList(eqs);
      setAssignments(asgns);
      setUsageLogs(logs);
      setFuelTxns(fuels);
      setMaintenanceRecords(maints);
      setProjects(projs);
      setCostCodes(codes);

      if (eqs.length > 0 && !assignForm.equipment_id) {
        setAssignForm((prev) => ({ ...prev, equipment_id: eqs[0].id }));
        setUsageForm((prev) => ({ ...prev, equipment_id: eqs[0].id }));
        setFuelForm((prev) => ({ ...prev, equipment_id: eqs[0].id }));
        setMaintForm((prev) => ({ ...prev, equipment_id: eqs[0].id }));
      }
      if (projs.length > 0 && !assignForm.project_id) {
        setAssignForm((prev) => ({ ...prev, project_id: projs[0].id }));
        setUsageForm((prev) => ({ ...prev, project_id: projs[0].id }));
        setFuelForm((prev) => ({ ...prev, project_id: projs[0].id }));
        setMaintForm((prev) => ({ ...prev, project_id: projs[0].id }));
      }
      if (codes.length > 0 && !usageForm.cost_code_id) {
        setUsageForm((prev) => ({ ...prev, cost_code_id: codes[0].id }));
        setFuelForm((prev) => ({ ...prev, cost_code_id: codes[0].id }));
        setMaintForm((prev) => ({ ...prev, cost_code_id: codes[0].id }));
      }
    } catch (err: any) {
      console.error(err);
      setError(err?.message || "Failed to load equipment fleet data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handleCreateEquipment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!eqForm.name || !eqForm.base_hourly_cost) return;
    setSubmitting(true);
    try {
      await createEquipment({
        name: eqForm.name,
        make: eqForm.make || undefined,
        model: eqForm.model || undefined,
        year: eqForm.year || undefined,
        serial_number: eqForm.serial_number || undefined,
        internal_id: eqForm.internal_id || undefined,
        base_hourly_cost: parseFloat(eqForm.base_hourly_cost),
      });
      setShowCreateEqModal(false);
      setEqForm({
        name: "",
        make: "",
        model: "",
        year: "2024",
        serial_number: "",
        internal_id: "",
        base_hourly_cost: "150.00",
      });
      await loadAll();
    } catch (err: any) {
      alert(err?.message || "Failed to create equipment");
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdateStatus = async (eqId: string, newStatus: string) => {
    try {
      await updateEquipment(eqId, { status: newStatus });
      await loadAll();
    } catch (err: any) {
      alert(err?.message || "Failed to update equipment status");
    }
  };

  const handleCreateAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assignForm.equipment_id || !assignForm.project_id || !assignForm.start_date) return;
    setSubmitting(true);
    try {
      await createEquipmentAssignment({
        equipment_id: assignForm.equipment_id,
        project_id: assignForm.project_id,
        start_date: assignForm.start_date,
        end_date: assignForm.end_date || undefined,
        hourly_cost_override: assignForm.hourly_cost_override ? parseFloat(assignForm.hourly_cost_override) : undefined,
      });
      setShowAssignModal(false);
      await loadAll();
    } catch (err: any) {
      alert(err?.message || "Failed to create assignment");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreateUsageLog = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!usageForm.equipment_id || !usageForm.project_id || !usageForm.cost_code_id) return;
    setSubmitting(true);
    try {
      await createEquipmentUsageLog({
        equipment_id: usageForm.equipment_id,
        period_start: usageForm.period_start,
        period_end: usageForm.period_end,
        lines: [
          {
            project_id: usageForm.project_id,
            cost_code_id: usageForm.cost_code_id,
            date: usageForm.date,
            hours: parseFloat(usageForm.hours),
          },
        ],
      });
      setShowUsageModal(false);
      await loadAll();
    } catch (err: any) {
      alert(err?.message || "Failed to create usage log");
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmitUsageLog = async (id: string) => {
    try {
      await submitEquipmentUsageLog(id);
      await loadAll();
    } catch (err: any) {
      alert(err?.message || "Failed to submit usage log");
    }
  };

  const handleApproveUsageLog = async (id: string) => {
    try {
      await approveEquipmentUsageLog(id);
      await loadAll();
    } catch (err: any) {
      alert(err?.message || "Failed to approve usage log");
    }
  };

  const handleCreateFuel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fuelForm.equipment_id || !fuelForm.volume || !fuelForm.unit_cost) return;
    setSubmitting(true);
    try {
      await createFuelTransaction({
        equipment_id: fuelForm.equipment_id,
        project_id: fuelForm.project_id || undefined,
        cost_code_id: fuelForm.cost_code_id || undefined,
        date: fuelForm.date,
        volume: parseFloat(fuelForm.volume),
        unit_cost: parseFloat(fuelForm.unit_cost),
      });
      setShowFuelModal(false);
      await loadAll();
    } catch (err: any) {
      alert(err?.message || "Failed to record fuel transaction");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreateMaintenance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!maintForm.equipment_id || !maintForm.description || !maintForm.cost) return;
    setSubmitting(true);
    try {
      await createMaintenanceRecord({
        equipment_id: maintForm.equipment_id,
        project_id: maintForm.project_id || undefined,
        cost_code_id: maintForm.cost_code_id || undefined,
        type: maintForm.type,
        date: maintForm.date,
        description: maintForm.description,
        duration_hours: maintForm.duration_hours ? parseFloat(maintForm.duration_hours) : undefined,
        cost: parseFloat(maintForm.cost),
      });
      setShowMaintModal(false);
      await loadAll();
    } catch (err: any) {
      alert(err?.message || "Failed to create maintenance record");
    } finally {
      setSubmitting(false);
    }
  };

  const filteredEquipment = equipmentList.filter((eq) => {
    const matchesStatus = statusFilter === "ALL" || eq.status === statusFilter;
    const matchesSearch =
      search === "" ||
      eq.name.toLowerCase().includes(search.toLowerCase()) ||
      (eq.internal_id && eq.internal_id.toLowerCase().includes(search.toLowerCase())) ||
      (eq.make && eq.make.toLowerCase().includes(search.toLowerCase())) ||
      (eq.model && eq.model.toLowerCase().includes(search.toLowerCase()));
    return matchesStatus && matchesSearch;
  });

  return (
    <AppLayout locale={params.locale}>
      <div className="space-y-6">
        {/* Header & Global Action Bar */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
          <div>
            <div className="flex items-center gap-3">
              <span className="p-2.5 bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-lg text-2xl">
                🚜
              </span>
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight">
                  Equipment Fleet & Machinery Workspace
                </h1>
                <p className="text-sm text-slate-400">
                  Heavy Machinery Register, Site Dispatch, Shift Timesheets, Fuel Logs & Maintenance Work Orders
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setShowCreateEqModal(true)}
              className="px-3.5 py-2 bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold rounded-lg shadow transition flex items-center gap-1.5"
            >
              <span>+</span> Register Equipment
            </button>
            <button
              onClick={() => setShowAssignModal(true)}
              className="px-3.5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg shadow transition flex items-center gap-1.5"
            >
              <span>📍</span> Dispatch to Site
            </button>
            <button
              onClick={() => setShowUsageModal(true)}
              className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg shadow transition flex items-center gap-1.5"
            >
              <span>⏱</span> Log Shift Hours
            </button>
            <button
              onClick={() => setShowFuelModal(true)}
              className="px-3.5 py-2 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold rounded-lg shadow transition flex items-center gap-1.5"
            >
              <span>⛽</span> Record Fuel
            </button>
            <button
              onClick={() => setShowMaintModal(true)}
              className="px-3.5 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold rounded-lg shadow transition flex items-center gap-1.5"
            >
              <span>🔧</span> Schedule Service
            </button>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-4 bg-rose-950/40 border border-rose-800/80 rounded-xl text-rose-300 text-sm flex items-center justify-between">
            <span>{error}</span>
            <button onClick={loadAll} className="underline text-xs hover:text-white">
              Retry
            </button>
          </div>
        )}

        {/* KPI Summary Cards */}
        {summary && (
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 shadow-md">
              <span className="text-xs text-slate-400 block mb-1">Total Machinery</span>
              <span className="text-xl font-bold text-white">{summary.total_units}</span>
              <span className="text-[10px] text-slate-500 block mt-0.5">Asset units</span>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 shadow-md">
              <span className="text-xs text-emerald-400 block mb-1">Active In Use</span>
              <span className="text-xl font-bold text-emerald-300">{summary.in_use_units}</span>
              <span className="text-[10px] text-emerald-500 block mt-0.5">On site</span>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 shadow-md">
              <span className="text-xs text-blue-400 block mb-1">Available</span>
              <span className="text-xl font-bold text-blue-300">{summary.available_units}</span>
              <span className="text-[10px] text-blue-500 block mt-0.5">Yard / Depot</span>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 shadow-md">
              <span className="text-xs text-amber-400 block mb-1">In Maintenance</span>
              <span className="text-xl font-bold text-amber-300">{summary.maintenance_units}</span>
              <span className="text-[10px] text-amber-500 block mt-0.5">In shop</span>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 shadow-md">
              <span className="text-xs text-indigo-400 block mb-1">Utilization Rate</span>
              <span className="text-xl font-bold text-indigo-300">{Number(summary.utilization_rate).toFixed(1)}%</span>
              <span className="text-[10px] text-indigo-500 block mt-0.5">Active / Fleet</span>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 shadow-md">
              <span className="text-xs text-cyan-400 block mb-1">Operating Hours</span>
              <span className="text-xl font-bold text-cyan-300">{Number(summary.total_operating_hours).toLocaleString()}</span>
              <span className="text-[10px] text-cyan-500 block mt-0.5">Approved shift hrs</span>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 shadow-md">
              <span className="text-xs text-purple-400 block mb-1">Fuel Incurred</span>
              <span className="text-xl font-bold text-purple-300">${Number(summary.total_fuel_cost).toLocaleString()}</span>
              <span className="text-[10px] text-purple-500 block mt-0.5">Diesel / Gas</span>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 shadow-md">
              <span className="text-xs text-rose-400 block mb-1">Maintenance Cost</span>
              <span className="text-xl font-bold text-rose-300">${Number(summary.total_maintenance_cost).toLocaleString()}</span>
              <span className="text-[10px] text-rose-500 block mt-0.5">Repairs & PM</span>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="border-b border-slate-800 flex items-center gap-2">
          <button
            onClick={() => setActiveTab("FLEET")}
            className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition ${
              activeTab === "FLEET"
                ? "border-amber-500 text-amber-400 bg-amber-500/5"
                : "border-transparent text-slate-400 hover:text-white"
            }`}
          >
            🚜 Fleet Master Register ({equipmentList.length})
          </button>
          <button
            onClick={() => setActiveTab("ASSIGNMENTS")}
            className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition ${
              activeTab === "ASSIGNMENTS"
                ? "border-amber-500 text-amber-400 bg-amber-500/5"
                : "border-transparent text-slate-400 hover:text-white"
            }`}
          >
            📍 Site Dispatch & Deployments ({assignments.length})
          </button>
          <button
            onClick={() => setActiveTab("USAGE")}
            className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition ${
              activeTab === "USAGE"
                ? "border-amber-500 text-amber-400 bg-amber-500/5"
                : "border-transparent text-slate-400 hover:text-white"
            }`}
          >
            ⏱ Shift Operating Timesheets ({usageLogs.length})
          </button>
          <button
            onClick={() => setActiveTab("FUEL")}
            className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition ${
              activeTab === "FUEL"
                ? "border-amber-500 text-amber-400 bg-amber-500/5"
                : "border-transparent text-slate-400 hover:text-white"
            }`}
          >
            ⛽ Fuel Consumption Logs ({fuelTxns.length})
          </button>
          <button
            onClick={() => setActiveTab("MAINTENANCE")}
            className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition ${
              activeTab === "MAINTENANCE"
                ? "border-amber-500 text-amber-400 bg-amber-500/5"
                : "border-transparent text-slate-400 hover:text-white"
            }`}
          >
            🔧 Service & Work Orders ({maintenanceRecords.length})
          </button>
        </div>

        {/* TAB 1: FLEET MASTER REGISTER */}
        {activeTab === "FLEET" && (
          <div className="space-y-4">
            {/* Filters */}
            <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-4 rounded-xl">
              <div className="flex items-center gap-3">
                <input
                  type="text"
                  placeholder="Search machinery, internal ID, make, model..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 w-64 md:w-80"
                />
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-amber-500"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="AVAILABLE">Available</option>
                  <option value="IN_USE">In Use</option>
                  <option value="MAINTENANCE">Maintenance</option>
                  <option value="RETIRED">Retired</option>
                </select>
              </div>
              <span className="text-xs text-slate-500">
                Showing {filteredEquipment.length} of {equipmentList.length} equipment units
              </span>
            </div>

            {/* Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-950/80 text-slate-400 uppercase font-semibold border-b border-slate-800">
                    <tr>
                      <th className="p-3.5">Internal Code</th>
                      <th className="p-3.5">Machine / Asset Name</th>
                      <th className="p-3.5">Make & Model</th>
                      <th className="p-3.5">Status</th>
                      <th className="p-3.5">Base Rate</th>
                      <th className="p-3.5">Current Site</th>
                      <th className="p-3.5 text-right">Hours Logged</th>
                      <th className="p-3.5 text-right">Fuel Cost</th>
                      <th className="p-3.5 text-right">Maint Cost</th>
                      <th className="p-3.5 text-center">Lifecycle Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {filteredEquipment.length === 0 ? (
                      <tr>
                        <td colSpan={10} className="p-8 text-center text-slate-500">
                          No machinery records match the search filter.
                        </td>
                      </tr>
                    ) : (
                      filteredEquipment.map((eq) => (
                        <tr key={eq.id} className="hover:bg-slate-800/40 transition">
                          <td className="p-3.5 font-mono text-amber-400 font-semibold">{eq.internal_id || "—"}</td>
                          <td className="p-3.5 font-medium text-white">
                            {eq.name}
                            <span className="text-[10px] text-slate-500 block font-normal">
                              S/N: {eq.serial_number || "N/A"} • Year {eq.year || "N/A"}
                            </span>
                          </td>
                          <td className="p-3.5 text-slate-300">
                            {eq.make || "—"} {eq.model || ""}
                          </td>
                          <td className="p-3.5">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                eq.status === "AVAILABLE"
                                  ? "bg-blue-500/10 text-blue-400 border border-blue-500/30"
                                  : eq.status === "IN_USE"
                                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                  : eq.status === "MAINTENANCE"
                                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                                  : "bg-slate-700/40 text-slate-400 border border-slate-600/30"
                              }`}
                            >
                              {eq.status}
                            </span>
                          </td>
                          <td className="p-3.5 font-mono text-slate-200">
                            ${Number(eq.base_hourly_cost).toFixed(2)}/hr
                          </td>
                          <td className="p-3.5 text-slate-300">
                            {eq.active_project_name ? (
                              <span className="text-emerald-400 font-medium">{eq.active_project_name}</span>
                            ) : (
                              <span className="text-slate-500">Depot / Unassigned</span>
                            )}
                          </td>
                          <td className="p-3.5 text-right font-mono text-cyan-300">
                            {Number(eq.total_operating_hours).toFixed(1)} hrs
                          </td>
                          <td className="p-3.5 text-right font-mono text-purple-300">
                            ${Number(eq.total_fuel_cost).toLocaleString()}
                          </td>
                          <td className="p-3.5 text-right font-mono text-rose-300">
                            ${Number(eq.total_maintenance_cost).toLocaleString()}
                          </td>
                          <td className="p-3.5 text-center">
                            <div className="flex items-center justify-center gap-1">
                              {eq.status !== "AVAILABLE" && (
                                <button
                                  onClick={() => handleUpdateStatus(eq.id, "AVAILABLE")}
                                  className="px-2 py-1 bg-blue-900/40 hover:bg-blue-800 text-blue-300 rounded text-[10px] transition"
                                  title="Mark Available"
                                >
                                  Make Available
                                </button>
                              )}
                              {eq.status !== "MAINTENANCE" && (
                                <button
                                  onClick={() => handleUpdateStatus(eq.id, "MAINTENANCE")}
                                  className="px-2 py-1 bg-amber-900/40 hover:bg-amber-800 text-amber-300 rounded text-[10px] transition"
                                  title="Send to Maintenance"
                                >
                                  Service
                                </button>
                              )}
                              {eq.status !== "RETIRED" && (
                                <button
                                  onClick={() => handleUpdateStatus(eq.id, "RETIRED")}
                                  className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded text-[10px] transition"
                                  title="Retire Machinery"
                                >
                                  Retire
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: SITE ASSIGNMENTS */}
        {activeTab === "ASSIGNMENTS" && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
            <div className="p-4 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
              <h2 className="text-sm font-bold text-white">Project Site Deployments & Deployments Schedule</h2>
              <button
                onClick={() => setShowAssignModal(true)}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg shadow transition"
              >
                + Dispatch Equipment
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/40 text-slate-400 uppercase font-semibold border-b border-slate-800">
                  <tr>
                    <th className="p-3.5">Machine Code</th>
                    <th className="p-3.5">Equipment Name</th>
                    <th className="p-3.5">Assigned Project Site</th>
                    <th className="p-3.5">Start Date</th>
                    <th className="p-3.5">End Date</th>
                    <th className="p-3.5 text-right">Chargeout Rate Override</th>
                    <th className="p-3.5 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {assignments.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-slate-500">
                        No equipment project deployments recorded yet.
                      </td>
                    </tr>
                  ) : (
                    assignments.map((a) => (
                      <tr key={a.id} className="hover:bg-slate-800/40 transition">
                        <td className="p-3.5 font-mono text-amber-400 font-semibold">
                          {a.equipment_internal_id || "—"}
                        </td>
                        <td className="p-3.5 font-medium text-white">{a.equipment_name || "—"}</td>
                        <td className="p-3.5 text-emerald-400 font-medium">{a.project_name || "—"}</td>
                        <td className="p-3.5 text-slate-300">{a.start_date}</td>
                        <td className="p-3.5 text-slate-300">{a.end_date || "Ongoing (Open)"}</td>
                        <td className="p-3.5 text-right font-mono text-slate-200">
                          {a.hourly_cost_override ? `$${Number(a.hourly_cost_override).toFixed(2)}/hr` : "Base Rate"}
                        </td>
                        <td className="p-3.5 text-center">
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                            DEPLOYED
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 3: SHIFT USAGE & TIMESHEETS */}
        {activeTab === "USAGE" && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
            <div className="p-4 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
              <h2 className="text-sm font-bold text-white">Shift Operating Timesheets & Job Site Chargeouts</h2>
              <button
                onClick={() => setShowUsageModal(true)}
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg shadow transition"
              >
                + Log Shift Hours
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/40 text-slate-400 uppercase font-semibold border-b border-slate-800">
                  <tr>
                    <th className="p-3.5">Machinery</th>
                    <th className="p-3.5">Timesheet Period</th>
                    <th className="p-3.5">Status</th>
                    <th className="p-3.5 text-right">Total Shift Hours</th>
                    <th className="p-3.5 text-right">Total Chargeout ($)</th>
                    <th className="p-3.5">Cost Code Allocations</th>
                    <th className="p-3.5 text-center">Workflow Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {usageLogs.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-slate-500">
                        No equipment shift timesheets logged yet.
                      </td>
                    </tr>
                  ) : (
                    usageLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-slate-800/40 transition">
                        <td className="p-3.5">
                          <span className="font-mono text-amber-400 font-semibold block">
                            {log.equipment_internal_id || "EQ"}
                          </span>
                          <span className="text-white text-xs">{log.equipment_name}</span>
                        </td>
                        <td className="p-3.5 text-slate-300">
                          {log.period_start} → {log.period_end}
                        </td>
                        <td className="p-3.5">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                              log.status === "APPROVED"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                : log.status === "SUBMITTED"
                                ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                                : "bg-slate-700/30 text-slate-400 border border-slate-600/30"
                            }`}
                          >
                            {log.status}
                          </span>
                        </td>
                        <td className="p-3.5 text-right font-mono text-cyan-300">
                          {Number(log.total_hours).toFixed(1)} hrs
                        </td>
                        <td className="p-3.5 text-right font-mono text-emerald-300 font-semibold">
                          ${Number(log.total_cost).toLocaleString()}
                        </td>
                        <td className="p-3.5 text-slate-400">
                          {log.lines && log.lines.length > 0 ? (
                            <span className="text-[11px] text-slate-300">
                              {log.lines.map((l) => `${l.cost_code_code || "CC"}: ${l.hours}h`).join(", ")}
                            </span>
                          ) : (
                            <span className="text-slate-500">—</span>
                          )}
                        </td>
                        <td className="p-3.5 text-center">
                          <div className="flex items-center justify-center gap-1">
                            {log.status === "DRAFT" && (
                              <button
                                onClick={() => handleSubmitUsageLog(log.id)}
                                className="px-2 py-1 bg-amber-600/30 hover:bg-amber-500 text-amber-300 rounded text-[10px] transition"
                              >
                                Submit
                              </button>
                            )}
                            {log.status === "SUBMITTED" && (
                              <button
                                onClick={() => handleApproveUsageLog(log.id)}
                                className="px-2 py-1 bg-emerald-600/30 hover:bg-emerald-500 text-emerald-300 rounded text-[10px] transition font-semibold"
                              >
                                Approve
                              </button>
                            )}
                            {log.status === "APPROVED" && (
                              <span className="text-[10px] text-slate-500">✓ Posted to Costs</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 4: FUEL CONSUMPTION LOGS */}
        {activeTab === "FUEL" && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
            <div className="p-4 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
              <h2 className="text-sm font-bold text-white">Fuel Delivery & Site Dispensing Register</h2>
              <button
                onClick={() => setShowFuelModal(true)}
                className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold rounded-lg shadow transition"
              >
                + Record Fuel Delivery
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/40 text-slate-400 uppercase font-semibold border-b border-slate-800">
                  <tr>
                    <th className="p-3.5">Date</th>
                    <th className="p-3.5">Machinery / Equipment</th>
                    <th className="p-3.5">Project Site</th>
                    <th className="p-3.5">Cost Code</th>
                    <th className="p-3.5 text-right">Fuel Volume</th>
                    <th className="p-3.5 text-right">Unit Price</th>
                    <th className="p-3.5 text-right">Total Fuel Cost</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {fuelTxns.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-slate-500">
                        No fuel transactions logged yet.
                      </td>
                    </tr>
                  ) : (
                    fuelTxns.map((f) => (
                      <tr key={f.id} className="hover:bg-slate-800/40 transition">
                        <td className="p-3.5 text-slate-300">{f.date}</td>
                        <td className="p-3.5">
                          <span className="font-mono text-amber-400 font-semibold block">
                            {f.equipment_internal_id || "EQ"}
                          </span>
                          <span className="text-white text-xs">{f.equipment_name}</span>
                        </td>
                        <td className="p-3.5 text-emerald-400">{f.project_name || "—"}</td>
                        <td className="p-3.5 font-mono text-slate-400">{f.cost_code_code || "—"}</td>
                        <td className="p-3.5 text-right font-mono text-cyan-300">
                          {Number(f.volume).toFixed(1)} gal
                        </td>
                        <td className="p-3.5 text-right font-mono text-slate-400">
                          ${Number(f.unit_cost).toFixed(2)}/gal
                        </td>
                        <td className="p-3.5 text-right font-mono text-purple-300 font-semibold">
                          ${Number(f.total_cost).toLocaleString()}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 5: MAINTENANCE & WORK ORDERS */}
        {activeTab === "MAINTENANCE" && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
            <div className="p-4 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
              <h2 className="text-sm font-bold text-white">Preventive & Corrective Maintenance Work Orders</h2>
              <button
                onClick={() => setShowMaintModal(true)}
                className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold rounded-lg shadow transition"
              >
                + Schedule Service
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/40 text-slate-400 uppercase font-semibold border-b border-slate-800">
                  <tr>
                    <th className="p-3.5">Date</th>
                    <th className="p-3.5">Machinery</th>
                    <th className="p-3.5">Service Type</th>
                    <th className="p-3.5">Work Order Description</th>
                    <th className="p-3.5 text-right">Downtime Hours</th>
                    <th className="p-3.5 text-right">Repair Cost</th>
                    <th className="p-3.5">Project Site</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {maintenanceRecords.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-slate-500">
                        No maintenance work orders logged yet.
                      </td>
                    </tr>
                  ) : (
                    maintenanceRecords.map((m) => (
                      <tr key={m.id} className="hover:bg-slate-800/40 transition">
                        <td className="p-3.5 text-slate-300">{m.date}</td>
                        <td className="p-3.5">
                          <span className="font-mono text-amber-400 font-semibold block">
                            {m.equipment_internal_id || "EQ"}
                          </span>
                          <span className="text-white text-xs">{m.equipment_name}</span>
                        </td>
                        <td className="p-3.5">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                              m.type === "PREVENTIVE"
                                ? "bg-blue-500/10 text-blue-400 border border-blue-500/30"
                                : "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                            }`}
                          >
                            {m.type}
                          </span>
                        </td>
                        <td className="p-3.5 text-white max-w-xs truncate">{m.description}</td>
                        <td className="p-3.5 text-right font-mono text-cyan-300">
                          {m.duration_hours ? `${Number(m.duration_hours).toFixed(1)} hrs` : "—"}
                        </td>
                        <td className="p-3.5 text-right font-mono text-rose-300 font-semibold">
                          ${Number(m.cost).toLocaleString()}
                        </td>
                        <td className="p-3.5 text-emerald-400">{m.project_name || "Unassigned"}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* MODAL 1: REGISTER EQUIPMENT */}
        {showCreateEqModal && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-base font-bold text-white">Register Heavy Machinery</h3>
                <button
                  onClick={() => setShowCreateEqModal(false)}
                  className="text-slate-400 hover:text-white text-lg"
                >
                  ✕
                </button>
              </div>
              <form onSubmit={handleCreateEquipment} className="space-y-3 text-xs">
                <div>
                  <label className="block text-slate-400 mb-1">Asset / Machine Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Caterpillar 336 Hydraulic Excavator"
                    value={eqForm.name}
                    onChange={(e) => setEqForm({ ...eqForm, name: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-slate-400 mb-1">Internal Asset ID</label>
                    <input
                      type="text"
                      placeholder="e.g. EQ-336-02"
                      value={eqForm.internal_id}
                      onChange={(e) => setEqForm({ ...eqForm, internal_id: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1">Base Rate ($/hr) *</label>
                    <input
                      type="number"
                      step="0.01"
                      required
                      value={eqForm.base_hourly_cost}
                      onChange={(e) => setEqForm({ ...eqForm, base_hourly_cost: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white font-mono"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-slate-400 mb-1">Manufacturer (Make)</label>
                    <input
                      type="text"
                      placeholder="e.g. Caterpillar"
                      value={eqForm.make}
                      onChange={(e) => setEqForm({ ...eqForm, make: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1">Model</label>
                    <input
                      type="text"
                      placeholder="e.g. 336 Next Gen"
                      value={eqForm.model}
                      onChange={(e) => setEqForm({ ...eqForm, model: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-slate-400 mb-1">Year</label>
                    <input
                      type="text"
                      value={eqForm.year}
                      onChange={(e) => setEqForm({ ...eqForm, year: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1">Serial Number</label>
                    <input
                      type="text"
                      placeholder="e.g. CAT0336XJ9922"
                      value={eqForm.serial_number}
                      onChange={(e) => setEqForm({ ...eqForm, serial_number: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white font-mono"
                    />
                  </div>
                </div>
                <div className="pt-2 flex justify-end gap-2 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowCreateEqModal(false)}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-1.5 bg-amber-600 hover:bg-amber-500 text-white font-semibold rounded-lg shadow"
                  >
                    {submitting ? "Saving..." : "Save Equipment"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* MODAL 2: DISPATCH TO SITE */}
        {showAssignModal && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-base font-bold text-white">Dispatch Equipment to Project Site</h3>
                <button
                  onClick={() => setShowAssignModal(false)}
                  className="text-slate-400 hover:text-white text-lg"
                >
                  ✕
                </button>
              </div>
              <form onSubmit={handleCreateAssignment} className="space-y-3 text-xs">
                <div>
                  <label className="block text-slate-400 mb-1">Select Machinery *</label>
                  <select
                    value={assignForm.equipment_id}
                    onChange={(e) => setAssignForm({ ...assignForm, equipment_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                  >
                    {equipmentList.map((eq) => (
                      <option key={eq.id} value={eq.id}>
                        {eq.internal_id ? `[${eq.internal_id}] ` : ""}{eq.name} ({eq.status})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Target Project Site *</label>
                  <select
                    value={assignForm.project_id}
                    onChange={(e) => setAssignForm({ ...assignForm, project_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                  >
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-slate-400 mb-1">Start Date *</label>
                    <input
                      type="date"
                      required
                      value={assignForm.start_date}
                      onChange={(e) => setAssignForm({ ...assignForm, start_date: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1">End Date (Optional)</label>
                    <input
                      type="date"
                      value={assignForm.end_date}
                      onChange={(e) => setAssignForm({ ...assignForm, end_date: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Hourly Rate Override ($/hr) (Optional)</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="Leave blank to use base machine rate"
                    value={assignForm.hourly_cost_override}
                    onChange={(e) => setAssignForm({ ...assignForm, hourly_cost_override: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white font-mono"
                  />
                </div>
                <div className="pt-2 flex justify-end gap-2 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowAssignModal(false)}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg shadow"
                  >
                    {submitting ? "Dispatching..." : "Confirm Dispatch"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* MODAL 3: LOG SHIFT HOURS */}
        {showUsageModal && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-base font-bold text-white">Log Shift Operating Hours</h3>
                <button
                  onClick={() => setShowUsageModal(false)}
                  className="text-slate-400 hover:text-white text-lg"
                >
                  ✕
                </button>
              </div>
              <form onSubmit={handleCreateUsageLog} className="space-y-3 text-xs">
                <div>
                  <label className="block text-slate-400 mb-1">Select Machinery *</label>
                  <select
                    value={usageForm.equipment_id}
                    onChange={(e) => setUsageForm({ ...usageForm, equipment_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                  >
                    {equipmentList.map((eq) => (
                      <option key={eq.id} value={eq.id}>
                        {eq.internal_id ? `[${eq.internal_id}] ` : ""}{eq.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Project Site *</label>
                  <select
                    value={usageForm.project_id}
                    onChange={(e) => setUsageForm({ ...usageForm, project_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                  >
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Chargeout CSI Cost Code *</label>
                  <select
                    value={usageForm.cost_code_id}
                    onChange={(e) => setUsageForm({ ...usageForm, cost_code_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                  >
                    {costCodes.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.code} - {c.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-slate-400 mb-1">Operating Date *</label>
                    <input
                      type="date"
                      required
                      value={usageForm.date}
                      onChange={(e) => setUsageForm({ ...usageForm, date: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1">Hours Operated *</label>
                    <input
                      type="number"
                      step="0.5"
                      required
                      value={usageForm.hours}
                      onChange={(e) => setUsageForm({ ...usageForm, hours: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white font-mono"
                    />
                  </div>
                </div>
                <div className="pt-2 flex justify-end gap-2 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowUsageModal(false)}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg shadow"
                  >
                    {submitting ? "Logging..." : "Submit Timesheet"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* MODAL 4: RECORD FUEL */}
        {showFuelModal && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-base font-bold text-white">Record Site Fuel Delivery</h3>
                <button
                  onClick={() => setShowFuelModal(false)}
                  className="text-slate-400 hover:text-white text-lg"
                >
                  ✕
                </button>
              </div>
              <form onSubmit={handleCreateFuel} className="space-y-3 text-xs">
                <div>
                  <label className="block text-slate-400 mb-1">Select Machinery *</label>
                  <select
                    value={fuelForm.equipment_id}
                    onChange={(e) => setFuelForm({ ...fuelForm, equipment_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                  >
                    {equipmentList.map((eq) => (
                      <option key={eq.id} value={eq.id}>
                        {eq.internal_id ? `[${eq.internal_id}] ` : ""}{eq.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Project Site</label>
                  <select
                    value={fuelForm.project_id}
                    onChange={(e) => setFuelForm({ ...fuelForm, project_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                  >
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">CSI Cost Code</label>
                  <select
                    value={fuelForm.cost_code_id}
                    onChange={(e) => setFuelForm({ ...fuelForm, cost_code_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                  >
                    {costCodes.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.code} - {c.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="block text-slate-400 mb-1">Date *</label>
                    <input
                      type="date"
                      required
                      value={fuelForm.date}
                      onChange={(e) => setFuelForm({ ...fuelForm, date: e.target.value })}
                      className="w-full px-2 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1">Volume (Gal) *</label>
                    <input
                      type="number"
                      step="0.1"
                      required
                      value={fuelForm.volume}
                      onChange={(e) => setFuelForm({ ...fuelForm, volume: e.target.value })}
                      className="w-full px-2 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1">Price ($/Gal) *</label>
                    <input
                      type="number"
                      step="0.01"
                      required
                      value={fuelForm.unit_cost}
                      onChange={(e) => setFuelForm({ ...fuelForm, unit_cost: e.target.value })}
                      className="w-full px-2 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white font-mono"
                    />
                  </div>
                </div>
                <div className="pt-2 flex justify-end gap-2 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowFuelModal(false)}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-1.5 bg-purple-600 hover:bg-purple-500 text-white font-semibold rounded-lg shadow"
                  >
                    {submitting ? "Recording..." : "Record Fuel"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* MODAL 5: SCHEDULE SERVICE */}
        {showMaintModal && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-base font-bold text-white">Schedule Maintenance Work Order</h3>
                <button
                  onClick={() => setShowMaintModal(false)}
                  className="text-slate-400 hover:text-white text-lg"
                >
                  ✕
                </button>
              </div>
              <form onSubmit={handleCreateMaintenance} className="space-y-3 text-xs">
                <div>
                  <label className="block text-slate-400 mb-1">Select Machinery *</label>
                  <select
                    value={maintForm.equipment_id}
                    onChange={(e) => setMaintForm({ ...maintForm, equipment_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                  >
                    {equipmentList.map((eq) => (
                      <option key={eq.id} value={eq.id}>
                        {eq.internal_id ? `[${eq.internal_id}] ` : ""}{eq.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-slate-400 mb-1">Service Type *</label>
                    <select
                      value={maintForm.type}
                      onChange={(e) => setMaintForm({ ...maintForm, type: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                    >
                      <option value="PREVENTIVE">Preventive Maintenance</option>
                      <option value="CORRECTIVE">Corrective Repair</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1">Service Date *</label>
                    <input
                      type="date"
                      required
                      value={maintForm.date}
                      onChange={(e) => setMaintForm({ ...maintForm, date: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Work Description *</label>
                  <textarea
                    required
                    rows={2}
                    placeholder="e.g. 250-hour oil & hydraulic filter change"
                    value={maintForm.description}
                    onChange={(e) => setMaintForm({ ...maintForm, description: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-slate-400 mb-1">Downtime (Hours)</label>
                    <input
                      type="number"
                      step="0.5"
                      value={maintForm.duration_hours}
                      onChange={(e) => setMaintForm({ ...maintForm, duration_hours: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1">Service Cost ($) *</label>
                    <input
                      type="number"
                      step="0.01"
                      required
                      value={maintForm.cost}
                      onChange={(e) => setMaintForm({ ...maintForm, cost: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white font-mono"
                    />
                  </div>
                </div>
                <div className="pt-2 flex justify-end gap-2 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowMaintModal(false)}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-1.5 bg-rose-600 hover:bg-rose-500 text-white font-semibold rounded-lg shadow"
                  >
                    {submitting ? "Saving..." : "Save Work Order"}
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
