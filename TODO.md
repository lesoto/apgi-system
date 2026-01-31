# TODO

## Bugs

## Issues

### Code Quality
- Mixed error handling approaches across GUIs
- Memory usage can grow unbounded in long sessions without manual reset

### User Experience
- Theme support only in Assistant-GUI, not in other GUIs (apgi_gui.py, Psychological-States-GUI.py, Utils-GUI.py)
- No accessibility features documented (screen reader support, keyboard navigation, high-contrast mode, font scaling)
- Tooltips only implemented in Assistant-GUI
- Event log font sizes differ across GUIs
- No unified design system documented
- Mixed visualization libraries (Matplotlib vs Plotly)

### Performance & Scalability
- No documented performance benchmarks or SLAs
- Missing load testing results
- GUI performance under heavy load not tested
- 3D state space visualization may lag with large datasets
- No CDN configuration for static assets
- Database query optimization not documented
- No caching strategy documented

### Testing Coverage
- Limited GUI component testing (only 1 test file for 4 GUI applications)
- No dedicated tests for `/apgi_system/neural/` modules
- Limited concurrency testing for session management
- No tests for 1000+ timestep scenarios
- Limited platform-specific testing

### Infrastructure & Reliability
- No global error recovery strategies documented
- Missing automated error reporting/alerting integration (beyond webhook URLs)
- No documented disaster recovery procedures
- Circuit breaker pattern not fully implemented across all services
- Missing graceful degradation strategies for partial system failures

- Automated dependency updates
- Accessibility features (screen reader, keyboard navigation)
- Unified design system or style guide
- Theme support extension to all GUIs

- GUI Components - Only 1 test file for 4 GUI applications
- Neural Network Modules - No dedicated tests for `/apgi_system/neural/`
- Concurrent Session Management - Limited concurrency testing
- Large-Scale Simulations - No tests for 1000+ timestep scenarios
- Cross-Platform Deployment - Limited platform-specific testing

## Missing Features

| ID | Bug Description | Location | Status | Expected vs Actual |
|----|-----------------|----------|--------|-------------------|
| M-001 | **Theme Inconsistency Across GUIs** | Multiple GUI files | ⏳ Pending | Expected: Consistent themes. Actual: Only Assistant-GUI has theme support |
| MF-002 | **Accessibility Features** | No screen reader, keyboard nav, high contrast | Limits user accessibility |
| MF-003 | **Unified Theme System** | Theme support only in one GUI | Poor UX consistency |
| MF-005 | **Performance Benchmarks/SLAs** | No documented performance targets | Cannot validate performance |