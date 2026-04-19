import { useState, useCallback } from "react";
import { useApi } from "../hooks/useApi";
import { useAction } from "../hooks/useAction";
import { useToast } from "../components/common/Toast";
import { api } from "../api/client";
import StatusBadge from "../components/common/StatusBadge";
import Modal from "../components/common/Modal";

const empty = {
  name: "",
  email: "",
  phone: "",
  company: "",
  currency: "CAD",
  default_rate: "",
  payment_terms: 30,
  notes: ""
};

export default function ClientsPage() {
  const {
    data: clients,
    loading,
    error,
    refetch
  } = useApi(() => api.getClients());
  const toast = useToast();
  const [modal, setModal] = useState(false);
  const [form, setForm] = useState(empty);
  const [editing, setEditing] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  const openNew = () => {
    setForm(empty);
    setEditing(null);
    setModal(true);
  };
  const openEdit = c => {
    setForm({ ...c, default_rate: c.default_rate || "" });
    setEditing(c.id);
    setModal(true);
  };

  const saveAction = useAction(
    useCallback(async (formData, editId) => {
      const data = {
        ...formData,
        default_rate: formData.default_rate
          ? Number(formData.default_rate)
          : null
      };
      if (editId) await api.updateClient(editId, data);
      else await api.createClient(data);
      return editId;
    }, []),
    {
      onSuccess: editId => {
        setModal(false);
        toast.success(editId ? "Client updated" : "Client created");
        refetch();
      },
      onError: msg => toast.error(`Failed to save client: ${msg}`)
    }
  );

  const deleteAction = useAction(
    useCallback(async id => {
      await api.deleteClient(id);
      return id;
    }, []),
    {
      onSuccess: () => {
        toast.success("Client deleted");
        setDeletingId(null);
        refetch();
      },
      onError: msg => {
        toast.error(`Failed to delete: ${msg}`);
        setDeletingId(null);
      }
    }
  );

  const save = async e => {
    e.preventDefault();
    await saveAction.run(form, editing);
  };

  const remove = async id => {
    if (
      !confirm(
        "Delete this client? Their sessions and invoices will remain in the system."
      )
    )
      return;
    setDeletingId(id);
    await deleteAction.run(id);
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
            Failed to load clients: {error}
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
          Clients
        </h1>
        <button onClick={openNew} className="btn-primary">
          + New Client
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
                <th>Name</th>
                <th>Email</th>
                <th>Currency</th>
                <th>Hourly Rate</th>
                <th>Payment Due</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {clients?.map(c => (
                <tr key={c.id}>
                  <td
                    className="font-medium"
                    style={{ color: "var(--color-text-primary)" }}
                  >
                    {c.name}
                  </td>
                  <td>{c.email || "-"}</td>
                  <td>{c.currency}</td>
                  <td style={{ fontFamily: "var(--font-heading)" }}>
                    {c.default_rate ? `$${c.default_rate}/hr` : "-"}
                  </td>
                  <td>{c.payment_terms} days</td>
                  <td>
                    <StatusBadge status={c.status} />
                  </td>
                  <td className="space-x-3">
                    <button
                      onClick={() => openEdit(c)}
                      className="text-xs font-medium transition-colors duration-150"
                      style={{ color: "var(--color-accent)" }}
                    >
                      Edit
                    </button>
                    {c.session_count === 0 && c.invoice_count === 0 && (
                      <button
                        onClick={() => remove(c.id)}
                        disabled={deletingId === c.id}
                        className="text-xs font-medium transition-colors duration-150"
                        style={{
                          color: "var(--color-status-red)",
                          opacity: deletingId === c.id ? 0.4 : 1
                        }}
                      >
                        {deletingId === c.id ? "Deleting..." : "Delete"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {clients?.length === 0 && (
                <tr>
                  <td
                    colSpan={7}
                    className="py-12! text-center"
                    style={{ color: "var(--color-text-tertiary)" }}
                  >
                    No clients yet. Click "+ New Client" to add one.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <Modal
        open={modal}
        onClose={() => setModal(false)}
        title={editing ? "Edit Client" : "New Client"}
      >
        <form onSubmit={save} className="space-y-4">
          <div>
            <label className="form-label">Client Name</label>
            <input
              required
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
              className="form-input"
            />
          </div>
          <div>
            <label className="form-label">Email</label>
            <input
              type="email"
              value={form.email}
              onChange={e => setForm({ ...form, email: e.target.value })}
              className="form-input"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="form-label">Phone</label>
              <input
                value={form.phone}
                onChange={e => setForm({ ...form, phone: e.target.value })}
                className="form-input"
              />
            </div>
            <div>
              <label className="form-label">Company</label>
              <input
                value={form.company}
                onChange={e => setForm({ ...form, company: e.target.value })}
                className="form-input"
              />
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="form-label">Currency</label>
              <select
                value={form.currency}
                onChange={e => setForm({ ...form, currency: e.target.value })}
                className="form-input"
              >
                <option value="CAD">CAD</option>
                <option value="USD">USD</option>
              </select>
            </div>
            <div>
              <label className="form-label">Default Hourly Rate</label>
              <input
                type="number"
                step="0.01"
                value={form.default_rate}
                onChange={e =>
                  setForm({ ...form, default_rate: e.target.value })
                }
                className="form-input"
                placeholder="e.g. 150"
              />
              <p
                className="text-xs mt-1"
                style={{ color: "var(--color-text-tertiary)" }}
              >
                Auto-filled when logging sessions
              </p>
            </div>
            <div>
              <label className="form-label">Payment Due In (days)</label>
              <input
                type="number"
                value={form.payment_terms}
                onChange={e =>
                  setForm({ ...form, payment_terms: Number(e.target.value) })
                }
                className="form-input"
              />
              <p
                className="text-xs mt-1"
                style={{ color: "var(--color-text-tertiary)" }}
              >
                How long after invoicing to expect payment
              </p>
            </div>
          </div>
          <div>
            <label className="form-label">Notes</label>
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
            className="w-full btn-primary py-2.5"
            style={{ opacity: saveAction.loading ? 0.6 : 1 }}
          >
            {saveAction.loading
              ? "Saving..."
              : editing
                ? "Update Client"
                : "Create Client"}
          </button>
        </form>
      </Modal>
    </div>
  );
}
