import { useState, useCallback } from 'react';
import { useApi } from '../hooks/useApi';
import { useAction } from '../hooks/useAction';
import { useToast } from '../components/common/Toast';
import { api } from '../api/client';
import StatusBadge from '../components/common/StatusBadge';
import Modal from '../components/common/Modal';
import Pagination from '../components/common/Pagination';

const fmt = (n) => `$${Number(n).toFixed(2)}`;

export default function InvoicesPage() {
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState('all');
  const invoiceParams = { page, per_page: 25, ...(filter !== 'all' ? { status: filter } : {}) };
  const { data: result, loading, refetch } = useApi(() => api.getInvoices(invoiceParams), [page, filter]);
  const { data: clients } = useApi(() => api.getClients());
  const { data: unbilled } = useApi(() => api.getUnbilled());
  const toast = useToast();
  const [showGenerate, setShowGenerate] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({ client_id: '', session_ids: [], tax_rate: 0 });
  const [generateTaxRate, setGenerateTaxRate] = useState('0');
  const [sendingId, setSendingId] = useState(null);

  const invoices = result?.items || [];
  const clientMap = Object.fromEntries((clients || []).map(c => [c.id, c]));

  const handleFilterChange = (f) => {
    setFilter(f);
    setPage(1);
  };

  const generateAction = useAction(
    useCallback(async (taxRate) => {
      await api.generateInvoices({ tax_rate: Number(taxRate) });
    }, []),
    {
      onSuccess: () => {
        setShowGenerate(false);
        setGenerateTaxRate('0');
        toast.success('Invoices created');
        refetch();
      },
      onError: (msg) => toast.error(`Failed to generate invoices: ${msg}`),
    }
  );

  const sendAction = useAction(
    useCallback(async (id) => {
      await api.sendInvoice(id);
      return id;
    }, []),
    {
      onSuccess: () => {
        toast.success('Invoice sent to client');
        setSendingId(null);
        refetch();
      },
      onError: (msg) => {
        toast.error(`Failed to send: ${msg}`);
        setSendingId(null);
      },
    }
  );

  const createAction = useAction(
    useCallback(async (formData) => {
      await api.createInvoice({
        client_id: Number(formData.client_id),
        session_ids: formData.session_ids,
        tax_rate: Number(formData.tax_rate),
      });
    }, []),
    {
      onSuccess: () => {
        setShowCreate(false);
        setCreateForm({ client_id: '', session_ids: [], tax_rate: 0 });
        toast.success('Invoice created');
        refetch();
      },
      onError: (msg) => toast.error(`Failed to create invoice: ${msg}`),
    }
  );

  const sendInvoice = async (id) => {
    setSendingId(id);
    await sendAction.run(id);
  };

  // Server-side filtering via params, no client-side filter needed

  const unbilledByClient = {};
  (unbilled || []).forEach(s => {
    if (!unbilledByClient[s.client_id]) unbilledByClient[s.client_id] = [];
    unbilledByClient[s.client_id].push(s);
  });

  const clientUnbilled = unbilled?.filter(s => String(s.client_id) === createForm.client_id) || [];

  if (loading) return (
    <div className="flex items-center justify-center h-64" style={{ color: 'var(--color-text-tertiary)' }}>
      <p className="text-sm">Loading...</p>
    </div>
  );

  return (
    <div className="animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <h1
          className="text-2xl font-bold tracking-tight"
          style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text-primary)' }}
        >
          Invoices
        </h1>
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
          {unbilled?.length > 0 && (
            <button
              onClick={() => setShowGenerate(true)}
              className="btn-success px-5 py-2.5 flex items-center justify-center gap-2"
            >
              <span className="w-2 h-2 rounded-full bg-white opacity-80 animate-pulse" />
              Create Invoices ({unbilled.length} sessions)
            </button>
          )}
          <button onClick={() => setShowCreate(true)} className="btn-primary">
            + Create Invoice
          </button>
        </div>
      </div>

      {/* Filter pills */}
      <div className="flex flex-wrap gap-2 mb-5">
        {['all', 'draft', 'sent', 'paid', 'overdue'].map(f => (
          <button
            key={f}
            onClick={() => handleFilterChange(f)}
            className="px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all duration-150"
            style={{
              fontFamily: 'var(--font-heading)',
              backgroundColor: filter === f ? 'var(--color-surface-dark)' : 'var(--color-canvas-sunken)',
              color: filter === f ? 'var(--color-text-inverse)' : 'var(--color-text-secondary)',
              border: filter === f ? 'none' : '1px solid var(--color-border-subtle)',
            }}
          >
            {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      <div
        className="rounded-xl overflow-hidden"
        style={{ backgroundColor: 'var(--color-canvas-raised)', boxShadow: 'var(--shadow-card)' }}
      >
        <div className="overflow-x-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th>Invoice #</th>
              <th>Client</th>
              <th>Created</th>
              <th>Payment Due</th>
              <th>Total</th>
              <th>Amount Paid</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map((inv) => (
              <tr key={inv.id}>
                <td className="font-mono text-xs" style={{ color: 'var(--color-text-tertiary)' }}>{inv.invoice_number}</td>
                <td className="font-medium" style={{ color: 'var(--color-text-primary)' }}>{clientMap[inv.client_id]?.name || `#${inv.client_id}`}</td>
                <td>{inv.issue_date}</td>
                <td>{inv.due_date}</td>
                <td className="font-medium" style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text-primary)' }}>{fmt(inv.total)} {inv.currency}</td>
                <td style={{ fontFamily: 'var(--font-heading)' }}>{fmt(inv.amount_paid)}</td>
                <td><StatusBadge status={inv.status} /></td>
                <td className="space-x-3">
                  {inv.status === 'draft' && (
                    <button
                      onClick={() => sendInvoice(inv.id)}
                      disabled={sendingId === inv.id}
                      className="text-xs font-medium transition-colors duration-150"
                      style={{
                        color: 'var(--color-accent)',
                        opacity: sendingId === inv.id ? 0.4 : 1,
                      }}
                    >
                      {sendingId === inv.id ? 'Sending...' : 'Send to Client'}
                    </button>
                  )}
                  {(inv.status === 'sent' || inv.status === 'overdue') && (
                    <a
                      href={`/reminders?invoice_id=${inv.id}`}
                      className="text-xs font-medium transition-colors duration-150"
                      style={{ color: 'var(--color-status-amber)' }}
                    >
                      View Reminders
                    </a>
                  )}
                </td>
              </tr>
            ))}
            {invoices.length === 0 && (
              <tr>
                <td colSpan={8} className="py-12! text-center" style={{ color: 'var(--color-text-tertiary)' }}>
                  No invoices found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
        </div>
        {result && (
          <Pagination
            page={result.page}
            totalPages={result.total_pages}
            total={result.total}
            perPage={result.per_page}
            onPageChange={setPage}
          />
        )}
      </div>

      {/* Generate All modal */}
      <Modal open={showGenerate} onClose={() => setShowGenerate(false)} title="Create Invoices for Unbilled Work">
        <p className="text-sm mb-5" style={{ color: 'var(--color-text-secondary)' }}>
          You have <strong style={{ color: 'var(--color-text-primary)' }}>{unbilled?.length}</strong> sessions that haven't been billed yet, across <strong style={{ color: 'var(--color-text-primary)' }}>{Object.keys(unbilledByClient).length}</strong> clients. Ready to create invoices?
        </p>
        <div className="space-y-2 mb-5 max-h-48 overflow-y-auto">
          {Object.entries(unbilledByClient).map(([cid, sessions]) => (
            <div
              key={cid}
              className="flex justify-between text-sm rounded-lg p-3"
              style={{ backgroundColor: 'var(--color-canvas-sunken)' }}
            >
              <span style={{ color: 'var(--color-text-primary)' }}>{clientMap[cid]?.name}</span>
              <span className="font-medium" style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text-secondary)' }}>
                {sessions.length} sessions &middot; {fmt(sessions.reduce((s, x) => s + x.amount, 0))}
              </span>
            </div>
          ))}
        </div>
        <div className="mb-5">
          <label className="form-label">Tax Rate %</label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={generateTaxRate}
            onChange={e => setGenerateTaxRate(e.target.value)}
            className="form-input"
            placeholder="0 for no tax"
          />
          <p className="text-xs mt-1" style={{ color: 'var(--color-text-tertiary)' }}>
            Leave at 0 if you don't charge tax. Applied to all invoices.
          </p>
        </div>
        <button
          onClick={() => generateAction.run(generateTaxRate)}
          disabled={generateAction.loading}
          className="w-full btn-success py-2.5"
          style={{ opacity: generateAction.loading ? 0.6 : 1 }}
        >
          {generateAction.loading ? 'Creating...' : 'Create All Invoices'}
        </button>
      </Modal>

      {/* Create Invoice modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create Invoice">
        <form onSubmit={(e) => { e.preventDefault(); createAction.run(createForm); }} className="space-y-4">
          <div>
            <label className="form-label">Client</label>
            <select required value={createForm.client_id} onChange={e => setCreateForm({ ...createForm, client_id: e.target.value, session_ids: [] })} className="form-input">
              <option value="">Select Client</option>
              {clients?.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          {clientUnbilled.length > 0 && (
            <div
              className="space-y-1.5 max-h-40 overflow-y-auto rounded-lg p-3"
              style={{ border: '1px solid var(--color-border-subtle)', backgroundColor: 'var(--color-canvas-sunken)' }}
            >
              <p className="form-label mb-2">Select sessions to include</p>
              {clientUnbilled.map(s => (
                <label key={s.id} className="flex items-center gap-2.5 text-sm cursor-pointer" style={{ color: 'var(--color-text-secondary)' }}>
                  <input
                    type="checkbox"
                    checked={createForm.session_ids.includes(s.id)}
                    onChange={(e) => {
                      const ids = e.target.checked
                        ? [...createForm.session_ids, s.id]
                        : createForm.session_ids.filter(x => x !== s.id);
                      setCreateForm({ ...createForm, session_ids: ids });
                    }}
                    className="rounded"
                    style={{ accentColor: 'var(--color-accent)' }}
                  />
                  {s.date} — {s.duration_minutes} min — {fmt(s.amount)}{s.description ? ` — ${s.description}` : ''}
                </label>
              ))}
            </div>
          )}
          <div>
            <label className="form-label">Tax Rate %</label>
            <input type="number" step="0.01" value={createForm.tax_rate} onChange={e => setCreateForm({ ...createForm, tax_rate: e.target.value })} className="form-input" />
          </div>
          <button
            type="submit"
            disabled={createAction.loading}
            className="w-full btn-primary py-2.5"
            style={{ opacity: createAction.loading ? 0.6 : 1 }}
          >
            {createAction.loading ? 'Creating...' : 'Create Invoice'}
          </button>
        </form>
      </Modal>
    </div>
  );
}
