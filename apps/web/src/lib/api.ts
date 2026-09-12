const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface Project {
  id: string;
  project_number: string;
  name: string;
  client_id?: string | null;
  start_date?: string | null;
  target_end_date?: string | null;
  planned_end_date?: string | null;
  budget_amount?: string | null;
  project_type?: string | null;
  location?: string | null;
  description?: string | null;
  status: string;
}

export interface Client {
  id: string;
  name: string;
  legal_name?: string | null;
  contact_information?: string | null;
  billing_address?: string | null;
  tax_identifier?: string | null;
  status: string;
  contacts?: Array<{
    id?: string;
    name: string;
    email?: string;
    phone?: string;
    role?: string;
  }>;
}

export interface Material {
  id: string;
  material_code: string;
  name: string;
  description?: string | null;
  category?: string | null;
  base_unit: string;
  active: boolean;
}

export interface Warehouse {
  id: string;
  code: string;
  name: string;
  location?: string | null;
  type?: string;
  project_id?: string | null;
  project_name?: string | null;
}

export interface GoodsReceiptLine {
  id: string;
  material_id: string;
  material_code?: string;
  material_name?: string;
  received_quantity: string | number;
  accepted_quantity: string | number;
  rejected_quantity: string | number;
  unit_cost: string | number;
  total_cost?: string | number;
  notes?: string | null;
}

export interface GoodsReceipt {
  id: string;
  receipt_number: string;
  purchase_order_id: string;
  po_number?: string;
  supplier_id: string;
  supplier_name?: string;
  warehouse_id: string;
  warehouse_name?: string;
  date: string;
  notes?: string | null;
  status: string;
  lines_count?: number;
  total_received_amount?: string | number;
  lines?: GoodsReceiptLine[];
}

export interface MaterialIssueLine {
  id: string;
  material_id: string;
  material_code?: string;
  material_name?: string;
  quantity: string | number;
  unit_cost?: string | number;
  total_cost?: string | number;
  notes?: string | null;
}

export interface MaterialIssue {
  id: string;
  issue_number: string;
  warehouse_id: string;
  warehouse_name?: string;
  project_id: string;
  project_name?: string;
  cost_code_id: string;
  cost_code_code?: string;
  cost_code_name?: string;
  date: string;
  purpose?: string | null;
  requested_by_id?: string | null;
  requested_by_name?: string | null;
  status: string;
  lines_count?: number;
  total_quantity?: string | number;
  total_amount?: string | number;
  lines?: MaterialIssueLine[];
}

export interface InventoryTransferLine {
  id: string;
  material_id: string;
  material_code?: string;
  material_name?: string;
  quantity: string | number;
  unit_cost?: string | number;
  notes?: string | null;
}

export interface InventoryTransfer {
  id: string;
  transfer_number: string;
  source_warehouse_id: string;
  source_warehouse_name?: string;
  destination_warehouse_id: string;
  destination_warehouse_name?: string;
  date: string;
  notes?: string | null;
  status: string;
  lines_count?: number;
  total_amount?: string | number;
  lines?: InventoryTransferLine[];
}

export interface InventorySummary {
  total_valuation: string | number;
  total_stock_quantity: string | number;
  total_items_count: number;
  total_warehouses_count: number;
  total_receipts_count: number;
  total_issues_count: number;
  total_transfers_count: number;
  recent_transactions: InventoryTransaction[];
  top_materials: InventoryBalanceDetail[];
}

export interface CreateMaterialInput {
  material_code: string;
  name: string;
  description?: string;
  category?: string;
  base_unit: string;
}

export interface CreateWarehouseInput {
  code: string;
  name: string;
  location?: string;
  type?: string;
  project_id?: string;
}

export interface CreateGoodsReceiptInput {
  receipt_number: string;
  purchase_order_id: string;
  supplier_id: string;
  warehouse_id: string;
  date: string;
  notes?: string;
  lines: Array<{
    purchase_order_line_id?: string;
    material_id: string;
    received_quantity: number;
    accepted_quantity: number;
    rejected_quantity?: number;
    unit_cost: number;
    notes?: string;
  }>;
}

export interface CreateMaterialIssueInput {
  issue_number: string;
  warehouse_id: string;
  project_id: string;
  cost_code_id: string;
  date: string;
  purpose?: string;
  requested_by_id?: string;
  lines: Array<{
    material_id: string;
    quantity: number;
    notes?: string;
  }>;
}

export interface CreateInventoryTransferInput {
  transfer_number: string;
  source_warehouse_id: string;
  destination_warehouse_id: string;
  date: string;
  notes?: string;
  lines: Array<{
    material_id: string;
    quantity: number;
    notes?: string;
  }>;
}

export interface InventoryBalanceDetail {
  id: string;
  warehouse_id: string;
  warehouse_name: string;
  material_id: string;
  material_code: string;
  material_name: string;
  base_unit: string;
  quantity: string;
  unit_cost: string;
  total_cost: string;
}

export interface InventoryTransaction {
  id: string;
  warehouse_id: string;
  material_id: string;
  project_id?: string | null;
  transaction_type: string;
  quantity: string;
  unit_cost: string;
  total_cost: string;
  reference_type?: string | null;
  transaction_date?: string | null;
}

export interface PurchaseOrder {
  id: string;
  po_number: string;
  project_id: string;
  supplier_id: string;
  supplier_name?: string;
  project_name?: string;
  status: string;
  total_amount: string;
  currency: string;
  notes?: string | null;
  issue_date?: string | null;
  delivery_date?: string | null;
  lines?: Array<{
    id?: string;
    item_description: string;
    unit: string;
    quantity: string;
    unit_price: string;
    amount: string;
  }>;
}

export interface Account {
  id: string;
  name: string;
  account_code: string;
  account_type?: string;
  is_control_account: boolean;
  chart_of_accounts_id?: string;
  chart_name?: string;
  parent_code?: string;
  parent_name?: string;
  balance?: number;
  total_debit?: number;
  total_credit?: number;
}

export interface CreateAccountInput {
  name: string;
  account_code: string;
  account_type: string;
  is_control_account?: boolean;
  parent_id?: string | null;
  chart_of_accounts_id?: string | null;
}

export interface JournalLine {
  id?: string;
  account_id: string;
  debit: string | number;
  credit: string | number;
  project_id?: string | null;
  cost_code_id?: string | null;
  department_id?: string | null;
  branch_id?: string | null;
  business_unit_id?: string | null;
  account_code?: string;
  account_name?: string;
  project_name?: string;
  cost_code_code?: string;
}

export interface Journal {
  id: string;
  date: string;
  reference?: string | null;
  description: string;
  status: string;
  reversal_journal_id?: string | null;
  lines_count?: number;
  total_debit?: number;
  total_credit?: number;
  is_balanced?: boolean;
  lines: JournalLine[];
}

export interface CreateJournalInput {
  date?: string;
  entry_date?: string;
  journal_number?: string;
  reference?: string | null;
  description: string;
  source_document_type?: string;
  source_document_id?: string;
  lines: Array<{
    account_id: string | null;
    debit?: number;
    credit?: number;
    debit_amount?: number;
    credit_amount?: number;
    line_number?: number;
    project_id?: string | null;
    cost_code_id?: string | null;
    description?: string | null;
  }>;
}

