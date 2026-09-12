"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface AppLayoutProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  locale?: string;
}

export default function AppLayout({ children, title, subtitle, actions }: AppLayoutProps) {
  const pathname = usePathname() || "/";
  const locale = pathname.startsWith("/ar") ? "ar" : "en";

  const navSections = [
    {
      title: "Management Reporting & Analytics",
      items: [
        { label: "Analytics Hub", path: `/${locale}/reports`, icon: "📈" },
        { label: "AP Aging", path: `/${locale}/reports/ap-aging`, icon: "⏳" },
        { label: "Trial Balance", path: `/${locale}/reports/trial-balance`, icon: "⚖️" },
      ],
    },
    {
      title: "Workforce Management",
      items: [
        { label: "Employees & Directory", path: `/${locale}/hr`, icon: "👥" },
      ],
    },
    {
      title: "Core Operations",
      items: [
        { label: "Executive Dashboard", path: `/${locale}`, icon: "📊" },
        { label: "Projects Directory", path: `/${locale}/projects`, icon: "📁" },
        { label: "Prime Contracts", path: `/${locale}/contracts`, icon: "📜" },
        { label: "Client Registry", path: `/${locale}/clients`, icon: "🏢" },
      ],
    },
    {
      title: "Commercial & Subcontracts",
      items: [
        { label: "Trade Subcontracts", path: `/${locale}/subcontracts`, icon: "🤝" },
        { label: "Variation / Change Orders", path: `/${locale}/change-orders`, icon: "🔄" },
        { label: "Progress Billings & Claims", path: `/${locale}/payment-applications`, icon: "📑" },
      ],
    },
    {
      title: "Procurement & Supply Chain",
      items: [
        { label: "Suppliers & Vendors", path: `/${locale}/suppliers`, icon: "🏭" },
        { label: "Purchase Requisitions", path: `/${locale}/requisitions`, icon: "📋" },
        { label: "RFQs & Tenders", path: `/${locale}/rfqs`, icon: "📬" },
        { label: "Purchase Orders", path: `/${locale}/purchase-orders`, icon: "📦" },
      ],
    },
    {
      title: "Inventory & Site Logistics",
      items: [
        { label: "Materials Master", path: `/${locale}/materials`, icon: "🧱" },
        { label: "Warehouses & Yards", path: `/${locale}/warehouses`, icon: "🏢" },
        { label: "Goods Receipts (GRN)", path: `/${locale}/goods-receipts`, icon: "📥" },
        { label: "Material Issues", path: `/${locale}/material-issues`, icon: "📤" },
        { label: "Equipment & Fleet", path: `/${locale}/equipment`, icon: "🚜" },
      ],
    },
    {
      title: "Accounts Payable",
      items: [
        { label: "AP Invoices & 3-Way Match", path: `/${locale}/ap/invoices`, icon: "🧾" },
        { label: "Vendor Payments", path: `/${locale}/ap/payments`, icon: "💳" },
      ],
    },
    {
      title: "Accounts Receivable & Billing",
      items: [
        { label: "Client Invoices (AR)", path: `/${locale}/ar/invoices`, icon: "🧾" },
        { label: "Customer Collections", path: `/${locale}/ar/receipts`, icon: "💰" },
      ],
    },
    {
      title: "General Ledger & Accounting",
      items: [
        { label: "Chart of Accounts", path: `/${locale}/accounting/accounts`, icon: "📑" },
        { label: "Journal Vouchers", path: `/${locale}/accounting/journals`, icon: "📒" },
        { label: "Financial Periods", path: `/${locale}/accounting/periods`, icon: "📅" },
        { label: "Financial Statements", path: `/${locale}/accounting/reports`, icon: "📊" },
      ],
    },
    {
      title: "Project Controls & Estimating",
      items: [
        { label: "Cost Control & EVM", path: `/${locale}/cost-control`, icon: "🎯" },
        { label: "Work Breakdown (WBS)", path: `/${locale}/wbs`, icon: "🌲" },
        { label: "Standard Cost Codes", path: `/${locale}/cost-codes`, icon: "🏷️" },
        { label: "Bill of Quantities (BOQ)", path: `/${locale}/boq`, icon: "📋" },
        { label: "Cost Estimating", path: `/${locale}/estimates`, icon: "📐" },
        { label: "Project Budgets", path: `/${locale}/budgets`, icon: "💰" },
      ],
    },
  ];

  const switchLocale = locale === "en" ? "ar" : "en";
  const switchPath = pathname.replace(`/${locale}`, `/${switchLocale}`);

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 font-sans overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between shrink-0 shadow-xl z-20">
        <div>
          {/* Logo & Brand */}
          <div className="h-16 flex items-center px-6 border-b border-slate-800 gap-3 bg-gradient-to-r from-slate-900 to-slate-950">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center font-black text-slate-950 text-xl shadow-lg shadow-amber-500/20">
              🏗️
            </div>
            <div>
              <div className="text-sm font-bold tracking-tight text-white flex items-center gap-1.5">
                Modern ERP
                <span className="text-[10px] bg-amber-500/20 text-amber-400 font-mono px-1.5 py-0.5 rounded border border-amber-500/30">
                  REAL
                </span>
              </div>
              <div className="text-[11px] text-slate-400 font-medium">Apex Construction Systems</div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-4 overflow-y-auto max-h-[calc(100vh-170px)]">
            {navSections.map((sec) => (
              <div key={sec.title} className="space-y-1">
                <div className="text-[10px] uppercase font-bold tracking-wider text-slate-500 px-3 py-1">
                  {sec.title}
                </div>
                {sec.items.map((item) => {
                  const isActive =
                    item.path === `/${locale}`
                      ? pathname === `/${locale}` || pathname === "/"
                      : pathname.startsWith(item.path);
                  return (
                    <Link
                      key={item.path}
                      href={item.path}
                      className={`flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                        isActive
                          ? "bg-amber-500/10 text-amber-400 font-semibold border border-amber-500/20 shadow-sm"
                          : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                      }`}
                    >
                      <span className="text-base">{item.icon}</span>
                      <span className="truncate">{item.label}</span>
                      {isActive && (
                        <span className="ml-auto w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                      )}
                    </Link>
                  );
                })}
              </div>
            ))}
          </nav>
        </div>

        {/* Tenant & DB Status Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60 text-xs">
          <div className="flex items-center gap-2 mb-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span className="text-[11px] font-mono text-emerald-400">PostgreSQL 15 Live</span>
          </div>
          <div className="text-[11px] text-slate-400 truncate">
            Tenant: <strong className="text-slate-200">Apex Contracting LLC</strong>
          </div>
          <div className="text-[10px] text-slate-500 mt-1">Commercial Operations Active</div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-16 bg-slate-900/80 backdrop-blur border-b border-slate-800 flex items-center justify-between px-8 z-10 shrink-0">
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
              {title || "Modern Construction ERP"}
            </h1>
            {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
          </div>

          <div className="flex items-center gap-4">
            {actions}

            {/* Language Switcher */}
            <Link
              href={switchPath}
              className="text-xs px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium border border-slate-700 transition"
            >
              {locale === "en" ? "العربية (AR)" : "English (EN)"}
            </Link>

            {/* User Profile */}
            <div className="flex items-center gap-2 pl-3 border-l border-slate-800">
              <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-amber-400">
                DA
              </div>
              <div className="hidden md:block text-left">
                <div className="text-xs font-medium text-slate-200 leading-tight">Demo Admin</div>
                <div className="text-[10px] text-slate-500 font-mono">admin@apexconstruction.com</div>
              </div>
            </div>
          </div>
        </header>

        {/* Scrollable Page Body */}
        <main className="flex-1 overflow-y-auto p-8 bg-slate-950">
          <div className="max-w-7xl mx-auto space-y-6">{children}</div>
        </main>
      </div>
    </div>
  );
}
