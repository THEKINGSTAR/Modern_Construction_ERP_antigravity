const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface Project {
  id: string;
  project_number: string;
  name: string;
  client_id?: string | null;
  start_date?: string | null;
  target_end_date?: string | null;
  budget_amount?: string | null;
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
  type: string;
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
  account_type: string;
  is_control_account: boolean;
  chart_of_accounts_id: string;
}

export interface JournalLine {
  id?: string;
  account_id: string;
  debit: string;
  credit: string;
  project_id?: string | null;
  cost_code_id?: string | null;
}

export interface Journal {
  id: string;
  date: string;
  reference?: string | null;
  description: string;
  status: string;
  lines: JournalLine[];
}

export interface APInvoice {
  id: string;
  number: string;
  supplier_id: string;
  date: string;
  due_date: string;
  status: string;
  invoice_type: string;
  total_amount: string;
  currency: string;
  description?: string | null;
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

// ----------------- Inventory -----------------
export async function getMaterials(): Promise<Material[]> {
  return request<Material[]>('/inventory/materials');
}

export async function createMaterial(data: Partial<Material>): Promise<Material> {
  return request<Material>('/inventory/materials', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getWarehouses(): Promise<Warehouse[]> {
  return request<Warehouse[]>('/inventory/warehouses');
}

export async function createWarehouse(data: Partial<Warehouse>): Promise<Warehouse> {
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

export async function createGoodsReceipt(data: any): Promise<any> {
  return request<any>('/inventory/goods-receipts', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function createInventoryAdjustment(data: any): Promise<any> {
  return request<any>("/inventory/adjustments", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function createMaterialIssue(data: any): Promise<any> {
  return request<any>('/inventory/material-issues', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ----------------- Procurement -----------------
export async function getSuppliers(): Promise<any[]> {
  return request<any[]>('/suppliers/');
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

// ----------------- Accounting & AP -----------------
export async function getAccounts(): Promise<Account[]> {
  return request<Account[]>('/accounting/accounts');
}

export async function getJournals(): Promise<Journal[]> {
  return request<Journal[]>('/accounting/journals');
}

export async function createJournal(data: any): Promise<Journal> {
  return request<Journal>('/accounting/journals?auto_post=true', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getAPInvoices(): Promise<APInvoice[]> {
  return request<APInvoice[]>('/ap/invoices');
}
