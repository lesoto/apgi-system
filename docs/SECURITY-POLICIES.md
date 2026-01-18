# Security Policies

## Secrets Rotation Policy

### Overview
This document outlines the secrets rotation policy for the APGI System to maintain security best practices and minimize the impact of potential credential leaks.

### Secrets Requiring Rotation

#### 1. JWT Secret Keys
- **Rotation Frequency**: Every 90 days
- **Purpose**: Used for signing and verifying JWT authentication tokens
- **Impact**: Requires all users to re-authenticate after rotation
- **Procedure**:
  1. Generate new 32+ character random secret
  2. Update `JWT_SECRET_KEY` environment variable
  3. Deploy new secret to all environments
  4. Monitor for authentication issues
  5. Old tokens will expire naturally (30-minute access tokens)

#### 2. Database Credentials
- **Rotation Frequency**: Every 180 days
- **Purpose**: PostgreSQL database access
- **Impact**: Requires database connection restart
- **Procedure**:
  1. Generate new strong password (32+ characters)
  2. Update `DATABASE_URL` environment variable
  3. Update database user password in PostgreSQL
  4. Restart application services
  5. Verify database connectivity

#### 3. Redis Credentials
- **Rotation Frequency**: Every 180 days
- **Purpose**: Redis cache and session storage access
- **Impact**: Session data may be temporarily unavailable
- **Procedure**:
  1. Generate new Redis password
  2. Update `REDIS_URL` environment variable
  3. Update Redis configuration
  4. Restart Redis service
  5. Restart application services

#### 4. API Keys
- **Rotation Frequency**: Every 90 days
- **Purpose**: External API integrations
- **Impact**: External integrations will need updated keys
- **Procedure**:
  1. Generate new API keys
  2. Update external service configurations
  3. Update environment variables
  4. Test all integrations
  5. Revoke old API keys

#### 5. Webhook URLs and Secrets
- **Rotation Frequency**: Every 180 days
- **Purpose**: Alerting and notification webhooks
- **Impact**: Webhook notifications may fail during transition
- **Procedure**:
  1. Generate new webhook secrets
  2. Update webhook providers
  3. Update environment variables
  4. Test webhook delivery
  5. Remove old webhook configurations

### Rotation Process

#### Pre-Rotation Checklist
- [ ] Schedule maintenance window during low-traffic period
- [ ] Notify stakeholders of upcoming rotation
- [ ] Create backup of current secrets
- [ ] Prepare rollback plan
- [ ] Ensure all environments are updated consistently

#### Rotation Steps
1. Generate new secrets using cryptographically secure random generator
2. Update secrets in all environments (development, staging, production)
3. Update documentation and configuration files
4. Deploy changes to production
5. Monitor application logs and metrics
6. Verify all services are functioning correctly
7. Revoke old secrets (after 24-hour grace period)

#### Post-Rotation Verification
- [ ] Verify all services are running
- [ ] Check authentication is working
- [ ] Test database connectivity
- [ ] Verify Redis operations
- [ ] Test external API integrations
- [ ] Confirm webhook delivery
- [ ] Review application logs for errors

### Emergency Rotation

If a secret is suspected to be compromised:
1. **Immediate Action**: Rotate the compromised secret immediately
2. **Scope**: Rotate all related secrets (e.g., if DB password leaked, rotate all DB credentials)
3. **Investigation**: Determine scope and impact of the breach
4. **Notification**: Notify security team and stakeholders
5. **Audit**: Review logs for unauthorized access
6. **Remediation**: Implement additional security measures

### Automation

#### Automated Rotation
- Implement automated rotation for non-critical secrets
- Use secret management tools (e.g., HashiCorp Vault, AWS Secrets Manager)
- Schedule automated rotation during maintenance windows
- Integrate with CI/CD pipeline for seamless updates

#### Rotation Monitoring
- Track secret age and rotation schedule
- Set alerts for upcoming rotation deadlines
- Monitor for failed rotation attempts
- Log all rotation activities

### Compliance

This policy aligns with:
- NIST SP 800-53 Rev. 5 (IA-5: Authenticator Management)
- CIS Controls 8.3 (Encrypt Sensitive Data in Transit)
- OWASP ASVS 2.8.1 (Verify that secrets are rotated)

### References

