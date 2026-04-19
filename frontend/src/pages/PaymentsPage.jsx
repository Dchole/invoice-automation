import { useState, useCallback } from "react";
import { useApi } from "../hooks/useApi";
import { useAction } from "../hooks/useAction";
import { useToast } from "../components/common/Toast";
import { api } from "../api/client";
import Modal from "../components/common/Modal";
import Pagination from "../components/common/Pagination";

const fmt = n => `$${Number(n).toFixed(2)}`;

export default function PaymentsPage() {
  const [page, setPage] = useState(1);
  const {
    data: result,
    loading,
    error,
    refetch
  } = useApi(() => api.getPayments({ page, per_page: 25 }), [page]);
  const { data: invoiceResult } = useApi(() =>
    api.getInvoices({ per_page: 100 })
  );
  const { data: clients } = useApi(() => api.getClients());
  const toast = useToast();
  const [modal, setModal] = useState(false);
  const [form, setForm] = useState({
    invoice_id: "",
    amount: "",
    payment_date: "",
    payment_method: "",
    reference: "",
    notes: ""
  });

  const payments = result?.items || [];
  const invoices = invoiceResult?.items || [];
  const clientMap = Object.fromEntries(
    (clients || []).map(c => [c.id, c.name])
  );
  const invoiceMap = Object.fromEntries(invoices.map(i => [i.id, i]));
  const unpaidInvoices = invoices.filter(
    i => i.status !== "paid" && i.status !== "void"
  );

  const prefillAmount = invId => {
    const inv = invoiceMap[Number(invId)];
    const remaining = inv ? (inv.total - inv.amount_paid).toFixed(2) : "";
    setForm({ ...form, invoice_id: invId, amount: remaining });
  };

  const saveAction = useAction(
    useCallback(async formData => {
      await api.createPayment({
        invoice_id: Number(formData.invoice_id),
        amount: Number(formData.amount),
        payment_date: formData.payment_date,
        payment_method: formData.payment_method || null,
        reference: formData.reference || null,
        notes: formData.notes || null
      });
    }, []),
    {
      onSuccess: () => {
        setModal(false);
        setForm({
          invoice_id: "",
          amount: "",
          payment_date: "",
          payment_method: "",
          reference: "",
          notes: ""
        });
        toast.success("Payment recorded");
        refetch();
      },
      onError: msg => toast.error(`Failed to record payment: ${msg}`)
    }
  );

  const save = async e => {
    e.preventDefault();
    await saveAction.run(form);
  };

  if (loading)
    return (
      <div
        className="flex items-center justify-center h-64"
        style={{ color: "var(--color-text-tertiary)" }}
      >
        <p className="text-sm">Loading...</p>
      </div>
    );

  if (error)
    return (
      <div
        className="flex items-center justify-center h-64"
        style={{ color: "var(--color-text-tertiary)" }}
      >
        <div className="text-center">
          <p className="text-sm mb-2" style={{ color: "#b84c4c" }}>
            Failed to load payments: {error}
          </p>
          <button
            onClick={refetch}
            className="text-sm underline"
            style={{ color: "var(--color-accent)" }}
          >
            Retry
          </button>
        </div>
      </div>
    );

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-8">
        <h1
          className="text-2xl font-bold tracking-tight"
          style={{
            fontFamily: "var(--font-heading)",
            color: "var(--color-text-primary)"
          }}
        >
          Payments Received
        </h1>
        <button
          onClick={() => {
            setForm({
              ...form,
              payment_date: new Date().toISOString().split("T")[0]
            });
            setModal(true);
          }}
          className="btn-primary"
        >
          + Record Payment
        </button>
      </div>

      <div
        className="rounded-xl overflow-hidden"
        style={{
          backgroundColor: "var(--color-canvas-raised)",
          boxShadow: "var(--shadow-card)"
        }}
      >
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>For Invoice</th>
                <th>Client</th>
                <th>Amount</th>
                <th>Payment Method</th>
                <th>Confirmation #</th>
              </tr>
            </thead>
            <tbody>
              {payments.map(p => {
                const inv = invoiceMap[p.invoice_id];
                return (
                  <tr key={p.id}>
                    <td>{p.payment_date}</td>
                    <td
                      className="font-mono text-xs"
                      style={{ color: "var(--color-text-tertiary)" }}
                    >
                      {inv?.invoice_number || `#${p.invoice_id}`}
                    </td>
                    <td>{inv ? clientMap[inv.client_id] || "-" : "-"}</td>
                    <td
                      className="font-semibold"
                      style={{
                        fontFamily: "var(--font-heading)",
                        color: "var(--color-status-green)"
                      }}
                    >
                      {fmt(p.amount)}
                    </td>
                    <td>{p.payment_method || "-"}</td>
                    <td style={{ color: "var(--color-text-tertiary)" }}>
                      {p.reference || "-"}
                    </td>
                  </tr>
                );
              })}
              {payments.length === 0 && (
                <tr>
                  <td
                    colSpan={6}
                    className="py-12! text-center"
                    style={{ color: "var(--color-text-tertiary)" }}
                  >
                    No payments recorded yet.
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

      <Modal
        open={modal}
        onClose={() => setModal(false)}
        title="Record a Payment You Received"
      >
        <form onSubmit={save} className="space-y-4">
          <div>
            <label className="form-label">Which invoice was paid?</label>
            <select
              required
              value={form.invoice_id}
              onChange={e => prefillAmount(e.target.value)}
              className="form-input"
            >
              <option value="">Select an invoice</option>
              {unpaidInvoices.map(i => (
                <option key={i.id} value={i.id}>
                  {i.invoice_number} - {clientMap[i.client_id]} -{" "}
                  {fmt(i.total - i.amount_paid)} remaining
                </option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="form-label">Amount</label>
              <input
                required
                type="number"
                step="0.01"
                value={form.amount}
                onChange={e => setForm({ ...form, amount: e.target.value })}
                className="form-input"
              />
            </div>
            <div>
              <label className="form-label">Date</label>
              <input
                required
                type="date"
                value={form.payment_date}
                onChange={e =>
                  setForm({ ...form, payment_date: e.target.value })
                }
                className="form-input"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="form-label">How did they pay?</label>
              <select
                value={form.payment_method}
                onChange={e =>
                  setForm({ ...form, payment_method: e.target.value })
                }
                className="form-input"
              >
                <option value="">Select method</option>
                <option value="e-transfer">E-Transfer</option>
                <option value="check">Check</option>
                <option value="cash">Cash</option>
                <option value="stripe">Stripe</option>
                <option value="paypal">PayPal</option>
              </select>
            </div>
            <div>
              <label className="form-label">Confirmation #</label>
              <input
                value={form.reference}
                onChange={e => setForm({ ...form, reference: e.target.value })}
                className="form-input"
                placeholder="From your bank or payment service"
              />
            </div>
          </div>
          <div>
            <label className="form-label">Notes (optional)</label>
            <textarea
              value={form.notes}
              onChange={e => setForm({ ...form, notes: e.target.value })}
              className="form-input"
              rows={2}
            />
          </div>
          <button
            type="submit"
            disabled={saveAction.loading}
            className="w-full btn-success py-2.5"
            style={{ opacity: saveAction.loading ? 0.6 : 1 }}
          >
            {saveAction.loading ? "Recording..." : "Record Payment"}
          </button>
        </form>
      </Modal>
    </div>
  );
}
