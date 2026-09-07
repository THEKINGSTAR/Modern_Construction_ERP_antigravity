'use client';

import React, { useState, useEffect } from 'react';
import AppLayout from '@/components/AppLayout';
import {
  getJournals,
  createJournal,
  postJournal,
  reverseJournal,
  getAccounts,
  getProjects,
  getCostCodes,
  getGLSummary,
  Journal,
  Account,
  Project,
  CostCode,
  GLSummary,
  CreateJournalInput,
} from '@/lib/api';

export default function JournalVouchersPage({ params }: { params: { locale: string } }) {
  const { locale } = params;
  const isAr = locale === 'ar';

  const [journals, setJournals] = useState<Journal[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [costCodes, setCostCodes] = useState<CostCode[]>([]);
  const [summary, setSummary] = useState<GLSummary | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Search
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedJournalId, setExpandedJournalId] = useState<string | null>(null);

  // Modal: New Journal Voucher
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [newJournalDate, setNewJournalDate] = useState(new Date().toISOString().split('T')[0]);
  const [newJournalRef, setNewJournalRef] = useState('');
  const [newJournalDesc, setNewJournalDesc] = useState('');
  const [newJournalLines, setNewJournalLines] = useState<Array<{
    account_id: string;
    debit: number;
    credit: number;
    project_id?: string;
    cost_code_id?: string;
  }>>([
    { account_id: '', debit: 0, credit: 0 },
    { account_id: '', debit: 0, credit: 0 },
  ]);

  // Modal: Reverse Journal
  const [isReverseOpen, setIsReverseOpen] = useState(false);
  const [targetReverseJournal, setTargetReverseJournal] = useState<Journal | null>(null);
  const [reversalDate, setReversalDate] = useState(new Date().toISOString().split('T')[0]);
  const [reversalReason, setReversalReason] = useState('');
  const [reversing, setReversing] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [jData, aData, pData, cData, sData] = await Promise.all([
        getJournals(),
        getAccounts(),
        getProjects().catch(() => []),
        getCostCodes().catch(() => []),
        getGLSummary().catch(() => null),
      ]);
      setJournals(jData);
      setAccounts(aData);
      setProjects(pData);
      setCostCodes(cData);
      setSummary(sData);
    } catch (err: any) {
      setError(err.message || 'Failed to load journals');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const totalDebitsCalc = newJournalLines.reduce((sum, l) => sum + (Number(l.debit) || 0), 0);
  const totalCreditsCalc = newJournalLines.reduce((sum, l) => sum + (Number(l.credit) || 0), 0);
  const diffCalc = Math.abs(totalDebitsCalc - totalCreditsCalc);
  const isFormBalanced = totalDebitsCalc > 0 && totalCreditsCalc > 0 && diffCalc < 0.0001;

  const handleAddLine = () => {
    setNewJournalLines([...newJournalLines, { account_id: '', debit: 0, credit: 0 }]);
  };

  const handleRemoveLine = (idx: number) => {
    if (newJournalLines.length <= 2) return;
    setNewJournalLines(newJournalLines.filter((_, i) => i !== idx));
  };

  const handleLineChange = (idx: number, field: string, val: any) => {
    const updated = [...newJournalLines];
    (updated[idx] as any)[field] = val;
    setNewJournalLines(updated);
  };

  const handleCreateJournal = async (autoPost: boolean) => {
    if (!newJournalDesc.trim()) {
      alert(isAr ? 'يرجى كتابة وصف قيد اليومية' : 'Please provide a journal description');
      return;
    }
    if (!isFormBalanced) {
      alert(isAr ? 'القيد غير متوازن! يجب أن يتساوى المدين مع الدائن' : 'Journal must balance! Debits must equal credits');
      return;
    }
    for (const l of newJournalLines) {
      if (!l.account_id) {
        alert(isAr ? 'يرجى اختيار الحساب لجميع البنود' : 'Please select an account for all lines');
        return;
      }
    }

    try {
      setSubmitting(true);
      const payload: CreateJournalInput = {
        date: newJournalDate,
        reference: newJournalRef || undefined,
        description: newJournalDesc,
        lines: newJournalLines.map((l) => ({
          account_id: l.account_id,
          debit: Number(l.debit) || 0,
          credit: Number(l.credit) || 0,
          project_id: l.project_id || undefined,
          cost_code_id: l.cost_code_id || undefined,
        })),
      };
      await createJournal(payload, autoPost);
      setIsCreateOpen(false);
      setNewJournalDesc('');
      setNewJournalRef('');
      setNewJournalLines([
        { account_id: '', debit: 0, credit: 0 },
        { account_id: '', debit: 0, credit: 0 },
      ]);
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to create journal');
    } finally {
      setSubmitting(false);
    }
  };

  const handlePost = async (journalId: string) => {
    if (!confirm(isAr ? 'هل أنت متأكد من ترحيل هذا القيد إلى دفتر الأستاذ العام؟' : 'Post this journal voucher to the General Ledger?')) return;
    try {
      await postJournal(journalId);
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to post journal');
    }
  };

  const handleExecuteReverse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetReverseJournal || !reversalReason.trim()) return;
    try {
      setReversing(true);
      await reverseJournal(targetReverseJournal.id, reversalDate, reversalReason);
      setIsReverseOpen(false);
      setTargetReverseJournal(null);
      setReversalReason('');
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to reverse journal');
    } finally {
      setReversing(false);
    }
  };

  const filteredJournals = journals.filter((j) => {
    const matchesStatus = statusFilter === 'ALL' || j.status === statusFilter;
    const matchesSearch =
      (j.reference || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      j.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'POSTED':
        return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300';
      case 'DRAFT':
        return 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300';
      case 'REVERSED':
        return 'bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-300';
      default:
        return 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300';
    }
  };

  return (
    <AppLayout locale={locale}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
              {isAr ? 'سندات قيود اليومية العامة' : 'General Ledger Journal Vouchers'}
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              {isAr
                ? 'إدخال ومراجعة وترحيل القيود المحاسبية المزدوجة المتوازنة'
                : 'Double-entry balanced accounting journal vouchers with real-time posting and reversal workflows'}
            </p>
          </div>
          <button
            onClick={() => setIsCreateOpen(true)}
            className="inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
          >
            <span className="mr-2">+</span>
            {isAr ? 'سند قيد جديد' : 'New Journal Voucher'}
          </button>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="text-sm font-medium text-slate-500 dark:text-slate-400">
              {isAr ? 'إجمالي السندات' : 'Total Vouchers'}
            </div>
            <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
              {summary ? summary.total_journals : journals.length}
            </div>
            <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {summary ? `${summary.posted_journals} Posted · ${summary.draft_journals} Drafts` : 'Financial Ledger'}
            </div>
          </div>

          <div className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="text-sm font-medium text-slate-500 dark:text-slate-400">
              {isAr ? 'حجم القيود المرحلة' : 'Posted Volume'}
            </div>
            <div className="mt-2 text-2xl font-bold text-emerald-600 dark:text-emerald-400">
              ${summary ? Number(summary.total_debits).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00'}
            </div>
            <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {isAr ? 'إجمالي المدين بالدفاتر' : 'Total Debits Posted'}
            </div>
          </div>

          <div className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="text-sm font-medium text-slate-500 dark:text-slate-400">
              {isAr ? 'قيد المسودات المعلقة' : 'Pending Drafts'}
            </div>
            <div className="mt-2 text-2xl font-bold text-amber-600 dark:text-amber-400">
              {summary ? summary.draft_journals : journals.filter((j) => j.status === 'DRAFT').length}
            </div>
            <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {isAr ? 'بانتظار المراجعة والترحيل' : 'Awaiting Review & Posting'}
            </div>
          </div>

          <div className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="text-sm font-medium text-slate-500 dark:text-slate-400">
              {isAr ? 'توازن القيود المزدوجة' : 'Double-Entry Integrity'}
            </div>
            <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span className={`inline-block w-3 h-3 rounded-full ${summary?.is_ledger_balanced ? 'bg-emerald-500' : 'bg-rose-500'}`} />
              {summary?.is_ledger_balanced ? (isAr ? 'متوازن دقيقاً 100%' : '100% Balanced') : (isAr ? 'اختلال بالقيد' : 'Variance Detected')}
            </div>
            <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {isAr ? 'مجموع المدين == مجموع الدائن' : 'Sum(Debits) == Sum(Credits)'}
            </div>
          </div>
        </div>

        {/* Filters & Search */}
        <div className="bg-white dark:bg-slate-800 p-4 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex flex-wrap gap-1">
            {['ALL', 'POSTED', 'DRAFT', 'REVERSED'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                  statusFilter === st
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-slate-100 dark:bg-slate-700/50 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                }`}
              >
                {st === 'ALL' && (isAr ? 'كافة السندات' : 'All Vouchers')}
                {st === 'POSTED' && (isAr ? 'مرحلة (POSTED)' : 'Posted')}
                {st === 'DRAFT' && (isAr ? 'مسودات (DRAFT)' : 'Drafts')}
                {st === 'REVERSED' && (isAr ? 'معكوسة (REVERSED)' : 'Reversed')}
              </button>
            ))}
          </div>

          <div className="relative min-w-[240px]">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder={isAr ? 'بحث بالرقم المرجعي أو البيان...' : 'Search reference or description...'}
              className="w-full pl-9 pr-3 py-1.5 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-900 dark:text-white"
            />
            <span className="absolute left-3 top-2 text-slate-400">🔍</span>
          </div>
        </div>

        {/* Journals Table */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-slate-500 dark:text-slate-400">
              <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full mx-auto mb-4" />
              {isAr ? 'جاري تحميل سندات القيد...' : 'Loading journal vouchers...'}
            </div>
          ) : error ? (
            <div className="p-8 text-center text-rose-500">
              <p>{error}</p>
              <button
                onClick={loadData}
                className="mt-3 px-4 py-1.5 bg-indigo-600 text-white text-xs font-semibold rounded-lg"
              >
                {isAr ? 'إعادة المحاولة' : 'Retry'}
              </button>
            </div>
          ) : filteredJournals.length === 0 ? (
            <div className="p-12 text-center text-slate-500 dark:text-slate-400">
              <span className="text-4xl">📒</span>
              <p className="mt-3 font-medium">
                {isAr ? 'لم يتم العثور على قيود مطابقة' : 'No journal vouchers found'}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
                <thead className="bg-slate-50 dark:bg-slate-900/60 text-xs uppercase text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
                  <tr>
                    <th className="px-5 py-3.5 font-semibold">{isAr ? 'التاريخ' : 'Date'}</th>
                    <th className="px-5 py-3.5 font-semibold">{isAr ? 'الرقم المرجعي' : 'Reference'}</th>
                    <th className="px-5 py-3.5 font-semibold">{isAr ? 'البيان المحاسبي' : 'Description'}</th>
                    <th className="px-5 py-3.5 font-semibold text-center">{isAr ? 'عدد البنود' : 'Lines'}</th>
                    <th className="px-5 py-3.5 font-semibold text-right">{isAr ? 'إجمالي القيد' : 'Voucher Amount'}</th>
                    <th className="px-5 py-3.5 font-semibold text-center">{isAr ? 'الحالة' : 'Status'}</th>
                    <th className="px-5 py-3.5 font-semibold text-center">{isAr ? 'الإجراءات' : 'Actions'}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                  {filteredJournals.map((j) => {
                    const isExpanded = expandedJournalId === j.id;
                    return (
                      <React.Fragment key={j.id}>
                        <tr className="hover:bg-slate-50/80 dark:hover:bg-slate-700/40 transition-colors">
                          <td className="px-5 py-3 font-mono text-xs">{j.date}</td>
                          <td className="px-5 py-3 font-mono font-bold text-indigo-600 dark:text-indigo-400">
                            {j.reference || j.id.slice(0, 8)}
                          </td>
                          <td className="px-5 py-3 max-w-xs truncate text-slate-900 dark:text-white font-medium">
                            {j.description}
                          </td>
                          <td className="px-5 py-3 text-center font-semibold">
                            {j.lines_count || j.lines.length}
                          </td>
                          <td className="px-5 py-3 text-right font-mono font-bold text-slate-900 dark:text-white">
                            ${Number(j.total_debit || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </td>
                          <td className="px-5 py-3 text-center">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${getStatusBadge(j.status)}`}>
                              {j.status}
                            </span>
                          </td>
                          <td className="px-5 py-3 text-center space-x-2">
                            <button
                              onClick={() => setExpandedJournalId(isExpanded ? null : j.id)}
                              className="text-xs px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 font-medium transition-colors"
                            >
                              {isExpanded ? (isAr ? 'إخفاء' : 'Hide') : (isAr ? 'عرض البنود' : 'Lines')}
                            </button>

                            {j.status === 'DRAFT' && (
                              <button
                                onClick={() => handlePost(j.id)}
                                className="text-xs px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-700 text-white font-medium transition-colors"
                              >
                                {isAr ? 'ترحيل' : 'Post'}
                              </button>
                            )}

                            {j.status === 'POSTED' && !j.reversal_journal_id && (
                              <button
                                onClick={() => {
                                  setTargetReverseJournal(j);
                                  setReversalReason(`Reversal of ${j.reference || j.id.slice(0, 8)}`);
                                  setIsReverseOpen(true);
                                }}
                                className="text-xs px-2.5 py-1 rounded bg-rose-50 hover:bg-rose-100 dark:bg-rose-900/30 dark:hover:bg-rose-900/50 text-rose-700 dark:text-rose-300 font-medium transition-colors"
                              >
                                {isAr ? 'عكس القيد' : 'Reverse'}
                              </button>
                            )}
                          </td>
                        </tr>

                        {/* Expanded Lines Drawer */}
                        {isExpanded && (
                          <tr className="bg-slate-50/70 dark:bg-slate-900/40">
                            <td colSpan={7} className="px-6 py-4">
                              <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4 shadow-inner">
                                <h4 className="text-xs font-bold uppercase text-slate-500 dark:text-slate-400 mb-3">
                                  {isAr ? 'بنود قيد اليومية' : 'Journal Lines Breakdown (Double-Entry Verification)'}
                                </h4>
                                <table className="w-full text-xs text-left">
                                  <thead>
                                    <tr className="border-b border-slate-200 dark:border-slate-700 text-slate-500">
                                      <th className="py-2">{isAr ? 'الحساب' : 'Account'}</th>
                                      <th className="py-2">{isAr ? 'المشروع' : 'Project Dimension'}</th>
                                      <th className="py-2">{isAr ? 'رمز التكلفة' : 'Cost Code'}</th>
                                      <th className="py-2 text-right">{isAr ? 'مدين ($)' : 'Debit ($)'}</th>
                                      <th className="py-2 text-right">{isAr ? 'دائن ($)' : 'Credit ($)'}</th>
                                    </tr>
                                  </thead>
                                  <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
                                    {j.lines.map((l, idx) => (
                                      <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-700/30">
                                        <td className="py-2 font-medium text-slate-800 dark:text-slate-200">
                                          <span className="font-mono text-indigo-600 dark:text-indigo-400 mr-2">
                                            {l.account_code || 'Acc'}
                                          </span>
                                          {l.account_name || l.account_id}
                                        </td>
                                        <td className="py-2 text-slate-500">
                                          {l.project_name || '-'}
                                        </td>
                                        <td className="py-2 font-mono text-slate-500">
                                          {l.cost_code_code || '-'}
                                        </td>
                                        <td className="py-2 text-right font-mono font-semibold text-slate-900 dark:text-white">
                                          {Number(l.debit) > 0 ? `$${Number(l.debit).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-'}
                                        </td>
                                        <td className="py-2 text-right font-mono font-semibold text-slate-900 dark:text-white">
                                          {Number(l.credit) > 0 ? `$${Number(l.credit).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-'}
                                        </td>
                                      </tr>
                                    ))}
                                    <tr className="border-t-2 border-slate-300 dark:border-slate-600 font-bold">
                                      <td colSpan={3} className="py-2 text-right uppercase text-slate-500">
                                        {isAr ? 'المجموع المتوازن' : 'Total (Debits == Credits):'}
                                      </td>
                                      <td className="py-2 text-right font-mono text-emerald-600 dark:text-emerald-400">
                                        ${Number(j.total_debit || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                      </td>
                                      <td className="py-2 text-right font-mono text-indigo-600 dark:text-indigo-400">
                                        ${Number(j.total_credit || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                      </td>
                                    </tr>
                                  </tbody>
                                </table>
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal: New Journal Voucher */}
        {isCreateOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 overflow-y-auto">
            <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl max-w-3xl w-full p-6 border border-slate-200 dark:border-slate-700 my-8">
              <div className="flex justify-between items-center mb-5">
                <div>
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                    {isAr ? 'إنشاء سند قيد يومية عامة' : 'New General Ledger Journal Voucher'}
                  </h3>
                  <p className="text-xs text-slate-500 mt-1">
                    {isAr ? 'أدخل بنود القيد بدقة وتأكد من توازن المدين مع الدائن' : 'Input balanced double-entry lines with project/cost code dimensions'}
                  </p>
                </div>
                <button
                  onClick={() => setIsCreateOpen(false)}
                  className="text-slate-400 hover:text-slate-500 text-lg"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-300 mb-1">
                      {isAr ? 'تاريخ السند' : 'Voucher Date'}
                    </label>
                    <input
                      type="date"
                      value={newJournalDate}
                      onChange={(e) => setNewJournalDate(e.target.value)}
                      className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-300 mb-1">
                      {isAr ? 'الرقم المرجعي (اختياري)' : 'Reference (Optional)'}
                    </label>
                    <input
                      type="text"
                      value={newJournalRef}
                      onChange={(e) => setNewJournalRef(e.target.value)}
                      placeholder="e.g. JRN-2026-009"
                      className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-300 mb-1">
                      {isAr ? 'البيان المحاسبي العام' : 'General Description'}
                    </label>
                    <input
                      type="text"
                      required
                      value={newJournalDesc}
                      onChange={(e) => setNewJournalDesc(e.target.value)}
                      placeholder="e.g. Monthly Accrual for Concrete Works"
                      className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                    />
                  </div>
                </div>

                {/* Lines Table */}
                <div className="mt-4 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
                  <div className="bg-slate-50 dark:bg-slate-900/60 px-4 py-2 text-xs font-bold uppercase text-slate-600 dark:text-slate-300 flex justify-between items-center">
                    <span>{isAr ? 'بنود القيد (مدين / دائن)' : 'Voucher Line Items'}</span>
                    <button
                      type="button"
                      onClick={handleAddLine}
                      className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded text-xs transition-colors"
                    >
                      + {isAr ? 'إضافة سطر' : 'Add Line'}
                    </button>
                  </div>

                  <div className="p-3 space-y-2 max-h-72 overflow-y-auto">
                    {newJournalLines.map((l, idx) => (
                      <div key={idx} className="flex flex-col sm:flex-row gap-2 items-center bg-slate-50/50 dark:bg-slate-900/30 p-2 rounded-lg">
                        <select
                          value={l.account_id}
                          onChange={(e) => handleLineChange(idx, 'account_id', e.target.value)}
                          className="flex-1 w-full px-2 py-1.5 text-xs bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded text-slate-900 dark:text-white"
                        >
                          <option value="">{isAr ? '-- اختر الحساب --' : '-- Select Account --'}</option>
                          {accounts.map((a) => (
                            <option key={a.id} value={a.id}>
                              {a.account_code} - {a.name} ({a.account_type})
                            </option>
                          ))}
                        </select>

                        <div className="w-full sm:w-28">
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            placeholder={isAr ? 'مدين' : 'Debit'}
                            value={l.debit || ''}
                            onChange={(e) => {
                              const val = parseFloat(e.target.value) || 0;
                              handleLineChange(idx, 'debit', val);
                              if (val > 0) handleLineChange(idx, 'credit', 0);
                            }}
                            className="w-full px-2 py-1.5 text-xs font-mono bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded text-slate-900 dark:text-white"
                          />
                        </div>

                        <div className="w-full sm:w-28">
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            placeholder={isAr ? 'دائن' : 'Credit'}
                            value={l.credit || ''}
                            onChange={(e) => {
                              const val = parseFloat(e.target.value) || 0;
                              handleLineChange(idx, 'credit', val);
                              if (val > 0) handleLineChange(idx, 'debit', 0);
                            }}
                            className="w-full px-2 py-1.5 text-xs font-mono bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded text-slate-900 dark:text-white"
                          />
                        </div>

                        <select
                          value={l.project_id || ''}
                          onChange={(e) => handleLineChange(idx, 'project_id', e.target.value || undefined)}
                          className="w-full sm:w-36 px-2 py-1.5 text-xs bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded text-slate-900 dark:text-white"
                        >
                          <option value="">{isAr ? '(المشروع اختياري)' : 'Project (Optional)'}</option>
                          {projects.map((p) => (
                            <option key={p.id} value={p.id}>{p.project_number} - {p.name}</option>
                          ))}
                        </select>

                        {newJournalLines.length > 2 && (
                          <button
                            type="button"
                            onClick={() => handleRemoveLine(idx)}
                            className="text-rose-500 hover:text-rose-700 p-1"
                          >
                            ✕
                          </button>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Balancing Status Footer */}
                  <div className="bg-slate-50 dark:bg-slate-900/60 p-3 border-t border-slate-200 dark:border-slate-700 flex flex-col sm:flex-row justify-between items-center gap-3">
                    <div className="flex items-center gap-2">
                      <span className={`inline-block w-3 h-3 rounded-full ${isFormBalanced ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                      <span className={`text-xs font-bold ${isFormBalanced ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}`}>
                        {isFormBalanced
                          ? (isAr ? 'القيد متوازن 100% (جاهز للترحيل)' : 'Voucher Balanced (Debits == Credits)')
                          : (isAr ? `غير متوازن! الفارق: $${diffCalc.toFixed(2)}` : `Unbalanced! Difference: $${diffCalc.toFixed(2)}`)}
                      </span>
                    </div>

                    <div className="flex gap-4 text-xs font-mono">
                      <div>
                        <span className="text-slate-500 mr-1">{isAr ? 'إجمالي المدين:' : 'Total Debits:'}</span>
                        <span className="font-bold text-slate-900 dark:text-white">${totalDebitsCalc.toFixed(2)}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 mr-1">{isAr ? 'إجمالي الدائن:' : 'Total Credits:'}</span>
                        <span className="font-bold text-slate-900 dark:text-white">${totalCreditsCalc.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-3 pt-4 border-t border-slate-200 dark:border-slate-700">
                  <button
                    type="button"
                    onClick={() => setIsCreateOpen(false)}
                    className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 rounded-lg"
                  >
                    {isAr ? 'إلغاء' : 'Cancel'}
                  </button>
                  <button
                    type="button"
                    disabled={submitting || !isFormBalanced}
                    onClick={() => handleCreateJournal(false)}
                    className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-200 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 rounded-lg disabled:opacity-50"
                  >
                    {isAr ? 'حفظ كمسودة (DRAFT)' : 'Save as Draft'}
                  </button>
                  <button
                    type="button"
                    disabled={submitting || !isFormBalanced}
                    onClick={() => handleCreateJournal(true)}
                    className="px-5 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg disabled:opacity-50"
                  >
                    {submitting ? (isAr ? 'جاري الحفظ والترحيل...' : 'Posting...') : (isAr ? 'ترحيل مباشر لدفتر الأستاذ' : 'Post Directly to GL')}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Modal: Reverse Journal */}
        {isReverseOpen && targetReverseJournal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl max-w-md w-full p-6 border border-slate-200 dark:border-slate-700">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                  {isAr ? 'عكس قيد اليومية (Reversal)' : 'Reverse Journal Voucher'}
                </h3>
                <button
                  onClick={() => setIsReverseOpen(false)}
                  className="text-slate-400 hover:text-slate-500 text-lg"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleExecuteReverse} className="space-y-4">
                <p className="text-xs text-slate-500">
                  {isAr
                    ? `سيتم إنشاء قيد عكسي مرحل فوراً يبادل جميع أسطر المدين والدائن لسند القيد ${targetReverseJournal.reference}`
                    : `This will generate an offsetting posted reversal journal swapping all debits and credits for ${targetReverseJournal.reference}.`}
                </p>

                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-300 mb-1">
                    {isAr ? 'تاريخ العكس' : 'Reversal Date'}
                  </label>
                  <input
                    type="date"
                    required
                    value={reversalDate}
                    onChange={(e) => setReversalDate(e.target.value)}
                    className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-300 mb-1">
                    {isAr ? 'سبب عكس القيد' : 'Reversal Reason / Explanation'}
                  </label>
                  <textarea
                    required
                    rows={3}
                    value={reversalReason}
                    onChange={(e) => setReversalReason(e.target.value)}
                    placeholder={isAr ? 'سبب إلغاء أو تصحيح القيد...' : 'Explanation for voucher reversal...'}
                    className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-slate-200 dark:border-slate-700">
                  <button
                    type="button"
                    onClick={() => setIsReverseOpen(false)}
                    className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 rounded-lg"
                  >
                    {isAr ? 'إلغاء' : 'Cancel'}
                  </button>
                  <button
                    type="submit"
                    disabled={reversing}
                    className="px-5 py-2 text-sm font-medium text-white bg-rose-600 hover:bg-rose-700 rounded-lg disabled:opacity-50"
                  >
                    {reversing ? (isAr ? 'جاري العكس...' : 'Reversing...') : (isAr ? 'تأكيد عكس القيد' : 'Confirm Reversal')}
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
