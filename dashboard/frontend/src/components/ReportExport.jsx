import React, { useState } from 'react';
import { api } from '../api/client';

export default function ReportExport() {
  const [fromMonth, setFromMonth] = useState('2019-01');
  const [toMonth, setToMonth]     = useState('2025-12');
  const [exporting, setExporting] = useState(false);

  const handleExport = (e) => {
    e.preventDefault();
    setExporting(true);
    try {
      api.exportPDF(fromMonth, toMonth);
      setExporting(false);
    } catch (err) {
      console.error("PDF export error:", err);
      setExporting(false);
    }
  };

  return (
    <div className="report-page">
      <div className="page-header">
        <h2 className="page-title">📄 Export Forest Health Reports</h2>
        <p className="page-subtitle">Generate formatted executive PDF summaries containing all metrics, benchmarks, corridor analyses, and priority maps.</p>
      </div>

      <div className="page-body" style={{ maxWidth: '600px' }}>
        <div className="card report-form-card">
          <h3 className="section-title">📄 PDF Report Generator</h3>
          <form onSubmit={handleExport} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div className="form-group" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>START MONTH (YYYY-MM)</label>
                <input 
                  type="month" 
                  value={fromMonth} 
                  onChange={(e) => setFromMonth(e.target.value)}
                  style={{ width: '100%', padding: '8px', background: 'var(--bg-surface)', border: '1px solid rgba(82, 183, 136, 0.3)', color: '#fff', borderRadius: '4px' }}
                />
              </div>
              <div>
                <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>END MONTH (YYYY-MM)</label>
                <input 
                  type="month" 
                  value={toMonth} 
                  onChange={(e) => setToMonth(e.target.value)}
                  style={{ width: '100%', padding: '8px', background: 'var(--bg-surface)', border: '1px solid rgba(82, 183, 136, 0.3)', color: '#fff', borderRadius: '4px' }}
                />
              </div>
            </div>

            <div style={{ background: 'rgba(82, 183, 136, 0.05)', border: '1px solid rgba(82, 183, 136, 0.15)', padding: '12px 14px', borderRadius: '4px', fontSize: '11px', lineHeight: 1.4, color: 'var(--text-muted)' }}>
              📄 <strong>Report Sections Included:</strong>
              <ul style={{ paddingLeft: '14px', marginTop: '6px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <li>Executive Health Summary & Degradation Stats</li>
                <li>3-Model Benchmark Metrics & Comparison Table</li>
                <li>Wildlife Corridor Integrity (Intact / Weakened / Broken)</li>
                <li>Fire Risk Counts & Landslide Hazards (Wayanad 2024 context)</li>
                <li>Carbon Asset Stock Value ($USD)</li>
                <li>Reforestation Action Priority Maps (Ranked Top 3)</li>
              </ul>
            </div>

            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={exporting}
              style={{ padding: '10px', fontSize: '13px', justifyContent: 'center' }}
            >
              {exporting ? 'Generating Report PDF...' : 'Download PDF Report'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
