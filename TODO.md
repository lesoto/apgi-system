# TODO

## Bugs

| Bug | Component | Location | Reproduction Steps | Expected vs Actual |
|-----|-----------|-----------|-------------------|-------------------|
| GUI Initialization Failure | GUI | `apgi_gui.py:99-178` | Launch `python apgi_gui.py` | Expected: GUI starts; Actual: RuntimeError about tkinter variables |
| API Structured Logging Error | API | `api/database/connection.py:109` | Start API server | Expected: Clean startup; Actual: TypeError with logger kwargs |
| Negative Duration Acceptance | Core System | `APGISystem.run()` | Call with negative duration_ms | Expected: Validation error; Actual: Accepts negative value |
| Auto-save Menu Item Error | GUI | `apgi_gui.py:211-216` | Start GUI and check File menu | Expected: Auto-save checkbox; Actual: Index error |
| Progress Bar Warnings | GUI | Multiple locations | Close GUI while running | Expected: Clean shutdown; Actual: Tkinter warnings |
| API Port Conflict | API | `api/main.py` | Start API server | Expected: Server starts; Actual: Address already in use |
| Memory Growth | Core System | Long simulations | Run extended simulations | Expected: Stable memory; Actual: Potential memory leaks |
| Deprecation Warnings | API | `api/main.py:142,202` | Start API server | Expected: No warnings; Actual: FastAPI deprecation warnings |
| GUI Performance | GUI | Real-time updates | Use GUI with many plots | Expected: Smooth updates; Actual: 10Hz refresh feels sluggish |

## Issues

- **Negative Duration:** System accepts negative simulation duration (should validate)
- **API Logging:** Structured logger incompatibility with standard logging
- **GUI Crashes:** Unhandled tkinter variable errors
- **Database Errors:** Limited error handling in database operations
- **Graceful Degradation:** Limited fallback mechanisms
- **Recovery Procedures:** No automatic recovery from errors
- **User Feedback:** Error messages could be more user-friendly
- **Simulation Speed:** 115 steps/sec is slow for real-time applications
- **Memory Growth:** Potential memory leaks in long-running sessions
- **GUI Updates:** 10Hz refresh rate may feel sluggish
- **API Port Conflicts:** Default port already in use
- **Deprecation Warnings:** FastAPI deprecation warnings for event handlers
- **Logging Inconsistency:** Mixed use of structured and standard logging
- **Error Recovery:** Limited error recovery mechanisms
- **Performance:** Suboptimal simulation performance
- **⚠️ Areas for Improvement:** GUI initialization issues, API logging problems, performance optimization needs
- **🔧 Critical Issues:** Tkinter variable initialization bugs, structured logging inconsistencies
- **GUI Initialization Bug:** Critical tkinter variable initialization failure
  - **Severity:** Critical
  - **Location:** `apgi_gui.py` lines 99-178
  - **Issue:** Tkinter variables created before root window ready
  - **Status:** Partially fixed with workarounds
  - **Impact:** Prevents GUI startup on some systems
- **Auto-save Menu Item:** Checkbutton addition fails with index error
- **Progress Bar Errors:** Tkinter progress bar warnings during shutdown
- **Memory Usage:** GUI consumes ~117MB memory

## Missing Features

- Additional cognitive tasks mentioned in TODO (Stroop, N-back)
- Clinical pathology models
- Cross-species comparative models
- Advanced analytics dashboard
- Voice input/output capabilities
- Screen reader compatibility
1. **Additional Cognitive Tasks**
   - Stroop Task (cognitive interference)
   - N-back Task (working memory)
   - **Impact:** Limits research capabilities
   - **Effort:** Medium (framework exists)
2. **Clinical Pathology Models**
   - Depression models
   - Anxiety disorders
   - Schizophrenia simulations
   - **Impact:** Limits clinical applications
   - **Effort:** High (requires research)
3. **Performance Optimization**
   - GPU acceleration for simulations
   - Vectorized operations
   - **Impact:** Affects usability
   - **Effort:** Medium-High
4. **Advanced Analytics Dashboard**
   - Real-time performance metrics
   - Statistical analysis tools
   - **Impact:** Limits research insights
   - **Effort:** Medium
5. **Voice Input/Output**
   - Speech-to-text for queries
   - Text-to-speech for responses
   - **Impact:** Accessibility limitation
   - **Effort:** Medium
6. **Screen Reader Compatibility**
   - ARIA labels
   - Keyboard navigation
   - **Impact:** Accessibility limitation
   - **Effort:** Low-Medium
7. **Cross-Species Comparative Models**
   - Animal consciousness models
   - Comparative analysis tools
   - **Impact:** Research limitation
   - **Effort:** High
8. **Cloud Synchronization**
   - Session cloud storage
   - Multi-device sync
   - **Impact:** Convenience feature
   - **Effort:** Medium

- Authentication overhead optimization
- DDoS protection
- Security audit tools
- Penetration testing framework
- Memory allocation improvements
- Memory optimization for GPU
- Load testing and performance tuning
- Additional cognitive tasks (Stroop, N-back)
- Clinical pathology models
- Cross-species comparative models
- Code generation tools
