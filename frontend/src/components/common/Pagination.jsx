export default function Pagination({ page, totalPages, total, perPage, onPageChange }) {
  if (totalPages <= 1) return null;

  const start = (page - 1) * perPage + 1;
  const end = Math.min(page * perPage, total);

  return (
    <div
      className="flex items-center justify-between px-4 py-3 text-xs"
      style={{ borderTop: '1px solid var(--color-border-subtle)' }}
    >
      <span style={{ color: 'var(--color-text-tertiary)' }}>
        Showing {start}–{end} of {total}
      </span>
      <div className="flex gap-1">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="px-2.5 py-1 rounded-md font-medium transition-all duration-150"
          style={{
            fontFamily: 'var(--font-heading)',
            color: page <= 1 ? 'var(--color-text-tertiary)' : 'var(--color-text-secondary)',
            backgroundColor: 'transparent',
            opacity: page <= 1 ? 0.4 : 1,
            cursor: page <= 1 ? 'default' : 'pointer',
          }}
        >
          Previous
        </button>
        {Array.from({ length: totalPages }, (_, i) => i + 1)
          .filter(p => p === 1 || p === totalPages || Math.abs(p - page) <= 1)
          .reduce((acc, p, i, arr) => {
            if (i > 0 && p - arr[i - 1] > 1) acc.push('...');
            acc.push(p);
            return acc;
          }, [])
          .map((p, i) =>
            p === '...' ? (
              <span key={`dot-${i}`} className="px-1" style={{ color: 'var(--color-text-tertiary)' }}>...</span>
            ) : (
              <button
                key={p}
                onClick={() => onPageChange(p)}
                className="w-7 h-7 rounded-md font-medium transition-all duration-150"
                style={{
                  fontFamily: 'var(--font-heading)',
                  backgroundColor: p === page ? 'var(--color-surface-dark)' : 'transparent',
                  color: p === page ? 'var(--color-text-inverse)' : 'var(--color-text-secondary)',
                }}
              >
                {p}
              </button>
            )
          )}
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="px-2.5 py-1 rounded-md font-medium transition-all duration-150"
          style={{
            fontFamily: 'var(--font-heading)',
            color: page >= totalPages ? 'var(--color-text-tertiary)' : 'var(--color-text-secondary)',
            backgroundColor: 'transparent',
            opacity: page >= totalPages ? 0.4 : 1,
            cursor: page >= totalPages ? 'default' : 'pointer',
          }}
        >
          Next
        </button>
      </div>
    </div>
  );
}
