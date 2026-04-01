import { useState, useCallback } from 'react';
import { useApi } from '../hooks/useApi';
import { useAction } from '../hooks/useAction';
import { useToast } from '../components/common/Toast';
import { api } from '../api/client';
import StatusBadge from '../components/common/StatusBadge';
import Pagination from '../components/common/Pagination';

const REMINDER_LABELS = {
  friendly: 'Friendly Reminder',
  due: 'Payment Due',
  overdue: 'Overdue Notice',
  escalation: 'Escalation',
};

export default function RemindersPage() {
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState('pending');
  const reminderParams = { page, per_page: 25, ...(filter !== 'all' ? { status: filter } : {}) };
  const { data: result, loading, refetch } = useApi(() => api.getReminders(reminderParams), [page, filter]);
  const { data: invoiceResult } = useApi(() => api.getInvoices({ per_page: 100 }));
  const invoices = invoiceResult?.items || [];
  const { data: clients } = useApi(() => api.getClients());
  const toast = useToast();
  const [actionId, setActionId] = useState(null);
  const [actionType, setActionType] = useState(null);

  const reminders = result?.items || [];

  const clientMap = Object.fromEntries((clients || []).map(c => [c.id, c.name]));
  const invoiceMap = Object.fromEntries((invoices || []).map(i => [i.id, i]));

  const sendAction = useAction(
    useCallback(async (id) => {
      await api.sendReminder(id);
      return id;
    }, []),
    {
      onSuccess: () => {
        toast.success('Reminder sent');
        setActionId(null);
        setActionType(null);
        refetch();
      },
      onError: (msg) => {
        toast.error(`Failed to send: ${msg}`);
        setActionId(null);
        setActionType(null);
      },
    }
  );

  const skipAction = useAction(
    useCallback(async (id) => {
      await api.skipReminder(id);
      return id;
    }, []),
    {
      onSuccess: () => {
        toast.success('Reminder skipped');
        setActionId(null);
        setActionType(null);
        refetch();
      },
      onError: (msg) => {
        toast.error(`Failed to skip: ${msg}`);
        setActionId(null);
        setActionType(null);
      },
    }
  );

  const runAction = useAction(
    useCallback(async () => {
      return await api.runReminders();
    }, []),
    {
      onSuccess: (result) => {
        if (result.reminders_sent > 0 || result.overdue_marked > 0) {
          toast.success(`${result.reminders_sent} reminder${result.reminders_sent !== 1 ? 's' : ''} sent, ${result.overdue_marked} marked overdue`);
        } else {
          toast.info('No reminders are due yet');
        }
        refetch();
      },
      onError: (msg) => toast.error(`Failed to process: ${msg}`),
    }
  );

  const sendReminder = async (id) => {
    setActionId(id);
    setActionType('send');
    await sendAction.run(id);
  };

  const skipReminder = async (id) => {
    setActionId(id);
    setActionType('skip');
    await skipAction.run(id);
  };

  const handleFilterChange = (f) => {
    setFilter(f);
    setPage(1);
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64" style={{ color: 'var(--color-text-tertiary)' }}>
      <p className="text-sm">Loading...</p>
    </div>
  );

  // When filtered to "pending", the first item (sorted by scheduled_date) is the next due
  const nextDue = (filter === 'pending' && reminders.length > 0) ? reminders[0].scheduled_date : null;

  return (
    <div className="animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1
            className="text-2xl font-bold tracking-tight"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text-primary)' }}
          >
            Reminders
          </h1>
          {result && (
            <p className="text-sm mt-1" style={{ color: 'var(--color-text-tertiary)' }}>
              <span className="font-medium" style={{ color: 'var(--color-status-amber)' }}>{result.total} {filter === 'all' ? 'total' : filter === 'pending' ? 'scheduled' : filter}</span>
              {nextDue && <span> — next due {nextDue}</span>}
            </p>
          )}
        </div>
        <button
          onClick={() => runAction.run()}
          disabled={runAction.loading}
          className="btn-primary px-5 py-2.5"
          style={{ opacity: runAction.loading ? 0.6 : 1 }}
        >
          {runAction.loading ? 'Checking...' : 'Send Due Reminders Now'}
        </button>
      </div>

      {/* Filter pills */}
      <div className="flex flex-wrap gap-2 mb-5">
        {['pending', 'sent', 'skipped', 'all'].map(f => (
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
            {f === 'all' ? 'All' : f === 'pending' ? 'Scheduled' : f === 'sent' ? 'Sent' : 'Skipped'}
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
                <th>Scheduled</th>
                <th>Invoice</th>
                <th>Client</th>
                <th>Type</th>
                <th>Status</th>
                <th>Sent</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {reminders.map((r) => {
                const inv = invoiceMap[r.invoice_id];
                const clientName = inv ? clientMap[inv.client_id] || '-' : '-';
                const isActing = actionId === r.id;
                return (
                  <tr key={r.id}>
                    <td>{r.scheduled_date}</td>
                    <td className="font-mono text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                      {inv?.invoice_number || `#${r.invoice_id}`}
                    </td>
                    <td className="font-medium" style={{ color: 'var(--color-text-primary)' }}>{clientName}</td>
                    <td>{REMINDER_LABELS[r.type] || r.type}</td>
                    <td><StatusBadge status={r.status} /></td>
                    <td style={{ color: 'var(--color-text-tertiary)' }}>
                      {r.sent_at ? new Date(r.sent_at).toLocaleDateString() : '-'}
                    </td>
                    <td className="space-x-3">
                      {r.status === 'pending' && (
                        <>
                          <button
                            onClick={() => sendReminder(r.id)}
                            disabled={isActing}
                            className="text-xs font-medium transition-colors duration-150"
                            style={{
                              color: 'var(--color-accent)',
                              opacity: isActing && actionType === 'send' ? 0.4 : 1,
                            }}
                          >
                            {isActing && actionType === 'send' ? 'Sending...' : 'Send Now'}
                          </button>
                          <button
                            onClick={() => skipReminder(r.id)}
                            disabled={isActing}
                            className="text-xs font-medium transition-colors duration-150"
                            style={{
                              color: 'var(--color-text-tertiary)',
                              opacity: isActing && actionType === 'skip' ? 0.4 : 1,
                            }}
                          >
                            {isActing && actionType === 'skip' ? 'Skipping...' : 'Skip'}
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                );
              })}
              {reminders.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-12 text-center" style={{ color: 'var(--color-text-tertiary)' }}>
                    No reminders found.
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
    </div>
  );
}
