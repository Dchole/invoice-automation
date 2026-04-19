import { useState, useRef } from 'react';
import { api } from '../api/client';
import { Upload, CheckCircle, AlertCircle, Download } from 'lucide-react';

export default function ImportPage() {
  const fileRef = useRef();
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);

  const handleFile = async (file) => {
    if (!file) return;
    setUploading(true);
    setResult(null);
    try {
      const res = await api.uploadExcel(file);
      setResult(res);
    } catch (e) {
      setResult({ error: e.message });
    }
    setUploading(false);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  return (
    <div className="animate-fade-in">
      <h1
        className="text-2xl font-bold tracking-tight mb-2"
        style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text-primary)' }}
      >
        Import from Excel
      </h1>
      <p className="text-sm mb-8" style={{ color: 'var(--color-text-tertiary)' }}>
        Upload your Excel spreadsheet to import clients and sessions. The system will read all tabs and auto-detect columns.
      </p>

      {/* Drop zone */}
      <div
        className="rounded-xl p-8 sm:p-16 text-center cursor-pointer transition-all duration-200"
        style={{
          border: `2px dashed ${dragging ? 'var(--color-accent)' : 'var(--color-border)'}`,
          backgroundColor: dragging ? 'var(--color-accent-muted)' : 'var(--color-canvas-raised)',
        }}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => fileRef.current?.click()}
        onMouseEnter={(e) => {
          if (!dragging) {
            e.currentTarget.style.borderColor = 'var(--color-accent-light)';
            e.currentTarget.style.backgroundColor = 'var(--color-accent-muted)';
          }
        }}
        onMouseLeave={(e) => {
          if (!dragging) {
            e.currentTarget.style.borderColor = 'var(--color-border)';
            e.currentTarget.style.backgroundColor = 'var(--color-canvas-raised)';
          }
        }}
      >
        <div
          className="w-14 h-14 rounded-xl flex items-center justify-center mx-auto mb-4"
          style={{ backgroundColor: 'var(--color-accent-muted)' }}
        >
          <Upload style={{ color: 'var(--color-accent)' }} size={24} />
        </div>
        <p className="text-sm font-medium mb-1" style={{ color: 'var(--color-text-primary)' }}>
          {uploading ? 'Uploading...' : 'Drag & drop your .xlsx file here, or click to browse'}
        </p>
        <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>Supports .xlsx and .xls files</p>
        <input ref={fileRef} type="file" accept=".xlsx,.xls" className="hidden" onChange={e => handleFile(e.target.files[0])} />
      </div>

      {/* Success result */}
      {result && !result.error && (
        <div
          className="mt-8 rounded-xl p-6 animate-slide-up"
          style={{ backgroundColor: 'var(--color-canvas-raised)', boxShadow: 'var(--shadow-card)' }}
        >
          <div className="flex items-center gap-2.5 mb-5">
            <CheckCircle style={{ color: 'var(--color-status-green)' }} size={20} />
            <h2
              className="text-base font-semibold"
              style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text-primary)' }}
            >
              Import Complete
            </h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mb-5">
            <div
              className="rounded-lg p-4 text-center"
              style={{ backgroundColor: 'var(--color-status-green-bg)', border: '1px solid var(--color-status-green-border)' }}
            >
              <p
                className="text-2xl font-bold"
                style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-status-green)' }}
              >
                {result.clients_created}
              </p>
              <p className="text-xs mt-0.5" style={{ color: 'var(--color-status-green)' }}>Clients Created</p>
            </div>
            <div
              className="rounded-lg p-4 text-center"
              style={{ backgroundColor: 'var(--color-status-blue-bg)', border: '1px solid var(--color-status-blue-border)' }}
            >
              <p
                className="text-2xl font-bold"
                style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-status-blue)' }}
              >
                {result.invoices_created}
              </p>
              <p className="text-xs mt-0.5" style={{ color: 'var(--color-status-blue)' }}>Invoices Created</p>
            </div>
            <div
              className="rounded-lg p-4 text-center"
              style={{ backgroundColor: 'var(--color-status-blue-bg)', border: '1px solid var(--color-status-blue-border)' }}
            >
              <p
                className="text-2xl font-bold"
                style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-status-blue)' }}
              >
                {result.sessions_created}
              </p>
              <p className="text-xs mt-0.5" style={{ color: 'var(--color-status-blue)' }}>Sessions Imported</p>
            </div>
            <div
              className="rounded-lg p-4 text-center"
              style={{ backgroundColor: 'var(--color-status-purple-bg, var(--color-status-blue-bg))', border: '1px solid var(--color-status-purple-border, var(--color-status-blue-border))' }}
            >
              <p
                className="text-2xl font-bold"
                style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-status-purple, var(--color-status-blue))' }}
              >
                {result.payments_created}
              </p>
              <p className="text-xs mt-0.5" style={{ color: 'var(--color-status-purple, var(--color-status-blue))' }}>Payments Created</p>
            </div>
          </div>
          {result.warnings?.length > 0 && (
            <div className="mb-4">
              <p className="form-label mb-1" style={{ color: 'var(--color-status-amber)' }}>Warnings</p>
              <ul className="text-xs space-y-0.5 max-h-32 overflow-y-auto" style={{ color: 'var(--color-status-amber)' }}>
                {result.warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            </div>
          )}
          {result.errors?.length > 0 && (
            <div>
              <p className="form-label mb-1" style={{ color: 'var(--color-status-red)' }}>Errors ({result.errors.length} rows skipped)</p>
              <ul className="text-xs space-y-0.5 max-h-32 overflow-y-auto" style={{ color: 'var(--color-status-red)' }}>
                {result.errors.map((e, i) => <li key={i}>{e}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Error result */}
      {result?.error && (
        <div
          className="mt-8 rounded-xl p-5 flex items-center gap-3 animate-slide-up"
          style={{
            backgroundColor: 'var(--color-status-red-bg)',
            border: '1px solid var(--color-status-red-border)',
          }}
        >
          <AlertCircle style={{ color: 'var(--color-status-red)' }} size={18} />
          <p className="text-sm" style={{ color: 'var(--color-status-red)' }}>{result.error}</p>
        </div>
      )}

      {/* Export section */}
      <div className="mt-12">
        <h2
          className="text-lg font-bold tracking-tight mb-2"
          style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text-primary)' }}
        >
          Export Data
        </h2>
        <p className="text-sm mb-5" style={{ color: 'var(--color-text-tertiary)' }}>
          Download your data as CSV files for accounting software or as a database backup.
        </p>
        <div className="flex flex-wrap gap-3">
          <a
            href={api.exportExcel()}
            download
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-150"
            style={{
              backgroundColor: 'var(--color-accent)',
              color: 'white',
            }}
          >
            <Download size={15} />
            Full Export (.xlsx)
          </a>
          <a
            href={api.exportInvoicesCsv()}
            download
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-150"
            style={{
              backgroundColor: 'var(--color-canvas-raised)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-secondary)',
            }}
          >
            <Download size={15} />
            Invoices CSV
          </a>
          <a
            href={api.exportPaymentsCsv()}
            download
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-150"
            style={{
              backgroundColor: 'var(--color-canvas-raised)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-secondary)',
            }}
          >
            <Download size={15} />
            Payments CSV
          </a>
          <a
            href={api.exportBackup()}
            download
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-150"
            style={{
              backgroundColor: 'var(--color-canvas-raised)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-secondary)',
            }}
          >
            <Download size={15} />
            Database Backup
          </a>
        </div>
      </div>
    </div>
  );
}
