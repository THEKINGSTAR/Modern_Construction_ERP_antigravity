'use client';

import React, { useState, useEffect } from 'react';
import AppLayout from '@/components/AppLayout';
import {
  getAccounts,
  createAccount,
  getGLSummary,
  Account,
  GLSummary,
  CreateAccountInput,
} from '@/lib/api';

export default function ChartOfAccountsPage({ params }: { params: { locale: string } }) {
  const { locale } = params;
  const isAr = locale === 'ar';

  const [accounts, setAccounts] = useState<Account[]>([]);
  const [summary, setSummary] = useState<GLSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Search
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  // Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [newAccount, setNewAccount] = useState<CreateAccountInput>({
    account_code: '',
    name: '',
    account_type: 'ASSET',
    is_control_account: false,
  });

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [accData, sumData] = await Promise.all([
        getAccounts(),
        getGLSummary().catch(() => null),
      ]);
      setAccounts(accData);
      setSummary(sumData);
    } catch (err: any) {
      setError(err.message || 'Failed to load chart of accounts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAccount.account_code || !newAccount.name) return;
    try {
      setSubmitting(true);
      await createAccount(newAccount);
      setIsModalOpen(false);
      setNewAccount({
        account_code: '',
        name: '',
        account_type: 'ASSET',
        is_control_account: false,
      });
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to create account');
    } finally {
      setSubmitting(false);
    }
  };

  const filteredAccounts = accounts.filter((acc) => {
    const matchesType = selectedType === 'ALL' || acc.account_type === selectedType;
    const matchesSearch =
      acc.account_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      acc.name.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesType && matchesSearch;
  });

  const getTypeBadge = (type?: string) => {
    switch (type) {
      case 'ASSET':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300';
      case 'LIABILITY':
        return 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300';
      case 'EQUITY':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300';
      case 'REVENUE':
        return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300';
      case 'EXPENSE':
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
              {isAr ? 'دليل الحسابات' : 'Chart of Accounts'}
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              {isAr
                ? 'الهيكل المالي الموحد للحسابات والأرصدة المحاسبية العامة'
                : 'Standardized general ledger account hierarchy and live balance verification'}
            </p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
          >
            <span className="mr-2">+</span>
            {isAr ? 'إضافة حساب جديد' : 'New Account'}
          </button>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="text-sm font-medium text-slate-500 dark:text-slate-400">
              {isAr ? 'إجمالي الحسابات' : 'Total Accounts'}
            </div>
            <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
              {summary ? summary.total_accounts : accounts.length}
            </div>
            <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {summary ? `${summary.asset_accounts} Assets · ${summary.liability_accounts} Liabilities` : 'Active General Ledger'}
            </div>
          </div>

          <div className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="text-sm font-medium text-slate-500 dark:text-slate-400">
              {isAr ? 'إجمالي المدين بالدفتر' : 'Total Debits'}
            </div>
            <div className="mt-2 text-2xl font-bold text-emerald-600 dark:text-emerald-400">
              ${summary ? Number(summary.total_debits).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00'}
            </div>
            <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {isAr ? 'قيود اليومية المرحلة' : 'Posted Journal Lines'}
            </div>
          </div>

          <div className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="text-sm font-medium text-slate-500 dark:text-slate-400">
              {isAr ? 'إجمالي الدائن بالدفتر' : 'Total Credits'}
            </div>
            <div className="mt-2 text-2xl font-bold text-indigo-600 dark:text-indigo-400">
              ${summary ? Number(summary.total_credits).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00'}
            </div>
            <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {isAr ? 'قيود اليومية المرحلة' : 'Posted Journal Lines'}
            </div>
          </div>

          <div className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="text-sm font-medium text-slate-500 dark:text-slate-400">
              {isAr ? 'حالة توازن ميزان المراجعة' : 'Trial Balance Status'}
            </div>
            <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span className={`inline-block w-3 h-3 rounded-full ${summary?.is_ledger_balanced ? 'bg-emerald-500' : 'bg-rose-500'}`} />
              {summary?.is_ledger_balanced ? (isAr ? 'متوازن دقيقاً' : 'Balanced (Debits == Credits)') : (isAr ? 'غير متوازن' : 'Unbalanced')}
            </div>
            <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {isAr ? 'القاعدة الذهبية للمحاسبة' : 'Double-Entry Golden Rule'}
            </div>
          </div>
        </div>

        {/* Filters & Search */}
        <div className="bg-white dark:bg-slate-800 p-4 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          {/* Account Type Tabs */}
          <div className="flex flex-wrap gap-1">
            {['ALL', 'ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE'].map((t) => (
              <button
                key={t}
                onClick={() => setSelectedType(t)}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                  selectedType === t
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-slate-100 dark:bg-slate-700/50 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                }`}
              >
                {t === 'ALL' && (isAr ? 'الكل' : 'All Accounts')}
                {t === 'ASSET' && (isAr ? 'أصول (1000s)' : 'Assets (1000s)')}
                {t === 'LIABILITY' && (isAr ? 'التزامات (2000s)' : 'Liabilities (2000s)')}
                {t === 'EQUITY' && (isAr ? 'حقوق ملكية (3000s)' : 'Equity (3000s)')}
                {t === 'REVENUE' && (isAr ? 'إيرادات (4000s)' : 'Revenue (4000s)')}
                {t === 'EXPENSE' && (isAr ? 'مصروفات (5000s)' : 'Expenses (5000s)')}
              </button>
            ))}
          </div>

          {/* Search Input */}
          <div className="relative min-w-[240px]">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder={isAr ? 'بحث برقم الحساب أو الاسم...' : 'Search by code or account name...'}
              className="w-full pl-9 pr-3 py-1.5 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-900 dark:text-white"
            />
            <span className="absolute left-3 top-2 text-slate-400">🔍</span>
          </div>
        </div>

        {/* Accounts Table */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-slate-500 dark:text-slate-400">
              <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full mx-auto mb-4" />
              {isAr ? 'جاري تحميل دليل الحسابات...' : 'Loading chart of accounts...'}
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
          ) : filteredAccounts.length === 0 ? (
            <div className="p-12 text-center text-slate-500 dark:text-slate-400">
              <span className="text-4xl">📑</span>
              <p className="mt-3 font-medium">
                {isAr ? 'لم يتم العثور على حسابات مطابقة' : 'No matching accounts found'}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
                <thead className="bg-slate-50 dark:bg-slate-900/60 text-xs uppercase text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
                  <tr>
                    <th className="px-5 py-3.5 font-semibold">{isAr ? 'رمز الحساب' : 'Account Code'}</th>
                    <th className="px-5 py-3.5 font-semibold">{isAr ? 'اسم الحساب' : 'Account Name'}</th>
                    <th className="px-5 py-3.5 font-semibold">{isAr ? 'النوع' : 'Category'}</th>
                    <th className="px-5 py-3.5 font-semibold text-center">{isAr ? 'حساب مراقبة' : 'Control Acct'}</th>
                    <th className="px-5 py-3.5 font-semibold text-right">{isAr ? 'إجمالي المدين' : 'Total Debit'}</th>
                    <th className="px-5 py-3.5 font-semibold text-right">{isAr ? 'إجمالي الدائن' : 'Total Credit'}</th>
                    <th className="px-5 py-3.5 font-semibold text-right">{isAr ? 'صافي الرصيد' : 'Net Balance'}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                  {filteredAccounts.map((acc) => (
                    <tr key={acc.id} className="hover:bg-slate-50/80 dark:hover:bg-slate-700/40 transition-colors">
                      <td className="px-5 py-3 font-mono font-bold text-indigo-600 dark:text-indigo-400">
                        {acc.account_code}
                      </td>
                      <td className="px-5 py-3 font-medium text-slate-900 dark:text-white">
                        {acc.name}
                      </td>
                      <td className="px-5 py-3">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${getTypeBadge(acc.account_type)}`}>
                          {acc.account_type}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-center">
                        {acc.is_control_account ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300">
                            {isAr ? 'نعم' : 'Yes'}
                          </span>
                        ) : (
                          <span className="text-slate-400">-</span>
                        )}
                      </td>
                      <td className="px-5 py-3 text-right font-mono text-slate-700 dark:text-slate-300">
                        ${Number(acc.total_debit || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td className="px-5 py-3 text-right font-mono text-slate-700 dark:text-slate-300">
                        ${Number(acc.total_credit || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td className="px-5 py-3 text-right font-mono font-bold text-slate-900 dark:text-white">
                        ${Number(acc.balance || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal: New Account */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl max-w-lg w-full p-6 border border-slate-200 dark:border-slate-700">
              <div className="flex justify-between items-center mb-5">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                  {isAr ? 'إنشاء حساب مالي جديد' : 'Create New General Ledger Account'}
                </h3>
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="text-slate-400 hover:text-slate-500 dark:hover:text-slate-300 text-lg"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleCreateAccount} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-300 mb-1">
                    {isAr ? 'رمز الحساب' : 'Account Code'}
                  </label>
                  <input
                    type="text"
                    required
                    value={newAccount.account_code}
                    onChange={(e) => setNewAccount({ ...newAccount, account_code: e.target.value })}
                    placeholder="e.g. 1040, 2050, 5050"
                    className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-300 mb-1">
                    {isAr ? 'اسم الحساب' : 'Account Name'}
                  </label>
                  <input
                    type="text"
                    required
                    value={newAccount.name}
                    onChange={(e) => setNewAccount({ ...newAccount, name: e.target.value })}
                    placeholder="e.g. Special Equipment Escrow Fund"
                    className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-300 mb-1">
                    {isAr ? 'نوع الحساب' : 'Account Category'}
                  </label>
                  <select
                    value={newAccount.account_type}
                    onChange={(e) => setNewAccount({ ...newAccount, account_type: e.target.value })}
                    className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white"
                  >
                    <option value="ASSET">ASSET (1000s - Resources Owned)</option>
                    <option value="LIABILITY">LIABILITY (2000s - Obligations Owed)</option>
                    <option value="EQUITY">EQUITY (3000s - Owner Equity & Capital)</option>
                    <option value="REVENUE">REVENUE (4000s - Construction Billings)</option>
                    <option value="EXPENSE">EXPENSE (5000s - Direct Costs & Overhead)</option>
                  </select>
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="checkbox"
                    id="is_ctrl"
                    checked={newAccount.is_control_account}
                    onChange={(e) => setNewAccount({ ...newAccount, is_control_account: e.target.checked })}
                    className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <label htmlFor="is_ctrl" className="text-sm text-slate-700 dark:text-slate-300 font-medium">
                    {isAr ? 'حساب مراقبة فرعي (Control Account)' : 'Control Account (Reconciles subledger balances)'}
                  </label>
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-slate-200 dark:border-slate-700">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                  >
                    {isAr ? 'إلغاء' : 'Cancel'}
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-5 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors disabled:opacity-50"
                  >
                    {submitting ? (isAr ? 'جاري الحفظ...' : 'Saving...') : (isAr ? 'حفظ الحساب' : 'Save Account')}
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