export interface GLSummary {
  total_journals: number;
  posted_journals: number;
  draft_journals: number;
  reversed_journals: number;
  total_debits: number;
  total_credits: number;
  is_ledger_balanced: boolean;
  total_accounts: number;
  asset_accounts: number;
  liability_accounts: number;
  equity_accounts: number;
  revenue_accounts: number;
  expense_accounts: number;
  total_periods: number;
  open_periods: number;
  closed_periods: number;
  total_revenue: number;
  total_expenses: number;
  net_income: number;
}

export interface FinancialStatementItem {
  account_id: string;
  account_code: string;
  account_name: string;
  account_type: string;
  debit: number;
  credit: number;
  balance: number;
}

export interface BalanceSheetReport {
  as_of_date: string;
  assets: FinancialStatementItem[];
  total_assets: number;
  liabilities: FinancialStatementItem[];
  total_liabilities: number;
  equity: FinancialStatementItem[];
  total_equity: number;
  retained_earnings: number;
  total_liabilities_and_equity: number;
  is_balanced: boolean;
}

export interface IncomeStatementReport {
  start_date: string;
  end_date: string;
  revenue: FinancialStatementItem[];
  total_revenue: number;
  expenses: FinancialStatementItem[];
  total_expenses: number;
  gross_profit: number;
  net_profit: number;
}

export interface APInvoiceLine {
  id: string;
  invoice_id: string;
  project_id?: string | null;
  cost_code_id?: string | null;
  purchase_order_line_id?: string | null;
  goods_receipt_line_id?: string | null;
  material_id?: string | null;
  description: string;
  quantity: number | string;
  unit_price: number | string;
  tax_rate?: number | string;
  tax_amount?: number | string;
  line_total: number | string;
  material_code?: string | null;
  material_name?: string | null;
  project_name?: string | null;
  cost_code_code?: string | null;
}

export interface APInvoice {
  id: string;
  number: string;
  supplier_id: string;
  purchase_order_id?: string | null;
  goods_receipt_id?: string | null;
  date: string;
  due_date: string;
  status: string;
  invoice_type?: string;
  matching_status: string;
  subtotal: string;
  tax_amount: string;
  total_amount: string;
  currency: string;
  journal_id?: string | null;
  description?: string | null;
  lines?: APInvoiceLine[];
  supplier_name?: string | null;
  po_number?: string | null;
  grn_number?: string | null;
  lines_count?: number;
  paid_amount?: number | string;
  outstanding_amount?: number | string;
  outstanding_balance?: number | string;
}

export interface ThreeWayMatchLineReport {
  invoice_line_id: string;
  description: string;
  invoice_qty: number | string;
  invoice_unit_price: number | string;
  invoice_line_total: number | string;
  po_qty?: number | string | null;
  po_unit_price?: number | string | null;
  grn_accepted_qty?: number | string | null;
  qty_variance: number | string;
  price_variance: number | string;
  total_variance: number | string;
  line_status: string;
  notes?: string | null;
}

export interface ThreeWayMatchReport {
  invoice_id: string;
  invoice_number: string;
  supplier_name?: string | null;
  purchase_order_id?: string | null;
  po_number?: string | null;
  goods_receipt_id?: string | null;
  grn_number?: string | null;
  matching_status: string;
  total_invoice_amount: number | string;
  total_po_amount?: number | string | null;
  total_grn_accepted_amount?: number | string | null;
  variance_amount: number | string;
  is_matched: boolean;
  can_approve: boolean;
  lines: ThreeWayMatchLineReport[];
}

export interface PaymentAllocation {
  id?: string;
  payment_id?: string;
  ap_invoice_id?: string | null;
  ar_invoice_id?: string | null;
  amount: number | string;
}

export interface Payment {
  id: string;
  reference: string;
  payment_type: string;
  date: string;
  amount: number | string;
  currency: string;
  status: string;
  supplier_id?: string | null;
  client_id?: string | null;
  bank_account_id: string;
  journal_id?: string | null;
  allocations?: PaymentAllocation[];
  supplier_name?: string | null;
  client_name?: string | null;
  bank_name?: string | null;
  bank_account_name?: string | null;
  allocations_count?: number;
}

export interface BankAccount {
  id: string;
  name: string;
  account_number: string;
  bank_name: string;
  currency: string;
  gl_account_id: string;
  is_active: boolean;
}

export interface APSummary {
  total_payables: number | string;
  total_invoiced: number | string;
  total_paid: number | string;
  invoices_count: number;
  draft_count: number;
  approved_count: number;
  posted_count: number;
  paid_count: number;
  matched_count: number;
  variance_count: number;
  aging_current: number | string;
  aging_31_60: number | string;
  aging_61_90: number | string;
  aging_over_90: number | string;
  recent_invoices: Array<{
    id: string;
    number: string;
    supplier_name: string;
    date: string;
    due_date: string;
    total_amount: number;
    outstanding_amount: number;
    status: string;
    matching_status: string;
    po_number?: string | null;
    grn_number?: string | null;
  }>;
  recent_payments: Array<{
    id: string;
    reference: string;
    supplier_name: string;
    bank_name: string;
    date: string;
    amount: number;
    status: string;
  }>;
}

export interface CreateAPInvoiceInput {
  number: string;
  supplier_id: string;
  purchase_order_id?: string;
  goods_receipt_id?: string;
  date: string;
  due_date: string;
  invoice_type?: string;
  currency?: string;
  description?: string;
  tax_amount?: number;
  lines: Array<{
    project_id?: string;
    cost_code_id?: string;
    purchase_order_line_id?: string;
    goods_receipt_line_id?: string;
    material_id?: string;
    description: string;
    quantity: number;
    unit_price: number;
    tax_rate?: number;
    tax_amount?: number;
  }>;
}

export interface CreatePaymentInput {
  reference: string;
  payment_type: string;
  date: string;
  amount: number;
  currency?: string;
  supplier_id?: string;
  bank_account_id: string;
  allocations: Array<{
    ap_invoice_id?: string;
    ar_invoice_id?: string;
    amount: number;
  }>;
}

export interface TrialBalanceReport {
  as_of_date: string;
  lines: Array<{
    account_id?: string;
    account_code: string;
    account_name: string;
    debit: string;
    credit: string;
  }>;
  total_debit: string;
  total_credit: string;
}

export interface ExecutiveDashboard {
  total_active_contracts: number;
  total_contract_value: string;
  total_projects: number;
  active_projects: number;
  total_on_hand_quantity: string;
  total_inventory_valuation: string;
  warehouse_count: number;
  total_journal_entries: number;
  total_debits: string;
  total_credits: string;
  is_ledger_balanced: boolean;
  total_ap_invoices: number;
  total_open_payables: string;
  total_clients: number;
}

export interface ProjectDashboard {
  project_id: string;
  contract_value: string;
  current_contract_value: string;
  original_budget: string;
  current_budget: string;
  committed_cost: string;
  actual_cost: string;
  forecast_cost: string;
  estimate_at_completion: string;
  variance: string;
  billed: string;
  collected: string;
  receivable: string;
  payable: string;
  gross_profit: string;
  margin_percentage: string;
}

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('erp_access_token');
}

export function setToken(token: string) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('erp_access_token', token);
  }
}