- [NIST SP 800-53](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [CIS Controls](https://www.cisecurity.org/controls/cis-controls-list)

---

## API Key Rotation Mechanism

### Overview
API keys are used for external service integrations and must be rotated regularly to maintain security.

### Rotation Procedure

#### 1. Key Generation
```bash
# Generate new API key (32+ characters)
openssl rand -base64 32
```

#### 2. Update Process
1. Generate new API key
2. Update external service configuration with new key
3. Update environment variable in all environments
4. Deploy changes
5. Test integration
6. Revoke old key after 24 hours

#### 3. Testing
```bash
# Test API key validity
curl -H "Authorization: Bearer <NEW_API_KEY>" https://api.example.com/health
```

### Key Storage
- Store API keys in environment variables
- Never commit API keys to version control
- Use secret management tools for production
- Rotate keys every 90 days

### Key Types

#### Internal API Keys
- Used for service-to-service communication
- Rotate every 90 days
- Store in Kubernetes secrets

#### External API Keys
- Used for third-party integrations
- Rotate according to provider requirements
- Store in environment variables

#### Webhook Secrets
- Used for webhook signature verification
- Rotate every 180 days
- Store in environment variables

### Monitoring
- Monitor API key usage patterns
- Alert on unusual activity
- Track key expiration dates
- Log all key rotations

---

## Response Caching Strategy

### Overview
Response caching improves API performance and reduces load on backend services.

### Cache Configuration

#### Redis Caching
- **Cache Store**: Redis
- **Default TTL**: 300 seconds (5 minutes)
- **Max Memory**: 1GB
- **Eviction Policy**: LRU (Least Recently Used)

#### Cacheable Endpoints
- GET requests with idempotent operations
- Static reference data
- Aggregated statistics
- Health check responses

#### Non-Cacheable Endpoints
- POST, PUT, DELETE, PATCH requests
- Authentication endpoints
- User-specific data with privacy concerns
- Real-time data

### Cache Key Strategy

#### Key Format
```
{endpoint}:{method}:{params_hash}:{user_id}
```

#### Example
```
/v1/sessions:GET:abc123:user_456
```

### Cache Invalidation

#### Manual Invalidation
```python
# Invalidate specific cache key
await redis_client.delete(f"v1:sessions:GET:{session_id}")

# Invalidate pattern
await redis_client.delete("v1:sessions:*")
```

#### Automatic Invalidation
- Time-based expiration (TTL)
- Event-based invalidation (data updates)
- Version-based invalidation

### Cache Headers
```
Cache-Control: public, max-age=300
ETag: "abc123def456"
Last-Modified: Wed, 21 Oct 2025 07:28:00 GMT
```

### Monitoring
- Cache hit rate (target: >80%)
- Cache miss rate (target: <20%)
- Average response time
- Memory usage

---

## Database Query Optimization

### Overview
Optimizing database queries ensures efficient data retrieval and maintains application performance.

### Indexing Strategy

#### Primary Indexes
- All foreign keys
- Frequently queried columns
- Unique constraints
- Primary keys

#### Composite Indexes
```sql
-- Example: Sessions table
CREATE INDEX idx_sessions_user_created 
ON sessions(user_id, created_at DESC);

-- Example: Tasks table
CREATE INDEX idx_tasks_status_priority 
ON tasks(status, priority DESC);
```

#### Index Maintenance
```sql
-- Analyze index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Rebuild indexes
REINDEX TABLE sessions;
REINDEX INDEX idx_sessions_user_created;
```

### Query Optimization

#### Use Prepared Statements
```python
# Good
await conn.execute(
    "SELECT * FROM sessions WHERE user_id = $1 AND status = $2",
    user_id, status
)

# Bad (SQL injection risk)
await conn.execute(
    f"SELECT * FROM sessions WHERE user_id = {user_id} AND status = '{status}'"
)
```

#### Select Only Required Columns
```python
# Good
await conn.fetchval(
    "SELECT COUNT(*) FROM sessions WHERE user_id = $1",
    user_id
)

# Bad (fetches all columns)
await conn.fetch(
    "SELECT * FROM sessions WHERE user_id = $1",
    user_id
)
```

#### Use JOINs Efficiently
```sql
-- Good: Use JOIN with indexed columns
SELECT s.*, u.username 
FROM sessions s
JOIN users u ON s.user_id = u.id
WHERE s.status = 'active';

-- Bad: Subquery without index
SELECT s.*, (SELECT username FROM users WHERE id = s.user_id)
FROM sessions s
WHERE s.status = 'active';
```

### Query Result Caching

#### Redis Caching
```python
# Cache query results
cache_key = f"query:sessions:{user_id}:{status}"
cached = await redis_client.get(cache_key)

if cached:
    return json.loads(cached)

results = await conn.fetch(
    "SELECT * FROM sessions WHERE user_id = $1 AND status = $2",
    user_id, status
)

await redis_client.setex(
    cache_key, 
    300, 
    json.dumps(results)
)
```

### Connection Pooling
- **Pool Size**: 20 connections
- **Max Overflow**: 10 connections
- **Pool Timeout**: 30 seconds
- **Pool Recycle**: 3600 seconds (1 hour)

### Monitoring

#### Query Performance
```sql
-- Slow query log
SELECT query, mean_exec_time, calls, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Table statistics
SELECT schemaname, tablename, seq_scan, idx_scan, n_tup_ins, n_tup_upd, n_tup_del
FROM pg_stat_user_tables
ORDER BY seq_scan DESC;
```

#### Performance Metrics
- Average query time (target: <100ms)
- Slow query count (target: <1%)
- Connection pool utilization (target: <80%)
- Index hit ratio (target: >99%)

### Best Practices

1. **Use EXPLAIN ANALYZE** for complex queries
2. **Avoid SELECT *** in production
3. **Use LIMIT** for large result sets
4. **Implement pagination** for list endpoints
5. **Use transactions** for multi-step operations
6. **Regularly vacuum and analyze** tables
7. **Monitor query performance** continuously
8. **Optimize hot paths** first

### Maintenance

#### Regular Tasks
```sql
-- Vacuum analyze tables
VACUUM ANALYZE sessions;
VACUUM ANALYZE users;

-- Update statistics
ANALYZE sessions;
ANALYZE users;

-- Reindex fragmented tables
REINDEX TABLE sessions;
```

#### Automated Maintenance
```yaml
# Kubernetes CronJob
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-maintenance
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: maintenance
            image: postgres:14
            command:
            - psql
            - -c
            - VACUUM ANALYZE;
```
