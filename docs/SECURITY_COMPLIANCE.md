# EvOLve Cyber Security Hardening & Compliance Report

**Assigned Engineer**: Ande Tarak (`cse23212` / `cse232212`)  
**Branch**: `tarak`  
**Feature Module**: `feature/security-rate-limiting` (Issue #3)  
**Project**: EvOLve — Evolutionary-Optimized Forest Degradation Intelligence Framework  
**Scope**: Backend API Rate Limiting, Coordinate Sanitization, Security Headers & Forensic Audit Logging  

---

## 1. Executive Summary

As part of production hardening and enterprise deployment readiness, the EvOLve platform requires cyber security controls across the FastAPI backend and React frontend. Prior to this implementation, API routes handling computationally intensive operations (Google Earth Engine raster fetches, Genetic Algorithm optimizations, and geotechnical inference) were vulnerable to Denial-of-Service (DoS) attacks, coordinate injection, and clickjacking vulnerabilities.

This deliverable establishes an automated defense-in-depth architecture adhering to OWASP API Security Top 10 standards.

---

## 2. Implemented Security Controls & Deliverables

### A. API Rate Limiting (`SlowAPI`)
* **Technology**: `slowapi` utilizing IP-based rate limiting via `get_remote_address`.
* **Quotas Configured**:
  | Endpoint | HTTP Method | Maximum Rate Limit | Resource Protected |
  | :--- | :---: | :---: | :--- |
  | `/api/run-ga-adaptation` | `POST` | **5 req / min** | Heavy multi-generation Genetic Algorithm optimization |
  | `/api/process-region` & `/api/dynamic-region` | `POST` | **30 req / min** | Google Earth Engine satellite raster ingestion pipeline |
  | `/api/inference/construction-suitability` | `POST` | **20 req / min** | Geotechnical slope & landslide inference simulations |
* **Throttling Response (HTTP 429)**:
  Returns RFC 6585-compliant response:
  ```json
  {
    "error": "Too Many Requests",
    "message": "API rate limit exceeded. Please wait before submitting additional requests.",
    "detail": "5 per 1 minute",
    "retry_after_seconds": 60
  }
  ```
  Includes HTTP header: `Retry-After: 60`.

---

### B. Geographic Coordinate & Parameter Sanitization
* **File**: `dashboard/backend/utils/sanitizer.py` & Pydantic models in `dynamic_region.py`, `health.py`, and `reports.py`.
* **Controls**:
  1. **Latitude Bounds**: Validates `-90.0 <= min_lat < max_lat <= 90.0`.
  2. **Longitude Bounds**: Validates `-180.0 <= min_lon < max_lon <= 180.0`.
  3. **Region Size Throttling**: Limits real-time analysis to `<= 0.35° x 0.35°` (~35km x 35km).
  4. **Strict ISO-8601 Date Parsing**: Enforces regex `^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$` and ensures `start_date <= end_date`.
  5. **XSS & Injection Sanitization**: Strips HTML tags, script signatures (`<script>`, `javascript:`, `onerror=`), and SQL injection patterns from string inputs.
  6. **Identifier Bounds**: Enforces `0 <= patch_id <= 10000` on path parameters to prevent directory traversal and buffer overflow attempts.

---

### C. Response Security Headers Middleware
* **File**: `dashboard/backend/middleware/security.py` (`SecurityHeadersMiddleware`).
* **Headers Injected on All HTTP Responses**:
  * `X-Content-Type-Options: nosniff` — Defends against MIME-sniffing attacks.
  * `X-Frame-Options: DENY` — Precludes iframe clickjacking embedding.
  * `Strict-Transport-Security: max-age=31536000; includeSubDomains` — Mandates encrypted HTTPS transport.
  * `Content-Security-Policy: default-src 'self'; ... frame-ancestors 'none';` — Restricts asset loading origins.
  * `Referrer-Policy: strict-origin-when-cross-origin` — Protects internal URI telemetry.
  * `X-XSS-Protection: 1; mode=block` — Enables browser-side XSS filters.
  * `Permissions-Policy: geolocation=(), camera=(), microphone=()` — Disables unauthorized browser hardware APIs.

---

### D. Strict Cross-Origin Resource Sharing (CORS)
* Configured in `dashboard/backend/main.py`.
* Whitelists strictly authorized local dashboard origins:
  * `http://localhost:3000`
  * `http://127.0.0.1:3000`
* Restricts allowable HTTP methods to `GET`, `POST`, `OPTIONS`.

---

### E. Audit Logging & Forensic Telemetry
* **File**: `dashboard/backend/middleware/audit.py` (`AuditLoggingMiddleware`).
* **Format**:
  ```text
  2026-09-07T11:13:17 [AUDIT_LOG] timestamp=2026-09-07T11:13:17.096596+00:00 client_ip=127.0.0.1 method=POST route=/api/dynamic-region status=200 latency_ms=26.47
  ```
* **Buffer & Endpoint**:
  * Maintains an in-memory ring buffer of the 100 most recent requests.
  * Exposes audit telemetry at `GET /api/security/audit-logs` for compliance inspection.
  * Injects `X-Response-Time` header on every response.

---

### F. Frontend Defense-in-Depth & Architectural Separation
* **Files**: `dashboard/frontend/src/api/client.js`, `ForestMap.jsx`, `GALog.jsx`.
* **Clean Architectural Separation of Concerns**:
  * Cybersecurity mechanisms (SlowAPI rate limiting, coordinate bounds verification, OWASP response headers, forensic audit logging) are implemented and enforced natively at the backend middleware and API gateway layer.
  * The frontend UI remains strictly dedicated to core ecological and forest degradation decision support (Forest Health, Wildlife Corridors, Risk, Conservation, GA Adaptation, and Reports), keeping the interface domain-focused and intuitive for forestry officers and stakeholders without exposing raw forensic security dashboards.
* **Client-Side Validation & Transparent Throttling**:
  * Prevents malformed bounding box coordinates or inverted coordinates before dispatching network requests.
  * Checks `startDate <= endDate` on client-side calendar filters.
  * Transparently intercepts HTTP 429 status codes via `handleResponse` in `client.js` and surfaces actionable, human-readable retry guidance whenever backend quotas are reached.

---

## 3. Verification & Automated Test Evidence

Automated validation was executed with the following outcomes:
* **Test 1**: Request with `lat > 90.0` was rejected with HTTP 400.
* **Test 2**: Request with inverted latitude (`min_lat >= max_lat`) was rejected with HTTP 400.
* **Test 3**: Malformed date `2025/13/45` was rejected with HTTP 422.
* **Test 4**: Inverted date range (`start_date > end_date`) was rejected with HTTP 400.
* **Test 5**: Out-of-bounds `patch_id` (`-5`) was rejected with HTTP 422.
* **Test 6**: Route `/api/run-ga-adaptation` allowed 5 requests and rejected the 6th with HTTP 429 (`Retry-After: 60`).
* **Test 7**: Outgoing responses verified to contain `x-frame-options: DENY` and `x-content-type-options: nosniff`.
