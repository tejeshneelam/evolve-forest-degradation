import React, { useState, useEffect } from 'react';
import { api } from '../api/client';

export default function SecurityTab() {
  const [auditLogs, setAuditLogs] = useState([]);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [rateTestResults, setRateTestResults] = useState([]);
  const [testingRateLimit, setTestingRateLimit] = useState(false);
  const [sanitizerInput, setSanitizerInput] = useState('76.0, 95.0, 76.5, 96.0');
  const [sanitizerResult, setSanitizerResult] = useState(null);

  const fetchAuditLogs = () => {
    setLoadingLogs(true);
    api.getAuditLogs(15)
      .then(res => {
        setAuditLogs(res.audit_logs || []);
        setLoadingLogs(false);
      })
      .catch(() => {
        setLoadingLogs(false);
      });
  };

  useEffect(() => {
    fetchAuditLogs();
  }, []);

  // Demo 1: Trigger Rate Limiter in real time
  const handleTestRateLimiting = async () => {
    setTestingRateLimit(true);
    setRateTestResults([]);
    const results = [];

    for (let i = 1; i <= 6; i++) {
      try {
        const response = await fetch('http://localhost:8000/api/run-ga-adaptation', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ target_objective: 'balanced', generations: 1 })
        });
        const data = await response.json().catch(() => ({}));
        results.push({
          attempt: i,
          status: response.status,
          statusText: response.status === 429 ? '429 TOO MANY REQUESTS (BLOCKED)' : '200 OK (ALLOWED)',
          detail: data.detail || (response.status === 429 ? 'Rate limit exceeded: 5 per 1 minute quota reached' : 'Request processed successfully'),
          blocked: response.status === 429
        });
      } catch (err) {
        results.push({
          attempt: i,
          status: 429,
          statusText: '429 BLOCKED',
          detail: err.message,
          blocked: true
        });
      }
      setRateTestResults([...results]);
      await new Promise(r => setTimeout(r, 120));
    }
    setTestingRateLimit(false);
    fetchAuditLogs();
  };

  // Demo 2: Test Coordinate & Injection Sanitizer
  const handleTestSanitizer = async () => {
    setSanitizerResult(null);
    try {
      const parts = sanitizerInput.split(',').map(s => parseFloat(s.trim()));
      const response = await fetch('http://localhost:8000/api/dynamic-region', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bbox: parts.length === 4 ? parts : [0, 0, 0, 0],
          region_name: sanitizerInput
        })
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setSanitizerResult({
          success: false,
          status: response.status,
          message: data.detail || 'Validation failed: Coordinates rejected by security policy.'
        });
      } else {
        setSanitizerResult({
          success: true,
          status: 200,
          message: 'Valid coordinates accepted by backend.'
        });
      }
    } catch (err) {
      setSanitizerResult({
        success: false,
        status: 400,
        message: err.message
      });
    }
    fetchAuditLogs();
  };

  return (
    <div className="security-tab" style={{ padding: '24px', overflowY: 'auto', maxHeight: '100vh', color: '#E8F5EE' }}>
      {/* ── Header ────────────────────────────────────────────── */}
      <div style={{ background: '#132A1E', borderRadius: '12px', padding: '20px 24px', border: '1px solid rgba(82,183,136,0.3)', marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h1 style={{ fontSize: '22px', fontWeight: '700', color: '#52B788', display: 'flex', alignItems: 'center', gap: '8px' }}>
              🛡️ Cyber Security Hardening & Rate Limiting Center
            </h1>
            <p style={{ color: '#95D5B2', fontSize: '14px', marginTop: '4px' }}>
              OWASP Defense-in-Depth, API Rate Limiting, Coordinate Sanitization & Forensic Telemetry
            </p>
          </div>
          <div style={{ background: 'rgba(82,183,136,0.15)', border: '1px solid #52B788', borderRadius: '8px', padding: '8px 16px', textAlign: 'right' }}>
            <div style={{ fontSize: '12px', color: '#95D5B2' }}>Assigned Team Member</div>
            <div style={{ fontSize: '14px', fontWeight: '700', color: '#E8F5EE' }}>Ande Tarak (cse23212)</div>
            <div style={{ fontSize: '11px', color: '#52B788' }}>Feature: feature/security-rate-limiting (#3)</div>
          </div>
        </div>
      </div>

      {/* ── Defense Status Cards ──────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        <div style={{ background: '#132A1E', padding: '16px', borderRadius: '10px', border: '1px solid rgba(82,183,136,0.2)' }}>
          <div style={{ fontSize: '12px', color: '#95D5B2', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Rate Limiting Engine</div>
          <div style={{ fontSize: '18px', fontWeight: '700', color: '#52B788', margin: '8px 0 4px 0' }}>SlowAPI (Active)</div>
          <div style={{ fontSize: '12px', color: '#A0B1A8' }}>
            • GA Tuning: <strong>5 req/min</strong><br />
            • Dynamic Region: <strong>30 req/min</strong><br />
            • Geo-Safety: <strong>20 req/min</strong>
          </div>
        </div>

        <div style={{ background: '#132A1E', padding: '16px', borderRadius: '10px', border: '1px solid rgba(82,183,136,0.2)' }}>
          <div style={{ fontSize: '12px', color: '#95D5B2', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Coordinate Sanitizer</div>
          <div style={{ fontSize: '18px', fontWeight: '700', color: '#52B788', margin: '8px 0 4px 0' }}>Pydantic v2 (Strict)</div>
          <div style={{ fontSize: '12px', color: '#A0B1A8' }}>
            • Latitude: <strong>-90° to +90°</strong><br />
            • Longitude: <strong>-180° to +180°</strong><br />
            • Anti-Injection: <strong>XSS/SQLi Stripped</strong>
          </div>
        </div>

        <div style={{ background: '#132A1E', padding: '16px', borderRadius: '10px', border: '1px solid rgba(82,183,136,0.2)' }}>
          <div style={{ fontSize: '12px', color: '#95D5B2', textTransform: 'uppercase', letterSpacing: '0.05em' }}>HTTP Security Headers</div>
          <div style={{ fontSize: '18px', fontWeight: '700', color: '#52B788', margin: '8px 0 4px 0' }}>OWASP Compliant</div>
          <div style={{ fontSize: '12px', color: '#A0B1A8' }}>
            • <code>X-Frame-Options: DENY</code><br />
            • <code>X-Content-Type: nosniff</code><br />
            • <code>HSTS & Strict CORS</code>
          </div>
        </div>

        <div style={{ background: '#132A1E', padding: '16px', borderRadius: '10px', border: '1px solid rgba(82,183,136,0.2)' }}>
          <div style={{ fontSize: '12px', color: '#95D5B2', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Audit Telemetry</div>
          <div style={{ fontSize: '18px', fontWeight: '700', color: '#52B788', margin: '8px 0 4px 0' }}>Forensic Logger</div>
          <div style={{ fontSize: '12px', color: '#A0B1A8' }}>
            • Logs: <strong>Client IP & Latency</strong><br />
            • Timing: <strong>X-Response-Time</strong><br />
            • Buffer: <strong>100 Event Audit Ring</strong>
          </div>
        </div>
      </div>

      {/* ── Live Interactive Verification Demos ───────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        {/* Demo 1: Rate Limiter */}
        <div style={{ background: '#132A1E', borderRadius: '12px', padding: '20px', border: '1px solid rgba(82,183,136,0.2)' }}>
          <h2 style={{ fontSize: '16px', fontWeight: '700', color: '#E8F5EE', marginBottom: '8px' }}>
            ⚡ Live Rate Limiting Test (DoS Defense)
          </h2>
          <p style={{ fontSize: '13px', color: '#95D5B2', marginBottom: '14px' }}>
            Simulates rapid API requests to <code>POST /api/run-ga-adaptation</code> (Threshold: 5 requests/min).
            Notice how requests 1–5 succeed and request 6 is instantly blocked by our SlowAPI limiter.
          </p>

          <button
            onClick={handleTestRateLimiting}
            disabled={testingRateLimit}
            style={{
              background: testingRateLimit ? '#2D6A4F' : '#52B788',
              color: '#0D1F17',
              border: 'none',
              padding: '10px 18px',
              borderRadius: '8px',
              fontWeight: '700',
              cursor: testingRateLimit ? 'not-allowed' : 'pointer',
              fontSize: '13px',
              marginBottom: '16px'
            }}
          >
            {testingRateLimit ? 'Running 6 Rapid Requests...' : '▶ Run Live Rate Limit Test (6 Requests)'}
          </button>

          {rateTestResults.length > 0 && (
            <div style={{ background: '#0D1F17', borderRadius: '8px', padding: '12px', border: '1px solid rgba(82,183,136,0.2)' }}>
              {rateTestResults.map(r => (
                <div key={r.attempt} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.05)', fontSize: '12px' }}>
                  <span>Request #{r.attempt}:</span>
                  <span style={{ fontWeight: '700', color: r.blocked ? '#E63946' : '#52B788' }}>
                    {r.statusText}
                  </span>
                  <span style={{ color: '#A0B1A8', fontSize: '11px', maxWidth: '200px', textAlign: 'right' }}>
                    {r.detail}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Demo 2: Input Sanitization & Bounds */}
        <div style={{ background: '#132A1E', borderRadius: '12px', padding: '20px', border: '1px solid rgba(82,183,136,0.2)' }}>
          <h2 style={{ fontSize: '16px', fontWeight: '700', color: '#E8F5EE', marginBottom: '8px' }}>
            🛡️ Geographic Bounds & Sanitization Test
          </h2>
          <p style={{ fontSize: '13px', color: '#95D5B2', marginBottom: '14px' }}>
            Test coordinate boundary validation (-90° to +90° Lat) and script injection defense.
          </p>

          <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
            <button
              onClick={() => setSanitizerInput('76.0, 95.0, 76.5, 96.0')}
              style={{ background: 'rgba(230,57,70,0.15)', border: '1px solid #E63946', color: '#E63946', padding: '4px 10px', borderRadius: '6px', fontSize: '11px', cursor: 'pointer' }}
            >
              Preset: Lat &gt; 90° (Illegal)
            </button>
            <button
              onClick={() => setSanitizerInput('76.0, 15.0, 76.5, 12.0')}
              style={{ background: 'rgba(244,162,97,0.15)', border: '1px solid #F4A261', color: '#F4A261', padding: '4px 10px', borderRadius: '6px', fontSize: '11px', cursor: 'pointer' }}
            >
              Preset: Inverted Lat
            </button>
            <button
              onClick={() => setSanitizerInput('76.325, 11.625, 76.375, 11.675')}
              style={{ background: 'rgba(82,183,136,0.15)', border: '1px solid #52B788', color: '#52B788', padding: '4px 10px', borderRadius: '6px', fontSize: '11px', cursor: 'pointer' }}
            >
              Preset: Valid Wayanad
            </button>
          </div>

          <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
            <input
              type="text"
              value={sanitizerInput}
              onChange={e => setSanitizerInput(e.target.value)}
              style={{ flex: 1, background: '#0D1F17', border: '1px solid #52B788', color: '#E8F5EE', padding: '8px 12px', borderRadius: '6px', fontSize: '13px' }}
            />
            <button
              onClick={handleTestSanitizer}
              style={{ background: '#52B788', color: '#0D1F17', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: '700', cursor: 'pointer', fontSize: '13px' }}
            >
              Validate
            </button>
          </div>

          {sanitizerResult && (
            <div style={{
              background: sanitizerResult.success ? 'rgba(82,183,136,0.1)' : 'rgba(230,57,70,0.1)',
              border: `1px solid ${sanitizerResult.success ? '#52B788' : '#E63946'}`,
              borderRadius: '8px',
              padding: '12px',
              fontSize: '12px',
              color: sanitizerResult.success ? '#52B788' : '#E63946'
            }}>
              <strong>HTTP {sanitizerResult.status}: </strong>
              {typeof sanitizerResult.message === 'string' ? sanitizerResult.message : JSON.stringify(sanitizerResult.message)}
            </div>
          )}
        </div>
      </div>

      {/* ── Live Forensic Audit Logs Table ────────────────────── */}
      <div style={{ background: '#132A1E', borderRadius: '12px', padding: '20px', border: '1px solid rgba(82,183,136,0.2)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: '700', color: '#E8F5EE' }}>
              📋 Real-Time Forensic Audit Telemetry
            </h2>
            <p style={{ fontSize: '12px', color: '#95D5B2' }}>
              Live stream from <code>/api/security/audit-logs</code> capturing client IP, endpoint, HTTP status, and latency (ms).
            </p>
          </div>
          <button
            onClick={fetchAuditLogs}
            disabled={loadingLogs}
            style={{ background: 'transparent', border: '1px solid #52B788', color: '#52B788', padding: '6px 14px', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' }}
          >
            {loadingLogs ? 'Refreshing...' : '🔄 Refresh Logs'}
          </button>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(82,183,136,0.3)', color: '#95D5B2' }}>
                <th style={{ padding: '8px 10px' }}>Timestamp (UTC)</th>
                <th style={{ padding: '8px 10px' }}>Client IP</th>
                <th style={{ padding: '8px 10px' }}>Method</th>
                <th style={{ padding: '8px 10px' }}>Route / Endpoint</th>
                <th style={{ padding: '8px 10px' }}>Status</th>
                <th style={{ padding: '8px 10px' }}>Latency</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.length === 0 ? (
                <tr>
                  <td colSpan="6" style={{ padding: '16px', textAlign: 'center', color: '#A0B1A8' }}>
                    No audit records buffered yet. Trigger any action above to generate telemetry!
                  </td>
                </tr>
              ) : (
                auditLogs.map((log, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <td style={{ padding: '8px 10px', color: '#A0B1A8' }}>{log.timestamp ? log.timestamp.split('T')[1].slice(0, 8) : '—'}</td>
                    <td style={{ padding: '8px 10px', fontFamily: 'monospace' }}>{log.client_ip}</td>
                    <td style={{ padding: '8px 10px', fontWeight: '700', color: log.method === 'POST' ? '#F4A261' : '#52B788' }}>{log.method}</td>
                    <td style={{ padding: '8px 10px', fontFamily: 'monospace' }}>{log.route}</td>
                    <td style={{ padding: '8px 10px' }}>
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontWeight: '700',
                        background: log.status_code === 200 ? 'rgba(82,183,136,0.2)' : 'rgba(230,57,70,0.2)',
                        color: log.status_code === 200 ? '#52B788' : '#E63946'
                      }}>
                        {log.status_code}
                      </span>
                    </td>
                    <td style={{ padding: '8px 10px', color: '#A0B1A8' }}>{log.latency_ms} ms</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
