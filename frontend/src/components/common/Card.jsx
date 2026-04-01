export default function Card({ title, value, subtitle, className = '', accent }) {
  return (
    <div
      className={`rounded-lg p-5 ${className}`}
      style={{
        backgroundColor: 'var(--color-canvas-raised)',
        borderTop: `2px solid ${accent || 'var(--color-accent)'}`,
        boxShadow: 'var(--shadow-card)',
      }}
    >
      <p
        className="text-[0.6875rem] font-medium uppercase tracking-[0.06em]"
        style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text-tertiary)' }}
      >
        {title}
      </p>
      <p
        className="text-2xl font-bold mt-1.5 tracking-tight"
        style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text-primary)' }}
      >
        {value}
      </p>
      {subtitle && (
        <p className="text-xs mt-1" style={{ color: 'var(--color-text-tertiary)' }}>
          {subtitle}
        </p>
      )}
    </div>
  );
}
