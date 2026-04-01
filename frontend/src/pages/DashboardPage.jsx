import { useState } from 'react';
import { useApi } from '../hooks/useApi';
import { api } from '../api/client';
import Card from '../components/common/Card';
import StatusBadge from '../components/common/StatusBadge';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';

const fmt = (n, cur) => {
  const s = `$${Number(n).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  return cur ? `${s} ${cur}` : s;
};

const PIE_COLORS = {
  'Paid': '#3d8b5e',
  'Awaiting Payment': '#4576a9',
  'Overdue': '#b84c4c',
  'Not Sent': '#7c7f86',
};

const CHART_AXIS = {
  tick: { fontSize: 11, fill: '#8e9099', fontFamily: 'DM Sans' },
  axisLine: false,
  tickLine: false,
};

const CHART_TOOLTIP = {
  contentStyle: {
    backgroundColor: '#1a1d23',
    border: 'none',
    borderRadius: '6px',
    fontSize: '12px',
    color: '#f0efe9',
    fontFamily: 'DM Sans',
    boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
  },
  itemStyle: { color: '#f0efe9' },
  labelStyle: { color: '#9a9ca3' },
};

function greetingText() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

function formatDate() {
  return new Date().toLocaleDateString('en-US', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  });
}

export default function DashboardPage() {
  const [currency, setCurrency] = useState(null); // null = mixed (no conversion)
  const { data: summary, loading: l1 } = useApi(() => api.getDashboardSummary(currency), [currency]);
  const { data: aging, loading: l2 } = useApi(() => api.getDashboardAging(currency), [currency]);
  const { data: scores, loading: l3 } = useApi(() => api.getClientScores(currency), [currency]);
  const [forecastDays, setForecastDays] = useState(90);
  const { data: cashflow, loading: l4 } = useApi(() => api.getCashflow(forecastDays), [forecastDays]);

  const currencySymbol = currency || 'Mixed';

  if (l1 || l2 || l3) return (
    <div className="flex items-center justify-center h-64" style={{ color: 'var(--color-text-tertiary)' }}>
      <div className="text-center">
        <div
          className="w-8 h-8 rounded-full border-2 border-t-transparent mx-auto mb-3 animate-spin"
          style={{ borderColor: 'var(--color-border)', borderTopColor: 'transparent' }}
        />
        <p className="text-sm">Loading dashboard...</p>
      </div>
    </div>
  );

  const agingData = aging ? [
    { name: 'Not Yet Due', value: aging.current },
    { name: '1–30 Days Late', value: aging.days_30 },
    { name: '31–60 Days Late', value: aging.days_60 },
    { name: '90+ Days Late', value: aging.days_90_plus },
  ] : [];

  const statusData = summary ? [
    { name: 'Paid', value: summary.paid_invoices },
    { name: 'Awaiting Payment', value: summary.sent_invoices },
    { name: 'Overdue', value: summary.overdue_invoices },
    { name: 'Not Sent', value: summary.draft_invoices },
  ].filter(d => d.value > 0) : [];

  const needsAttention = summary && (summary.overdue_invoices > 0 || summary.unbilled_sessions > 0 || summary.draft_invoices > 0);

  return (
    <div className="animate-fade-in">
      {/* Greeting header + currency toggle */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1
            className="text-2xl font-bold tracking-tight"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text-primary)' }}
          >
            {greetingText()}
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--color-text-tertiary)' }}>
            {formatDate()}
          </p>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-1 rounded-lg p-1" style={{ backgroundColor: 'var(--color-canvas-sunken)', border: '1px solid var(--color-border-subtle)' }}>
            {[null, 'CAD', 'USD'].map(c => (
              <button
                key={c || 'mixed'}
                onClick={() => setCurrency(c)}
                className="px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-150"
                style={{
                  fontFamily: 'var(--font-heading)',
                  backgroundColor: currency === c ? 'var(--color-surface-dark)' : 'transparent',
                  color: currency === c ? 'var(--color-text-inverse)' : 'var(--color-text-tertiary)',
                }}
              >
                {c || 'Mixed'}
              </button>
            ))}
          </div>
          <p className="text-[0.65rem] mt-1.5" style={{ color: 'var(--color-text-tertiary)' }}>
            {currency ? `All amounts in ${currency}` : 'Amounts in original currencies'}
          </p>
        </div>
      </div>

      {/* Action alerts */}
      {needsAttention && (
        <div className="space-y-3 mb-8">
          {summary.overdue_invoices > 0 && (
            <a
              href="/invoices?status=overdue"
              className="flex items-center justify-between rounded-xl px-5 py-4 transition-all duration-150"
              style={{
                backgroundColor: 'rgba(184, 76, 76, 0.08)',
                border: '1px solid rgba(184, 76, 76, 0.25)',
              }}
              onMouseEnter={e => { e.currentTarget.style.backgroundColor = 'rgba(184, 76, 76, 0.14)'; }}
              onMouseLeave={e => { e.currentTarget.style.backgroundColor = 'rgba(184, 76, 76, 0.08)'; }}
            >
              <div className="flex items-center gap-3">
                <span className="w-2.5 h-2.5 rounded-full animate-pulse" style={{ backgroundColor: 'var(--color-status-red)' }} />
                <span className="text-sm font-medium" style={{ color: 'var(--color-status-red)' }}>
                  {summary.overdue_invoices} overdue invoice{summary.overdue_invoices !== 1 ? 's' : ''} — {fmt(summary.total_overdue)} unpaid
                </span>
              </div>
              <span className="text-xs font-medium" style={{ color: 'var(--color-status-red)', opacity: 0.7 }}>
                View &rarr;
              </span>
            </a>
          )}
          {summary.unbilled_sessions > 0 && (
            <a
              href="/invoices"
              className="flex items-center justify-between rounded-xl px-5 py-4 transition-all duration-150"
              style={{
                backgroundColor: 'rgba(200, 150, 50, 0.08)',
                border: '1px solid rgba(200, 150, 50, 0.25)',
              }}
              onMouseEnter={e => { e.currentTarget.style.backgroundColor = 'rgba(200, 150, 50, 0.14)'; }}
              onMouseLeave={e => { e.currentTarget.style.backgroundColor = 'rgba(200, 150, 50, 0.08)'; }}
            >
              <div className="flex items-center gap-3">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: 'var(--color-status-amber)' }} />
                <span className="text-sm font-medium" style={{ color: 'var(--color-status-amber)' }}>
                  {summary.unbilled_sessions} session{summary.unbilled_sessions !== 1 ? 's' : ''} ready to invoice — {fmt(summary.unbilled_amount)}
                </span>
              </div>
              <span className="text-xs font-medium" style={{ color: 'var(--color-status-amber)', opacity: 0.7 }}>
                Generate &rarr;
              </span>
            </a>
          )}
          {summary.draft_invoices > 0 && (
            <a
              href="/invoices?status=draft"
              className="flex items-center justify-between rounded-xl px-5 py-4 transition-all duration-150"
              style={{
                backgroundColor: 'rgba(69, 118, 169, 0.08)',
                border: '1px solid rgba(69, 118, 169, 0.25)',
              }}
              onMouseEnter={e => { e.currentTarget.style.backgroundColor = 'rgba(69, 118, 169, 0.14)'; }}
              onMouseLeave={e => { e.currentTarget.style.backgroundColor = 'rgba(69, 118, 169, 0.08)'; }}
            >
              <div className="flex items-center gap-3">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#4576a9' }} />
                <span className="text-sm font-medium" style={{ color: '#4576a9' }}>
                  {summary.draft_invoices} invoice{summary.draft_invoices !== 1 ? 's' : ''} still in draft — not sent to client yet
                </span>
              </div>
              <span className="text-xs font-medium" style={{ color: '#4576a9', opacity: 0.7 }}>
                Review &rarr;
              </span>
            </a>
          )}
        </div>
      )}

      {/* Summary cards — row 1: money */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-5 stagger-children">
          <Card
            title="Money Owed to You"
            value={fmt(summary.total_outstanding)}
            subtitle={`across ${summary.total_invoices} invoices`}
          />
          <Card
            title="Past Due"
            value={fmt(summary.total_overdue)}
            subtitle={`${summary.overdue_invoices} invoice${summary.overdue_invoices !== 1 ? 's' : ''} overdue`}
            accent={summary.total_overdue > 0 ? 'var(--color-status-red)' : undefined}
          />
          <Card
            title="Ready to Bill"
            value={fmt(summary.unbilled_amount)}
            subtitle={`${summary.unbilled_sessions} session${summary.unbilled_sessions !== 1 ? 's' : ''} not yet invoiced`}
            accent={summary.unbilled_amount > 0 ? 'var(--color-status-amber)' : undefined}
          />
          <Card
            title="Collected This Month"
            value={fmt(summary.revenue_this_month)}
            subtitle={`Last month: ${fmt(summary.revenue_last_month)}`}
            accent="var(--color-status-green)"
          />
        </div>
      )}

      {/* Summary cards — row 2: performance KPIs */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-10">
          <Card
            title="This Quarter"
            value={fmt(summary.revenue_this_quarter)}
            subtitle="Total collected"
          />
          <Card
            title="Collection Rate"
            value={summary.collection_rate != null ? `${summary.collection_rate}%` : '—'}
            subtitle="Invoices paid vs. sent"
            accent={summary.collection_rate != null && summary.collection_rate >= 90 ? 'var(--color-status-green)' : summary.collection_rate != null && summary.collection_rate < 70 ? 'var(--color-status-red)' : undefined}
          />
          <Card
            title="Invoicing Speed"
            value={summary.avg_invoicing_days != null ? `${summary.avg_invoicing_days} days` : '—'}
            subtitle="Avg session to invoice"
            accent={summary.avg_invoicing_days != null && summary.avg_invoicing_days <= 1 ? 'var(--color-status-green)' : summary.avg_invoicing_days != null && summary.avg_invoicing_days > 7 ? 'var(--color-status-red)' : undefined}
          />
          <Card
            title="Active Clients"
            value={summary.total_clients}
            subtitle={`${summary.total_invoices} total invoices`}
          />
        </div>
      )}

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
        {/* Aging chart */}
        <div
          className="rounded-xl p-6"
          style={{
            backgroundColor: 'var(--color-canvas-raised)',
            boxShadow: 'var(--shadow-card)',
          }}
        >
          <h2
            className="text-[0.6875rem] font-medium uppercase tracking-[0.06em] mb-5"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text-tertiary)' }}
          >
            How Long Clients Owe You
          </h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={agingData} barCategoryGap="25%">
              <XAxis dataKey="name" {...CHART_AXIS} />
              <YAxis {...CHART_AXIS} tickFormatter={v => `$${v}`} />
              <Tooltip formatter={v => fmt(v)} {...CHART_TOOLTIP} cursor={{ fill: 'rgba(200,135,95,0.06)' }} />
              <Bar dataKey="value" fill="var(--color-accent)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Status pie */}
        <div
          className="rounded-xl p-6"
          style={{
            backgroundColor: 'var(--color-canvas-raised)',
            boxShadow: 'var(--shadow-card)',
          }}
        >
          <h2
            className="text-[0.6875rem] font-medium uppercase tracking-[0.06em] mb-5"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text-tertiary)' }}
          >
            Where Your Invoices Stand
          </h2>
          {statusData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  innerRadius={40}
                  dataKey="value"
                  strokeWidth={2}
                  stroke="var(--color-canvas-raised)"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {statusData.map((d, i) => <Cell key={i} fill={PIE_COLORS[d.name] || '#7c7f86'} />)}
                </Pie>
                <Tooltip {...CHART_TOOLTIP} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-center py-16 text-sm" style={{ color: 'var(--color-text-tertiary)' }}>No invoices yet</p>
          )}
        </div>
      </div>

      {/* Cash flow forecast with 30/60/90 toggle */}
      <div
        className="rounded-xl p-6 mb-10"
        style={{
          backgroundColor: 'var(--color-canvas-raised)',
          boxShadow: 'var(--shadow-card)',
        }}
      >
        <div className="flex items-center justify-between mb-5">
          <h2
            className="text-[0.6875rem] font-medium uppercase tracking-[0.06em]"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text-tertiary)' }}
          >
            Expected Income
          </h2>
          <div className="flex gap-1">
            {[30, 60, 90].map(d => (
              <button
                key={d}
                onClick={() => setForecastDays(d)}
                className="px-3 py-1 rounded-md text-xs font-medium transition-all duration-150"
                style={{
                  fontFamily: 'var(--font-heading)',
                  backgroundColor: forecastDays === d ? 'var(--color-surface-dark)' : 'transparent',
                  color: forecastDays === d ? 'var(--color-text-inverse)' : 'var(--color-text-tertiary)',
                }}
              >
                {d} days
              </button>
            ))}
          </div>
        </div>
        {l4 ? (
          <div className="flex items-center justify-center h-[250px]" style={{ color: 'var(--color-text-tertiary)' }}>
            <p className="text-sm">Loading forecast...</p>
          </div>
        ) : cashflow && cashflow.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={cashflow}>
              <XAxis dataKey="date" {...CHART_AXIS} />
              <YAxis {...CHART_AXIS} tickFormatter={v => `$${v}`} />
              <Tooltip formatter={v => fmt(v)} {...CHART_TOOLTIP} />
              <Line
                type="monotone"
                dataKey="cumulative"
                stroke="var(--color-status-green)"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: 'var(--color-status-green)', strokeWidth: 2, stroke: 'var(--color-canvas-raised)' }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-center py-16 text-sm" style={{ color: 'var(--color-text-tertiary)' }}>No outstanding invoices to forecast</p>
        )}
        <p className="text-xs mt-3" style={{ color: 'var(--color-text-tertiary)' }}>
          Based on outstanding invoices, adjusted by each client's payment history
        </p>
      </div>

      {/* Client scorecard */}
      {scores && scores.length > 0 && (
        <div
          className="rounded-xl overflow-hidden"
          style={{
            backgroundColor: 'var(--color-canvas-raised)',
            boxShadow: 'var(--shadow-card)',
          }}
        >
          <div className="px-6 pt-6 pb-4">
            <h2
              className="text-[0.6875rem] font-medium uppercase tracking-[0.06em]"
              style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text-tertiary)' }}
            >
              How Your Clients Pay
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Client</th>
                  <th>Owed</th>
                  <th>Total Paid</th>
                  <th>Avg Days to Pay</th>
                  <th>Last Payment</th>
                  <th>Reliability</th>
                </tr>
              </thead>
              <tbody>
                {scores.map((s) => (
                  <tr key={s.client_id}>
                    <td className="font-medium" style={{ color: 'var(--color-text-primary)' }}>{s.client_name}</td>
                    <td style={{ fontFamily: 'var(--font-heading)' }}>{fmt(s.outstanding_balance)}</td>
                    <td style={{ fontFamily: 'var(--font-heading)' }}>{fmt(s.total_paid)}</td>
                    <td>{s.avg_payment_days ?? '-'}</td>
                    <td>{s.last_payment_date || '-'}</td>
                    <td><StatusBadge status={s.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
