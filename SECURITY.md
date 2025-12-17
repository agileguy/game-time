# Security Policy

## Overview

The security of Game Time is a top priority. This document outlines our security practices, policies, and procedures for reporting vulnerabilities.

## Supported Versions

| Version | Supported          | Security Updates |
| ------- | ------------------ | ---------------- |
| 1.0.x   | :white_check_mark: | Active           |
| < 1.0   | :x:                | Not supported    |

## Reporting a Vulnerability

### How to Report

If you discover a security vulnerability, please report it responsibly:

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please report security issues via:

1. **Email**: security@example.com (replace with actual email)
2. **GitHub Security Advisories**: Use the "Security" tab on our repository

### What to Include

Please include the following information in your report:

- **Description**: Clear description of the vulnerability
- **Impact**: Potential impact and severity
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Proof of Concept**: Code or screenshots demonstrating the vulnerability
- **Suggested Fix**: If you have ideas for remediation
- **Your Contact Info**: So we can follow up with questions

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - Critical: 24-72 hours
  - High: 1-2 weeks
  - Medium: 2-4 weeks
  - Low: Next release cycle

### Disclosure Policy

- We follow coordinated disclosure
- We will work with you to understand and fix the issue
- We request 90 days before public disclosure
- Credit will be given to reporters (if desired)
- CVEs will be requested for significant vulnerabilities

## Security Features

### Authentication & Authorization

#### Session Management
- **Session IDs**: 256-bit cryptographically secure random tokens (SHA-256)
- **Storage**: Redis with configurable TTL (default 24 hours)
- **Regeneration**: New session ID on privilege escalation
- **Invalidation**: Automatic cleanup of expired sessions
- **Transport**: Secure cookies in production (httpOnly, SameSite, Secure flags)

#### Host Privileges
- **Host Assignment**: First player to join becomes host
- **Host Transfer**: Automatic transfer if host disconnects
- **Action Validation**: Server-side validation of host-only actions
  - Start game
  - Select game
  - Kick players
- **No Client-Side Trust**: All privileges validated server-side

### Input Validation

#### Player Names
```python
Constraints:
- Length: 1-50 characters
- Allowed: Alphanumeric, spaces, basic punctuation
- Sanitization: HTML entities escaped
- Profanity Filter: Configurable word list (optional)
```

#### Room Codes
```python
Format:
- Length: 4-6 characters
- Characters: A-Z, 2-9 (excludes 0/O, 1/I/L for clarity)
- Validation: Regex pattern matching
- Uniqueness: Checked against active rooms
- Expiration: 24 hours after creation
```

#### WebSocket Messages
- **Schema Validation**: All messages validated with Pydantic
- **Type Checking**: Event types must match allowed set
- **Size Limits**: Maximum 10KB per message
- **Rate Limiting**: 60 messages per connection per minute
- **Malformed Messages**: Rejected with error response

#### Database Inputs
- **ORM**: SQLAlchemy with parameterized queries
- **No Raw SQL**: Unless absolutely necessary and validated
- **Escape Hatches**: Explicitly marked and reviewed
- **JSONB Validation**: Schema validation before storing in JSONB fields

### Rate Limiting

Implemented at multiple levels to prevent abuse:

#### Per-IP Limits
```python
Room Creation: 5 per hour
Room Join Attempts: 10 per minute
API Requests: 100 per minute
WebSocket Connections: 10 concurrent max
```

#### Per-Connection Limits
```python
WebSocket Messages: 60 per minute
Action Spam: 10 identical actions per minute (per game)
```

#### Global Limits
```python
Total Concurrent Rooms: Configurable (default 10,000)
Players per Room: 2-12 (configurable max)
Database Connections: Pool limits (min=10, max=50)
```

#### Rate Limit Responses
- HTTP 429 (Too Many Requests) for API endpoints
- WebSocket error message with retry-after
- Exponential backoff encouraged
- Temporary bans for severe abuse (1-24 hours)

### Cross-Site Scripting (XSS) Prevention

#### Content Security Policy (CSP)
```http
Content-Security-Policy:
  default-src 'self';
  script-src 'self';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  font-src 'self';
  connect-src 'self' wss:;
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self'
```

#### Input Sanitization
- **HTML Escaping**: All user-generated content
- **JavaScript Context**: No user input in script tags
- **URL Validation**: Whitelist for external links
- **Markdown**: Disabled (plain text only for v1.0)

#### Output Encoding
- **HTML Entities**: Encoded before display
- **JSON**: Proper escaping in API responses
- **Attribute Values**: Quoted and escaped

### Cross-Site Request Forgery (CSRF) Protection

#### Stateless API Design
- Primary protection: stateless WebSocket + session tokens
- No cookies for critical state (development only)

#### Production CSRF Measures
- **CSRF Tokens**: For any future form submissions
- **SameSite Cookies**: Strict mode in production
- **Origin Validation**: Check Origin/Referer headers
- **Custom Headers**: Require X-Requested-With header

