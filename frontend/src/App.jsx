import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/common/Layout';
import { ToastProvider } from './components/common/Toast';
import DashboardPage from './pages/DashboardPage';
import ClientsPage from './pages/ClientsPage';
import SessionsPage from './pages/SessionsPage';
import InvoicesPage from './pages/InvoicesPage';
import PaymentsPage from './pages/PaymentsPage';
import RemindersPage from './pages/RemindersPage';
import ImportPage from './pages/ImportPage';

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
      <Layout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/clients" element={<ClientsPage />} />
          <Route path="/sessions" element={<SessionsPage />} />
          <Route path="/invoices" element={<InvoicesPage />} />
          <Route path="/payments" element={<PaymentsPage />} />
          <Route path="/reminders" element={<RemindersPage />} />
          <Route path="/import" element={<ImportPage />} />
        </Routes>
      </Layout>
      </ToastProvider>
    </BrowserRouter>
  );
}
