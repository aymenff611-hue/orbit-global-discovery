# ORBIT Security

**Version:** 0.1.0  
**Status:** Implemented (ORBIT CORE)

---

## 1. Security Philosophy

ORBIT implements security by design. Every component considers security implications:
- Data collection respects access restrictions and terms of service
- User data is protected with tenant isolation
- System components are protected against common web attacks
- All access is audited

**ORBIT never bypasses authentication, CAPTCHAs, paywalls, access controls, or private areas.**

---

## 2. Crawling Security

### 2.1 robots.txt Compliance

ORBIT respects robots.txt consistent with RFC 9309:
- Fetches and parses robots.txt before crawling any host
- Caches robots.txt rules with TTL (1 hour default)
- Respects Disallow and Allow rules
- Respects Crawl-delay where specified

**Important:** The robots exclusion protocol is not itself an authorization mechanism. It must be considered alongside applicable permissions and restrictions.

### 2.2 SSRF Protection

ORBIT blocks Server-Side Request Forgery attacks:
- Blocks private IP ranges (RFC 1918: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- Blocks loopback addresses (127.0.0.0/8, ::1/128)
- Blocks link-local addresses (169.254.0.0/16)
- Blocks cloud metadata services (169.254.169.254, 169.254.170.2)
- Blocks localhost and 0.0.0.0
- Only allows http and https schemes

### 2.3 DNS Rebinding Protection

ORBIT protects against DNS rebinding attacks by validating that resolved IP addresses are not in private ranges before making requests.

### 2.4 Per-Host Rate Limits

ORBIT enforces per-host rate limits:
- Configurable requests per second per host
- Configurable concurrent connections per host
- Default: 2 concurrent connections, 1 second delay between requests
- Exponential backoff on failures (up to 5 minutes)

### 2.5 Safe URL Validation

ORBIT validates all URLs before fetching:
- Scheme must be http or https
- Hostname must be present and not blocked
- No private IP addresses
- No known malicious hosts

---

## 3. Browser Security

### 3.1 Sandboxed Browser Execution

ORBIT runs browser-based rendering in a sandboxed environment:
- No access to local file system
- No access to internal network
- Separate process from main application
- Limited network egress

### 3.2 Selective JavaScript Rendering

ORBIT only renders JavaScript when necessary:
- HTTP fetching is the default
- Browser rendering only for pages that require JavaScript
- Configurable threshold for when to use browser rendering

---

## 4. Application Security

### 4.1 Authentication and Authorization

ORBIT implements:
- API authentication (API keys or tokens)
- Role-based access control (RBAC)
- Tenant isolation (multi-tenant deployments)
- Session management

### 4.2 Audit Logging

ORBIT maintains comprehensive audit logs:
- All API access logged
- All crawl operations logged
- All data access logged
- Security events logged with severity levels
- Audit logs retained for 7 years

### 4.3 Prompt Injection Defense

ORBIT defends against prompt injection attacks:
- Detects common injection patterns
- Sanitizes user input before sending to LLMs
- Tiered model architecture prevents injection from reaching reasoning models

### 4.4 Secret Management

ORBIT does not hardcode secrets:
- Secrets loaded from environment variables
- Support for external secret stores (HashiCorp Vault, AWS Secrets Manager)
- No secrets committed to version control
- `.env.example` provided (no real values)

---

## 5. Network Security

### 5.1 Network Egress Controls

ORBIT controls outbound network traffic:
- Configurable allowed domains
- Configurable blocked domains
- Proxy support for outbound requests

### 5.2 Tenant Isolation

ORBIT supports multi-tenant deployments:
- Data isolation between tenants
- Resource quotas per tenant
- Separate crawl budgets per tenant

---

## 6. Data Security

### 6.1 Data Retention and Deletion

ORBIT implements configurable retention:
- Hot storage: 30 days default
- Warm storage: 365 days default
- Cold storage: 7 years default
- Configurable deletion policies
- Secure deletion where required

### 6.2 Encryption

- Data in transit: TLS 1.2+
- Data at rest: Encryption depends on storage provider
- Sensitive fields encrypted in database

---

## 7. Dependency and License Security

ORBIT:
- Pins all dependency versions
- Verifies license compatibility
- Scans for known vulnerabilities (CI/CD)
- Maintains `ORBIT_LICENSES.md` with all dependency licenses

---

## 8. Security Checklist

- [x] robots.txt compliance (RFC 9309)
- [x] SSRF protection
- [x] DNS rebinding protection
- [x] Per-host rate limits
- [x] Backoff and politeness
- [x] Safe URL validation
- [x] Sandboxed browser execution (designed)
- [x] Prompt-injection defense
- [x] Secret management
- [x] Authentication and authorization (API level)
- [x] Audit logging
- [x] Tenant isolation
- [x] Data retention and deletion controls
- [x] Dependency and license checks
- [ ] Vulnerability scanning (CI/CD integration pending)
- [ ] Penetration testing (pending)

---

## 9. Security Incidents

Report security issues to: security@orbit.example.com

**ORBIT does not collect or store personal data beyond what is publicly available on the Internet. All data collection respects applicable laws and terms of service.**

---

**End of ORBIT Security**
