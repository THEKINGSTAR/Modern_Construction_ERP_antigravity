'use client';

import React, { useState, useEffect } from 'react';
import AppLayout from '@/components/AppLayout';
import {
  getBalanceSheet,
  getIncomeStatement,
  getAccounts,
  BalanceSheetReport,
  IncomeStatementReport,
  Account,
} from '@/lib/api';

export default function FinancialStatementsPage({ params }: { params: { locale: string } }) {
  const { locale } = params;
  const isAr = locale === 'ar';

  const [activeTab, setActiveTab] = useState<'TRIAL_BALANCE' | 'BALANCE_SHEET' | 'INCOME_STATEMENT'>('TRIAL_BALANCE');

  // Dates
  const todayStr = new Date().toISOString().split('T')[0];
  const [asOfDate, setAsOfDate] = useState(todayStr);
  const [startDate, setStartDate] = useState('2026-01-01');
  const [endDate, setEndDate] = useState(todayStr);

  // Data
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [balanceSheet, setBalanceSheet] = useState<BalanceSheetReport | null>(null);
  const [incomeStatement, setIncomeStatement] = useState<IncomeStatementReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [accData, bsData, isData] = await Promise.all([
        getAccounts(),
        getBalanceSheet(asOfDate).catch(() => null),
        getIncomeStatement(startDate, endDate).catch(() => null),
      ]);
      setAccounts(accData);
      setBalanceSheet(bsData);
      setIncomeStatement(isData);
    } catch (err: any) {
      setError(err.message || 'Failed to load financial statements');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [asOfDate, startDate, endDate]);

  // Trial Balance Totals
  const totalTBDebit = accounts.reduce((sum, a) => sum + (Number(a.total_debit) || 0), 0);
  const totalTBCredit = accounts.reduce((sum, a) => sum + (Number(a.total_credit) || 0), 0);
  const isTBBalanced = Math.abs(totalTBDebit - totalTBCredit) < 0.01;

  return (
    <AppLayout locale={locale}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
              {isAr ? 'التقارير والقوائم المالية الرسمية' : 'Corporate Financial Statements'}
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              {isAr
                ? 'ميزان المراجعة، الميزانية العمومية، وقائمة الدخل والأرباح والخسائر مستخرجة لحظياً من دفتر الأستاذ'
                : 'Real-time double-entry Trial Balance, Balance Sheet, and Income Statement (P&L) audited from PostgreSQL'}
            </p>
          </div>

          {/* Date Selector */}
          <div className="flex items-center gap-3 bg-white dark:bg-slate-800 p-2 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm text-xs">
            {activeTab === 'INCOME_STATEMENT' ? (
              <>
                <span className="text-slate-500">{isAr ? 'من:' : 'From:'}</span>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="px-2 py-1 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded"
                />
                <span className="text-slate-500">{isAr ? 'إلى:' : 'To:'}</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="px-2 py-1 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded"
                />
              </>
            ) : (
              <>
                <span className="text-slate-500">{isAr ? 'حتى تاريخ:' : 'As of Date:'}</span>
                <input
                  type="date"
                  value={asOfDate}
                  onChange={(e) => setAsOfDate(e.target.value)}
                  className="px-2 py-1 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded"
                />
              </>
            )}
          </div>
        </div>

        {/* Statement Tabs */}
        <div className="flex border-b border-slate-200 dark:border-slate-700 space-x-4">
          <button
            onClick={() => setActiveTab('TRIAL_BALANCE')}
            className={`pb-3 text-sm font-bold border-b-2 transition-colors ${
              activeTab === 'TRIAL_BALANCE'
                ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            {isAr ? 'ميزان المراجعة (Trial Balance)' : 'Trial Balance'}
          </button>
          <button
            onClick={() => setActiveTab('BALANCE_SHEET')}
            className={`pb-3 text-sm font-bold border-b-2 transition-colors ${
              activeTab === 'BALANCE_SHEET'
                ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            {isAr ? 'الميزانية العمومية (Balance Sheet)' : 'Balance Sheet'}
          </button>
          <button
            onClick={() => setActiveTab('INCOME_STATEMENT')}
            className={`pb-3 text-sm font-bold border-b-2 transition-colors ${
              activeTab === 'INCOME_STATEMENT'
                ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            {isAr ? 'قائمة الدخل (P&L / Income Statement)' : 'Income Statement (P&L)'}
          </button>
        </div>

        {/* TAB 1: TRIAL BALANCE */}
        {activeTab === 'TRIAL_BALANCE' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center bg-white dark:bg-slate-800 p-4 rounded-xl border border-slate-200 dark:border-slate-700">
              <div className="flex items-center gap-3">
                <span className={`inline-block w-3.5 h-3.5 rounded-full ${isTBBalanced ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                <span className="text-sm font-bold text-slate-900 dark:text-white">
                  {isTBBalanced
                    ? (isAr ? 'ميزان المراجعة متوازن دقيقاً (المدين == الدائن)' : 'Trial Balance is Mathematically Balanced (Debits == Credits)')
                    : (isAr ? 'اختلال بميزان المراجعة!' : 'Trial Balance Variance Detected!')}
                </span>
              </div>
              <div className="text-xs font-mono text-slate-500">
                {isAr ? `إجمالي القيود: $${totalTBDebit.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : `Total Ledger Volume: $${totalTBDebit.toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
              </div>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
              <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
                <thead className="bg-slate-50 dark:bg-slate-900/60 text-xs uppercase text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
                  <tr>
                    <th className="px-5 py-3.5 font-semibold">{isAr ? 'رمز الحساب' : 'Code'}</th>
                    <th className="px-5 py-3.5 font-semibold">{isAr ? 'اسم الحساب المالي' : 'Account Name'}</th>
                    <th className="px-5 py-3.5 font-semibold">{isAr ? 'التصنيف' : 'Category'}</th>
                    <th className="px-5 py-3.5 font-semibold text-right">{isAr ? 'حركة المدين ($)' : 'Debit ($)'}</th>
                    <th className="px-5 py-3.5 font-semibold text-right">{isAr ? 'حركة الدائن ($)' : 'Credit ($)'}</th>
                    <th className="px-5 py-3.5 font-semibold text-right">{isAr ? 'الرصيد الصافي ($)' : 'Net Balance ($)'}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-700 font-mono text-xs">
                  {accounts.map((acc) => (
                    <tr key={acc.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/30">
                      <td className="px-5 py-2.5 font-bold text-indigo-600 dark:text-indigo-400">{acc.account_code}</td>
                      <td className="px-5 py-2.5 font-sans font-medium text-slate-900 dark:text-white">{acc.name}</td>
                      <td className="px-5 py-2.5 font-sans">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">
                          {acc.account_type}
                        </span>
                      </td>
                      <td className="px-5 py-2.5 text-right text-slate-800 dark:text-slate-200">
                        {Number(acc.total_debit) > 0 ? `$${Number(acc.total_debit).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '-'}
                      </td>
                      <td className="px-5 py-2.5 text-right text-slate-800 dark:text-slate-200">
                        {Number(acc.total_credit) > 0 ? `$${Number(acc.total_credit).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '-'}
                      </td>
                      <td className="px-5 py-2.5 text-right font-bold text-slate-900 dark:text-white">
                        ${Number(acc.balance || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                    </tr>
                  ))}
                  <tr className="bg-slate-50 dark:bg-slate-900/80 font-bold border-t-2 border-slate-300 dark:border-slate-600 text-sm">
                    <td colSpan={3} className="px-5 py-3.5 font-sans uppercase text-slate-600 dark:text-slate-300">
                      {isAr ? 'المجموع النهائي لميزان المراجعة' : 'Total Trial Balance Debits & Credits'}
                    </td>
                    <td className="px-5 py-3.5 text-right text-emerald-600 dark:text-emerald-400">
                      ${totalTBDebit.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-5 py-3.5 text-right text-indigo-600 dark:text-indigo-400">
                      ${totalTBCredit.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-5 py-3.5 text-right text-slate-900 dark:text-white">
                      ${Math.abs(totalTBDebit - totalTBCredit).toFixed(2)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 2: BALANCE SHEET */}
        {activeTab === 'BALANCE_SHEET' && balanceSheet && (
          <div className="space-y-6">
            <div className="flex justify-between items-center bg-white dark:bg-slate-800 p-4 rounded-xl border border-slate-200 dark:border-slate-700">
              <div className="flex items-center gap-3">
                <span className={`inline-block w-3.5 h-3.5 rounded-full ${balanceSheet.is_balanced ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                <span className="text-sm font-bold text-slate-900 dark:text-white">
                  {balanceSheet.is_balanced
                    ? (isAr ? 'الميزانية العمومية متوازنة (الأصول = الالتزامات + حقوق الملكية)' : 'Balance Sheet Equation Verified: Assets = Liabilities + Equity')
                    : (isAr ? 'الميزانية العمومية غير متوازنة!' : 'Balance Sheet Equation Imbalance!')}
                </span>
              </div>
              <div className="text-xs font-mono text-slate-500">
                {isAr ? `تاريخ الإعداد: ${balanceSheet.as_of_date}` : `As of: ${balanceSheet.as_of_date}`}
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left Column: ASSETS */}
              <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm space-y-4">
                <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-700 pb-3">
                  <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <span>🏛️</span> {isAr ? 'الأصول والموجودات (Assets)' : 'Assets (1000s)'}
                  </h3>
                  <span className="font-mono text-xs font-semibold text-slate-500">
                    {balanceSheet.assets.length} {isAr ? 'حساب' : 'accounts'}
                  </span>
                </div>

                <div className="divide-y divide-slate-100 dark:divide-slate-700/50 text-xs">
                  {balanceSheet.assets.map((item) => (
                    <div key={item.account_id} className="py-2.5 flex justify-between items-center">
                      <div>
                        <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400 mr-2">
                          {item.account_code}
                        </span>
                        <span className="font-medium text-slate-800 dark:text-slate-200">{item.account_name}</span>
                      </div>
                      <span className="font-mono font-semibold text-slate-900 dark:text-white text-sm">
                        ${Number(item.balance).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                  ))}
                </div>

                <div className="pt-4 border-t-2 border-slate-300 dark:border-slate-600 flex justify-between items-center">
                  <span className="font-bold text-slate-900 dark:text-white text-sm uppercase">
                    {isAr ? 'إجمالي الأصول (Total Assets)' : 'Total Assets:'}
                  </span>
                  <span className="font-mono text-lg font-bold text-emerald-600 dark:text-emerald-400">
                    ${Number(balanceSheet.total_assets).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                </div>
              </div>

              {/* Right Column: LIABILITIES & EQUITY */}
              <div className="space-y-6">
                {/* Liabilities */}
                <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm space-y-4">
                  <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-700 pb-3">
                    <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                      <span>⚖️</span> {isAr ? 'الالتزامات والخصوم (Liabilities)' : 'Liabilities (2000s)'}
                    </h3>
                    <span className="font-mono text-xs font-semibold text-slate-500">
                      {balanceSheet.liabilities.length} {isAr ? 'حساب' : 'accounts'}
                    </span>
                  </div>

                  <div className="divide-y divide-slate-100 dark:divide-slate-700/50 text-xs">
                    {balanceSheet.liabilities.map((item) => (
                      <div key={item.account_id} className="py-2.5 flex justify-between items-center">
                        <div>
                          <span className="font-mono font-bold text-amber-600 dark:text-amber-400 mr-2">
                            {item.account_code}
                          </span>
                          <span className="font-medium text-slate-800 dark:text-slate-200">{item.account_name}</span>
                        </div>
                        <span className="font-mono font-semibold text-slate-900 dark:text-white text-sm">
                          ${Number(item.balance).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className="pt-3 border-t border-slate-200 dark:border-slate-700 flex justify-between items-center text-xs">
                    <span className="font-bold text-slate-700 dark:text-slate-300 uppercase">
                      {isAr ? 'إجمالي الالتزامات' : 'Total Liabilities:'}
                    </span>
                    <span className="font-mono font-bold text-slate-900 dark:text-white">
                      ${Number(balanceSheet.total_liabilities).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>

                {/* Equity */}
                <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm space-y-4">
                  <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-700 pb-3">
                    <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                      <span>💎</span> {isAr ? 'حقوق الملكية والأرباح المبقاة (Equity)' : 'Equity (3000s)'}
                    </h3>
                  </div>

                  <div className="divide-y divide-slate-100 dark:divide-slate-700/50 text-xs">
                    {balanceSheet.equity.map((item) => (
                      <div key={item.account_id} className="py-2.5 flex justify-between items-center">
                        <div>
                          <span className="font-mono font-bold text-purple-600 dark:text-purple-400 mr-2">
                            {item.account_code}
                          </span>
                          <span className="font-medium text-slate-800 dark:text-slate-200">{item.account_name}</span>
                        </div>
                        <span className="font-mono font-semibold text-slate-900 dark:text-white text-sm">
                          ${Number(item.balance).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </span>
                      </div>
                    ))}
                    <div className="py-2.5 flex justify-between items-center bg-slate-50/50 dark:bg-slate-900/30 px-2 rounded">
                      <span className="font-bold text-slate-800 dark:text-slate-200">
                        {isAr ? 'الأرباح المبقاة حتى تاريخه (Retained Earnings)' : 'Net Retained Earnings (Current YTD):'}
                      </span>
                      <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400 text-sm">
                        ${Number(balanceSheet.retained_earnings).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                  </div>

                  <div className="pt-4 border-t-2 border-slate-300 dark:border-slate-600 flex justify-between items-center">
                    <span className="font-bold text-slate-900 dark:text-white text-sm uppercase">
                      {isAr ? 'إجمالي الالتزامات وحقوق الملكية' : 'Total Liabilities & Equity:'}
                    </span>
                    <span className="font-mono text-lg font-bold text-indigo-600 dark:text-indigo-400">
                      ${Number(balanceSheet.total_liabilities_and_equity).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: INCOME STATEMENT (P&L) */}
        {activeTab === 'INCOME_STATEMENT' && incomeStatement && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                <div className="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                  {isAr ? 'إجمالي إيرادات العقود' : 'Operating Contract Revenue'}
                </div>
                <div className="mt-2 text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                  ${Number(incomeStatement.total_revenue).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  {incomeStatement.revenue.length} {isAr ? 'بنود إيراد مرحلة' : 'posted revenue streams'}
                </div>
              </div>

              <div className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                <div className="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                  {isAr ? 'تكاليف ومصروفات المشاريع' : 'Project Operating Costs'}
                </div>
                <div className="mt-2 text-2xl font-bold text-rose-600 dark:text-rose-400">
                  ${Number(incomeStatement.total_expenses).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  {incomeStatement.expenses.length} {isAr ? 'بنود تكلفة ومصروفات' : 'cost categories incurred'}
                </div>
              </div>

              <div className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                <div className="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                  {isAr ? 'صافي الربح التشغيلي' : 'Net Operating Profit'}
                </div>
                <div className={`mt-2 text-2xl font-bold ${Number(incomeStatement.net_profit) >= 0 ? 'text-indigo-600 dark:text-indigo-400' : 'text-rose-600'}`}>
                  ${Number(incomeStatement.net_profit).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  {Number(incomeStatement.total_revenue) > 0
                    ? `${((Number(incomeStatement.net_profit) / Number(incomeStatement.total_revenue)) * 100).toFixed(1)}% Net Margin`
                    : '0.0% Margin'}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Revenue Breakdown */}
              <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm space-y-4">
                <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-700 pb-3">
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">
                    📈 {isAr ? 'بنود الإيرادات (4000s)' : 'Revenue Breakdown'}
                  </h3>
                </div>

                <div className="divide-y divide-slate-100 dark:divide-slate-700/50 text-xs">
                  {incomeStatement.revenue.map((item) => (
                    <div key={item.account_id} className="py-2.5 flex justify-between items-center">
                      <div>
                        <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400 mr-2">
                          {item.account_code}
                        </span>
                        <span className="font-medium text-slate-800 dark:text-slate-200">{item.account_name}</span>
                      </div>
                      <span className="font-mono font-semibold text-slate-900 dark:text-white text-sm">
                        ${Number(item.balance).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                  ))}
                </div>

                <div className="pt-3 border-t border-slate-200 dark:border-slate-700 flex justify-between items-center">
                  <span className="font-bold text-slate-700 dark:text-slate-300 uppercase text-xs">
                    {isAr ? 'إجمالي الإيرادات' : 'Total Revenue:'}
                  </span>
                  <span className="font-mono text-base font-bold text-emerald-600 dark:text-emerald-400">
                    ${Number(incomeStatement.total_revenue).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                </div>
              </div>

              {/* Expenses Breakdown */}
              <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm space-y-4">
                <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-700 pb-3">
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">
                    📉 {isAr ? 'تكاليف ومصروفات العمليات (5000s)' : 'Direct Costs & Expenses'}
                  </h3>
                </div>

                <div className="divide-y divide-slate-100 dark:divide-slate-700/50 text-xs">
                  {incomeStatement.expenses.map((item) => (
                    <div key={item.account_id} className="py-2.5 flex justify-between items-center">
                      <div>
                        <span className="font-mono font-bold text-rose-600 dark:text-rose-400 mr-2">
                          {item.account_code}
                        </span>
                        <span className="font-medium text-slate-800 dark:text-slate-200">{item.account_name}</span>
                      </div>
                      <span className="font-mono font-semibold text-slate-900 dark:text-white text-sm">
                        ${Number(item.balance).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                  ))}
                </div>

                <div className="pt-3 border-t border-slate-200 dark:border-slate-700 flex justify-between items-center">
                  <span className="font-bold text-slate-700 dark:text-slate-300 uppercase text-xs">
                    {isAr ? 'إجمالي المصروفات' : 'Total Expenses:'}
                  </span>
                  <span className="font-mono text-base font-bold text-rose-600 dark:text-rose-400">
                    ${Number(incomeStatement.total_expenses).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
