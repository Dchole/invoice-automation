const styles = {
  draft:      { color: 'var(--color-status-gray)',   bg: 'var(--color-status-gray-bg)',   border: 'var(--color-status-gray-border)' },
  sent:       { color: 'var(--color-status-blue)',   bg: 'var(--color-status-blue-bg)',   border: 'var(--color-status-blue-border)' },
  viewed:     { color: 'var(--color-status-indigo)', bg: 'var(--color-status-indigo-bg)', border: 'var(--color-status-indigo-border)' },
  paid:       { color: 'var(--color-status-green)',  bg: 'var(--color-status-green-bg)',  border: 'var(--color-status-green-border)' },
  overdue:    { color: 'var(--color-status-red)',    bg: 'var(--color-status-red-bg)',    border: 'var(--color-status-red-border)' },
  void:       { color: 'var(--color-status-gray)',   bg: 'var(--color-status-gray-bg)',   border: 'var(--color-status-gray-border)' },
  active:     { color: 'var(--color-status-green)',  bg: 'var(--color-status-green-bg)',  border: 'var(--color-status-green-border)' },
  inactive:   { color: 'var(--color-status-gray)',   bg: 'var(--color-status-gray-bg)',   border: 'var(--color-status-gray-border)' },
  unbilled:   { color: 'var(--color-status-amber)',  bg: 'var(--color-status-amber-bg)',  border: 'var(--color-status-amber-border)' },
  invoiced:   { color: 'var(--color-status-blue)',   bg: 'var(--color-status-blue-bg)',   border: 'var(--color-status-blue-border)' },
  pending:    { color: 'var(--color-status-amber)',  bg: 'var(--color-status-amber-bg)',  border: 'var(--color-status-amber-border)' },
  skipped:    { color: 'var(--color-status-gray)',   bg: 'var(--color-status-gray-bg)',   border: 'var(--color-status-gray-border)' },
  good:       { color: 'var(--color-status-green)',  bg: 'var(--color-status-green-bg)',  border: 'var(--color-status-green-border)' },
  slow_payer: { color: 'var(--color-status-amber)',  bg: 'var(--color-status-amber-bg)',  border: 'var(--color-status-amber-border)' },
  at_risk:    { color: 'var(--color-status-red)',    bg: 'var(--color-status-red-bg)',    border: 'var(--color-status-red-border)' },
};

const labels = {
  draft:      'Not Sent',
  sent:       'Awaiting Payment',
  viewed:     'Viewed',
  paid:       'Paid',
  overdue:    'Overdue',
  void:       'Cancelled',
  active:     'Active',
  inactive:   'Inactive',
  unbilled:   'Needs Invoice',
  invoiced:   'On Invoice',
  pending:    'Scheduled',
  skipped:    'Not Needed',
  good:       'On Track',
  slow_payer: 'Pays Late',
  at_risk:    'Needs Attention',
};

const fallback = { color: 'var(--color-status-gray)', bg: 'var(--color-status-gray-bg)', border: 'var(--color-status-gray-border)' };

export default function StatusBadge({ status }) {
  const s = styles[status] || fallback;
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded-md text-[0.6875rem] font-medium"
      style={{
        color: s.color,
        backgroundColor: s.bg,
        border: `1px solid ${s.border}`,
        fontFamily: 'var(--font-heading)',
      }}
    >
      {labels[status] || status.replace('_', ' ')}
    </span>
  );
}