### SQL Injection Prevention

#### ORM Usage
- **SQLAlchemy**: All database access via ORM
- **Parameterized Queries**: Never string concatenation
- **Type Safety**: Pydantic schemas enforce types

#### Raw Query Protection
```python
# If raw queries needed (rare):
- Use bind parameters: session.execute(text(query), {"param": value})
- Validate all inputs with Pydantic
- Whitelist allowed table/column names
- Code review required
```

#### Database Configuration
```sql
-- Principle of least privilege
CREATE USER gametime_app WITH PASSWORD 'secure_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO gametime_app;
REVOKE CREATE ON SCHEMA public FROM gametime_app;
REVOKE ALL ON pg_catalog FROM gametime_app;
```

### WebSocket Security

#### Connection Security

**Origin Validation**
```python
Allowed origins from environment variable
Reject connections from unauthorized origins
Log rejected connection attempts
```

**Authentication**
```python
Session ID required for all connections
Session validated against Redis store
Expired sessions rejected immediately
```

**Connection Limits**
```python
Max 2 concurrent connections per session
Max 10 connections per IP address
Auto-disconnect idle connections (5 minute timeout)
```

#### Message Security

**Message Validation**
- Pydantic schema for every message type
- Reject malformed messages immediately
- Log validation failures for monitoring
- No reflection of unvalidated user input

**State Validation**
- All game actions validated against current state
- Prevent out-of-order actions
- Verify player is in room before processing
- Check game phase before allowing actions

**Broadcasting**
- Display receives full state
- Controllers receive filtered state (no secrets)
- Never broadcast session IDs or sensitive data
- Sanitize all player-generated content before broadcast

### Transport Layer Security (TLS)

#### Production Requirements
- **TLS 1.3 Required**: TLS 1.2 minimum
- **Strong Ciphers Only**: ECDHE-RSA-AES256-GCM-SHA384 and similar
- **HSTS Enabled**: Strict-Transport-Security header
- **Certificate Validation**: Valid certificates from trusted CA
- **WebSocket Security**: wss:// protocol enforced

#### Development
- HTTP allowed for local development only
- ws:// protocol for local WebSockets
- Clear warnings about production requirements

### Security Headers

All HTTP responses include:

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

### Denial of Service (DoS) Protection

#### Application Level

**Resource Limits**
```python
Max room lifetime: 24 hours
Max game duration: 2 hours
Max player name length: 50 characters
Max WebSocket message size: 10KB
Max concurrent rooms per server: 10,000
```

**Automatic Cleanup**
- Rooms inactive >1 hour auto-deleted
- Disconnected players removed after 5 minutes
- Orphaned sessions cleaned every hour
- Database vacuum scheduled weekly

**Graceful Degradation**
- Non-critical features disabled under load
- Reduced update frequency if overloaded
- Clear error messages when at capacity

#### Infrastructure Level

**Nginx**
```nginx
# Connection limits
limit_conn_zone $binary_remote_addr zone=conn_limit:10m;
limit_conn conn_limit 10;

# Request rate limiting
limit_req_zone $binary_remote_addr zone=req_limit:10m rate=10r/s;
limit_req zone=req_limit burst=20 nodelay;

# Request size limits
client_max_body_size 1M;
client_body_buffer_size 16K;
```

**Database**
- Connection pooling (prevent exhaustion)
- Query timeout limits (30 seconds max)
- Prepared statement caching
- Read replicas for analytics

**Redis**
- Memory limits configured
- Eviction policy: allkeys-lru
- Maxmemory-policy configured

### Data Privacy & Protection

#### Data Collection
**We collect minimal data:**
- Room codes (temporary, auto-expire)
- Player names (ephemeral, no persistence required)
- Session IDs (hashed, temporary)
- Game scores (aggregate only, no PII)
- IP addresses (for rate limiting, not stored long-term)

**We DO NOT collect:**
- Email addresses (no accounts in v1.0)
- Passwords (no authentication in v1.0)
- Payment information (free to play)
- Location data (beyond IP for rate limiting)
- Device fingerprinting

#### Data Retention
```
Session data: 24 hours (Redis TTL)
Room data: 24 hours after last activity
Game history: 30 days (configurable)
Audit logs: 90 days
Error logs: 30 days
Metrics: 1 year (aggregated)
```

#### Data Deletion
- Automatic cleanup of expired data
- Manual deletion via admin interface (future)
- Database-level cascade deletes configured
- Redis TTL ensures automatic cleanup

#### GDPR Compliance (if applicable)
- No personal data collected for gameplay
- Right to erasure: automatic via TTLs
- Data portability: game stats exportable (future)
- Privacy by design: minimal data collection

### Audit Logging

#### Events Logged
```python
Security Events:
- Failed authentication attempts
- Rate limit violations
- Invalid message types
- Kicked players
- Suspicious patterns

Application Events:
- Room creation/deletion
- Game start/end
- Player join/leave
- Host transfers
- Errors and exceptions
```

