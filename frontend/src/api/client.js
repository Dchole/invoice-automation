const BASE = '/api';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (options.method === 'DELETE' && res.status === 204) return null;
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

export const api = {
  // Clients
  getClients: (params) => request(`/clients${params ? `?${new URLSearchParams(params)}` : ''}`),
  getClient: (id) => request(`/clients/${id}`),
  createClient: (data) => request('/clients', { method: 'POST', body: JSON.stringify(data) }),
  updateClient: (id, data) => request(`/clients/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteClient: (id) => request(`/clients/${id}`, { method: 'DELETE' }),

  // Sessions
  getSessions: (params) => request(`/sessions${params ? `?${new URLSearchParams(params)}` : ''}`),
  getUnbilled: (params) => request(`/sessions/unbilled${params ? `?${new URLSearchParams(params)}` : ''}`),
  createSession: (data) => request('/sessions', { method: 'POST', body: JSON.stringify(data) }),
  updateSession: (id, data) => request(`/sessions/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteSession: (id) => request(`/sessions/${id}`, { method: 'DELETE' }),

  // Invoices
  getInvoices: (params) => request(`/invoices${params ? `?${new URLSearchParams(params)}` : ''}`),
  getInvoice: (id) => request(`/invoices/${id}`),
  createInvoice: (data) => request('/invoices', { method: 'POST', body: JSON.stringify(data) }),
  generateInvoices: (data) => request('/invoices/generate', { method: 'POST', body: JSON.stringify(data) }),
  sendInvoice: (id) => request(`/invoices/${id}/send`, { method: 'POST' }),

  // Payments
  getPayments: (params) => request(`/payments${params ? `?${new URLSearchParams(params)}` : ''}`),
  createPayment: (data) => request('/payments', { method: 'POST', body: JSON.stringify(data) }),

  // Reminders
  getReminders: (params) => request(`/reminders${params ? `?${new URLSearchParams(params)}` : ''}`),
  sendReminder: (id) => request(`/reminders/${id}/send`, { method: 'POST' }),
  skipReminder: (id) => request(`/reminders/${id}/skip`, { method: 'PUT' }),
  runReminders: () => request('/reminders/run', { method: 'POST' }),

  // Dashboard
  getDashboardSummary: (currency) => request(`/dashboard/summary${currency ? `?display_currency=${currency}` : ''}`),
  getDashboardAging: (currency) => request(`/dashboard/aging${currency ? `?display_currency=${currency}` : ''}`),
  getClientScores: (currency) => request(`/dashboard/client-scores${currency ? `?display_currency=${currency}` : ''}`),
  getCashflow: (days = 90) => request(`/dashboard/cashflow?days=${days}`),

  // Export
  exportInvoicesCsv: () => `${BASE}/import/export/invoices-csv`,
  exportPaymentsCsv: () => `${BASE}/import/export/payments-csv`,
  exportBackup: () => `${BASE}/import/export/backup`,

  // Import
  uploadExcel: (file) => {
    const form = new FormData();
    form.append('file', file);
    return fetch(`${BASE}/import/excel`, { method: 'POST', body: form }).then(r => r.json());
  },
};
