# APGI Incident Response Runbooks

## Overview

This document provides standardized incident response procedures for the APGI Framework. Each runbook contains:

- Detection criteria
- Immediate response steps
- Escalation procedures
- Recovery steps
- Post-incident actions

---

## Incident Severity Levels

|Level|Description|Response Time|Examples
|---|---|---|---
|**P1 (Critical)**|Service down, data breach, security compromise|15 minutes|Unauthorized data access, system compromise, complete service outage
|**P2 (High)**|Major functionality impaired, potential data loss|1 hour|Authentication failures, experiment data corruption, performance degradation
|**P3 (Medium)**|Partial service impact, workarounds available|4 hours|Non-critical feature failures, UI issues, minor data inconsistencies
|**P4 (Low)**|Minimal impact, cosmetic issues|24 hours|Documentation errors, minor UI bugs, logging gaps

---

## Runbook 1: Data Breach / Unauthorized Access

**Severity:** P1 (Critical)  
**Trigger:** Security alert, anomaly detection, user report

### Detection (Data Breach)

- Security monitoring alerts on unauthorized access patterns
- Unusual data export volumes
- Failed authentication spikes followed by successful access
- Correlation ID traces showing anomalous request patterns

### Immediate Response (First 15 minutes) - Data Breach

1. **Alert the Security Team**

   ```python
   # Use standardized logging to capture incident start
   from apgi_framework.logging.standardized_logging import get_security_logger
   security_logger = get_security_logger()
   security_logger.critical("Potential data breach detected", 
                          incident_type="data_breach",
                          correlation_id="<incident_cid>")
   ```

2. **Preserve Evidence**
   - Do NOT restart services yet
   - Capture current process state: `ps aux > /tmp/process_snapshot_$(date +%s).txt`
   - Save logs: `cp -r logs/ /tmp/evidence_logs_$(date +%s)/`
   - Record active connections: `netstat -tuln > /tmp/connections_$(date +%s).txt`

3. **Isolate Affected Systems**
   - Enable maintenance mode if available
   - Block suspicious IP addresses at firewall level
   - Revoke potentially compromised tokens (see Runbook 4)

### Investigation Steps - Data Breach

1. **Identify Scope**

   ```sql
   -- Query audit logs for affected data
   SELECT * FROM audit_log 
   WHERE timestamp > NOW() - INTERVAL '1 hour'
   AND correlation_id IN (SELECT cid FROM suspicious_activity)
   ORDER BY timestamp;
   ```

2. **Trace Attacker Movement**
   - Follow correlation IDs through log chain
   - Check for lateral movement indicators
   - Review authentication logs for compromised credentials

3. **Determine Data Exposure**
   - List potentially accessed experiment data
   - Check for PHI/PII exposure
   - Document affected user accounts

### Recovery

1. **Containment**
   - Rotate all potentially exposed credentials
   - Revoke all active sessions
   - Patch identified vulnerabilities

2. **Service Restoration**
   - Restart services in clean state
   - Verify security controls are active
   - Gradually restore traffic

3. **Verification**
   - Run security validation: `python -m apgi_framework.security.security_validator`
   - Check data integrity
   - Verify access controls

### Post-Incident

1. **Notification Requirements**
   - Internal: Within 24 hours to stakeholders
   - External: Per data breach notification laws (72 hours for GDPR)
   - Regulatory: File required reports

2. **Documentation**
   - Complete incident timeline
   - Document all actions taken
   - Update threat model if new attack vector discovered

---

## Runbook 2: Experiment Data Corruption

**Severity:** P1-P2 (Critical to High)  
**Trigger:** Data validation failures, checksum mismatches, user reports

### Detection (Data Corruption)

- Automated data integrity checks fail

- Users report inconsistent results
- Checksum verification failures in logs
- Database constraint violations

### Immediate Response - Data Corruption

1. **Stop Data Modifications**

   ```python
   # Enable read-only mode
   from apgi_framework.data.persistence_layer import PersistenceLayer
   PersistenceLayer.enable_read_only_mode()
   ```

2. **Assess Corruption Scope**

   ```bash
   # Run data integrity check
   python -m apgi_framework.data.integrity_checker --full-scan
   ```

3. **Notify Stakeholders**
   - Alert research teams using affected data
   - Post status update
   - Establish communication channel

### Investigation - Data Corruption

1. **Identify Corrupted Records**

   ```python
   from apgi_framework.data.data_manager import DataManager
   dm = DataManager()
   corrupted = dm.identify_corrupted_records()
   print(f"Found {len(corrupted)} corrupted records")
   ```

2. **Determine Root Cause**
   - Check for:
     - Storage hardware failures
     - Concurrent write conflicts
     - Software bugs in recent deployments
     - Incomplete transactions

3. **Assess Impact**
   - Count affected experiments
   - Identify users impacted
   - Determine data recovery point objective (RPO)

