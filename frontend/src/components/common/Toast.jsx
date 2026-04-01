import { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';

const ToastContext = createContext(null);

export function useToast() {
  return useContext(ToastContext);
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const idRef = useRef(0);

  const addToast = useCallback((message, type = 'success', duration = 4000) => {
    const id = ++idRef.current;
    setToasts(prev => [...prev, { id, message, type, removing: false }]);
    setTimeout(() => {
      setToasts(prev => prev.map(t => t.id === id ? { ...t, removing: true } : t));
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== id));
      }, 300);
    }, duration);
  }, []);

  const toast = useCallback({
    success: (msg) => addToast(msg, 'success'),
    error: (msg) => addToast(msg, 'error', 6000),
    info: (msg) => addToast(msg, 'info'),
  }, [addToast]);

  // Make toast callable as toast.success() etc
  const value = { success: toast.success, error: toast.error, info: toast.info };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer toasts={toasts} />
    </ToastContext.Provider>
  );
}

const TOAST_STYLES = {
  success: {
    bg: 'rgba(61, 139, 94, 0.95)',
    color: '#ffffff',
  },
  error: {
    bg: 'rgba(184, 76, 76, 0.95)',
    color: '#ffffff',
  },
  info: {
    bg: 'rgba(69, 118, 169, 0.95)',
    color: '#ffffff',
  },
};

function ToastContainer({ toasts }) {
  if (toasts.length === 0) return null;

  return (
    <div style={{
      position: 'fixed',
      bottom: '24px',
      right: '24px',
      zIndex: 9999,
      display: 'flex',
      flexDirection: 'column',
      gap: '8px',
      maxWidth: '380px',
    }}>
      {toasts.map(t => (
        <ToastItem key={t.id} toast={t} />
      ))}
    </div>
  );
}

function ToastItem({ toast }) {
  const s = TOAST_STYLES[toast.type] || TOAST_STYLES.info;

  return (
    <div
      style={{
        backgroundColor: s.bg,
        color: s.color,
        padding: '12px 20px',
        borderRadius: '10px',
        fontSize: '13px',
        fontWeight: 500,
        boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
        backdropFilter: 'blur(8px)',
        transform: toast.removing ? 'translateX(120%)' : 'translateX(0)',
        opacity: toast.removing ? 0 : 1,
        transition: 'transform 0.3s ease, opacity 0.3s ease',
        animation: toast.removing ? 'none' : 'toast-in 0.3s ease',
      }}
    >
      {toast.message}
      <style>{`
        @keyframes toast-in {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
