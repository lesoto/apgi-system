# ADR 0001: Configuration Strict Mode for Security

## Status
Accepted

## Context
The APGI Framework had insecure defaults in configuration management:
- Default API key fallbacks that could be used in production
- No validation to fail startup when secrets were missing
- Placeholder secret keys in `.env.example` could accidentally be deployed

## Decision
Implement environment-aware strict mode configuration that:
1. Adds `strict_mode` field to `APGIConfig`
2. Introduces `APGI_STRICT_MODE` environment variable
3. Detects placeholder/placeholder-like secret key patterns
4. Raises `ConfigurationError` on validation failures in strict mode
5. Auto-generates development secrets only in non-strict mode

## Consequences
### Positive
- Prevents deployment with placeholder secrets in production
- Fails fast when critical configuration is missing
- Clear error messages guide developers to fix configuration issues
- Maintains developer convenience in non-strict mode

### Negative
- Requires explicit configuration in strict mode (less convenient for local development)
- May break existing workflows that rely on auto-generated secrets
- Requires documentation update for deployment procedures

### Alternatives Considered
1. **Remove all auto-generation**: Too restrictive for development
2. **Environment-based strict mode only**: Chosen as it provides flexibility
3. **Separate configuration validation tool**: More complex, inline validation preferred

## References
- Files modified: `apgi_framework/config/manager.py`, `.env.example`
- Related: TODO item #1 (Eliminate insecure defaults)
