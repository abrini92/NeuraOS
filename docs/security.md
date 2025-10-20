# 🔒 NEURA Security Guide

Security model and best practices for NEURA Cognitive OS.

## Table of Contents

1. [Security Philosophy](#security-philosophy)
2. [Threat Model](#threat-model)
3. [Encryption](#encryption)
4. [Authentication](#authentication)
5. [Authorization](#authorization)
6. [Audit Trail](#audit-trail)
7. [Best Practices](#best-practices)
8. [Security Checklist](#security-checklist)
9. [Incident Response](#incident-response)

---

## Security Philosophy

NEURA is built on three security principles:

### 1. Privacy by Design
- **Local-first**: All data stays on your machine
- **Zero telemetry**: No data sent to external servers
- **Minimal permissions**: Request only what's needed

### 2. Defense in Depth
- **Multiple layers**: Encryption, policies, audit
- **Fail secure**: Deny by default
- **Least privilege**: Minimal access rights

### 3. Transparency
- **Open source**: Code is auditable
- **Audit trail**: Every action logged
- **User control**: Full data ownership

---

## Threat Model

### What We Protect Against

#### ✅ Data Breach
**Threat**: Unauthorized access to stored data

**Protection**:
- AES-256 encryption at rest
- SQLCipher for databases
- Argon2 password hashing

**Example**:
```
Attacker gains file system access
     ↓
Encrypted database files
     ↓
Cannot decrypt without master password
     ↓
Data remains secure
```

#### ✅ Malicious Commands
**Threat**: Execution of harmful system commands

**Protection**:
- OPA policy engine
- Action whitelist/blacklist
- User confirmation for risky actions

**Example**:
```
Malicious prompt: "Delete all files"
     ↓
Policy check: DENY (destructive action)
     ↓
Action blocked
     ↓
Logged in WHY Journal
```

#### ✅ Credential Theft
**Threat**: Stealing API keys, passwords

**Protection**:
- Vault encryption
- No plaintext storage
- Secure memory handling

#### ✅ Data Exfiltration
**Threat**: Leaking data to external services

**Protection**:
- No cloud dependencies
- Network monitoring
- Outbound connection control

#### ✅ Memory Tampering
**Threat**: Modifying stored memories

**Protection**:
- Checksums for integrity
- Audit trail for changes
- Encrypted storage

### What We Don't Protect Against

#### ❌ Physical Access
If attacker has physical access to an **unlocked** machine:
- Can access running NEURA instance
- Can read decrypted memory
- Can execute commands

**Mitigation**: Lock your machine when away

#### ❌ OS-Level Malware
If attacker has root/admin access:
- Can keylog master password
- Can dump memory
- Can bypass all protections

**Mitigation**: Keep OS updated, use antivirus

#### ❌ Social Engineering
If attacker tricks user:
- User may reveal master password
- User may approve malicious actions

**Mitigation**: User education, confirmation prompts

---

## Encryption

### At Rest

#### Vault (Secrets)

```python
# Encryption flow
User Password
     ↓
Argon2 KDF
  - Time cost: 3
  - Memory cost: 65536 KB
  - Parallelism: 4
     ↓
Master Key (256-bit)
     ↓
AES-256-GCM
  - Unique IV per secret
  - Authentication tag
     ↓
SQLCipher Database
  - Page size: 4096
  - KDF iterations: 256000
```

**Code Example**:
```python
from neura.vault.crypto import VaultCrypto

crypto = VaultCrypto()
encrypted = crypto.encrypt(
    data=b"secret_api_key",
    password="master_password"
)
# Returns: (ciphertext, salt, iv, tag)
```

#### Memory (Embeddings)

```python
# Sensitive memories are encrypted
Memory Storage
     ↓
Check if sensitive (PII, credentials)
     ↓
If sensitive: Encrypt with vault key
     ↓
Store encrypted blob
     ↓
Embeddings stored separately (not encrypted)
```

**Note**: Embeddings cannot be encrypted as they need to be searchable. Sensitive data is not embedded.

### In Transit

#### Local API (HTTP)

```bash
# Development: HTTP
http://localhost:8000

# Production: HTTPS with self-signed cert
https://localhost:8443
```

**Generate Self-Signed Certificate**:
```bash
openssl req -x509 -newkey rsa:4096 \
  -keyout key.pem -out cert.pem \
  -days 365 -nodes \
  -subj "/CN=localhost"
```

#### Remote API (Future)

```bash
# TLS 1.3 only
# Perfect forward secrecy
# Certificate pinning
```

---

## Authentication

### Master Password

**Requirements**:
- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- Not in common password lists
- Unique to NEURA

**Storage**:
```python
# Never stored in plaintext
# Only Argon2 hash stored

password = "user_password"
     ↓
Argon2id hash
     ↓
Store hash in config
     ↓
Verify on unlock
```

**Password Verification**:
```python
from neura.vault.crypto import verify_password

is_valid = verify_password(
    password="user_input",
    stored_hash="$argon2id$v=19$m=65536..."
)
```

### Session Management

```python
# Sessions expire after inactivity
SESSION_TIMEOUT = 3600  # 1 hour

# Auto-lock on system sleep
# Re-authentication required
```

### API Keys (Future)

```python
# For remote API access
POST /auth/create-key
{
  "name": "mobile_app",
  "permissions": ["read"],
  "expires_at": "2025-12-31"
}

# Returns
{
  "key": "neura_abc123xyz...",
  "secret": "secret_def456uvw..."
}
```

---

## Authorization

### Policy Engine (OPA)

#### Safe Actions (Always Allowed)

```rego
package neura.motor

# Read-only operations
allow {
    input.action in [
        "read_file",
        "list_files",
        "search_files",
        "get_calendar",
        "check_email"
    ]
}
```

#### Confirmation Required

```rego
# Write operations
require_confirmation {
    input.action in [
        "create_file",
        "modify_file",
        "send_email",
        "create_event"
    ]
}
```

#### Denied Actions

```rego
# Dangerous operations
deny {
    input.action in [
        "delete_file",
        "run_shell_command",
        "modify_system"
    ]
    # Unless explicitly allowed
    not input.user_confirmed
}

# System files always denied
deny {
    input.action == "delete_file"
    startswith(input.path, "/System")
}
```

### Risk Levels

```python
class RiskLevel(Enum):
    LOW = "low"        # Read operations
    MEDIUM = "medium"  # Write operations
    HIGH = "high"      # Destructive operations
    CRITICAL = "critical"  # System modifications

# Policy decision includes risk level
{
    "allowed": true,
    "risk_level": "medium",
    "requires_confirmation": true
}
```

---

## Audit Trail

### WHY Journal

Every action is logged with:

```json
{
  "id": "why_abc123",
  "timestamp": "2025-01-20T10:30:00Z",
  "action": "open_application",
  "parameters": {
    "application": "Safari"
  },
  "reason": "User requested via voice command",
  "context": {
    "user": "default",
    "session_id": "sess_xyz789"
  },
  "policy_decision": {
    "allowed": true,
    "risk_level": "low",
    "rules_evaluated": ["safe_actions"]
  },
  "outcome": {
    "success": true,
    "execution_time": 0.5
  }
}
```

### Audit Log Analysis

```bash
# Search for failed actions
poetry run python -c "
from neura.core.why_journal import WHYJournal
journal = WHYJournal()
failed = journal.search(outcome='failure')
for entry in failed:
    print(f'{entry.timestamp}: {entry.action} - {entry.reason}')
"

# Export audit log
poetry run python -c "
from neura.core.why_journal import WHYJournal
journal = WHYJournal()
journal.export('audit_log.json', start_date='2025-01-01')
"
```

### Tamper Detection

```python
# Each entry has a checksum
entry_hash = sha256(
    entry.id +
    entry.timestamp +
    entry.action +
    entry.outcome
).hexdigest()

# Verify integrity
def verify_journal_integrity():
    for entry in journal.all():
        computed_hash = compute_hash(entry)
        if computed_hash != entry.hash:
            raise TamperDetected(entry.id)
```

---

## Best Practices

### 1. Master Password

✅ **Do**:
- Use a password manager
- Use 20+ character passphrase
- Enable biometric unlock (future)
- Change periodically (every 90 days)

❌ **Don't**:
- Reuse passwords
- Share password
- Write down password
- Use personal information

### 2. Vault Usage

✅ **Do**:
```python
# Store API keys in vault
vault.store(
    key="github_token",
    value="ghp_abc123",
    tags=["api", "github"]
)

# Retrieve when needed
token = vault.retrieve("github_token")
```

❌ **Don't**:
```python
# Hardcode secrets
GITHUB_TOKEN = "ghp_abc123"  # ❌ BAD

# Store in plaintext files
with open("secrets.txt", "w") as f:
    f.write("github_token=ghp_abc123")  # ❌ BAD
```

### 3. File Permissions

```bash
# Secure NEURA directory
chmod 700 ~/.neura
chmod 600 ~/.neura/data/*.db
chmod 600 ~/.neura/config/*.json

# Verify permissions
ls -la ~/.neura/data/
# Should show: -rw------- (600)
```

### 4. Network Security

```bash
# Firewall: Block external access to NEURA API
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /path/to/neura
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --block /path/to/neura

# Only allow localhost
# In config: bind_address = "127.0.0.1"
```

### 5. Backup Security

```bash
# Encrypt backups
tar czf - ~/.neura/data | \
  openssl enc -aes-256-cbc -pbkdf2 -out neura_backup.tar.gz.enc

# Decrypt backup
openssl enc -d -aes-256-cbc -pbkdf2 -in neura_backup.tar.gz.enc | \
  tar xzf -
```

### 6. Secure Deletion

```python
# Use secure deletion for sensitive files
from neura.vault.crypto import secure_delete

secure_delete("/path/to/sensitive_file")
# Overwrites with random data before deletion
```

### 7. Update Regularly

```bash
# Check for updates
cd NeuraOS
git pull origin main

# Update dependencies
poetry update

# Review changelog
cat CHANGELOG.md
```

---

## Security Checklist

### Initial Setup

- [ ] Set strong master password (20+ chars)
- [ ] Enable FileVault (macOS disk encryption)
- [ ] Configure firewall
- [ ] Review default policies
- [ ] Test backup/restore

### Regular Maintenance

- [ ] Review audit logs weekly
- [ ] Update NEURA monthly
- [ ] Rotate master password quarterly
- [ ] Backup data weekly
- [ ] Check file permissions monthly

### Before Sharing Device

- [ ] Lock NEURA session
- [ ] Clear sensitive memories
- [ ] Review recent actions
- [ ] Lock screen

### Incident Response

- [ ] Change master password immediately
- [ ] Review audit logs for suspicious activity
- [ ] Export data for forensics
- [ ] Revoke API keys (if applicable)
- [ ] Report to security@neura.dev

---

## Incident Response

### Suspected Breach

1. **Isolate**
   ```bash
   # Stop NEURA
   pkill -f neura
   
   # Disconnect network
   sudo ifconfig en0 down
   ```

2. **Assess**
   ```bash
   # Check audit log
   tail -n 100 ~/.neura/logs/why.jsonl
   
   # Check for unauthorized access
   grep "outcome.*failure" ~/.neura/logs/why.jsonl
   ```

3. **Contain**
   ```bash
   # Change master password
   poetry run neura vault change-password
   
   # Revoke API keys
   poetry run neura auth revoke-all
   ```

4. **Recover**
   ```bash
   # Restore from backup
   cp -r ~/backups/neura_clean ~/.neura
   
   # Verify integrity
   poetry run neura verify
   ```

5. **Report**
   ```bash
   # Export incident data
   poetry run neura export-incident-report
   
   # Email to security@neura.dev
   ```

### Data Loss

1. **Stop writes**
   ```bash
   pkill -f neura
   ```

2. **Restore from backup**
   ```bash
   cp -r ~/backups/neura_latest ~/.neura
   ```

3. **Verify integrity**
   ```bash
   poetry run neura verify
   ```

### Forgotten Master Password

⚠️ **There is NO password recovery**

If you forget your master password:
- Vault data is **permanently inaccessible**
- Must create new vault
- Lose all encrypted secrets

**Prevention**: Use a password manager!

---

## Security Reporting

### Responsible Disclosure

Found a security vulnerability?

1. **DO NOT** open a public issue
2. Email: security@neura.dev
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (optional)

### Response Timeline

- **24 hours**: Initial response
- **7 days**: Vulnerability assessment
- **30 days**: Patch development
- **90 days**: Public disclosure (coordinated)

### Bug Bounty

Coming soon! We'll reward security researchers who help improve NEURA's security.

---

## Compliance

### GDPR

NEURA is GDPR-compliant:
- ✅ Data minimization (local-only)
- ✅ Right to access (export data)
- ✅ Right to erasure (delete data)
- ✅ Data portability (JSON export)
- ✅ Privacy by design

### HIPAA

For healthcare use:
- ✅ Encryption at rest
- ✅ Audit trail
- ✅ Access controls
- ⚠️ Requires additional configuration

### SOC 2

For enterprise use:
- ✅ Security controls
- ✅ Availability
- ✅ Confidentiality
- ⚠️ Requires audit (coming in v1.0)

---

## Security Roadmap

### v0.2
- [ ] Biometric unlock (Touch ID)
- [ ] Hardware key support (YubiKey)
- [ ] Encrypted backups
- [ ] Security dashboard

### v0.3
- [ ] Multi-factor authentication
- [ ] Role-based access control
- [ ] Security audit logs
- [ ] Intrusion detection

### v1.0
- [ ] SOC 2 compliance
- [ ] Penetration testing
- [ ] Security certifications
- [ ] Bug bounty program

---

**Questions?** Email security@neura.dev or open a discussion on GitHub.

**Remember**: Security is a shared responsibility. Stay vigilant! 🔒