export function clearToken() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('erp_access_token');
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (options.body && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let errorDetail = `HTTP ${res.status} ${res.statusText}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // fallback
    }
    throw new Error(errorDetail);
  }

  if (res.status === 204) {
    return {} as T;
  }

  return res.json();
}

// ----------------- Auth -----------------
export async function login(username: string, password: string): Promise<{ access_token: string }> {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData.toString(),
  });

  if (!res.ok) {
    throw new Error('Authentication failed. Check credentials.');
  }

  const data = await res.json();
  setToken(data.access_token);
  return data;
}

export function logout() {
  clearToken();
}

// ----------------- Dashboard & Reports -----------------
export async function getExecutiveDashboard(): Promise<ExecutiveDashboard> {
  return request<ExecutiveDashboard>('/reports/executive-dashboard');
}

export async function getProjectDashboard(projectId: string): Promise<ProjectDashboard> {
  return request<ProjectDashboard>(`/reports/projects/${projectId}/dashboard`);
}

export async function getTrialBalance(): Promise<TrialBalanceReport> {
  return request<TrialBalanceReport>('/reports/accounting/trial-balance');
}

// ----------------- Projects -----------------
export async function getProjects(): Promise<Project[]> {
  return request<Project[]>('/projects/');
}

export async function createProject(data: Partial<Project>): Promise<Project> {
  return request<Project>('/projects/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateProject(id: string, data: Partial<Project>): Promise<Project> {
  return request<Project>(`/projects/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteProject(id: string): Promise<void> {
  return request<void>(`/projects/${id}`, {
    method: 'DELETE',
  });
}

// ----------------- Clients -----------------
export async function getClients(): Promise<Client[]> {
  return request<Client[]>('/clients/');
}

export async function createClient(data: Partial<Client>): Promise<Client> {
  return request<Client>('/clients/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateClient(id: string, data: Partial<Client>): Promise<Client> {
  return request<Client>(`/clients/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteClient(id: string): Promise<void> {
  return request<void>(`/clients/${id}`, {
    method: 'DELETE',
  });
}

// ----------------- Inventory & Logistics -----------------
export async function getMaterials(): Promise<Material[]> {
  return request<Material[]>('/inventory/materials');
}

export async function createMaterial(data: CreateMaterialInput): Promise<Material> {
  return request<Material>('/inventory/materials', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getWarehouses(): Promise<Warehouse[]> {
  return request<Warehouse[]>('/inventory/warehouses');
}

export async function createWarehouse(data: CreateWarehouseInput): Promise<Warehouse> {
  return request<Warehouse>('/inventory/warehouses', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getDetailedBalances(): Promise<InventoryBalanceDetail[]> {
  return request<InventoryBalanceDetail[]>('/inventory/balances/detail');
}

export async function getInventoryTransactions(): Promise<InventoryTransaction[]> {
  return request<InventoryTransaction[]>('/inventory/transactions');
}

export async function getGoodsReceipts(): Promise<GoodsReceipt[]> {
  return request<GoodsReceipt[]>('/inventory/goods-receipts');
}

export async function getGoodsReceipt(id: string): Promise<GoodsReceipt> {
  return request<GoodsReceipt>(`/inventory/goods-receipts/${id}`);
}

export async function createGoodsReceipt(data: CreateGoodsReceiptInput): Promise<GoodsReceipt> {
  return request<GoodsReceipt>('/inventory/goods-receipts', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getMaterialIssues(): Promise<MaterialIssue[]> {
  return request<MaterialIssue[]>('/inventory/material-issues');
}

export async function getMaterialIssue(id: string): Promise<MaterialIssue> {
  return request<MaterialIssue>(`/inventory/material-issues/${id}`);
}

export async function createMaterialIssue(data: CreateMaterialIssueInput): Promise<MaterialIssue> {
  return request<MaterialIssue>('/inventory/material-issues', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getInventoryTransfers(): Promise<InventoryTransfer[]> {
  return request<InventoryTransfer[]>('/inventory/transfers');
}

export async function getInventoryTransfer(id: string): Promise<InventoryTransfer> {
  return request<InventoryTransfer>(`/inventory/transfers/${id}`);
}

export async function createInventoryTransfer(data: CreateInventoryTransferInput): Promise<InventoryTransfer> {
  return request<InventoryTransfer>('/inventory/transfers', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function createInventoryAdjustment(data: any): Promise<any> {
  return request<any>('/inventory/adjustments', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getInventorySummary(): Promise<InventorySummary> {
  return request<InventorySummary>('/inventory/summary');
}

// ----------------- Procurement -----------------
export interface Supplier {
  id: string;
  name: string;
  legal_name?: string;
  tax_identifier?: string;
  address?: string;
  status: string;
}

export async function getSuppliers(): Promise<Supplier[]> {
  return request<Supplier[]>('/suppliers/');
}

export async function getPurchaseOrders(): Promise<PurchaseOrder[]> {
  return request<PurchaseOrder[]>('/purchase-orders/');
}

export async function createPurchaseOrder(data: any): Promise<PurchaseOrder> {
  return request<PurchaseOrder>('/purchase-orders/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function issuePurchaseOrder(poId: string): Promise<{ status: string }> {
  return request<{ status: string }>(`/purchase-orders/${poId}/issue`, {
    method: 'POST',
  });
}

export async function cancelPurchaseOrder(poId: string): Promise<{ status: string }> {
  return request<{ status: string }>(`/purchase-orders/${poId}/cancel`, {
    method: 'POST',
  });
}

// ----------------- General Ledger & Accounting -----------------
export async function getGLSummary(): Promise<GLSummary> {
  return request<GLSummary>('/accounting/summary');
}

export async function getAccounts(params?: {
  account_type?: string;
  search?: string;
}): Promise<Account[]> {
  const query = new URLSearchParams();
  if (params?.account_type) query.append('account_type', params.account_type);
  if (params?.search) query.append('search', params.search);
  const qStr = query.toString() ? `?${query.toString()}` : '';
  return request<Account[]>(`/accounting/accounts${qStr}`);
}

export async function getAccount(id: string): Promise<Account> {
  return request<Account>(`/accounting/accounts/${id}`);
}

export async function createAccount(data: CreateAccountInput): Promise<Account> {
  return request<Account>('/accounting/accounts', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getJournals(params?: {
  status?: string;
  search?: string;
  start_date?: string;
  end_date?: string;
}): Promise<Journal[]> {
  const query = new URLSearchParams();
  if (params?.status) query.append('status_filter', params.status);
  if (params?.search) query.append('search', params.search);
  if (params?.start_date) query.append('start_date', params.start_date);
  if (params?.end_date) query.append('end_date', params.end_date);
  const qStr = query.toString() ? `?${query.toString()}` : '';
  return request<Journal[]>(`/accounting/journals${qStr}`);
}

export async function getJournal(id: string): Promise<Journal> {
  return request<Journal>(`/accounting/journals/${id}`);
}

export async function createJournal(data: CreateJournalInput, auto_post: boolean = false): Promise<Journal> {
  const payload = {
    ...data,
    date: data.date || data.entry_date || new Date().toISOString().split('T')[0],
    entry_date: data.entry_date || data.date || new Date().toISOString().split('T')[0],
    lines: data.lines.map((l, idx) => ({
      account_id: l.account_id || '',
      debit: l.debit !== undefined ? l.debit : (l.debit_amount || 0),
      credit: l.credit !== undefined ? l.credit : (l.credit_amount || 0),
      line_number: l.line_number ?? idx + 1,
      project_id: l.project_id || null,
      cost_code_id: l.cost_code_id || null,
      description: l.description || null,
    })),
  };
  return request<Journal>(`/accounting/journals?auto_post=${auto_post}`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function postJournal(id: string): Promise<Journal> {
  return request<Journal>(`/accounting/journals/${id}/post`, {
    method: 'POST',
  });
}

export async function reverseJournal(id: string, reversal_date: string, description: string): Promise<Journal> {
  return request<Journal>(`/accounting/journals/${id}/reverse`, {
    method: 'POST',
    body: JSON.stringify({ reversal_date, description }),
  });
}

export async function getAccountingPeriods(): Promise<AccountingPeriod[]> {
  return request<AccountingPeriod[]>('/accounting/periods');
}

export async function closeAccountingPeriod(id: string): Promise<AccountingPeriod> {
  return request<AccountingPeriod>(`/accounting/periods/${id}/close`, {
    method: 'POST',
  });
}

export async function reopenAccountingPeriod(id: string): Promise<AccountingPeriod> {
  return request<AccountingPeriod>(`/accounting/periods/${id}/reopen`, {
    method: 'POST',
  });
}

export async function getBalanceSheet(as_of_date?: string): Promise<BalanceSheetReport> {
  const qStr = as_of_date ? `?as_of_date=${as_of_date}` : '';
  return request<BalanceSheetReport>(`/accounting/reports/balance-sheet${qStr}`);
}

export async function getIncomeStatement(start_date?: string, end_date?: string): Promise<IncomeStatementReport> {
  const query = new URLSearchParams();
  if (start_date) query.append('start_date', start_date);
  if (end_date) query.append('end_date', end_date);
  const qStr = query.toString() ? `?${query.toString()}` : '';
  return request<IncomeStatementReport>(`/accounting/reports/income-statement${qStr}`);
}

export async function getAPInvoices(params?: {
  supplier_id?: string;
  status?: string;
  matching_status?: string;
  purchase_order_id?: string;
}): Promise<APInvoice[]> {
  const query = new URLSearchParams();
  if (params?.supplier_id) query.append('supplier_id', params.supplier_id);
  if (params?.status) query.append('status', params.status);
  if (params?.matching_status) query.append('matching_status', params.matching_status);
  if (params?.purchase_order_id) query.append('purchase_order_id', params.purchase_order_id);
  const qStr = query.toString() ? `?${query.toString()}` : '';
  return request<APInvoice[]>(`/ap/invoices${qStr}`);
}

export async function getAPInvoice(id: string): Promise<APInvoice> {
  return request<APInvoice>(`/ap/invoices/${id}`);
}

export async function createAPInvoice(data: CreateAPInvoiceInput): Promise<APInvoice> {
  return request<APInvoice>('/ap/invoices', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function matchAPInvoice(id: string): Promise<ThreeWayMatchReport> {
  return request<ThreeWayMatchReport>(`/ap/invoices/${id}/match`, {
    method: 'POST',
  });
}

export async function approveAPInvoice(id: string): Promise<APInvoice> {
  return request<APInvoice>(`/ap/invoices/${id}/approve`, {
    method: 'POST',
  });
}

export async function postAPInvoice(id: string): Promise<APInvoice> {
  return request<APInvoice>(`/ap/invoices/${id}/post`, {
    method: 'POST',
  });
}

export async function getPayments(supplier_id?: string): Promise<Payment[]> {
  const qStr = supplier_id ? `?supplier_id=${supplier_id}` : '';
  return request<Payment[]>(`/ap/payments${qStr}`);
}

export async function getPayment(id: string): Promise<Payment> {
  return request<Payment>(`/ap/payments/${id}`);
}

export async function createPayment(data: CreatePaymentInput): Promise<Payment> {
  return request<Payment>('/ap/payments', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getAPSummary(): Promise<APSummary> {
  return request<APSummary>('/ap/summary');
}

export async function getBankAccounts(): Promise<BankAccount[]> {
  return request<BankAccount[]>('/ap/bank-accounts');
}

export async function createBankAccount(data: any): Promise<BankAccount> {
  return request<BankAccount>('/ap/bank-accounts', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ----------------- Contracts -----------------
export interface ContractType {
  id: string;
  name: string;
  description?: string;
  is_active: boolean;
}

export interface Contract {
  id: string;
  project_id: string;
  client_id?: string;
  contract_number: string;
  contract_type_id: string;
  original_value: number;
  current_value: number;
  currency_code: string;
  start_date?: string;
  end_date?: string;
  retention_rate: number;
  payment_terms?: string;
  status: string;
  created_at?: string;
}

export async function getContracts(projectId?: string): Promise<Contract[]> {
  const q = projectId ? ("?project_id=" + projectId) : "";
  return request<Contract[]>("/contracts" + q);
}

export async function getContract(id: string): Promise<Contract> {
  return request<Contract>("/contracts/" + id);
}

export async function createContract(data: Partial<Contract>): Promise<Contract> {
  return request<Contract>("/contracts", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateContract(id: string, data: Partial<Contract>): Promise<Contract> {
  return request<Contract>("/contracts/" + id, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deleteContract(id: string): Promise<void> {
  return request<void>("/contracts/" + id, {
    method: "DELETE",
  });
}

export async function getContractTypes(): Promise<ContractType[]> {
  return request<ContractType[]>("/contracts/types");
}

// ----------------- WBS -----------------
export interface WBSNode {
  id: string;
  project_id: string;
  parent_id?: string | null;
  code: string;
  name: string;
  description?: string;
  is_active: boolean;
  children?: WBSNode[];
}

export async function getWBSNodes(projectId?: string): Promise<WBSNode[]> {
  const q = projectId ? ("?project_id=" + projectId) : "";
  return request<WBSNode[]>("/wbs" + q);
}

export async function getWBSTree(projectId: string): Promise<WBSNode[]> {
  return request<WBSNode[]>("/wbs/tree/" + projectId);
}

export async function createWBSNode(data: Partial<WBSNode>): Promise<WBSNode> {
  return request<WBSNode>("/wbs", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ----------------- Cost Codes -----------------
export interface CostCode {
  id: string;
  parent_id?: string | null;
  code: string;
  name: string;
  category?: string;
  is_active: boolean;
  children?: CostCode[];
}

export async function getCostCodes(): Promise<CostCode[]> {
  return request<CostCode[]>("/cost-codes");
}

export async function getCostCodesTree(): Promise<CostCode[]> {
  return request<CostCode[]>("/cost-codes/tree");
}

export async function createCostCode(data: Partial<CostCode>): Promise<CostCode> {
  return request<CostCode>("/cost-codes", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ----------------- BOQ -----------------
export interface BOQItem {
  id?: string;
  item_code: string;
  description: string;
  unit: string;
  quantity: number;
  unit_rate: number;
  cost_code_id?: string;
}

export interface BOQ {
  id: string;
  project_id: string;
  name: string;
  status: string;
  current_revision_id?: string;
  created_at?: string;
}

export async function getBOQs(projectId?: string): Promise<BOQ[]> {
  const q = projectId ? ("?project_id=" + projectId) : "";
  return request<BOQ[]>("/boqs/" + q);
}

export async function createBOQ(data: Partial<BOQ>): Promise<BOQ> {
  return request<BOQ>("/boqs/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ----------------- Estimates -----------------
export interface EstimateItem {
  id?: string;
  item_code: string;
  description: string;
  unit: string;
  quantity: number;
  unit_rate: number;
  cost_code_id?: string;
}

export interface Estimate {
  id: string;
  project_id: string;
  name: string;
  status: string;
  current_revision_id?: string;
  created_at?: string;
}

export async function getEstimates(projectId?: string): Promise<Estimate[]> {
  const q = projectId ? ("?project_id=" + projectId) : "";
  return request<Estimate[]>("/estimates/" + q);
}

export async function createEstimate(data: Partial<Estimate>): Promise<Estimate> {
  return request<Estimate>("/estimates/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ----------------- Budgets -----------------
export interface BudgetLine {
  id?: string;
  budget_id?: string;
  cost_code_id: string;
  original_budget: number;
  approved_changes: number;
  current_budget?: number;
}

export interface Budget {
  id: string;
  project_id: string;
  name: string;
  created_at?: string;
  lines?: BudgetLine[];
}

export async function getBudgets(projectId?: string): Promise<Budget[]> {
  const q = projectId ? ("?project_id=" + projectId) : "";
  return request<Budget[]>("/budgets/" + q);
}

export async function createBudget(data: Partial<Budget>): Promise<Budget> {
  return request<Budget>("/budgets/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}



// ----------------- Commercial: Subcontracts -----------------
export interface Subcontract {
  id: string;
  project_id: string;
  supplier_id: string;
  subcontract_number: string;
  original_value: number;
  current_value: number;
  currency_code: string;
  retention_rate: number;
  start_date?: string;
  end_date?: string;
  project_name?: string;
  supplier_name?: string;
  created_at?: string;
}

export async function getSubcontracts(projectId?: string): Promise<Subcontract[]> {
  const q = projectId ? `?project_id=${projectId}` : "";
  return request<Subcontract[]>(`/commercial/subcontracts${q}`);
}

export async function getSubcontract(id: string): Promise<Subcontract> {
  return request<Subcontract>(`/commercial/subcontracts/${id}`);
}

export async function createSubcontract(data: Partial<Subcontract>): Promise<Subcontract> {
  return request<Subcontract>("/commercial/subcontracts", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ----------------- Commercial: Change Orders -----------------
export interface ClientChangeOrder {
  id: string;
  contract_id: string;
  number: string;
  title: string;
  description?: string;
  amount: number;
  status: "DRAFT" | "SUBMITTED" | "UNDER_REVIEW" | "APPROVED" | "REJECTED" | "CANCELLED";
  approved_date?: string;
  contract_number?: string;
  created_at?: string;
}

export async function getClientChangeOrders(contractId?: string): Promise<ClientChangeOrder[]> {
  const q = contractId ? `?contract_id=${contractId}` : "";
  return request<ClientChangeOrder[]>(`/commercial/client-change-orders${q}`);
}

export async function createClientChangeOrder(data: Partial<ClientChangeOrder>): Promise<ClientChangeOrder> {
  return request<ClientChangeOrder>("/commercial/client-change-orders", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function approveClientChangeOrder(id: string): Promise<ClientChangeOrder> {
  return request<ClientChangeOrder>(`/commercial/client-change-orders/${id}/approve`, {
    method: "POST",
  });
}

export interface SubcontractChangeOrder {
  id: string;
  subcontract_id: string;
  number: string;
  title: string;
  description?: string;
  amount: number;
  status: "DRAFT" | "SUBMITTED" | "UNDER_REVIEW" | "APPROVED" | "REJECTED" | "CANCELLED";
  approved_date?: string;
  subcontract_number?: string;
  created_at?: string;
}

export async function getSubcontractChangeOrders(subcontractId?: string): Promise<SubcontractChangeOrder[]> {
  const q = subcontractId ? `?subcontract_id=${subcontractId}` : "";
  return request<SubcontractChangeOrder[]>(`/commercial/subcontract-change-orders${q}`);
}

export async function createSubcontractChangeOrder(data: Partial<SubcontractChangeOrder>): Promise<SubcontractChangeOrder> {
  return request<SubcontractChangeOrder>("/commercial/subcontract-change-orders", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function approveSubcontractChangeOrder(id: string): Promise<SubcontractChangeOrder> {
  return request<SubcontractChangeOrder>(`/commercial/subcontract-change-orders/${id}/approve`, {
    method: "POST",
  });
}

// ----------------- Commercial: Payment Applications -----------------
export interface ClientPaymentApplication {
  id: string;
  contract_id: string;
  accounting_period_id: string;
  number: string;
  date: string;
  gross_work: number;
  previous_certified_work: number;
  retention_amount: number;
  advance_recovery_amount: number;
  deductions_amount: number;
  adjustments_amount: number;
  net_amount_due: number;
  status: "DRAFT" | "SUBMITTED" | "APPROVED" | "POSTED" | "PAID";
  journal_id?: string;
  contract_number?: string;
  period_name?: string;
  created_at?: string;
}

export async function getClientPaymentApplications(contractId?: string): Promise<ClientPaymentApplication[]> {
  const q = contractId ? `?contract_id=${contractId}` : "";
  return request<ClientPaymentApplication[]>(`/commercial/client-payment-applications${q}`);
}

export async function createClientPaymentApplication(data: Partial<ClientPaymentApplication>): Promise<ClientPaymentApplication> {
  return request<ClientPaymentApplication>("/commercial/client-payment-applications", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function approveClientPaymentApplication(id: string): Promise<ClientPaymentApplication> {
  return request<ClientPaymentApplication>(`/commercial/client-payment-applications/${id}/approve`, {
    method: "POST",
  });
}

export async function postClientPaymentApplication(
  id: string,
  arAccountId: string,
  revenueAccountId: string,
  retentionAccountId: string
): Promise<ClientPaymentApplication> {
  const q = `?ar_account_id=${arAccountId}&revenue_account_id=${revenueAccountId}&retention_account_id=${retentionAccountId}`;
  return request<ClientPaymentApplication>(`/commercial/client-payment-applications/${id}/post${q}`, {
    method: "POST",
  });
}

export interface SubcontractPaymentApplication {
  id: string;
  subcontract_id: string;
  accounting_period_id: string;
  number: string;
  date: string;
  gross_work: number;
  previous_certified_work: number;
  retention_amount: number;
  advance_recovery_amount: number;
  deductions_amount: number;
  adjustments_amount: number;
  net_amount_due: number;
  status: "DRAFT" | "SUBMITTED" | "APPROVED" | "POSTED" | "PAID";
  journal_id?: string;
  subcontract_number?: string;
  period_name?: string;
  created_at?: string;
}

export async function getSubcontractPaymentApplications(subcontractId?: string): Promise<SubcontractPaymentApplication[]> {
  const q = subcontractId ? `?subcontract_id=${subcontractId}` : "";
  return request<SubcontractPaymentApplication[]>(`/commercial/subcontract-payment-applications${q}`);
}

export async function createSubcontractPaymentApplication(data: Partial<SubcontractPaymentApplication>): Promise<SubcontractPaymentApplication> {
  return request<SubcontractPaymentApplication>("/commercial/subcontract-payment-applications", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function approveSubcontractPaymentApplication(id: string): Promise<SubcontractPaymentApplication> {
  return request<SubcontractPaymentApplication>(`/commercial/subcontract-payment-applications/${id}/approve`, {
    method: "POST",
  });
}

export async function postSubcontractPaymentApplication(
  id: string,
  wipAccountId: string,
  apAccountId: string,
  retentionAccountId: string
): Promise<SubcontractPaymentApplication> {
  const q = `?wip_account_id=${wipAccountId}&ap_account_id=${apAccountId}&retention_account_id=${retentionAccountId}`;
  return request<SubcontractPaymentApplication>(`/commercial/subcontract-payment-applications/${id}/post${q}`, {
    method: "POST",
  });
}

// ----------------- Commercial Summary & Periods -----------------
export interface CommercialSummary {
  total_prime_contract_value: number;
  total_subcontracts_value: number;
  total_client_change_orders_approved: number;
  total_client_change_orders_pending: number;
  total_subcontract_change_orders_approved: number;
  total_client_billed: number;
  total_client_retention: number;
  total_subcontractor_billed: number;
  total_subcontractor_retention: number;
  subcontracts_count: number;
  change_orders_count: number;
  payment_applications_count: number;
}

export async function getCommercialSummary(): Promise<CommercialSummary> {
  return request<CommercialSummary>("/commercial/summary");
}

export interface AccountingPeriod {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  is_closed: boolean;
  fiscal_year_id?: string;
  fiscal_year_name?: string;
}

// using getAccountingPeriods from accounting section above

// ----------------- Procurement & Supply Chain Extensions -----------------

export interface CreateSupplierInput {
  name: string;
  legal_name?: string;
  tax_identifier?: string;
  address?: string;
  status?: string;
  contacts?: Array<{
    name: string;
    email?: string;
    phone?: string;
    role?: string;
  }>;
}

export async function createSupplier(data: CreateSupplierInput): Promise<Supplier> {
  return request<Supplier>("/suppliers/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export interface PurchaseRequisitionLine {
  id?: string;
  requisition_id?: string;
  cost_code_id?: string;
  item_description: string;
  unit: string;
  quantity: number | string;
}

export interface PurchaseRequisition {
  id: string;
  pr_number: string;
  project_id: string;
  project_name?: string;
  requester_id: string;
  requester_name?: string;
  description?: string;
  status: "DRAFT" | "SUBMITTED" | "APPROVED" | "REJECTED" | "CANCELLED";
  required_date?: string;
  lines_count?: number;
  lines?: PurchaseRequisitionLine[];
  created_at?: string;
}

export interface CreatePurchaseRequisitionInput {
  pr_number: string;
  project_id: string;
  requester_id: string;
  description?: string;
  status?: string;
  required_date?: string;
  lines: Array<{
    cost_code_id?: string;
    item_description: string;
    unit: string;
    quantity: number;
  }>;
}

export async function getRequisitions(): Promise<PurchaseRequisition[]> {
  return request<PurchaseRequisition[]>("/requisitions/");
}

export async function createRequisition(data: CreatePurchaseRequisitionInput): Promise<PurchaseRequisition> {
  return request<PurchaseRequisition>("/requisitions/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function submitRequisition(id: string): Promise<{ status: string }> {
  return request<{ status: string }>(`/requisitions/${id}/submit`, {
    method: "POST",
  });
}

export async function approveRequisition(id: string): Promise<{ status: string }> {
  return request<{ status: string }>(`/requisitions/${id}/approve`, {
    method: "POST",
  });
}

export interface RFQLine {
  id?: string;
  rfq_id?: string;
  pr_line_id?: string;
  item_description: string;
  unit: string;
  quantity: number | string;
}

export interface RFQ {
  id: string;
  rfq_number: string;
  project_id: string;
  project_name?: string;
  requisition_id?: string;
  requisition_number?: string;
  title: string;
  description?: string;
  status: "DRAFT" | "PUBLISHED" | "CLOSED" | "CANCELLED";
  due_date?: string;
  lines_count?: number;
  lines?: RFQLine[];
  created_at?: string;
}

export interface CreateRFQInput {
  rfq_number: string;
  project_id: string;
  requisition_id?: string;
  title: string;
  description?: string;
  status?: string;
  due_date?: string;
  lines: Array<{
    pr_line_id?: string;
    item_description: string;
    unit: string;
    quantity: number;
  }>;
}

export async function getRFQs(): Promise<RFQ[]> {
  return request<RFQ[]>("/rfqs/");
}

export async function createRFQ(data: CreateRFQInput): Promise<RFQ> {
  return request<RFQ>("/rfqs/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function publishRFQ(id: string): Promise<{ status: string }> {
  return request<{ status: string }>(`/rfqs/${id}/publish`, {
    method: "POST",
  });
}

export async function closeRFQ(id: string): Promise<{ status: string }> {
  return request<{ status: string }>(`/rfqs/${id}/close`, {
    method: "POST",
  });
}

export interface SupplierQuotationLine {
  id?: string;
  quotation_id?: string;
  rfq_line_id: string;
  unit_price: number | string;
  quoted_quantity: number | string;
  amount: number | string;
  lead_time_days?: number;
  is_selected?: boolean;
}

export interface SupplierQuotation {
  id: string;
  rfq_id: string;
  rfq_title?: string;
  supplier_id: string;
  supplier_name?: string;
  quotation_reference?: string;
  status: "DRAFT" | "SUBMITTED" | "EVALUATED" | "ACCEPTED" | "REJECTED";
  valid_until?: string;
  currency?: string;
  notes?: string;
  total_amount?: number | string;
  lines?: SupplierQuotationLine[];
  created_at?: string;
}

export interface CreateSupplierQuotationInput {
  rfq_id: string;
  supplier_id: string;
  quotation_reference?: string;
  currency?: string;
  valid_until?: string;
  notes?: string;
  lines: Array<{
    rfq_line_id: string;
    unit_price: number;
    quoted_quantity: number;
    amount: number;
    lead_time_days?: number;
  }>;
}

export async function getQuotations(): Promise<SupplierQuotation[]> {
  return request<SupplierQuotation[]>("/quotations/");
}

export async function createQuotation(data: CreateSupplierQuotationInput): Promise<SupplierQuotation> {
  return request<SupplierQuotation>("/quotations/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function submitQuotation(id: string): Promise<{ status: string }> {
  return request<{ status: string }>(`/quotations/${id}/submit`, {
    method: "POST",
  });
}

export async function acceptQuotation(id: string): Promise<{ status: string }> {
  return request<{ status: string }>(`/quotations/${id}/accept`, {
    method: "POST",
  });
}

export interface ProcurementSummary {
  total_po_value: number;
  active_pos_count: number;
  pending_requisitions_count: number;
  approved_suppliers_count: number;
  total_suppliers_count: number;
  recent_pos: PurchaseOrder[];
}

export async function getProcurementSummary(): Promise<ProcurementSummary> {
  return request<ProcurementSummary>("/purchase-orders/summary");
}


// ==========================================
// Accounts Receivable (AR) & Progress Billing
// ==========================================

export interface ARSummary {
  total_invoiced: number;
  total_receivables: number;
  total_received: number;
  total_retention_held: number;
  current_receivables: number;
  aging_30_days: number;
  aging_60_days: number;
  aging_90_days: number;
  aging_over_90_days: number;
}

export interface ARInvoiceLine {
  id: string;
  invoice_id: string;
  project_id?: string;
  project_name?: string;
  cost_code_id?: string;
  cost_code_code?: string;
  description: string;
  quantity: number;
  unit_price: number;
  line_total: number;
  tax_rate?: number;
  tax_amount?: number;
}

export interface ARInvoice {
  id: string;
  number: string;
  client_id: string;
  client_name?: string;
  contract_id?: string;
  contract_number?: string;
  payment_application_id?: string;
  payment_application_number?: string;
  date: string;
  due_date: string;
  invoice_type: "STANDARD" | "PROGRESS_BILLING" | "RETAINAGE_RELEASE" | "CREDIT_NOTE";
  subtotal: number;
  tax_amount: number;
  retention_amount: number;
  total_amount: number;
  paid_amount?: number;
  outstanding_amount?: number;
  currency: string;
  description?: string;
  status: "DRAFT" | "SUBMITTED" | "APPROVED" | "POSTED" | "PARTIAL" | "PAID" | "CANCELLED";
  journal_id?: string;
  lines_count?: number;
  lines?: ARInvoiceLine[];
  created_at: string;
  updated_at?: string;
}

export interface CreateARInvoiceInput {
  number: string;
  client_id: string;
  contract_id?: string;
  payment_application_id?: string;
  date: string;
  due_date: string;
  invoice_type?: "STANDARD" | "PROGRESS_BILLING" | "RETAINAGE_RELEASE" | "CREDIT_NOTE";
  retention_amount?: number;
  currency?: string;
  description?: string;
  lines: Array<{
    project_id?: string;
    cost_code_id?: string;
    description: string;
    quantity: number;
    unit_price: number;
    tax_rate?: number;
    tax_amount?: number;
  }>;
}

export interface CustomerReceiptAllocation {
  id: string;
  payment_id: string;
  invoice_id: string;
  invoice_number?: string;
  allocated_amount: number;
}

export interface CustomerReceipt {
  id: string;
  payment_number: string;
  payment_type: "RECEIPT";
  client_id: string;
  client_name?: string;
  bank_account_id: string;
  bank_name?: string;
  bank_account_name?: string;
  payment_date: string;
  amount: number;
  currency: string;
  reference?: string;
  status: "DRAFT" | "SUBMITTED" | "APPROVED" | "POSTED" | "CLEARED" | "RECONCILED" | "VOIDED";
  journal_id?: string;
  allocations?: CustomerReceiptAllocation[];
  created_at: string;
}

export interface CreateCustomerReceiptInput {
  payment_number: string;
  client_id: string;
  bank_account_id: string;
  payment_date: string;
  amount: number;
  currency?: string;
  reference?: string;
  invoice_id?: string;
}

export async function getARSummary(): Promise<ARSummary> {
  return request<ARSummary>("/ar/summary");
}

export async function getARInvoices(params?: { client_id?: string; status?: string }): Promise<ARInvoice[]> {
  const query = new URLSearchParams();
  if (params?.client_id) query.append("client_id", params.client_id);
  if (params?.status) query.append("status", params.status);
  const qStr = query.toString() ? `?${query.toString()}` : "";
  return request<ARInvoice[]>(`/ar/invoices${qStr}`);
}

export async function getARInvoice(id: string): Promise<ARInvoice> {
  return request<ARInvoice>(`/ar/invoices/${id}`);
}

export async function createARInvoice(data: CreateARInvoiceInput): Promise<ARInvoice> {
  return request<ARInvoice>("/ar/invoices", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function createARInvoiceFromPaymentApp(paymentAppId: string): Promise<ARInvoice> {
  return request<ARInvoice>(`/ar/invoices/from-payment-application/${paymentAppId}`, {
    method: "POST",
  });
}

export async function approveARInvoice(id: string): Promise<ARInvoice> {
  return request<ARInvoice>(`/ar/invoices/${id}/approve`, {
    method: "POST",
  });
}

export async function postARInvoice(id: string): Promise<ARInvoice> {
  return request<ARInvoice>(`/ar/invoices/${id}/post`, {
    method: "POST",
  });
}

export async function getCustomerReceipts(params?: { client_id?: string; status?: string }): Promise<CustomerReceipt[]> {
  const query = new URLSearchParams();
  if (params?.client_id) query.append("client_id", params.client_id);
  if (params?.status) query.append("status", params.status);
  const qStr = query.toString() ? `?${query.toString()}` : "";
  return request<CustomerReceipt[]>(`/ar/receipts${qStr}`);
}

export async function getCustomerReceipt(id: string): Promise<CustomerReceipt> {
  return request<CustomerReceipt>(`/ar/receipts/${id}`);
}

export async function createCustomerReceipt(data: CreateCustomerReceiptInput): Promise<CustomerReceipt> {
  const payload = {
    reference: data.payment_number || data.reference || `REC-${Date.now()}`,
    payment_type: "AR_RECEIPT",
    date: data.payment_date,
    amount: data.amount,
    currency: data.currency || "USD",
    client_id: data.client_id,
    bank_account_id: data.bank_account_id,
    allocations: data.invoice_id
      ? [{ ar_invoice_id: data.invoice_id, amount: data.amount }]
      : [],
  };
  return request<CustomerReceipt>("/ar/receipts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ==========================================
// STAGE 27: PROJECT COST CONTROL & EVM TYPES
// ==========================================

export interface CostCodeSummary {
  cost_code_id: string;
  cost_code_code?: string;
  cost_code_name?: string;
  cost_category?: string;
  original_budget: number | string;
  approved_changes: number | string;
  current_budget: number | string;
  committed_cost: number | string;
  actual_cost: number | string;
  estimate_to_complete: number | string;
  estimate_at_completion: number | string;
  variance: number | string;
  variance_percentage?: number | string;
  status: "UNDER_BUDGET" | "ON_TRACK" | "AT_RISK" | "OVER_BUDGET" | string;
}

export interface ProjectCostKPISummary {
  project_id: string;
  project_name: string;
  project_number?: string;
  total_original_budget: number | string;
  total_approved_changes: number | string;
  total_current_budget: number | string;
  total_committed: number | string;
  total_actual: number | string;
  total_estimate_to_complete: number | string;
  total_estimate_at_completion: number | string;
  total_variance: number | string;
  cost_performance_index: number | string;
  status: "UNDER_BUDGET" | "ON_TRACK" | "AT_RISK" | "OVER_BUDGET" | string;
}

export interface PortfolioCostSummary {
  total_projects: number;
  total_budget: number | string;
  total_committed: number | string;
  total_actual: number | string;
  total_etc: number | string;
  total_eac: number | string;
  total_variance: number | string;
  overall_cpi: number | string;
  projects: ProjectCostKPISummary[];
}

export interface CostTransaction {
  project_id: string;
  cost_code_id?: string;
  cost_code_code?: string;
  cost_code_name?: string;
  date: string;
  amount: number | string;
  currency: string;
  source_type: "PURCHASE_ORDER" | "SUBCONTRACT" | "MATERIAL_ISSUE" | "AP_INVOICE" | "TIMESHEET" | "EQUIPMENT_USAGE" | "EQUIPMENT_FUEL" | "EQUIPMENT_MAINTENANCE" | string;
  source_id: string;
  source_reference?: string;
  cost_type: "COMMITTED" | "ACTUAL" | string;
}

export interface CreateProjectForecastLineInput {
  cost_code_id: string;
  etc_amount: number | string;
  notes?: string;
}

export interface CreateProjectForecastInput {
  forecast_number: string;
  date: string;
  notes?: string;
  lines: CreateProjectForecastLineInput[];
}

export interface ProjectForecastResponse {
  id: string;
  project_id: string;
  forecast_number: string;
  date: string;
  status: string;
}

export async function getPortfolioCostSummary(): Promise<PortfolioCostSummary> {
  return request<PortfolioCostSummary>("/project-cost/portfolio/summary");
}

export async function getProjectCostKPIs(projectId: string): Promise<ProjectCostKPISummary> {
  return request<ProjectCostKPISummary>(`/project-cost/projects/${projectId}/costs/kpi`);
}

export async function getProjectCostSummary(projectId: string): Promise<CostCodeSummary[]> {
  return request<CostCodeSummary[]>(`/project-cost/projects/${projectId}/costs/summary`);
}

export async function getProjectCostTransactions(projectId: string): Promise<CostTransaction[]> {
  return request<CostTransaction[]>(`/project-cost/projects/${projectId}/costs/transactions`);
}

export async function createProjectForecast(projectId: string, data: CreateProjectForecastInput): Promise<ProjectForecastResponse> {
  return request<ProjectForecastResponse>(`/project-cost/projects/${projectId}/forecasts`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}


// ============================================================================
// Stage 28: Equipment Fleet Lifecycle & Maintenance Workspace Types & APIs
// ============================================================================

export interface EquipmentSummary {
  total_units: number;
  available_units: number;
  in_use_units: number;
  maintenance_units: number;
  retired_units: number;
  utilization_rate: number | string;
  total_operating_hours: number | string;
  total_fuel_cost: number | string;
  total_maintenance_cost: number | string;
  total_equipment_cost: number | string;
}

export interface Equipment {
  id: string;
  name: string;
  make?: string;
  model?: string;
  year?: string;
  serial_number?: string;
  internal_id?: string;
  status: "AVAILABLE" | "IN_USE" | "MAINTENANCE" | "RETIRED" | string;
  base_hourly_cost: number | string;
  active_project_id?: string;
  active_project_name?: string;
  total_operating_hours: number | string;
  total_fuel_cost: number | string;
  total_maintenance_cost: number | string;
}

export interface CreateEquipmentInput {
  name: string;
  make?: string;
  model?: string;
  year?: string;
  serial_number?: string;
  internal_id?: string;
  status?: string;
  base_hourly_cost: number | string;
}

export interface UpdateEquipmentInput {
  name?: string;
  make?: string;
  model?: string;
  year?: string;
  serial_number?: string;
  internal_id?: string;
  status?: string;
  base_hourly_cost?: number | string;
}

export interface EquipmentAssignment {
  id: string;
  equipment_id: string;
  project_id: string;
  start_date: string;
  end_date?: string;
  hourly_cost_override?: number | string;
  equipment_name?: string;
  equipment_internal_id?: string;
  project_name?: string;
}

export interface CreateEquipmentAssignmentInput {
  equipment_id: string;
  project_id: string;
  start_date: string;
  end_date?: string;
  hourly_cost_override?: number | string;
}

export interface EquipmentUsageLine {
  id: string;
  usage_log_id: string;
  project_id: string;
  cost_code_id: string;
  date: string;
  hours: number | string;
  hourly_cost_rate?: number | string;
  total_cost?: number | string;
  project_name?: string;
  cost_code_code?: string;
  cost_code_name?: string;
}

export interface EquipmentUsageLog {
  id: string;
  equipment_id: string;
  equipment_name?: string;
  equipment_internal_id?: string;
  period_start: string;
  period_end: string;
  status: "DRAFT" | "SUBMITTED" | "APPROVED" | string;
  total_hours: number | string;
  total_cost: number | string;
  lines: EquipmentUsageLine[];
}

export interface CreateEquipmentUsageLineInput {
  project_id: string;
  cost_code_id: string;
  date: string;
  hours: number | string;
}

export interface CreateEquipmentUsageLogInput {
  equipment_id: string;
  period_start: string;
  period_end: string;
  lines: CreateEquipmentUsageLineInput[];
}

export interface FuelTransaction {
  id: string;
  equipment_id: string;
  project_id?: string;
  cost_code_id?: string;
  date: string;
  volume: number | string;
  unit_cost: number | string;
  total_cost: number | string;
  equipment_name?: string;
  equipment_internal_id?: string;
  project_name?: string;
  cost_code_code?: string;
}

export interface CreateFuelTransactionInput {
  equipment_id: string;
  project_id?: string;
  cost_code_id?: string;
  date: string;
  volume: number | string;
  unit_cost: number | string;
}

export interface MaintenanceRecord {
  id: string;
  equipment_id: string;
  project_id?: string;
  cost_code_id?: string;
  type: "PREVENTIVE" | "CORRECTIVE" | string;
  date: string;
  description: string;
  duration_hours?: number | string;
  cost: number | string;
  equipment_name?: string;
  equipment_internal_id?: string;
  project_name?: string;
  cost_code_code?: string;
}

export interface CreateMaintenanceRecordInput {
  equipment_id: string;
  project_id?: string;
  cost_code_id?: string;
  type: string;
  date: string;
  description: string;
  duration_hours?: number | string;
  cost: number | string;
}

export async function getEquipmentSummary(): Promise<EquipmentSummary> {
  return request<EquipmentSummary>("/equipment/summary");
}

export async function getEquipmentList(): Promise<Equipment[]> {
  return request<Equipment[]>("/equipment/");
}

export async function createEquipment(data: CreateEquipmentInput): Promise<Equipment> {
  return request<Equipment>("/equipment/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateEquipment(id: string, data: UpdateEquipmentInput): Promise<Equipment> {
  return request<Equipment>(`/equipment/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function getEquipmentAssignments(): Promise<EquipmentAssignment[]> {
  return request<EquipmentAssignment[]>("/equipment/assignments");
}

export async function createEquipmentAssignment(data: CreateEquipmentAssignmentInput): Promise<EquipmentAssignment> {
  return request<EquipmentAssignment>("/equipment/assignments", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getEquipmentUsageLogs(): Promise<EquipmentUsageLog[]> {
  return request<EquipmentUsageLog[]>("/equipment/usage-logs");
}

export async function createEquipmentUsageLog(data: CreateEquipmentUsageLogInput): Promise<EquipmentUsageLog> {
  return request<EquipmentUsageLog>("/equipment/usage-logs", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function submitEquipmentUsageLog(id: string): Promise<EquipmentUsageLog> {
  return request<EquipmentUsageLog>(`/equipment/usage-logs/${id}/submit`, {
    method: "POST",
  });
}

export async function approveEquipmentUsageLog(id: string): Promise<EquipmentUsageLog> {
  return request<EquipmentUsageLog>(`/equipment/usage-logs/${id}/approve`, {
    method: "POST",
  });
}

export async function getFuelTransactions(): Promise<FuelTransaction[]> {
  return request<FuelTransaction[]>("/equipment/fuel");
}

export async function createFuelTransaction(data: CreateFuelTransactionInput): Promise<FuelTransaction> {
  return request<FuelTransaction>("/equipment/fuel", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getMaintenanceRecords(): Promise<MaintenanceRecord[]> {
  return request<MaintenanceRecord[]>("/equipment/maintenance");
}

export async function createMaintenanceRecord(data: CreateMaintenanceRecordInput): Promise<MaintenanceRecord> {
  return request<MaintenanceRecord>("/equipment/maintenance", {
    method: "POST",
    body: JSON.stringify(data),
  });
}


// HR
export interface Employee {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  position_id: string;
  department_id: string;
  base_hourly_rate: number;
}
export async function getEmployees(): Promise<Employee[]> {
  return request<Employee[]>('/employees');
}