### Recovery - Data Corruption

1. **Restore from Backup**

   ```python
   from apgi_framework.utils.backup_manager import BackupManager
   bm = BackupManager()
   
   # List available backups
   backups = bm.list_backups()
   
   # Restore to last known good state
   bm.restore_backup(backups[-1], verify=True)
   ```

2. **Repair If Possible**
   - For minor corruption: Use data repair tools
   - For major corruption: Full restore + replay transactions

3. **Verify Integrity**

   ```bash
   python -m apgi_framework.data.integrity_checker --verify-all
   ```

### Post-Incident - Data Corruption

1. **Data Validation**
   - Re-run all experiments that used corrupted data
   - Notify affected publications/papers
   - Update data quality metrics

2. **Prevention**
   - Review backup frequency
   - Implement additional checksums
   - Add real-time integrity monitoring

---

## Runbook 3: Performance Degradation / Service Outage

**Severity:** P1-P2 (Critical to High)  
**Trigger:** Monitoring alerts, user reports, automated health checks failing

### Detection (Performance Degradation)

- Response time > 5 seconds (normal < 1s)

- Error rate > 1% (normal < 0.1%)
- CPU/memory thresholds exceeded
- Health check endpoints failing

### Immediate Response - Performance Degradation

1. **Assess Impact**

   ```bash
   # Check system health
   curl http://localhost:8080/health
   
   # Review resource usage
   top -bn1 | head -20
   df -h
   ```

2. **Enable Circuit Breakers**

   ```python
   from apgi_framework.core.circuit_breaker import CircuitBreaker
   CircuitBreaker.enable_all()
   ```

3. **Scale Resources (if applicable)**

   ```bash
   # Kubernetes deployment
   kubectl scale deployment apgi-app --replicas=5
   ```

### Investigation - Performance Degradation

1. **Identify Bottleneck**
   - Review performance dashboards
   - Check database query times
   - Analyze slow request traces (use correlation IDs)
   - Review recent deployments

2. **Check Logs**

   ```bash
   # Find error spikes
   grep "ERROR" logs/application.log | grep -o "correlation_id=[^ ]*" | sort | uniq -c | sort -rn | head -10
   ```

3. **Database Health**

   ```sql
   -- Check for long-running queries
   SELECT pid, query, now() - query_start AS duration
   FROM pg_stat_activity
   WHERE state = 'active' AND now() - query_start > interval '30 seconds';
   ```

### Recovery - Performance Degradation

1. **Immediate Mitigation**
   - Restart affected services
   - Clear caches if corrupted
   - Disable non-critical features

2. **Root Cause Fix**
   - Deploy hotfix if software issue
   - Scale resources if capacity issue
   - Restart database if connection pool exhausted

3. **Verify Recovery**

   ```bash
   # Run load test
   python -m pytest benchmarks/test_performance.py -v
   ```

---

## Runbook 4: Authentication/Authorization Failure

**Severity:** P1-P2 (Critical to High)  
**Trigger:** Login failures, authorization errors, token validation issues

### Detection (Authentication Failure)

- Authentication success rate drops

- Token validation failures spike
- Users report login issues
- Security audit alerts

### Immediate Response - Authentication Failure

1. **Check Auth Service Status**

   ```python
   from apgi_framework.security.authentication import JWTAuthManager
   auth = JWTAuthManager()
   # Verify token generation works
   test_token = auth.generate_token_pair("test_user", Role.VIEWER)
   ```

2. **Preserve Security Logs**

   ```bash
   cp logs/security.log /tmp/security_evidence_$(date +%s).log
   ```

3. **Enable Fail-Safe Mode**
   - Enable emergency admin access
   - Consider manual authentication verification

### Investigation - Authentication Failure

1. **Check Token Status**

   ```python
   # Check for token blacklisting issues
   from apgi_framework.security.authentication import JWTAuthManager
   auth = JWTAuthManager()
   
   # Verify token hasn't been revoked
   # (Check if hash is in blacklist)
   ```

2. **Review Recent Changes**
   - Check for recent secret rotations
   - Verify JWT algorithm consistency
   - Review role/permission changes

3. **Check External Auth (if using OAuth2)**

   ```python
   from apgi_framework.security.authentication import OAuth2Client
   # Verify OAuth2 provider status
   ```

### Recovery - Authentication Failure

1. **Rotate Secrets (if compromised)**

   ```python
   # Generate new signing key
   import secrets
   new_key = secrets.token_urlsafe(32)
   # Update configuration and restart
   ```

2. **Clear Token Blacklist (if corrupted)**

   ```python
   # Emergency: Clear and re-establish valid sessions
   auth._token_blacklist.clear()
   # Force all users to re-authenticate
   ```

3. **Verify Fix**
   - Test all authentication flows
   - Verify RBAC permissions work
   - Check audit logging

