import { useState, useCallback } from "react";
import { useApi } from "../hooks/useApi";
import { useAction } from "../hooks/useAction";
import { useToast } from "../components/common/Toast";
import { api } from "../api/client";
import StatusBadge from "../components/common/StatusBadge";
import Modal from "../components/common/Modal";
import Pagination from "../components/common/Pagination";

const empty = {
  client_id: "",
  date: "",
  start_time: "",
  end_time: "",
  duration_minutes: "",
  hourly_rate: "",
  description: "",
  timeMode: "times"
};

const fmt = n => `$${Number(n).toFixed(2)}`;

function fmtDuration(mins) {
  const m = Number(mins);
  if (!m || m <= 0) return "";
  if (m < 60) return `${m} min`;
  const h = Math.floor(m / 60);
  const r = m % 60;
  return r > 0 ? `${h} hr ${r} min` : `${h} hr`;
}

function computeDurationFromTimes(start, end) {
  if (!start || !end) return "";
  const [sh, sm] = start.split(":").map(Number);
  const [eh, em] = end.split(":").map(Number);
  const diff = eh * 60 + em - (sh * 60 + sm);
  return diff > 0 ? String(diff) : "";
}

export default function SessionsPage() {
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState("all");
  const params = {
    page,
    per_page: 25,
    ...(filter !== "all" ? { status: filter } : {})
  };
  const {
    data: result,
    loading,
    error,
    refetch
  } = useApi(() => api.getSessions(params), [page, filter]);
  const { data: clients } = useApi(() => api.getClients());
  const { data: summaryData } = useApi(() => api.getDashboardSummary());
  const toast = useToast();
  const [modal, setModal] = useState(false);
  const [form, setForm] = useState(empty);

  const clientById = Object.fromEntries((clients || []).map(c => [c.id, c]));

  const handleClientChange = clientId => {
    const client = clientById[clientId];
    setForm(prev => ({
      ...prev,
      client_id: clientId,
      hourly_rate: client?.default_rate
        ? String(client.default_rate)
        : prev.hourly_rate
    }));
  };

  const handleTimeChange = (field, value) => {
    const updated = { ...form, [field]: value };
    if (field === "start_time" || field === "end_time") {
      updated.duration_minutes = computeDurationFromTimes(
        updated.start_time,
        updated.end_time
      );
    }
    setForm(updated);
  };

  const saveAction = useAction(
    useCallback(async formData => {
      const data = {
        client_id: Number(formData.client_id),
        date: formData.date,
        hourly_rate: Number(formData.hourly_rate),
        description: formData.description || null
      };
      if (
        formData.timeMode === "times" &&
        formData.start_time &&
        formData.end_time
      ) {
        data.start_time = formData.start_time;
        data.end_time = formData.end_time;
        data.duration_minutes = Number(formData.duration_minutes);
      } else if (formData.duration_minutes) {
        data.duration_minutes = Number(formData.duration_minutes);
      }
      await api.createSession(data);
    }, []),
    {
      onSuccess: () => {
        setModal(false);
        setForm(empty);
        toast.success("Session recorded");
        refetch();
      },
      onError: msg => toast.error(`Failed to save session: ${msg}`)
    }
  );

  const save = async e => {
    e.preventDefault();
    await saveAction.run(form);
  };

  const sessions = result?.items || [];
  const clientMap = Object.fromEntries(
    (clients || []).map(c => [c.id, c.name])
  );
  const unbilledTotal = summaryData?.unbilled_amount || 0;

  const handleFilterChange = f => {
    setFilter(f);
    setPage(1);
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
            Failed to load sessions: {error}
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
        <div>
          <h1
            className="text-2xl font-bold tracking-tight"
            style={{
              fontFamily: "var(--font-heading)",
              color: "var(--color-text-primary)"
            }}
          >
            Sessions
          </h1>
          {unbilledTotal > 0 && (
            <p
              className="text-sm font-medium mt-1"
              style={{ color: "var(--color-status-amber)" }}
            >
              Unbilled work: {fmt(unbilledTotal)}
            </p>
          )}
        </div>
        <button
          onClick={() => {
            setForm({ ...empty, date: new Date().toISOString().split("T")[0] });
            setModal(true);
          }}
          className="btn-primary"
        >
          + Record Session
        </button>
      </div>

      {/* Filter pills */}
      <div className="flex flex-wrap gap-2 mb-5">
        {["all", "unbilled", "invoiced", "paid"].map(f => (
          <button
            key={f}
            onClick={() => handleFilterChange(f)}
            className="px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all duration-150"
            style={{
              fontFamily: "var(--font-heading)",
              backgroundColor:
                filter === f
                  ? "var(--color-surface-dark)"
                  : "var(--color-canvas-sunken)",
              color:
                filter === f
                  ? "var(--color-text-inverse)"
                  : "var(--color-text-secondary)",
              border:
                filter === f ? "none" : "1px solid var(--color-border-subtle)"
            }}
          >
            {f === "all" ? "All" : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
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
                <th>Client</th>
                <th>Duration</th>
                <th>Rate/hr</th>
                <th>Earned</th>
                <th>Description</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map(s => (
                <tr key={s.id}>
                  <td>{s.date}</td>
                  <td
                    className="font-medium"
                    style={{ color: "var(--color-text-primary)" }}
                  >
                    {clientMap[s.client_id] || `#${s.client_id}`}
                  </td>
                  <td>{fmtDuration(s.duration_minutes)}</td>
                  <td style={{ fontFamily: "var(--font-heading)" }}>
                    ${s.hourly_rate}/hr
                  </td>
                  <td
                    className="font-medium"
                    style={{
                      fontFamily: "var(--font-heading)",
                      color: "var(--color-text-primary)"
                    }}
                  >
                    {fmt(s.amount)}
                  </td>
                  <td className="max-w-xs truncate">{s.description || "-"}</td>
                  <td>
                    <StatusBadge status={s.status} />
                  </td>
                </tr>
              ))}
              {sessions.length === 0 && (
                <tr>
                  <td
                    colSpan={7}
                    className="py-12! text-center"
                    style={{ color: "var(--color-text-tertiary)" }}
                  >
                    No sessions found.
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
        title="Record a Work Session"
      >
        <form onSubmit={save} className="space-y-4">
          <div>
            <label className="form-label">Client</label>
            <select
              required
              value={form.client_id}
              onChange={e => handleClientChange(e.target.value)}
              className="form-input"
            >
              <option value="">Select Client</option>
              {clients?.map(c => (
                <option key={c.id} value={c.id}>
                  {c.name}
                  {c.default_rate ? ` — $${c.default_rate}/hr` : ""}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="form-label">Date</label>
            <input
              required
              type="date"
              value={form.date}
              onChange={e => setForm({ ...form, date: e.target.value })}
              className="form-input"
            />
          </div>

          {/* Time mode toggle */}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() =>
                setForm({
                  ...form,
                  timeMode: "times",
                  duration_minutes: computeDurationFromTimes(
                    form.start_time,
                    form.end_time
                  )
                })
              }
              className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-150"
              style={{
                fontFamily: "var(--font-heading)",
                backgroundColor:
                  form.timeMode === "times"
                    ? "var(--color-surface-dark)"
                    : "var(--color-canvas-sunken)",
                color:
                  form.timeMode === "times"
                    ? "var(--color-text-inverse)"
                    : "var(--color-text-secondary)",
                border:
                  form.timeMode === "times"
                    ? "none"
                    : "1px solid var(--color-border-subtle)"
              }}
            >
              Start / End Time
            </button>
            <button
              type="button"
              onClick={() =>
                setForm({
                  ...form,
                  timeMode: "duration",
                  start_time: "",
                  end_time: ""
                })
              }
              className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-150"
              style={{
                fontFamily: "var(--font-heading)",
                backgroundColor:
                  form.timeMode === "duration"
                    ? "var(--color-surface-dark)"
                    : "var(--color-canvas-sunken)",
                color:
                  form.timeMode === "duration"
                    ? "var(--color-text-inverse)"
                    : "var(--color-text-secondary)",
                border:
                  form.timeMode === "duration"
                    ? "none"
                    : "1px solid var(--color-border-subtle)"
              }}
            >
              Duration Only
            </button>
          </div>

          {form.timeMode === "times" ? (
            <div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="form-label">Start Time</label>
                  <input
                    type="time"
                    value={form.start_time}
                    onChange={e =>
                      handleTimeChange("start_time", e.target.value)
                    }
                    className="form-input"
                  />
                </div>
                <div>
                  <label className="form-label">End Time</label>
                  <input
                    type="time"
                    value={form.end_time}
                    onChange={e => handleTimeChange("end_time", e.target.value)}
                    className="form-input"
                  />
                </div>
              </div>
              {form.duration_minutes && (
                <p
                  className="text-xs mt-2 font-medium"
                  style={{ color: "var(--color-status-green)" }}
                >
                  = {fmtDuration(form.duration_minutes)}
                </p>
              )}
            </div>
          ) : (
            <div>
              <label className="form-label">Duration (minutes)</label>
              <input
                required
                type="number"
                min="1"
                value={form.duration_minutes}
                onChange={e =>
                  setForm({ ...form, duration_minutes: e.target.value })
                }
                className="form-input"
                placeholder="e.g. 60"
              />
            </div>
          )}

          <div>
            <label className="form-label">Rate/hr</label>
            <input
              required
              type="number"
              step="0.01"
              value={form.hourly_rate}
              onChange={e => setForm({ ...form, hourly_rate: e.target.value })}
              className="form-input"
            />
            {form.client_id && clientById[form.client_id]?.default_rate && (
              <p
                className="text-xs mt-1"
                style={{ color: "var(--color-text-tertiary)" }}
              >
                Client default: ${clientById[form.client_id].default_rate}/hr
              </p>
            )}
          </div>
          <div>
            <label className="form-label">Description (optional)</label>
            <textarea
              value={form.description}
              onChange={e => setForm({ ...form, description: e.target.value })}
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
            {saveAction.loading ? "Saving..." : "Save Session"}
          </button>
        </form>
      </Modal>
    </div>
  );
}