#### Log Format
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "INFO",
  "event": "player_joined",
  "room_code": "ABCD",
  "player_id": 123,
  "ip_hash": "sha256_hash",
  "user_agent_hash": "sha256_hash",
  "request_id": "uuid",
  "details": {}
}
```

#### Log Security
- PII hashed or excluded
- Centralized logging (future: ELK stack)
- Access controls on log files
- Retention policies enforced
- Regular review for suspicious activity

### Dependency Management

#### Security Scanning
```bash
# Automated scanning
pip-audit                    # Python dependency vulnerabilities
bandit -r app                # Python security linting
trivy scan .                 # Container scanning (Docker)
```

#### Update Policy
- **Critical vulnerabilities**: Patch within 24 hours
- **High severity**: Patch within 1 week
- **Medium severity**: Next release cycle
- **Low severity**: Evaluated case-by-case

#### Dependency Pinning
```python
# requirements.txt uses exact versions
fastapi==0.104.1
sqlalchemy==2.0.23

# Regular updates scheduled
- Security updates: Weekly review
- Minor updates: Monthly
- Major updates: Quarterly (with testing)
```

### Secrets Management

#### Environment Variables
```bash
# Never commit to Git
.env files in .gitignore
Use .env.example for templates
```

#### Production Secrets
- **Secret Key**: 256-bit random, rotated quarterly
- **Database Password**: Strong, unique, rotated annually
- **Redis Password**: Strong, unique, rotated annually
- **API Keys**: Scoped, rotated as needed

#### Secret Storage
- Environment variables (development)
- HashiCorp Vault (production recommended)
- AWS Secrets Manager (cloud deployment)
- Never hardcoded in source

### Monitoring & Incident Response

#### Security Monitoring

**Automated Alerts**
- High rate of 4xx/5xx errors
- Rate limit violations spike
- Failed authentication attempts
- Unusual traffic patterns
- Resource exhaustion warnings

**Metrics Tracked**
```
security.auth.failures
security.rate_limit.violations
security.websocket.invalid_messages
security.suspicious_activity
```

#### Incident Response Plan

**Detection** (0-1 hour)
- Automated alerting via Prometheus
- On-call rotation for critical alerts
- Slack/PagerDuty integration

**Assessment** (1-4 hours)
- Severity classification (P0-P4)
- Impact analysis
- Affected users identified

**Containment** (Immediate)
- Isolate affected systems
- Block malicious IPs
- Disable compromised features
- Preserve evidence (logs, memory dumps)

**Remediation** (4-48 hours)
- Apply patches/fixes
- Update security rules
- Rotate compromised secrets
- Restore from clean backups if needed

**Recovery** (24-72 hours)
- Gradual service restoration
- Monitor for recurrence
- Enhanced monitoring activated

**Post-Incident** (1-2 weeks)
- Root cause analysis
- Post-mortem document
- Action items for prevention
- Update security policies
- Team training if needed

### Security Testing

#### Automated Testing
```bash
# Run with CI/CD
pytest tests/security/        # Security-specific tests
bandit -r app                 # SAST scanning
safety check                  # Dependency vulnerabilities
```

#### Manual Testing
- **Penetration Testing**: Annually by third-party
- **Code Reviews**: All PRs require security review
- **Security Audits**: Quarterly internal reviews

#### Bug Bounty Program
- Planned for version 2.0
- Responsible disclosure encouraged
- Rewards for valid vulnerabilities
- Scope and rules to be published

## Security Best Practices for Contributors

### Code Reviews
- All code changes require review
- Security-sensitive changes require 2 reviews
- Use GitHub's security features

### Development Environment
- Use virtual environments
- Keep dependencies updated
- Never commit secrets
- Use pre-commit hooks

### Testing Requirements
- Unit tests for security functions
- Integration tests for auth flows
- Fuzz testing for input validation

### Secure Coding Guidelines
- Input validation on all user data
- Output encoding for XSS prevention
- Parameterized queries only
- Principle of least privilege
- Fail securely (deny by default)
- Defense in depth

## Compliance & Standards

### Standards Followed
- **OWASP Top 10**: Mitigations for all categories
- **CWE/SANS Top 25**: Regular review and fixes
- **NIST Cybersecurity Framework**: Aligned practices

### Accessibility
- **WCAG 2.1 AA**: Compliance target
- Security features accessible to all users
- Clear error messages and guidance

## Security Contacts

- **Security Team**: security@example.com
- **Emergency Contact**: +1-XXX-XXX-XXXX (24/7 on-call)
- **PGP Key**: Available on keybase.io or website

## Updates to This Policy

This security policy is reviewed and updated:
- Quarterly as part of security review
- After any security incident
- When new features are added
- Based on community feedback

Last Updated: 2025-01-15
Version: 1.0

## Acknowledgments

We thank the security researchers and community members who help keep Game Time secure. Responsible disclosure is appreciated and recognized.

---

**Remember**: Security is everyone's responsibility. If you see something, say something.
