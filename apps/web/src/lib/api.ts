const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface Project {
  id: string;
  project_number: string;
  name: string;
  client_id?: string;
  start_date?: string;
  target_end_date?: string;
  budget_amount?: string;
  status: string;
}

export interface Client {
  id: string;
  name: string;
  legal_name?: string;
  contact_information?: string;
  billing_address?: string;
  tax_identifier?: string;
  status: string;
}

export interface InventoryBalance {
  id: string;
  warehouse_id: string;
  material_id: string;
  quantity: string;
  total_cost: string;
}

export interface TrialBalanceReport {
  as_of_date: string;
  lines: Array<{
    account_code: string;
    account_name: string;
    account_type: string;
    debit_balance: string;
    credit_balance: string;
  }>;
  total_debit: string;
  total_credit: string;
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

  return res.json();
}

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
    throw new Error('Authentication failed. Check demo credentials.');
  }

  const data = await res.json();
  setToken(data.access_token);
  return data;
}

export async function getProjects(): Promise<Project[]> {
  return request<Project[]>('/projects/');
}

export async function createProject(data: Partial<Project>): Promise<Project> {
  return request<Project>('/projects/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getClients(): Promise<Client[]> {
  return request<Client[]>('/clients/');
}

export async function createClient(data: Partial<Client>): Promise<Client> {
  return request<Client>('/clients/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getInventoryBalances(): Promise<InventoryBalance[]> {
  return request<InventoryBalance[]>('/inventory/balances');
}

export async function getTrialBalance(): Promise<TrialBalanceReport> {
  return request<TrialBalanceReport>('/reports/accounting/trial-balance');
}

export async function getProjectDashboard(projectId: string): Promise<ProjectDashboard> {
  return request<ProjectDashboard>(`/reports/projects/${projectId}/dashboard`);
}