---

## Runbook 5: Dependency/Supply Chain Compromise

**Severity:** P1 (Critical)  
**Trigger:** Vulnerability scan alerts, suspicious package behavior

### Detection (Supply Chain Compromise)

- Automated vulnerability scan finds critical CVE
- Unexpected network connections from dependencies
- Unusual file system access patterns
- Dependency hash mismatches

### Immediate Response - Supply Chain Compromise

1. **Isolate Affected Systems**

   ```bash
   # Block outbound connections except essential
   iptables -A OUTPUT -p tcp --dport 443 -d pypi.org -j ACCEPT
   iptables -A OUTPUT -p tcp --dport 443 -j DROP
   ```

2. **Capture Evidence**

   ```bash
   # Document current dependencies
   pip freeze > /tmp/dependencies_$(date +%s).txt
   pip check > /tmp/dependency_conflicts_$(date +%s).txt
   ```

3. **Stop Deployments**
   - Halt CI/CD pipeline
   - Block new container builds
   - Quarantine affected artifacts

### Investigation - Supply Chain Compromise

1. **Identify Compromised Packages**

   ```bash
   # Check for suspicious packages
   pip list | grep -i -E "(test|demo|example)"
   # Verify package signatures if available
   ```

2. **Review Supply Chain**
   - Check package repository status
   - Verify package hashes against lock file
   - Review recent package updates

3. **Check for Indicators of Compromise**
   - Unusual imports in codebase
   - Network connections from Python processes
   - File modifications outside application scope

### Recovery - Supply Chain Compromise

1. **Clean Environment**

   ```bash
   # Create fresh virtual environment
   rm -rf venv/
   python -m venv venv
   source venv/bin/activate
   
   # Install from verified lock file
   pip install -r requirements.lock --require-hashes
   ```

2. **Verify Packages**

   ```bash
   # Run security scan
   pip-audit --desc --format=json
   safety check
   ```

3. **Restore Services**
   - Deploy from clean environment
   - Monitor for anomalous behavior
   - Verify functionality

---

## Escalation Procedures

### Escalation Matrix

| Time | Action | Notify
| ---- | ------ | -----
| 0 min | Initial response | On-call engineer
| 15 min | P1 not resolved | Engineering Manager + Security
| 30 min | P1 not resolved | VP Engineering + Legal (if data breach)
| 1 hour | P2 not resolved | Engineering Manager
| 4 hours | Any incident unresolved | Full incident response team

### Communication Templates

#### Slack/Teams Alert (P1)

```text
🚨 P1 INCIDENT: [Brief description]
- Service: [Affected component]
- Impact: [User/data impact]
- Started: [Timestamp]
- Channel: #incident-[id]
- Lead: [Engineer name]
```

#### Status Page Update

```text
[Investigating] APGI [Service] - [Brief issue description]
We are currently investigating issues with [service]. 
We will provide updates every 30 minutes.
Posted: [Time] UTC
```

---

## Post-Incident Review Template

### Metadata

- **Incident ID**: INC-YYYY-MM-DD-NNN
- **Severity**: P1/P2/P3/P4
- **Duration**: [Start] to [Resolved]
- **Downtime**: [Duration or N/A]
- **Lead**: [Name]
- **Team**: [Names]

### Timeline

| Time  | Event     | Action Taken
|-------|-----------|-------------
| 09:00 | Detection | Alert fired
| 09:05 | Response  | Engineer paged
| ...   | ...       | ...

### Root Cause

[Detailed technical explanation]

### Impact Assessment

- **Users Affected**: [Count]
- **Data Affected**: [Description]
- **Experiments Disrupted**: [Count]
- **Financial Impact**: [If applicable]

### Lessons Learned

1. [What went well]
2. [What could improve]
3. [Process gaps identified]

### Action Items

| Item          | Owner       | Due Date  | Priority
|---------------|-------------|-----------|----------
| [Description] | [Name]      | [Date]    | P1/P2

---

## Tools and Resources

### Diagnostic Commands

```bash
# System status
systemctl status apgi-*
docker ps | grep apgi
kubectl get pods -l app=apgi

# Logs
tail -f logs/application.log | grep -E "ERROR|CRITICAL"
journalctl -u apgi-service -f

# Database
psql -c "SELECT count(*) FROM experiments WHERE status='running';"

# Security
python -m apgi_framework.security.security_validator
```

### Key Contacts

- Security Team: <security@apgi.local>
- On-Call Engineer: <oncall@apgi.local>
- Engineering Manager: <eng-manager@apgi.local>
- Legal/Compliance: <legal@apgi.local> (for data incidents)

### External Resources

- Status Page: <status.apgi.local>
- Documentation: <docs.apgi.local>
- Security Playbook: [Link]

---

*Last Updated: 2024*  
*Review Cycle: Quarterly*  
*Next Review: [Date]*
