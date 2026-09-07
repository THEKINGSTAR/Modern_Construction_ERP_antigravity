'use client';

import React, { useState, useEffect } from 'react';
import AppLayout from '@/components/AppLayout';
import {
  getAccountingPeriods,
  closeAccountingPeriod,
  reopenAccountingPeriod,
  getGLSummary,
  AccountingPeriod,
  GLSummary,
} from '@/lib/api';

export default function AccountingPeriodsPage({ params }: { params: { locale: string } }) {
  const { locale } = params;
  const isAr = locale === 'ar';

  const [periods, setPeriods] = useState<AccountingPeriod[]>([]);
  const [summary, setSummary] = useState<GLSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  const [statusFilter, setStatusFilter] = useState<'ALL' | 'OPEN' | 'CLOSED'>('ALL');

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [perData, sumData] = await Promise.all([
        getAccountingPeriods(),
        getGLSummary().catch(() => null),
      ]);
      setPeriods(perData);
      setSummary(sumData);
    } catch (err: any) {
      setError(err.message || 'Failed to load accounting periods');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleClosePeriod = async (id: string, name: string) => {
    if (!confirm(isAr ? `إغلاق الفترة المحاسبية "${name}"؟ سيتم منع ترحيل قيود جديدة في هذا التاريخ.` : `Close accounting period "${name}"? Future postings in this date range will be prevented.`)) return;
    try {
      setActionLoadingId(id);
      await closeAccountingPeriod(id);
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to close period');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleReopenPeriod = async (id: string, name: string) => {
    if (!confirm(isAr ? `إعادة فتح الفترة المحاسبية "${name}"؟` : `Reopen accounting period "${name}"?`)) return;
    try {
      setActionLoadingId(id);
      await reopenAccountingPeriod(id);
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to reopen period');
    } finally {
      setActionLoadingId(null);
    }
  };

  const filteredPeriods = periods.filter((p) => {
    if (statusFilter === 'OPEN') return !p.is_closed;
    if (statusFilter === 'CLOSED') return p.is_closed;
    return true;
  });

  return (
    <AppLayout locale={locale}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
              {isAr ? 'الفترات المالية والإقفال الشهري' : 'Financial Periods & Month-End Close'}
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              {isAr
                ? 'إدارة جداول الإقفال الشهري والسنوي والتحكم بترحيل القيود المحاسبية'
                : 'Manage monthly accounting periods, lock historical periods, and control GL ledger postings'}
            </p>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="text-sm font-medium text-slate-500 dark:text-slate-400">
              {isAr ? 'إجمالي الفترات' : 'Total Periods'}
            </div>
            <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
              {summary ? summary.total_periods : periods.length}
            </div>
            <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {isAr ? 'دورة السنة المالية 2026' : 'Fiscal Year 2026 Cycle'}
            </div>
          </div>

          <div className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="text-sm font-medium text-slate-500 dark:text-slate-400">
              {isAr ? 'الفترات المفتوحة' : 'Open Periods'}
            </div>
            <div className="mt-2 text-2xl font-bold text-emerald-600 dark:text-emerald-400">
              {summary ? summary.open_periods : periods.filter((p) => !p.is_closed).length}
            </div>
            <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {isAr ? 'متاحة للترحيل والعمليات' : 'Active for Journal Postings'}
            </div>
          </div>

          <div className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="text-sm font-medium text-slate-500 dark:text-slate-400">
              {isAr ? 'الفترات المقفلة' : 'Closed Periods'}
            </div>
            <div className="mt-2 text-2xl font-bold text-indigo-600 dark:text-indigo-400">
              {summary ? summary.closed_periods : periods.filter((p) => p.is_closed).length}
            </div>
            <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {isAr ? 'مقفلة لمنع التعديل' : 'Locked from Ledger Modification'}
            </div>
          </div>

          <div className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="text-sm font-medium text-slate-500 dark:text-slate-400">
              {isAr ? 'السنة المالية الحالية' : 'Active Fiscal Year'}
            </div>
            <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
              FY-2026
            </div>
            <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              2026-01-01 {isAr ? 'إلى' : 'to'} 2026-12-31
            </div>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="flex gap-2">
          {(['ALL', 'OPEN', 'CLOSED'] as const).map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                statusFilter === st
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
              }`}
            >
              {st === 'ALL' && (isAr ? 'جميع الفترات' : 'All Periods')}
              {st === 'OPEN' && (isAr ? 'الفترات المفتوحة فقط' : 'Open Periods Only')}
              {st === 'CLOSED' && (isAr ? 'الفترات المقفلة' : 'Closed Historical Periods')}
            </button>
          ))}
        </div>

        {/* Periods Grid */}
        {loading ? (
          <div className="bg-white dark:bg-slate-800 p-12 text-center rounded-xl border border-slate-200 dark:border-slate-700">
            <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full mx-auto mb-4" />
            {isAr ? 'جاري تحميل الفترات المالية...' : 'Loading accounting periods...'}
          </div>
        ) : error ? (
          <div className="bg-white dark:bg-slate-800 p-8 text-center text-rose-500 rounded-xl border border-slate-200 dark:border-slate-700">
            <p>{error}</p>
            <button
              onClick={loadData}
              className="mt-3 px-4 py-1.5 bg-indigo-600 text-white text-xs font-semibold rounded-lg"
            >
              {isAr ? 'إعادة المحاولة' : 'Retry'}
            </button>
          </div>
        ) : filteredPeriods.length === 0 ? (
          <div className="bg-white dark:bg-slate-800 p-12 text-center rounded-xl border border-slate-200 dark:border-slate-700 text-slate-500">
            <span className="text-4xl">📅</span>
            <p className="mt-3 font-medium">
              {isAr ? 'لا توجد فترات مالية مطابقة' : 'No matching accounting periods found'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredPeriods.map((period) => (
              <div
                key={period.id}
                className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5 shadow-sm hover:border-slate-300 dark:hover:border-slate-600 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-bold text-slate-900 dark:text-white text-base">
                      {period.name}
                    </h3>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                        period.is_closed
                          ? 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300'
                          : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300'
                      }`}
                    >
                      {period.is_closed ? (isAr ? 'مقفل' : 'CLOSED') : (isAr ? 'مفتوح' : 'OPEN')}
                    </span>
                  </div>

                  <div className="mt-3 space-y-1.5 text-xs text-slate-500 dark:text-slate-400">
                    <div className="flex justify-between">
                      <span>{isAr ? 'تاريخ البداية:' : 'Start Date:'}</span>
                      <span className="font-mono font-medium text-slate-800 dark:text-slate-200">{period.start_date}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>{isAr ? 'تاريخ النهاية:' : 'End Date:'}</span>
                      <span className="font-mono font-medium text-slate-800 dark:text-slate-200">{period.end_date}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>{isAr ? 'السنة المالية:' : 'Fiscal Year:'}</span>
                      <span className="font-medium text-slate-800 dark:text-slate-200">{period.fiscal_year_name || 'FY-2026'}</span>
                    </div>
                  </div>
                </div>

                <div className="mt-5 pt-4 border-t border-slate-100 dark:border-slate-700/60 flex justify-end">
                  {period.is_closed ? (
                    <button
                      disabled={actionLoadingId === period.id}
                      onClick={() => handleReopenPeriod(period.id, period.name)}
                      className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 text-xs font-semibold rounded-lg transition-colors disabled:opacity-50"
                    >
                      {actionLoadingId === period.id ? (isAr ? 'جاري الفتح...' : 'Reopening...') : (isAr ? 'إعادة فتح الفترة' : 'Reopen Period')}
                    </button>
                  ) : (
                    <button
                      disabled={actionLoadingId === period.id}
                      onClick={() => handleClosePeriod(period.id, period.name)}
                      className="px-3 py-1.5 bg-rose-50 hover:bg-rose-100 dark:bg-rose-900/30 dark:hover:bg-rose-900/50 text-rose-700 dark:text-rose-300 text-xs font-semibold rounded-lg transition-colors disabled:opacity-50"
                    >
                      {actionLoadingId === period.id ? (isAr ? 'جاري الإقفال...' : 'Closing...') : (isAr ? 'إقفال الفترة المحاسبية' : 'Lock / Close Period')}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
