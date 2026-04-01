export default function Modal({ open, onClose, title, children }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center animate-fade-in">
      {/* Backdrop */}
      <div
        className="fixed inset-0"
        style={{ backgroundColor: 'rgba(26, 29, 35, 0.5)', backdropFilter: 'blur(4px)' }}
        onClick={onClose}
      />
      {/* Panel */}
      <div
        className="relative w-full max-w-lg mx-2 sm:mx-4 max-h-[95vh] sm:max-h-[90vh] overflow-y-auto rounded-xl animate-scale-in"
        style={{
          backgroundColor: 'var(--color-canvas-raised)',
          boxShadow: 'var(--shadow-modal)',
        }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-6 py-4"
          style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
        >
          <h2
            className="text-base font-semibold"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text-primary)' }}
          >
            {title}
          </h2>
          <button
            onClick={onClose}
            className="w-7 h-7 flex items-center justify-center rounded-md text-lg transition-colors duration-150"
            style={{ color: 'var(--color-text-tertiary)' }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--color-canvas-sunken)';
              e.currentTarget.style.color = 'var(--color-text-primary)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = 'var(--color-text-tertiary)';
            }}
          >
            &times;
          </button>
        </div>
        {/* Body */}
        <div className="px-6 py-5">{children}</div>
      </div>
    </div>
  );
}
