import { useState, useEffect, useCallback } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Users, Clock, FileText, CreditCard, Bell, Upload, Menu, X } from 'lucide-react';

const nav = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/clients', label: 'Clients', icon: Users },
  { to: '/sessions', label: 'Sessions', icon: Clock },
  { to: '/invoices', label: 'Invoices', icon: FileText },
  { to: '/payments', label: 'Payments', icon: CreditCard },
  { to: '/reminders', label: 'Reminders', icon: Bell },
  { to: '/import', label: 'Excel Import', icon: Upload },
];

export default function Layout({ children }) {
  const { pathname } = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 767px)');
    const update = () => setIsMobile(mq.matches);
    update();
    mq.addEventListener('change', update);
    return () => mq.removeEventListener('change', update);
  }, []);

  // Close sidebar on route change (mobile)
  useEffect(() => {
    if (isMobile) setSidebarOpen(false);
  }, [pathname, isMobile]);

  // Close sidebar on Escape key
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') setSidebarOpen(false);
  }, []);

  useEffect(() => {
    if (sidebarOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
      return () => {
        document.removeEventListener('keydown', handleKeyDown);
        document.body.style.overflow = '';
      };
    }
  }, [sidebarOpen, handleKeyDown]);

  const showSidebar = isMobile ? sidebarOpen : true;

  return (
    <div className="min-h-screen flex" style={{ backgroundColor: 'var(--color-canvas)' }}>
      {/* Mobile top bar */}
      {isMobile && (
        <div
          className="fixed top-0 left-0 right-0 z-40 flex items-center gap-3 px-4 h-14"
          style={{ backgroundColor: 'var(--color-surface-dark)' }}
        >
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1.5 rounded-md"
            style={{ color: 'var(--color-text-inverse)' }}
            aria-label="Toggle navigation"
          >
            {sidebarOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
          <h1
            className="text-base font-bold tracking-tight"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text-inverse)' }}
          >
            InvoiceFlow
          </h1>
        </div>
      )}

      {/* Mobile overlay backdrop */}
      {isMobile && sidebarOpen && (
        <div
          className="fixed inset-0 z-40 animate-fade-in"
          style={{ backgroundColor: 'rgba(26, 29, 35, 0.5)', backdropFilter: 'blur(4px)' }}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className="w-60 flex flex-col fixed h-full z-50 transition-transform duration-250 ease-out"
        style={{
          backgroundColor: 'var(--color-surface-dark)',
          transform: showSidebar ? 'translateX(0)' : 'translateX(-100%)',
        }}
      >
        {/* Brand */}
        <div className="px-6 pt-7 pb-6">
          <h1
            className="text-lg font-bold tracking-tight"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text-inverse)' }}
          >
            InvoiceFlow
          </h1>
          <p
            className="text-[0.65rem] mt-0.5 uppercase tracking-[0.15em] font-medium"
            style={{ color: 'var(--color-text-inverse-muted)' }}
          >
            Billing Made Simple
          </p>
        </div>

        {/* Divider */}
        <div className="mx-5 mb-4" style={{ borderTop: '1px solid var(--color-border-dark)' }} />

        {/* Navigation */}
        <nav className="flex-1 px-3 space-y-0.5">
          {nav.map(({ to, label, icon: Icon }) => {
            const active = pathname === to;
            return (
              <Link
                key={to}
                to={to}
                className="relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-[0.8125rem] font-medium transition-all duration-150"
                style={{
                  color: active ? 'var(--color-text-inverse)' : 'var(--color-text-inverse-muted)',
                  backgroundColor: active ? 'var(--color-surface-dark-active)' : 'transparent',
                }}
                onMouseEnter={(e) => {
                  if (!active) {
                    e.currentTarget.style.backgroundColor = 'var(--color-surface-dark-hover)';
                    e.currentTarget.style.color = 'var(--color-text-inverse)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!active) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = 'var(--color-text-inverse-muted)';
                  }
                }}
              >
                {active && (
                  <span
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full"
                    style={{ backgroundColor: 'var(--color-accent)' }}
                  />
                )}
                <Icon size={17} strokeWidth={active ? 2 : 1.5} />
                <span style={{ fontFamily: 'var(--font-heading)' }}>{label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-6 py-4" style={{ borderTop: '1px solid var(--color-border-dark)' }}>
          <p
            className="text-[0.6rem] uppercase tracking-[0.12em]"
            style={{ color: 'var(--color-text-inverse-muted)' }}
          >
            InvoiceFlow v1.0
          </p>
        </div>
      </aside>

      {/* Main content */}
      <main
        className="flex-1 min-h-screen bg-canvas-pattern"
        style={{
          marginLeft: isMobile ? 0 : '15rem',
          paddingTop: isMobile ? '3.5rem' : 0,
        }}
      >
        <div className="max-w-6xl mx-auto px-4 py-6 sm:px-6 md:px-8 md:py-8">
          {children}
        </div>
      </main>
    </div>
  );
}
