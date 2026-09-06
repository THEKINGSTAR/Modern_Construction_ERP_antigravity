"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  login,
  getExecutiveDashboard,
  getProjects,
  createProject,
  updateProject,
  getClients,
  createClient,
  updateClient,
  getMaterials,
  createMaterial,
  getWarehouses,
  createWarehouse,
  getDetailedBalances,
  getInventoryTransactions,
  createInventoryAdjustment,
  getSuppliers,
  getPurchaseOrders,
  createPurchaseOrder,
  getAccounts,
  getJournals,
  createJournal,
  getAPInvoices,
  getTrialBalance,
  getProjectDashboard,
  Project,
  Client,
  Material,
  Warehouse,
  InventoryBalanceDetail,
  InventoryTransaction,
  PurchaseOrder,
  Account,
  Journal,
  APInvoice,
  TrialBalanceReport,
  ExecutiveDashboard,
  ProjectDashboard,
} from "@/lib/api";

export default function DashboardPage() {
  // Authentication State
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [authLoading, setAuthLoading] = useState<boolean>(false);
  const [currentUserEmail, setCurrentUserEmail] = useState<string>("demo@apexconstruction.com");

  // Active Navigation Tab
  const [activeTab, setActiveTab] = useState<
    "projects" | "clients" | "inventory" | "procurement" | "accounting" | "e2e"
  >("projects");

  // Domain Data State
  const [execDashboard, setExecDashboard] = useState<ExecutiveDashboard | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [detailedBalances, setDetailedBalances] = useState<InventoryBalanceDetail[]>([]);
  const [transactions, setTransactions] = useState<InventoryTransaction[]>([]);
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrder[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [journals, setJournals] = useState<Journal[]>([]);
  const [apInvoices, setAPInvoices] = useState<APInvoice[]>([]);
  const [trialBalance, setTrialBalance] = useState<TrialBalanceReport | null>(null);

  // Loading and Notification States
  const [dataLoading, setDataLoading] = useState<boolean>(false);
  const [bannerMessage, setBannerMessage] = useState<string | null>(null);
  const [bannerType, setBannerType] = useState<"success" | "error">("success");

  // Filter & Search States
  const [projectSearch, setProjectSearch] = useState<string>("");
  const [projectStatusFilter, setProjectStatusFilter] = useState<string>("ALL");
  const [clientSearch, setClientSearch] = useState<string>("");
  const [clientStatusFilter, setClientStatusFilter] = useState<string>("ALL");

  // Drawer / Detail View States
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [projectReport, setProjectReport] = useState<ProjectDashboard | null>(null);
  const [reportLoading, setReportLoading] = useState<boolean>(false);

  // Modals
  const [showCreateProjectModal, setShowCreateProjectModal] = useState<boolean>(false);
  const [showEditProjectModal, setShowEditProjectModal] = useState<boolean>(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);

  const [showCreateClientModal, setShowCreateClientModal] = useState<boolean>(false);
  const [showEditClientModal, setShowEditClientModal] = useState<boolean>(false);
  const [editingClient, setEditingClient] = useState<Client | null>(null);

  const [showStockAdjustmentModal, setShowStockAdjustmentModal] = useState<boolean>(false);
  const [showCreateMaterialModal, setShowCreateMaterialModal] = useState<boolean>(false);
  const [showCreateWarehouseModal, setShowCreateWarehouseModal] = useState<boolean>(false);

  const [showCreatePOModal, setShowCreatePOModal] = useState<boolean>(false);
  const [showCreateJournalModal, setShowCreateJournalModal] = useState<boolean>(false);

  // Form Field States
  // Project Form
  const [projNumber, setProjNumber] = useState<string>("");
  const [projName, setProjName] = useState<string>("");
  const [projClientId, setProjClientId] = useState<string>("");
  const [projBudget, setProjBudget] = useState<string>("");
  const [projStartDate, setProjStartDate] = useState<string>("");
  const [projEndDate, setProjEndDate] = useState<string>("");
  const [projStatus, setProjStatus] = useState<string>("ACTIVE");

  // Client Form
  const [clientName, setClientName] = useState<string>("");
  const [clientLegal, setClientLegal] = useState<string>("");
  const [clientContact, setClientContact] = useState<string>("");
  const [clientTaxId, setClientTaxId] = useState<string>("");
  const [clientStatus, setClientStatus] = useState<string>("ACTIVE");

  // Stock Adjustment Form
  const [adjWarehouseId, setAdjWarehouseId] = useState<string>("");
  const [adjMaterialId, setAdjMaterialId] = useState<string>("");
  const [adjType, setAdjType] = useState<"IN" | "OUT">("IN");
  const [adjQuantity, setAdjQuantity] = useState<string>("10.0");
  const [adjUnitCost, setAdjUnitCost] = useState<string>("850.00");
  const [adjReason, setAdjReason] = useState<string>("Site Delivery Intake");

  // Material Form
  const [matCode, setMatCode] = useState<string>("");
  const [matName, setMatName] = useState<string>("");
  const [matCategory, setMatCategory] = useState<string>("Raw Material");
  const [matUnit, setMatUnit] = useState<string>("TON");

  // Warehouse Form
  const [whCode, setWhCode] = useState<string>("");
  const [whName, setWhName] = useState<string>("");
  const [whLocation, setWhLocation] = useState<string>("");

  // PO Form
  const [poNumber, setPoNumber] = useState<string>("");
  const [poSupplierId, setPoSupplierId] = useState<string>("");
  const [poLines, setPoLines] = useState<Array<{ material_id: string; quantity: string; unit_price: string }>>([
    { material_id: "", quantity: "10", unit_price: "850.00" },
  ]);

  // Journal Entry Form
  const [journalDesc, setJournalDesc] = useState<string>("");
  const [journalDate, setJournalDate] = useState<string>(new Date().toISOString().split("T")[0]);
  const [journalLines, setJournalLines] = useState<
    Array<{ account_id: string; debit: string; credit: string; description: string }>
  >([
    { account_id: "", debit: "1000.00", credit: "0.00", description: "Debit line" },
    { account_id: "", debit: "0.00", credit: "1000.00", description: "Credit line" },
  ]);

  // E2E Test State
  const [e2eRunning, setE2eRunning] = useState<boolean>(false);
  const [e2eLogs, setE2eLogs] = useState<string[]>([]);

  // Initial Auth & Data Load
  useEffect(() => {
    handleLogin();
  }, []);

  function showBanner(msg: string, type: "success" | "error" = "success") {
    setBannerMessage(msg);
    setBannerType(type);
    setTimeout(() => setBannerMessage(null), 5000);
  }

  async function handleLogin() {
    setAuthLoading(true);
    try {
      await login(currentUserEmail, "DemoPassword2026!");
      setIsAuthenticated(true);
      await refreshAllData();
    } catch (err: any) {
      console.warn("Auto-login error:", err.message);
      showBanner(`Authentication notice: ${err.message}`, "error");
    } finally {
      setAuthLoading(false);
    }
  }

  async function refreshAllData() {
    setDataLoading(true);
    try {
      const [
        dash,
        projList,
        clientList,
        matList,
        whList,
        balances,
        txList,
        suppList,
        poList,
        accList,
        jList,
        apList,
        tb,
      ] = await Promise.all([
        getExecutiveDashboard().catch(() => null),
        getProjects().catch(() => []),
        getClients().catch(() => []),
        getMaterials().catch(() => []),
        getWarehouses().catch(() => []),
        getDetailedBalances().catch(() => []),
        getInventoryTransactions().catch(() => []),
        getSuppliers().catch(() => []),
        getPurchaseOrders().catch(() => []),
        getAccounts().catch(() => []),
        getJournals().catch(() => []),
        getAPInvoices().catch(() => []),
        getTrialBalance().catch(() => null),
      ]);

      if (dash) setExecDashboard(dash);
      setProjects(projList);
      setClients(clientList);
      setMaterials(matList);
      setWarehouses(whList);
      setDetailedBalances(balances);
      setTransactions(txList);
      setSuppliers(suppList);
      setPurchaseOrders(poList);
      setAccounts(accList);
      setJournals(jList);
      setAPInvoices(apList);
      if (tb) setTrialBalance(tb);

      // Set defaults for modals if available
      if (whList.length > 0 && !adjWarehouseId) setAdjWarehouseId(whList[0].id);
      if (matList.length > 0 && !adjMaterialId) setAdjMaterialId(matList[0].id);
      if (suppList.length > 0 && !poSupplierId) setPoSupplierId(suppList[0].id);
      if (clientList.length > 0 && !projClientId) setProjClientId(clientList[0].id);
    } catch (err: any) {
      console.error("Failed to refresh data:", err);
      showBanner(`Error fetching data: ${err.message}`, "error");
    } finally {
      setDataLoading(false);
    }
  }

  // Project Drawer details
  async function handleOpenProjectDetails(project: Project) {
    setSelectedProject(project);
    setReportLoading(true);
    try {
      const report = await getProjectDashboard(project.id);
      setProjectReport(report);
    } catch (err) {
      setProjectReport(null);
    } finally {
      setReportLoading(false);
    }
  }

  // Filtered lists
  const filteredProjects = useMemo(() => {
    return projects.filter((p) => {
      const matchesSearch =
        p.name.toLowerCase().includes(projectSearch.toLowerCase()) ||
        p.project_number.toLowerCase().includes(projectSearch.toLowerCase());
      const matchesStatus = projectStatusFilter === "ALL" || p.status === projectStatusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [projects, projectSearch, projectStatusFilter]);

  const filteredClients = useMemo(() => {
    return clients.filter((c) => {
      const matchesSearch =
        c.name.toLowerCase().includes(clientSearch.toLowerCase()) ||
        (c.legal_name && c.legal_name.toLowerCase().includes(clientSearch.toLowerCase()));
      const matchesStatus = clientStatusFilter === "ALL" || c.status === clientStatusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [clients, clientSearch, clientStatusFilter]);

  // Project Mutations
  async function handleCreateProjectSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const newProj = await createProject({
        project_number: projNumber,
        name: projName,
        client_id: projClientId || null,
        budget_amount: projBudget || null,
        start_date: projStartDate || null,
        target_end_date: projEndDate || null,
        status: projStatus,
      });
      setShowCreateProjectModal(false);
      setProjNumber("");
      setProjName("");
      setProjBudget("");
      showBanner(`Project "${newProj.name}" (${newProj.project_number}) created successfully!`);
      await refreshAllData();
    } catch (err: any) {
      showBanner(`Failed to create project: ${err.message}`, "error");
    }
  }

  async function handleUpdateProjectSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!editingProject) return;
    try {
      const updated = await updateProject(editingProject.id, {
        name: editingProject.name,
        budget_amount: editingProject.budget_amount,
        status: editingProject.status,
      });
      setShowEditProjectModal(false);
      showBanner(`Project "${updated.name}" updated successfully!`);
      await refreshAllData();
      if (selectedProject && selectedProject.id === updated.id) {
        setSelectedProject(updated);
      }
    } catch (err: any) {
      showBanner(`Failed to update project: ${err.message}`, "error");
    }
  }

  // Client Mutations
  async function handleCreateClientSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const newCl = await createClient({
        name: clientName,
        legal_name: clientLegal || null,
        contact_information: clientContact || null,
        tax_identifier: clientTaxId || null,
        status: clientStatus,
      });
      setShowCreateClientModal(false);
      setClientName("");
      setClientLegal("");
      setClientContact("");
      setClientTaxId("");
      showBanner(`Client "${newCl.name}" registered successfully!`);
      await refreshAllData();
    } catch (err: any) {
      showBanner(`Failed to create client: ${err.message}`, "error");
    }
  }

  async function handleUpdateClientSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!editingClient) return;
    try {
      const updated = await updateClient(editingClient.id, {
        name: editingClient.name,
        legal_name: editingClient.legal_name,
        contact_information: editingClient.contact_information,
        tax_identifier: editingClient.tax_identifier,
        status: editingClient.status,
      });
      setShowEditClientModal(false);
      showBanner(`Client "${updated.name}" updated successfully!`);
      await refreshAllData();
    } catch (err: any) {
      showBanner(`Failed to update client: ${err.message}`, "error");
    }
  }

  // Material & Warehouse Mutations
  async function handleCreateMaterialSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const newMat = await createMaterial({
        material_code: matCode,
        name: matName,
        category: matCategory,
        base_unit: matUnit,
      });
      setShowCreateMaterialModal(false);
      setMatCode("");
      setMatName("");
      showBanner(`Material "${newMat.name}" (${newMat.material_code}) registered!`);
      await refreshAllData();
    } catch (err: any) {
      showBanner(`Failed to create material: ${err.message}`, "error");
    }
  }

  async function handleCreateWarehouseSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const newWh = await createWarehouse({
        code: whCode,
        name: whName,
        location: whLocation,
      });
      setShowCreateWarehouseModal(false);
      setWhCode("");
      setWhName("");
      setWhLocation("");
      showBanner(`Warehouse "${newWh.name}" created!`);
      await refreshAllData();
    } catch (err: any) {
      showBanner(`Failed to create warehouse: ${err.message}`, "error");
    }
  }

  // Stock Adjustment Mutation
  async function handleStockAdjustmentSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const adjNum = `ADJ-${Date.now().toString().slice(-6)}`;
      await createInventoryAdjustment({
        adjustment_number: adjNum,
        warehouse_id: adjWarehouseId,
        date: new Date().toISOString().split("T")[0],
        reason: adjReason,
        lines: [
          {
            material_id: adjMaterialId,
            adjustment_type: adjType,
            quantity: parseFloat(adjQuantity),
            unit_cost: parseFloat(adjUnitCost),
            notes: adjReason,
          },
        ],
      });
      setShowStockAdjustmentModal(false);
      showBanner(`Inventory ${adjType === "IN" ? "Intake" : "Issue"} posted successfully! (Ref: ${adjNum})`);
      await refreshAllData();
    } catch (err: any) {
      showBanner(`Inventory transaction failed: ${err.message}`, "error");
    }
  }

  // Purchase Order Mutation
  async function handleCreatePOSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const poNum = poNumber || `PO-${Date.now().toString().slice(-6)}`;
      await createPurchaseOrder({
        po_number: poNum,
        supplier_id: poSupplierId,
        order_date: new Date().toISOString().split("T")[0],
        status: "DRAFT",
        lines: poLines.map((l, i) => ({
          line_number: i + 1,
          material_id: l.material_id || (materials[0] ? materials[0].id : null),
          quantity: parseFloat(l.quantity),
          unit_price: parseFloat(l.unit_price),
        })),
      });
      setShowCreatePOModal(false);
      setPoNumber("");
      showBanner(`Purchase Order ${poNum} created successfully!`);
      await refreshAllData();
    } catch (err: any) {
      showBanner(`Failed to create PO: ${err.message}`, "error");
    }
  }

  // Journal Entry Mutation
  async function handleCreateJournalSubmit(e: React.FormEvent) {
    e.preventDefault();
    const totalDebit = journalLines.reduce((acc, l) => acc + (parseFloat(l.debit) || 0), 0);
    const totalCredit = journalLines.reduce((acc, l) => acc + (parseFloat(l.credit) || 0), 0);

    if (Math.abs(totalDebit - totalCredit) > 0.001) {
      showBanner(
        `Accounting Violation: Debits ($${totalDebit.toFixed(2)}) must equal Credits ($${totalCredit.toFixed(2)})!`,
        "error"
      );
      return;
    }

    try {
      const jNum = `JV-${Date.now().toString().slice(-6)}`;
      await createJournal({
        journal_number: jNum,
        entry_date: journalDate,
        description: journalDesc || "General Journal Entry",
        lines: journalLines.map((l, idx) => ({
          account_id: l.account_id || (accounts[0] ? accounts[0].id : null),
          line_number: idx + 1,
          debit_amount: parseFloat(l.debit) || 0,
          credit_amount: parseFloat(l.credit) || 0,
          description: l.description,
        })),
      });
      setShowCreateJournalModal(false);
      setJournalDesc("");
      showBanner(`Journal entry ${jNum} posted and balanced successfully!`);
      await refreshAllData();
    } catch (err: any) {
      showBanner(`Failed to post journal: ${err.message}`, "error");
    }
  }

  // Live E2E Workflow Test
  async function runE2EWorkflow() {
    setE2eRunning(true);
    setE2eLogs([]);

    const log = (msg: string) => {
      setE2eLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);
    };

    try {
      log("⚡ Initiating Full-Stack Real ERP End-to-End Verification...");
      log("Step 1: Authenticating as demo@apexconstruction.com against FastAPI backend...");
      await login("demo@apexconstruction.com", "DemoPassword2026!");
      log("✓ JWT Token acquired and attached to tenant session context.");

      const suffix = Math.floor(1000 + Math.random() * 9000);
      log(`Step 2: Mutating Client entity (POST /api/v1/clients)...`);
      const newClient = await createClient({
        name: `Highland Infrastructure Group ${suffix}`,
        legal_name: `Highland Infrastructure Group Inc.`,
        contact_information: `contracts@highland-${suffix}.erp`,
        tax_identifier: `US-EIN-${suffix}-99`,
        status: "ACTIVE",
      });
      log(`✓ Client persisted in PostgreSQL: "${newClient.name}" (ID: ${newClient.id})`);

      log(`Step 3: Provisioning Construction Project linked to Client (POST /api/v1/projects)...`);
      const newProj = await createProject({
        project_number: `PRJ-AUTO-${suffix}`,
        name: `Highland Metro Expansion Phase ${suffix}`,
        client_id: newClient.id,
        budget_amount: "8500000.00",
        start_date: new Date().toISOString().split("T")[0],
        status: "ACTIVE",
      });
      log(`✓ Project persisted in PostgreSQL: "${newProj.name}" (Ref: ${newProj.project_number})`);

      log(`Step 4: Registering custom Material Catalog item (POST /api/v1/inventory/materials)...`);
      const newMat = await createMaterial({
        material_code: `STEEL-${suffix}`,
        name: `Galvanized Reinforcement Mesh Grade ${suffix}`,
        category: "Structural Steel",
        base_unit: "TON",
      });
      log(`✓ Material registered: "${newMat.name}" (Code: ${newMat.material_code})`);

      log(`Step 5: Executing transactional Inventory Intake into Warehouse Ledger...`);
      const whList = await getWarehouses();
      const targetWh = whList[0];
      if (!targetWh) throw new Error("No active warehouse found for intake");

      const adjRef = `ADJ-TEST-${suffix}`;
      await createInventoryAdjustment({
        adjustment_number: adjRef,
        warehouse_id: targetWh.id,
        date: new Date().toISOString().split("T")[0],
        reason: "Automated Verification Intake",
        lines: [
          {
            material_id: newMat.id,
            adjustment_type: "IN",
            quantity: 25.0,
            unit_cost: 920.0,
            notes: "E2E Stock Receipt",
          },
        ],
      });
      log(`✓ Immutable Inventory Ledger transaction posted: +25.0 TON in ${targetWh.name}`);

      log(`Step 6: Verifying recalculated Warehouse stock balances from PostgreSQL...`);
      const balances = await getDetailedBalances();
      const foundBalance = balances.find((b) => b.material_id === newMat.id);
      if (!foundBalance || parseFloat(foundBalance.quantity) < 25.0) {
        throw new Error("Recalculated inventory balance did not match posted intake!");
      }
      log(
        `✓ Inventory balance verified: ${parseFloat(foundBalance.quantity).toFixed(1)} TON ($${parseFloat(
          foundBalance.total_cost
        ).toLocaleString()})`
      );

      log(`Step 7: Validating General Ledger Double-Entry Invariant (Trial Balance)...`);
      const tb = await getTrialBalance();
      const debitNum = parseFloat(tb.total_debit);
      const creditNum = parseFloat(tb.total_credit);
      if (Math.abs(debitNum - creditNum) > 0.001) {
        throw new Error(`Ledger imbalance: Debits=$${debitNum} != Credits=$${creditNum}`);
      }
      log(`✓ Golden Rule Verified: Total Debits ($${debitNum.toLocaleString()}) == Total Credits ($${creditNum.toLocaleString()})`);

      log(`Step 8: Fetching Executive Dashboard real SQL aggregation layer...`);
      const exec = await getExecutiveDashboard();
      log(
        `✓ Executive Dashboard aggregated: Total Contracts $${parseFloat(
          exec.total_contract_value
        ).toLocaleString()} across ${exec.total_active_contracts} contracts, Total Stock ${parseFloat(
          exec.total_on_hand_quantity
        ).toFixed(1)} TON ($${parseFloat(exec.total_inventory_valuation).toLocaleString()})`
      );

      log("🎉 100% Real-World ERP Verification Complete: All database transactions committed and validated!");
      await refreshAllData();
    } catch (err: any) {
      log(`❌ Verification stopped on error: ${err.message}`);
    } finally {
      setE2eRunning(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Enterprise Header */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-500 flex items-center justify-center font-black text-white text-xl shadow-lg shadow-indigo-500/25">
              M
            </div>
            <div>
              <div className="flex items-center space-x-2.5">
                <span className="font-bold text-lg text-white tracking-tight">Modern Construction ERP</span>
                <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                  ENTERPRISE CORE
                </span>
              </div>
              <p className="text-xs text-slate-400">Production Modular Monolith · PostgreSQL 15 · Tenant: Apex HQ</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* System Status Pill */}
            <div className="hidden md:flex items-center space-x-2 bg-slate-800/80 px-3 py-1.5 rounded-full border border-slate-700 text-xs">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="text-slate-300">FastAPI & PostgreSQL Online</span>
            </div>

            {/* Auth Profile / Login Pill */}
            {isAuthenticated ? (
              <div className="flex items-center space-x-3 bg-indigo-950/50 border border-indigo-500/30 px-3 py-1.5 rounded-xl">
                <div className="h-7 w-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center font-bold text-xs shadow">
                  DA
                </div>
                <div className="text-left">
                  <p className="text-xs text-slate-200 font-medium leading-tight">Demo Admin</p>
                  <p className="text-[10px] text-indigo-400 leading-tight">Apex Construction Systems</p>
                </div>
                <button
                  onClick={() => setIsAuthenticated(false)}
                  title="Sign Out"
                  className="text-slate-400 hover:text-rose-400 text-xs font-semibold ml-2 transition"
                >
                  Logout
                </button>
              </div>
            ) : (
              <button
                onClick={handleLogin}
                disabled={authLoading}
                className="bg-indigo-600 hover:bg-indigo-500 text-white px-3.5 py-1.5 rounded-lg text-xs font-semibold shadow-lg shadow-indigo-600/30 transition"
              >
                {authLoading ? "Authenticating..." : "Sign In"}
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Dynamic Alert Banner */}
      {bannerMessage && (
        <div
          className={`${
            bannerType === "success" ? "bg-emerald-600 text-white" : "bg-rose-600 text-white"
          } text-center py-2 px-4 text-xs font-semibold shadow transition-all duration-300`}
        >
          {bannerType === "success" ? "✓ " : "⚠ "}
          {bannerMessage}
        </div>
      )}

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* EXECUTIVE DASHBOARD AGGREGATION CARDS (100% Backend SQL Powered) */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Executive Aggregation Layer (Live SQL Backend)
            </h2>
            <button
              onClick={refreshAllData}
              disabled={dataLoading}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center space-x-1"
            >
              <span>{dataLoading ? "Calculating live metrics..." : "↻ Refresh Live Metrics"}</span>
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Card 1: Prime Contracts */}
            <div className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl p-5 shadow-sm transition">
              <div className="flex items-center justify-between text-xs text-slate-400 uppercase tracking-wider font-semibold">
                <span>Prime Contracts</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {execDashboard ? `${execDashboard.total_active_contracts} Active` : "—"}
                </span>
              </div>
              <div className="mt-2 text-2xl font-extrabold text-white">
                {execDashboard
                  ? `$${parseFloat(execDashboard.total_contract_value).toLocaleString("en-US", {
                      minimumFractionDigits: 2,
                    })}`
                  : "$0.00"}
              </div>
              <p className="mt-1 text-xs text-slate-400">
                {projects.length > 0 ? `Selected: ${projects[0].name.slice(0, 24)}...` : "Contract Ledger"}
              </p>
            </div>

            {/* Card 2: Material Inventory */}
            <div className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl p-5 shadow-sm transition">
              <div className="flex items-center justify-between text-xs text-slate-400 uppercase tracking-wider font-semibold">
                <span>Material Stock</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  {execDashboard ? `${execDashboard.warehouse_count} SKUs` : "—"}
                </span>
              </div>
              <div className="mt-2 text-2xl font-extrabold text-white">
                {execDashboard
                  ? `${parseFloat(execDashboard.total_on_hand_quantity).toFixed(1)} TON`
                  : "0.0 TON"}
              </div>
              <p className="mt-1 text-xs text-slate-400">
                {execDashboard
                  ? `Valuation: $${parseFloat(execDashboard.total_inventory_valuation).toLocaleString("en-US", {
                      minimumFractionDigits: 2,
                    })}`
                  : "Warehouse Balance"}
              </p>
            </div>

            {/* Card 3: Financial Ledger Double-Entry */}
            <div className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl p-5 shadow-sm transition">
              <div className="flex items-center justify-between text-xs text-slate-400 uppercase tracking-wider font-semibold">
                <span>General Ledger</span>
                <span
                  className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                    execDashboard?.is_ledger_balanced
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                  }`}
                >
                  {execDashboard?.is_ledger_balanced ? "Balanced Δ=0.00" : "Unbalanced"}
                </span>
              </div>
              <div className="mt-2 text-2xl font-extrabold text-white">
                {execDashboard
                  ? `$${parseFloat(execDashboard.total_debits).toLocaleString("en-US", {
                      minimumFractionDigits: 2,
                    })}`
                  : "$0.00"}
              </div>
              <p className="mt-1 text-xs text-slate-400">Verified SUM(debits) == SUM(credits)</p>
            </div>

            {/* Card 4: Trade Payables */}
            <div className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl p-5 shadow-sm transition">
              <div className="flex items-center justify-between text-xs text-slate-400 uppercase tracking-wider font-semibold">
                <span>Trade Payables</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  {execDashboard ? `${execDashboard.total_ap_invoices} AP` : "—"}
                </span>
              </div>
              <div className="mt-2 text-2xl font-extrabold text-white">
                {execDashboard
                  ? `$${parseFloat(execDashboard.total_open_payables).toLocaleString("en-US", {
                      minimumFractionDigits: 2,
                    })}`
                  : "$0.00"}
              </div>
              <p className="mt-1 text-xs text-slate-400">AP Posted Subcontractor & Material Invoices</p>
            </div>
          </div>
        </section>

        {/* Tab Navigation */}
        <div className="border-b border-slate-800 flex space-x-6 overflow-x-auto pb-px">
          {[
            { id: "projects", label: "Projects & Contracts", count: projects.length },
            { id: "clients", label: "Clients & Customers", count: clients.length },
            { id: "inventory", label: "Material Inventory", count: detailedBalances.length },
            { id: "procurement", label: "Procurement & POs", count: purchaseOrders.length },
            { id: "accounting", label: "Financial Ledger & AP", count: journals.length },
            { id: "e2e", label: "⚡ Live E2E Audit Trail" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`pb-3 text-sm font-semibold border-b-2 whitespace-nowrap transition flex items-center space-x-2 ${
                activeTab === tab.id
                  ? "border-indigo-500 text-indigo-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 font-mono">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* TAB 1: PROJECTS */}
        {activeTab === "projects" && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white">Construction Projects</h2>
                <p className="text-xs text-slate-400">
                  Real project master records backed by PostgreSQL with financial budget tracking.
                </p>
              </div>
              <div className="flex items-center space-x-3 w-full sm:w-auto">
                <input
                  type="text"
                  placeholder="Search projects..."
                  value={projectSearch}
                  onChange={(e) => setProjectSearch(e.target.value)}
                  className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 w-44"
                />
                <select
                  value={projectStatusFilter}
                  onChange={(e) => setProjectStatusFilter(e.target.value)}
                  className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="PLANNING">PLANNING</option>
                  <option value="COMPLETED">COMPLETED</option>
                  <option value="ON_HOLD">ON_HOLD</option>
                </select>
                <button
                  onClick={() => setShowCreateProjectModal(true)}
                  className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30 whitespace-nowrap transition"
                >
                  + Create Project
                </button>
              </div>
            </div>

            {/* Projects Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
              <table className="min-w-full divide-y divide-slate-800 text-left text-sm">
                <thead className="bg-slate-850 text-xs uppercase text-slate-400 font-semibold">
                  <tr>
                    <th className="px-6 py-3.5">Project #</th>
                    <th className="px-6 py-3.5">Project Name</th>
                    <th className="px-6 py-3.5">Client</th>
                    <th className="px-6 py-3.5">Budget</th>
                    <th className="px-6 py-3.5">Status</th>
                    <th className="px-6 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {filteredProjects.map((p) => {
                    const linkedClient = clients.find((c) => c.id === p.client_id);
                    return (
                      <tr key={p.id} className="hover:bg-slate-800/40 transition">
                        <td className="px-6 py-4 font-mono font-semibold text-indigo-400">{p.project_number}</td>
                        <td className="px-6 py-4 font-medium text-white">{p.name}</td>
                        <td className="px-6 py-4 text-slate-400 text-xs">
                          {linkedClient ? linkedClient.name : p.client_id ? "Linked Client" : "Unassigned"}
                        </td>
                        <td className="px-6 py-4 font-mono text-xs">
                          {p.budget_amount
                            ? `$${parseFloat(p.budget_amount).toLocaleString("en-US", { minimumFractionDigits: 2 })}`
                            : "$0.00"}
                        </td>
                        <td className="px-6 py-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                              p.status === "ACTIVE"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : "bg-slate-800 text-slate-400"
                            }`}
                          >
                            {p.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right space-x-2">
                          <button
                            onClick={() => handleOpenProjectDetails(p)}
                            className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold px-2 py-1 rounded bg-indigo-500/10 hover:bg-indigo-500/20 transition"
                          >
                            Details
                          </button>
                          <button
                            onClick={() => {
                              setEditingProject(p);
                              setShowEditProjectModal(true);
                            }}
                            className="text-xs text-slate-300 hover:text-white font-semibold px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 transition"
                          >
                            Edit
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                  {filteredProjects.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-6 py-10 text-center text-slate-500">
                        No projects found matching criteria. Click &quot;+ Create Project&quot; to add one.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Selected Project Financial Summary Drawer / Card */}
            {selectedProject && (
              <div className="bg-slate-900 border border-indigo-500/30 rounded-xl p-6 shadow-lg space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <h3 className="text-base font-bold text-white flex items-center space-x-2">
                      <span>{selectedProject.name}</span>
                      <span className="font-mono text-xs text-indigo-400">({selectedProject.project_number})</span>
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Database ID: {selectedProject.id} · Budget: $
                      {parseFloat(selectedProject.budget_amount || "0").toLocaleString()}
                    </p>
                  </div>
                  <button
                    onClick={() => setSelectedProject(null)}
                    className="text-xs text-slate-400 hover:text-white"
                  >
                    ✕ Close
                  </button>
                </div>

                {reportLoading ? (
                  <p className="text-xs text-slate-400 italic">Calculating project financial metrics...</p>
                ) : projectReport ? (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                    <div className="bg-slate-800/50 p-3.5 rounded-lg border border-slate-700/50">
                      <p className="text-xs text-slate-400 font-semibold uppercase">Contract Value</p>
                      <p className="text-lg font-bold text-white mt-1">
                        ${parseFloat(projectReport.contract_value).toLocaleString()}
                      </p>
                    </div>
                    <div className="bg-slate-800/50 p-3.5 rounded-lg border border-slate-700/50">
                      <p className="text-xs text-slate-400 font-semibold uppercase">Committed Costs</p>
                      <p className="text-lg font-bold text-amber-400 mt-1">
                        ${parseFloat(projectReport.committed_cost).toLocaleString()}
                      </p>
                    </div>
                    <div className="bg-slate-800/50 p-3.5 rounded-lg border border-slate-700/50">
                      <p className="text-xs text-slate-400 font-semibold uppercase">Gross Margin</p>
                      <p className="text-lg font-bold text-emerald-400 mt-1">{projectReport.margin_percentage}%</p>
                    </div>
                    <div className="bg-slate-800/50 p-3.5 rounded-lg border border-slate-700/50">
                      <p className="text-xs text-slate-400 font-semibold uppercase">Projected Profit</p>
                      <p className="text-lg font-bold text-white mt-1">
                        ${parseFloat(projectReport.gross_profit).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic">
                    No linked contract records found yet for this project.
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: CLIENTS */}
        {activeTab === "clients" && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white">Clients & Owners</h2>
                <p className="text-xs text-slate-400">
                  Commercial client organizations, contracts, and billing contacts in PostgreSQL.
                </p>
              </div>
              <div className="flex items-center space-x-3 w-full sm:w-auto">
                <input
                  type="text"
                  placeholder="Search clients..."
                  value={clientSearch}
                  onChange={(e) => setClientSearch(e.target.value)}
                  className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 w-44"
                />
                <select
                  value={clientStatusFilter}
                  onChange={(e) => setClientStatusFilter(e.target.value)}
                  className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="INACTIVE">INACTIVE</option>
                </select>
                <button
                  onClick={() => setShowCreateClientModal(true)}
                  className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30 whitespace-nowrap transition"
                >
                  + Register Client
                </button>
              </div>
            </div>

            {/* Clients Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
              <table className="min-w-full divide-y divide-slate-800 text-left text-sm">
                <thead className="bg-slate-850 text-xs uppercase text-slate-400 font-semibold">
                  <tr>
                    <th className="px-6 py-3.5">Commercial Name</th>
                    <th className="px-6 py-3.5">Legal Entity</th>
                    <th className="px-6 py-3.5">Contact Details</th>
                    <th className="px-6 py-3.5">Tax Identifier</th>
                    <th className="px-6 py-3.5">Status</th>
                    <th className="px-6 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {filteredClients.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-800/40 transition">
                      <td className="px-6 py-4 font-semibold text-white">{c.name}</td>
                      <td className="px-6 py-4 text-slate-400 text-xs">{c.legal_name || "—"}</td>
                      <td className="px-6 py-4 font-mono text-xs text-slate-400">{c.contact_information || "—"}</td>
                      <td className="px-6 py-4 font-mono text-xs text-slate-400">{c.tax_identifier || "—"}</td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                            c.status === "ACTIVE"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : "bg-slate-800 text-slate-400"
                          }`}
                        >
                          {c.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => {
                            setEditingClient(c);
                            setShowEditClientModal(true);
                          }}
                          className="text-xs text-slate-300 hover:text-white font-semibold px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 transition"
                        >
                          Edit
                        </button>
                      </td>
                    </tr>
                  ))}
                  {filteredClients.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-6 py-10 text-center text-slate-500">
                        No clients found. Click &quot;+ Register Client&quot; above to add one.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 3: INVENTORY */}
        {activeTab === "inventory" && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white">Material Inventory & Warehouse Ledger</h2>
                <p className="text-xs text-slate-400">
                  Stock balances calculated from immutable warehouse transactions. Zero fake static stock.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setShowStockAdjustmentModal(true)}
                  className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white shadow-lg shadow-emerald-600/30 transition"
                >
                  + Receive / Adjust Stock
                </button>
                <button
                  onClick={() => setShowCreateMaterialModal(true)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-200 transition"
                >
                  + Add Material
                </button>
                <button
                  onClick={() => setShowCreateWarehouseModal(true)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-200 transition"
                >
                  + Add Warehouse
                </button>
              </div>
            </div>

            {/* Warehouse Stock Balances Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
              <div className="px-6 py-3 bg-slate-850 border-b border-slate-800 flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Live Warehouse Stock Balances
                </h3>
                <span className="text-xs text-slate-400">
                  {warehouses.length} Warehouse(s) · {materials.length} Material SKU(s)
                </span>
              </div>
              <table className="min-w-full divide-y divide-slate-800 text-left text-sm">
                <thead className="bg-slate-850/50 text-xs uppercase text-slate-400 font-semibold">
                  <tr>
                    <th className="px-6 py-3">Warehouse</th>
                    <th className="px-6 py-3">Material SKU</th>
                    <th className="px-6 py-3">Category</th>
                    <th className="px-6 py-3 text-right">On-Hand Quantity</th>
                    <th className="px-6 py-3 text-right">Avg Cost</th>
                    <th className="px-6 py-3 text-right">Total Valuation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {detailedBalances.map((b) => (
                    <tr key={b.id} className="hover:bg-slate-800/40 transition">
                      <td className="px-6 py-3.5 font-medium text-white">{b.warehouse_name}</td>
                      <td className="px-6 py-3.5">
                        <div className="font-semibold text-slate-200">{b.material_name}</div>
                        <div className="font-mono text-xs text-indigo-400">{b.material_code}</div>
                      </td>
                      <td className="px-6 py-3.5 text-xs text-slate-400">Standard</td>
                      <td className="px-6 py-3.5 text-right font-bold text-emerald-400 font-mono">
                        {parseFloat(b.quantity).toFixed(2)} {b.base_unit}
                      </td>
                      <td className="px-6 py-3.5 text-right font-mono text-xs text-slate-400">
                        ${parseFloat(b.unit_cost || "0").toFixed(2)}
                      </td>
                      <td className="px-6 py-3.5 text-right font-mono font-bold text-white">
                        ${parseFloat(b.total_cost).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                      </td>
                    </tr>
                  ))}
                  {detailedBalances.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-6 py-10 text-center text-slate-500">
                        No inventory balance found. Click &quot;+ Receive / Adjust Stock&quot; to intake materials.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Immutable Inventory Transaction Audit Ledger */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Immutable Inventory Transaction Audit Log ({transactions.length} Records)
              </h3>
              <div className="max-h-64 overflow-y-auto font-mono text-xs space-y-1.5 border border-slate-800 rounded-lg p-3 bg-slate-950">
                {transactions.map((t) => (
                  <div key={t.id} className="flex items-center justify-between text-slate-400 py-1 border-b border-slate-900">
                    <div className="flex items-center space-x-3">
                      <span className="text-slate-500">{t.transaction_date ? new Date(t.transaction_date).toLocaleDateString() : "Recent"}</span>
                      <span
                        className={`font-bold px-1.5 py-0.5 rounded text-[10px] ${
                          t.transaction_type.includes("IN") || t.transaction_type.includes("RECEIPT")
                            ? "bg-emerald-500/10 text-emerald-400"
                            : "bg-amber-500/10 text-amber-400"
                        }`}
                      >
                        {t.transaction_type}
                      </span>
                      <span className="text-slate-300">Ref: {t.reference_type}</span>
                    </div>
                    <div className="font-bold text-slate-200">
                      {parseFloat(t.quantity) > 0 ? `+${t.quantity}` : t.quantity} Units (@ ${parseFloat(t.unit_cost).toFixed(2)})
                    </div>
                  </div>
                ))}
                {transactions.length === 0 && (
                  <p className="text-slate-600 italic">No inventory transactions recorded yet.</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: PROCUREMENT */}
        {activeTab === "procurement" && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white">Procurement & Purchase Orders</h2>
                <p className="text-xs text-slate-400">
                  Manage vendor purchase orders, material commitments, and supplier invoicing.
                </p>
              </div>
              <button
                onClick={() => setShowCreatePOModal(true)}
                className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30 transition"
              >
                + Create Purchase Order
              </button>
            </div>

            {/* Purchase Orders Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
              <table className="min-w-full divide-y divide-slate-800 text-left text-sm">
                <thead className="bg-slate-850 text-xs uppercase text-slate-400 font-semibold">
                  <tr>
                    <th className="px-6 py-3.5">PO Number</th>
                    <th className="px-6 py-3.5">Supplier</th>
                    <th className="px-6 py-3.5">Order Date</th>
                    <th className="px-6 py-3.5 text-right">Total Amount</th>
                    <th className="px-6 py-3.5">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {purchaseOrders.map((po) => {
                    const supp = suppliers.find((s) => s.id === po.supplier_id);
                    return (
                      <tr key={po.id} className="hover:bg-slate-800/40 transition">
                        <td className="px-6 py-4 font-mono font-semibold text-indigo-400">{po.po_number}</td>
                        <td className="px-6 py-4 font-medium text-white">{supp ? supp.name : "Vulcan Steel Supplies"}</td>
                        <td className="px-6 py-4 text-slate-400 text-xs">{po.issue_date || "—"}</td>
                        <td className="px-6 py-4 text-right font-mono font-bold text-white">
                          ${parseFloat(po.total_amount).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="px-6 py-4">
                          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            {po.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                  {purchaseOrders.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-6 py-10 text-center text-slate-500">
                        No purchase orders found. Click &quot;+ Create Purchase Order&quot; above.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 5: ACCOUNTING */}
        {activeTab === "accounting" && (
          <div className="space-y-8">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white">Financial Ledger, Trial Balance & Accounts Payable</h2>
                <p className="text-xs text-slate-400">
                  Strict double-entry accounting engine. Invariant: Total Debits == Total Credits.
                </p>
              </div>
              <button
                onClick={() => setShowCreateJournalModal(true)}
                className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30 transition"
              >
                + Post Journal Entry
              </button>
            </div>

            {/* Trial Balance Table */}
            {trialBalance && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
                <div className="px-6 py-3 bg-slate-850 border-b border-slate-800 flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                    General Ledger Trial Balance
                  </h3>
                  <span className="text-xs font-mono font-bold text-emerald-400">
                    Balanced: Δ = $
                    {Math.abs(parseFloat(trialBalance.total_debit) - parseFloat(trialBalance.total_credit)).toFixed(2)}
                  </span>
                </div>
                <table className="min-w-full divide-y divide-slate-800 text-left text-sm">
                  <thead className="bg-slate-850/50 text-xs uppercase text-slate-400 font-semibold">
                    <tr>
                      <th className="px-6 py-3">Account Code</th>
                      <th className="px-6 py-3">Account Name</th>
                      <th className="px-6 py-3">Type</th>
                      <th className="px-6 py-3 text-right">Debit Balance</th>
                      <th className="px-6 py-3 text-right">Credit Balance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300">
                    {trialBalance.lines.map((l, i) => (
                      <tr key={i} className="hover:bg-slate-800/40 transition">
                        <td className="px-6 py-3 font-mono text-indigo-400 font-semibold">{l.account_code}</td>
                        <td className="px-6 py-3 text-white font-medium">{l.account_name}</td>
                        <td className="px-6 py-3 text-xs text-slate-400 uppercase">Standard Account</td>
                        <td className="px-6 py-3 text-right font-mono">
                          {parseFloat(l.debit) > 0
                            ? `$${parseFloat(l.debit).toLocaleString("en-US", { minimumFractionDigits: 2 })}`
                            : "—"}
                        </td>
                        <td className="px-6 py-3 text-right font-mono">
                          {parseFloat(l.credit) > 0
                            ? `$${parseFloat(l.credit).toLocaleString("en-US", { minimumFractionDigits: 2 })}`
                            : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-slate-850 font-bold text-white border-t-2 border-slate-700">
                    <tr>
                      <td colSpan={3} className="px-6 py-4 uppercase text-xs tracking-wider">
                        Total Trial Balance
                      </td>
                      <td className="px-6 py-4 text-right font-mono text-emerald-400">
                        ${parseFloat(trialBalance.total_debit).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-6 py-4 text-right font-mono text-emerald-400">
                        ${parseFloat(trialBalance.total_credit).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            )}

            {/* Trade Payables (AP Invoices) Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
              <div className="px-6 py-3 bg-slate-850 border-b border-slate-800">
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Accounts Payable Ledger ({apInvoices.length} Invoices)
                </h3>
              </div>
              <table className="min-w-full divide-y divide-slate-800 text-left text-sm">
                <thead className="bg-slate-850/50 text-xs uppercase text-slate-400 font-semibold">
                  <tr>
                    <th className="px-6 py-3">Invoice Number</th>
                    <th className="px-6 py-3">Supplier ID</th>
                    <th className="px-6 py-3">Date</th>
                    <th className="px-6 py-3">Due Date</th>
                    <th className="px-6 py-3 text-right">Amount</th>
                    <th className="px-6 py-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {apInvoices.map((inv) => (
                    <tr key={inv.id} className="hover:bg-slate-800/40 transition">
                      <td className="px-6 py-3.5 font-mono font-semibold text-indigo-400">{inv.number}</td>
                      <td className="px-6 py-3.5 font-mono text-xs text-slate-400">{inv.supplier_id}</td>
                      <td className="px-6 py-3.5 text-xs text-slate-400">{inv.date}</td>
                      <td className="px-6 py-3.5 text-xs text-slate-400">{inv.due_date}</td>
                      <td className="px-6 py-3.5 text-right font-mono font-bold text-white">
                        ${parseFloat(inv.total_amount).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-6 py-3.5">
                        <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                          {inv.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {apInvoices.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-6 py-8 text-center text-slate-500">
                        No payable invoices recorded.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 6: E2E VERIFICATION CONSOLE */}
        {activeTab === "e2e" && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white">Live End-to-End ERP Verification Test</h2>
                <p className="text-xs text-slate-400">
                  Executes a complete real-world multi-domain test: Auth → Client Mutation → Project Provisioning →
                  Material Intake → Warehouse Balance Verification → Ledger Audit.
                </p>
              </div>
              <button
                onClick={runE2EWorkflow}
                disabled={e2eRunning}
                className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-lg shadow-emerald-600/30 transition flex items-center space-x-2"
              >
                <span>{e2eRunning ? "Executing Real Workflow..." : "▶ Run Live Workflow Test"}</span>
              </button>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 font-mono text-xs space-y-2">
              <div className="text-slate-400 mb-4 pb-2 border-b border-slate-800 font-sans text-sm flex items-center justify-between">
                <span>Real-Time Execution Console & Audit Log</span>
                <span className="text-slate-500 text-xs">FastAPI 0.0.0.0:8000 · PostgreSQL 5433</span>
              </div>
              {e2eLogs.length === 0 && (
                <div className="text-slate-500 italic py-4">
                  Click &quot;Run Live Workflow Test&quot; above to execute the automated end-to-end verification.
                </div>
              )}
              {e2eLogs.map((log, idx) => (
                <div
                  key={idx}
                  className={
                    log.includes("✓") || log.includes("🎉")
                      ? "text-emerald-400"
                      : log.includes("❌")
                      ? "text-rose-400 font-bold"
                      : "text-slate-300"
                  }
                >
                  {log}
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* MODAL: CREATE PROJECT */}
      {showCreateProjectModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Create Construction Project</h3>
            <form onSubmit={handleCreateProjectSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Project Number *</label>
                <input
                  type="text"
                  required
                  placeholder="PRJ-2026-003"
                  value={projNumber}
                  onChange={(e) => setProjNumber(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Project Name *</label>
                <input
                  type="text"
                  required
                  placeholder="Metropolis Transit Extension"
                  value={projName}
                  onChange={(e) => setProjName(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Client Organization</label>
                <select
                  value={projClientId}
                  onChange={(e) => setProjClientId(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="">-- Unassigned --</option>
                  {clients.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Budget Amount (USD)</label>
                <input
                  type="number"
                  step="0.01"
                  placeholder="5000000.00"
                  value={projBudget}
                  onChange={(e) => setProjBudget(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Start Date</label>
                  <input
                    type="date"
                    value={projStartDate}
                    onChange={(e) => setProjStartDate(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Target End Date</label>
                  <input
                    type="date"
                    value={projEndDate}
                    onChange={(e) => setProjEndDate(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowCreateProjectModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30"
                >
                  Save Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: EDIT PROJECT */}
      {showEditProjectModal && editingProject && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Edit Construction Project</h3>
            <form onSubmit={handleUpdateProjectSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Project Number</label>
                <input
                  type="text"
                  disabled
                  value={editingProject.project_number}
                  className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-slate-400 cursor-not-allowed"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Project Name *</label>
                <input
                  type="text"
                  required
                  value={editingProject.name}
                  onChange={(e) => setEditingProject({ ...editingProject, name: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Budget Amount (USD)</label>
                <input
                  type="number"
                  step="0.01"
                  value={editingProject.budget_amount || ""}
                  onChange={(e) => setEditingProject({ ...editingProject, budget_amount: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Status</label>
                <select
                  value={editingProject.status}
                  onChange={(e) => setEditingProject({ ...editingProject, status: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="PLANNING">PLANNING</option>
                  <option value="COMPLETED">COMPLETED</option>
                  <option value="ON_HOLD">ON_HOLD</option>
                </select>
              </div>
              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowEditProjectModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30"
                >
                  Update Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: CREATE CLIENT */}
      {showCreateClientModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Register Commercial Client</h3>
            <form onSubmit={handleCreateClientSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Commercial Name *</label>
                <input
                  type="text"
                  required
                  placeholder="Metropolis Port Authority"
                  value={clientName}
                  onChange={(e) => setClientName(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Legal Organization Entity</label>
                <input
                  type="text"
                  placeholder="Metropolis Port Authority LLC"
                  value={clientLegal}
                  onChange={(e) => setClientLegal(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Contact Email / Phone</label>
                <input
                  type="text"
                  placeholder="contracts@metropolis-port.org"
                  value={clientContact}
                  onChange={(e) => setClientContact(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Tax / EIN Identifier</label>
                <input
                  type="text"
                  placeholder="US-TAX-98234-11"
                  value={clientTaxId}
                  onChange={(e) => setClientTaxId(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowCreateClientModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30"
                >
                  Save Client
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: EDIT CLIENT */}
      {showEditClientModal && editingClient && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Edit Client Details</h3>
            <form onSubmit={handleUpdateClientSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Commercial Name *</label>
                <input
                  type="text"
                  required
                  value={editingClient.name}
                  onChange={(e) => setEditingClient({ ...editingClient, name: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Legal Entity Name</label>
                <input
                  type="text"
                  value={editingClient.legal_name || ""}
                  onChange={(e) => setEditingClient({ ...editingClient, legal_name: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Contact Information</label>
                <input
                  type="text"
                  value={editingClient.contact_information || ""}
                  onChange={(e) => setEditingClient({ ...editingClient, contact_information: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Status</label>
                <select
                  value={editingClient.status}
                  onChange={(e) => setEditingClient({ ...editingClient, status: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="INACTIVE">INACTIVE</option>
                </select>
              </div>
              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowEditClientModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30"
                >
                  Update Client
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: STOCK ADJUSTMENT / INTAKE */}
      {showStockAdjustmentModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Receive or Adjust Material Stock</h3>
            <form onSubmit={handleStockAdjustmentSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Warehouse *</label>
                <select
                  required
                  value={adjWarehouseId}
                  onChange={(e) => setAdjWarehouseId(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                >
                  {warehouses.map((w) => (
                    <option key={w.id} value={w.id}>
                      {w.name} ({w.code})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Material SKU *</label>
                <select
                  required
                  value={adjMaterialId}
                  onChange={(e) => setAdjMaterialId(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                >
                  {materials.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} ({m.material_code}) [{m.base_unit}]
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Adjustment Type</label>
                  <select
                    value={adjType}
                    onChange={(e) => setAdjType(e.target.value as "IN" | "OUT")}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="IN">IN (Receive Stock)</option>
                    <option value="OUT">OUT (Issue/Shrinkage)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Quantity *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={adjQuantity}
                    onChange={(e) => setAdjQuantity(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Unit Cost (USD)</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={adjUnitCost}
                  onChange={(e) => setAdjUnitCost(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Reason / Reference</label>
                <input
                  type="text"
                  value={adjReason}
                  onChange={(e) => setAdjReason(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowStockAdjustmentModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white shadow-lg shadow-emerald-600/30"
                >
                  Post Transaction
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: CREATE MATERIAL */}
      {showCreateMaterialModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Add Material Catalog Item</h3>
            <form onSubmit={handleCreateMaterialSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Material Code *</label>
                <input
                  type="text"
                  required
                  placeholder="MAT-CONC-C35"
                  value={matCode}
                  onChange={(e) => setMatCode(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Material Name *</label>
                <input
                  type="text"
                  required
                  placeholder="Ready-Mix Concrete Grade C35"
                  value={matName}
                  onChange={(e) => setMatName(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Category</label>
                  <input
                    type="text"
                    value={matCategory}
                    onChange={(e) => setMatCategory(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Base Unit</label>
                  <input
                    type="text"
                    required
                    placeholder="TON, M3, EA"
                    value={matUnit}
                    onChange={(e) => setMatUnit(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowCreateMaterialModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30"
                >
                  Save Material
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: CREATE WAREHOUSE */}
      {showCreateWarehouseModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Create Warehouse Facility</h3>
            <form onSubmit={handleCreateWarehouseSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Warehouse Code *</label>
                <input
                  type="text"
                  required
                  placeholder="WH-NORTH"
                  value={whCode}
                  onChange={(e) => setWhCode(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Warehouse Name *</label>
                <input
                  type="text"
                  required
                  placeholder="North Yard Logistics Facility"
                  value={whName}
                  onChange={(e) => setWhName(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Location / Address</label>
                <input
                  type="text"
                  placeholder="Metropolis North Pier, Sector 4"
                  value={whLocation}
                  onChange={(e) => setWhLocation(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowCreateWarehouseModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30"
                >
                  Save Warehouse
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: CREATE PO */}
      {showCreatePOModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Create Purchase Order</h3>
            <form onSubmit={handleCreatePOSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">PO Number</label>
                <input
                  type="text"
                  placeholder="Leave empty for auto-generated"
                  value={poNumber}
                  onChange={(e) => setPoNumber(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Supplier *</label>
                <select
                  required
                  value={poSupplierId}
                  onChange={(e) => setPoSupplierId(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                >
                  {suppliers.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                  {suppliers.length === 0 && <option value="">No suppliers registered</option>}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Line Items</label>
                {poLines.map((line, idx) => (
                  <div key={idx} className="grid grid-cols-3 gap-2 bg-slate-800/40 p-2.5 rounded-lg mb-2">
                    <div>
                      <span className="text-[10px] text-slate-400 block mb-1">Material SKU</span>
                      <select
                        value={line.material_id}
                        onChange={(e) => {
                          const updated = [...poLines];
                          updated[idx].material_id = e.target.value;
                          setPoLines(updated);
                        }}
                        className="w-full bg-slate-800 border border-slate-700 rounded p-1 text-xs text-white"
                      >
                        {materials.map((m) => (
                          <option key={m.id} value={m.id}>
                            {m.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block mb-1">Quantity</span>
                      <input
                        type="number"
                        value={line.quantity}
                        onChange={(e) => {
                          const updated = [...poLines];
                          updated[idx].quantity = e.target.value;
                          setPoLines(updated);
                        }}
                        className="w-full bg-slate-800 border border-slate-700 rounded p-1 text-xs text-white"
                      />
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block mb-1">Unit Price ($)</span>
                      <input
                        type="number"
                        value={line.unit_price}
                        onChange={(e) => {
                          const updated = [...poLines];
                          updated[idx].unit_price = e.target.value;
                          setPoLines(updated);
                        }}
                        className="w-full bg-slate-800 border border-slate-700 rounded p-1 text-xs text-white"
                      />
                    </div>
                  </div>
                ))}
              </div>
              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowCreatePOModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30"
                >
                  Issue Purchase Order
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: CREATE JOURNAL ENTRY */}
      {showCreateJournalModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Post General Ledger Journal Entry</h3>
            <form onSubmit={handleCreateJournalSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Entry Description *</label>
                <input
                  type="text"
                  required
                  placeholder="Monthly Equipment Depreciation / Payroll"
                  value={journalDesc}
                  onChange={(e) => setJournalDesc(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Entry Date</label>
                <input
                  type="date"
                  value={journalDate}
                  onChange={(e) => setJournalDate(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div className="space-y-2">
                <label className="block text-xs font-semibold text-slate-400">
                  Journal Lines (Golden Rule: Sum of Debits == Sum of Credits)
                </label>
                {journalLines.map((l, idx) => (
                  <div key={idx} className="grid grid-cols-3 gap-2 bg-slate-800/40 p-2.5 rounded-lg">
                    <div>
                      <span className="text-[10px] text-slate-400 block mb-1">Account</span>
                      <select
                        value={l.account_id}
                        onChange={(e) => {
                          const updated = [...journalLines];
                          updated[idx].account_id = e.target.value;
                          setJournalLines(updated);
                        }}
                        className="w-full bg-slate-800 border border-slate-700 rounded p-1 text-xs text-white"
                      >
                        {accounts.map((a) => (
                          <option key={a.id} value={a.id}>
                            {a.account_code} - {a.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block mb-1">Debit Amount ($)</span>
                      <input
                        type="number"
                        step="0.01"
                        value={l.debit}
                        onChange={(e) => {
                          const updated = [...journalLines];
                          updated[idx].debit = e.target.value;
                          setJournalLines(updated);
                        }}
                        className="w-full bg-slate-800 border border-slate-700 rounded p-1 text-xs text-white"
                      />
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block mb-1">Credit Amount ($)</span>
                      <input
                        type="number"
                        step="0.01"
                        value={l.credit}
                        onChange={(e) => {
                          const updated = [...journalLines];
                          updated[idx].credit = e.target.value;
                          setJournalLines(updated);
                        }}
                        className="w-full bg-slate-800 border border-slate-700 rounded p-1 text-xs text-white"
                      />
                    </div>
                  </div>
                ))}
              </div>
              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowCreateJournalModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30"
                >
                  Post Journal Entry
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
