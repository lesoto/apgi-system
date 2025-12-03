# Implementation Plan

- [x] 1. Set up testing infrastructure and framework
  - Install Hypothesis for property-based testing (add to pyproject.toml dependencies)
  - Create testing directory structure (tests/unit/, tests/property/, tests/integration/)
  - Create tests/conftest.py with shared fixtures (apgi_system, config, body_model, random_observation, random_body_state)
  - Configure Hypothesis profiles in tests/conftest.py (ci, dev, thorough) with appropriate max_examples settings
  - Update pytest.ini with coverage settings and test discovery
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 2. Create custom Hypothesis strategies for APGI data types
  - Create tests/strategies.py module
  - Implement body_state_strategy for generating valid physiological states
  - Implement observation_strategy for generating valid observation vectors
  - Implement belief_state_strategy for generating valid belief states
  - Implement config_strategy for generating valid configuration dictionaries
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 3. Complete core system implementation
  - Implement missing methods in APGISystem class (step, reset, get_state)
  - Complete implementation of core components that are partially implemented
  - Ensure all components can be instantiated and basic methods work
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 8.1_

- [x] 4. Implement core system property-based tests
  - Create tests/property/test_properties_core.py
  - Use @given decorator from Hypothesis with custom strategies
  - Configure to run minimum 100 iterations per property
  - [x] 4.1 Write property test for free energy decrease with learning
    - **Property 1: Free energy decreases with learning**
    - **Validates: Requirements 2.1**
    - Test: For any observation sequence, repeated processing should decrease free energy
  - [x] 4.2 Write property test for precision-error variance inverse correlation
    - **Property 2: Precision inversely correlates with error variance**
    - **Validates: Requirements 2.2**
  - [x] 4.3 Write property test for prediction error decrease with learning
    - **Property 3: Prediction errors decrease with learning**
    - **Validates: Requirements 2.3**
  - [x] 4.4 Write property test for system state consistency
    - **Property 4: System state consistency**
    - **Validates: Requirements 2.4**
  - [x] 4.5 Write property test for physiological bounds maintenance
    - **Property 5: Physiological bounds maintained**
    - **Validates: Requirements 2.5**
  - [x] 4.6 Write property test for non-negative free energy
    - **Property 16: Non-negative free energy**
    - **Validates: Requirements 5.1**
  - [x] 4.7 Write property test for finite positive precision
    - **Property 17: Finite positive precision**
    - **Validates: Requirements 5.2**
  - [x] 4.8 Write property test for metabolic reserve bounds
    - **Property 18: Metabolic reserve bounds**
    - **Validates: Requirements 5.3**
  - [x] 4.9 Write property test for consistent ignition cost
    - **Property 19: Consistent ignition cost**
    - **Validates: Requirements 5.4**
  - [x] 4.10 Write property test for reset restores initial state
    - **Property 20: Reset restores initial state**
    - **Validates: Requirements 5.5**

- [x] 5. Implement core system unit tests
  - Write unit tests for ActiveInferenceEngine (specific examples, edge cases)
  - Write unit tests for HierarchicalPredictor (multi-level prediction scenarios)
  - Write unit tests for PrecisionWeighting (boundary conditions)
  - Write unit tests for FreeEnergyCalculator (numerical edge cases)
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 6. Implement ignition dynamics property-based tests
  - Create tests/property/test_properties_ignition.py
  - Use custom strategies for generating precision-weighted errors
  - [x] 6.1 Write property test for ignition threshold crossing
    - **Property 6: Ignition occurs when signal exceeds threshold**
    - **Validates: Requirements 3.1**
    - Test: For any signal exceeding threshold (outside refractory), ignition should occur with high probability
  - [x] 6.2 Write property test for workspace broadcast duration
    - **Property 7: Workspace broadcast duration**
    - **Validates: Requirements 3.2**
  - [x] 6.3 Write property test for threshold increase with depleted reserves
    - **Property 8: Threshold increases with depleted reserves**
    - **Validates: Requirements 3.3**
  - [x] 6.4 Write property test for threshold modulation by allostatic load
    - **Property 9: Threshold modulation by allostatic load**
    - **Validates: Requirements 3.4**
  - [x] 6.5 Write property test for somatic marker gain incorporation
    - **Property 10: Somatic marker gain incorporation**
    - **Validates: Requirements 3.5**

- [x] 7. Implement ignition dynamics unit tests
  - Write unit tests for IgnitionThreshold (specific threshold scenarios)
  - Write unit tests for GlobalWorkspace (broadcasting mechanics)
  - Write unit tests for IgnitionTimeline (temporal orchestration)
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 8. Implement interoception and allostasis property-based tests
  - Create tests/property/test_properties_interoception.py
  - Use body_state_strategy for generating valid physiological states
  - [x] 8.1 Write property test for homeostatic bounds invariant
    - **Property 11: Homeostatic bounds invariant**
    - **Validates: Requirements 4.1**
    - Test: For any extended simulation, all homeostatic variables remain within physiological bounds
  - [x] 8.2 Write property test for allostatic load accumulation
    - **Property 12: Allostatic load accumulation**
    - **Validates: Requirements 4.2**
  - [x] 8.3 Write property test for somatic marker storage completeness
    - **Property 13: Somatic marker storage completeness**
    - **Validates: Requirements 4.3**
  - [x] 8.4 Write property test for somatic marker retrieval accuracy
    - **Property 14: Somatic marker retrieval accuracy**
    - **Validates: Requirements 4.4**
  - [x] 8.5 Write property test for interoceptive prediction error computation
    - **Property 15: Interoceptive prediction error computation**
    - **Validates: Requirements 4.5**

- [x] 9. Implement interoception and allostasis unit tests
  - Write unit tests for BodyModel (specific physiological scenarios)
  - Write unit tests for AllostaticRegulator (homeostatic control)
  - Write unit tests for SomaticMarkerSystem (learning and retrieval)
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 10. Checkpoint - Ensure all core and subsystem tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Add comprehensive docstrings to remaining components
  - Add docstrings to interoception components (BodyModel, AllostaticRegulator, SomaticMarkerSystem)
  - Add docstrings to neural components (OscillationEngine, LargeScaleNetworkManager, etc.)
  - Add docstrings to self-model components (MinimalSelf, NarrativeSelf, CoherenceMaintenance)
  - Add docstrings to thermodynamic components (MetabolicBudget, EntropyTracker)
  - Add docstrings to visualization components (RealTimeMonitor)
  - _Requirements: 1.1_

- [x] 12. Add type hints throughout codebase
  - Create apgi_system/types.py with type aliases (FloatArray, IntArray, BodyState, BeliefState, SystemState, ConfigDict)
  - Add type hints to all core component methods (active_inference.py, predictive_processing.py, precision.py, free_energy.py)
  - Add type hints to all ignition component methods (threshold.py, global_workspace.py, temporal_dynamics.py)
  - Add type hints to all interoception component methods (body_model.py, allostasis.py, somatic_markers.py)
  - Add type hints to APGISystem main class (system.py)
  - _Requirements: 1.2_

- [x] 13. Implement input validation infrastructure
  - Create apgi_system/validation.py with InputValidator class
  - Implement validate_array method with shape and range checking
  - Implement validate_scalar method with range and positivity checking
  - Add NaN/Inf detection to all validation methods
  - _Requirements: 10.1_

- [x] 14. Add input validation to core components
  - Add validation to ActiveInferenceEngine.update()
  - Add validation to HierarchicalPredictor.predict()
  - Add validation to PrecisionWeighting.update()
  - Add validation to FreeEnergyCalculator.compute()
  - _Requirements: 10.1_

- [x] 15. Add input validation to ignition components
  - Add validation to IgnitionThreshold.compute_ignition_signal()
  - Add validation to GlobalWorkspace.broadcast()
  - _Requirements: 10.1_

- [x] 16. Add input validation to interoception components
  - Add validation to BodyModel.update()
  - Add validation to AllostaticRegulator.compute_load()
  - Add validation to SomaticMarkerSystem.learn() and retrieve()
  - _Requirements: 10.1_

- [x] 17. Implement numerical stability monitoring




  - Create apgi_system/stability.py with NumericalStabilityMonitor class
  - Implement check_stability method with warning and error thresholds (configurable via config)
  - Add custom exceptions (NumericalInstabilityError, NumericalStabilityWarning) to stability.py
  - Integrate stability checks into critical computation paths (FreeEnergyCalculator, HierarchicalGaussianFilter)
  - _Requirements: 8.3, 10.2_

- [x] 18. Implement GUI and interaction property-based tests
  - Create tests/property/test_properties_gui.py
  - Test GUI parameter updates without launching full GUI (test backend logic)
  - [x] 18.1 Write property test for parameter adjustment application
    - **Property 21: Parameter adjustment application**
    - **Validates: Requirements 6.2**
    - Test: For any valid parameter value, adjustment should update system parameter immediately
  - [x] 18.2 Write property test for data export completeness
    - **Property 22: Data export completeness**
    - **Validates: Requirements 6.3**
  - [x] 18.3 Write property test for intervention application
    - **Property 24: Intervention application**
    - **Validates: Requirements 6.5**

- [x] 19. Implement GUI unit tests





  - Write unit tests for GUI initialization (test_gui_launches_without_errors)
  - Write unit tests for plot update mechanisms
  - Write unit tests for slider parameter updates
  - Write unit tests for manual intervention buttons
  - _Requirements: 6.1, 6.2, 6.4, 6.5_





- [x] 20. Implement experimental task property-based tests







  - Create tests/property/test_properties_tasks.py
  - Test task behavior across different random seeds and configurations


  - [x] 20.1 Write property test for Iowa Gambling Task learning


    - **Property 25: Iowa Gambling Task learning**




    - **Validates: Requirements 7.1**
    - Test: For any task run, system should show increasing preference for advantageous decks
  - [x] 20.2 Write property test for Masking SOA effect


    - **Property 26: Masking SOA effect**
    - **Validates: Requirements 7.2**
  - [x] 20.3 Write property test for Attentional Blink effect


    - **Property 27: Attentional blink effect**
    - **Validates: Requirements 7.3**
  - [x] 20.4 Write property test for task result completeness


    - **Property 28: Task result completeness**
    - **Validates: Requirements 7.5**

- [x] 21. Implement experimental task unit tests




  - Write unit tests for Iowa Gambling Task (specific trial sequences)
  - Write unit tests for Masking Paradigm (specific SOA values)
  - Write unit tests for Attentional Blink (specific lag conditions)
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 22. Implement integration and consistency property-based tests

  - Create tests/property/test_properties_system.py
  - Test full system integration across random inputs
  - [ ] 22.1 Write property test for state information completeness
    - **Property 29: State information completeness**
    - **Validates: Requirements 8.2**
    - Test: For any system state query, returned state includes all subsystem metrics
  - [ ] 22.2 Write property test for numerical stability
    - **Property 30: Numerical stability**
    - **Validates: Requirements 8.3**
  - [ ] 22.3 Write property test for task cleanup
    - **Property 31: Task cleanup**
    - **Validates: Requirements 8.5**
-

- [x] 23. Implement system integration unit tests






  - Write integration test for full system step execution
  - Write integration test for subsystem update ordering
  - Write integration test for state consistency across components
  - Write integration test for extended simulation runs
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 24. Implement error handling property-based tests



  - Add to tests/property/test_properties_system.py

  - [x] 24.1 Write property test for input validation

    - **Property 32: Input validation**
    - **Validates: Requirements 10.1**
    - Test: For any invalid input, system should raise informative error


- [x] 25. Implement configuration property-based tests




  - Add to tests/property/test_properties_system.py
  - [x] 25.1 Write property test for parameter validation and application


    - **Property 33: Parameter validation and application**
    - **Validates: Requirements 11.1**
    - Test: For any config parameter modification, system validates and applies correctly

- [ ] 26. Implement data export property-based tests

  - Create tests/property/test_properties_export.py
  - [ ] 26.1 Write property test for export data completeness
    - **Property 34: Export data completeness**
    - **Validates: Requirements 12.1**
    - Test: For any simulation run, exported data includes all required fields
  - [ ] 26.2 Write property test for analysis report statistics
    - **Property 35: Analysis report statistics**
    - **Validates: Requirements 12.2**
  - [ ] 26.3 Write property test for CSV format consistency
    - **Property 36: CSV format consistency**
    - **Validates: Requirements 12.3**
  - [ ] 26.4 Write property test for JSON round-trip preservation
    - **Property 37: JSON round-trip preservation**
    - **Validates: Requirements 12.4**

- [ ] 27. Implement data export unit tests



  - Write unit tests for CSV export with specific data
  - Write unit tests for JSON export with nested structures
  - Write unit tests for analysis report generation
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 28. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 30. Set up continuous integration pipeline

  - Create .github/workflows/ directory
  - Create .github/workflows/test.yml with pytest, coverage, and linting jobs
  - Configure CI to run black, flake8, mypy
  - Configure CI to run pytest with coverage reporting (pytest-cov)
  - Set coverage threshold to 80% and fail if not met
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ]* 31. Generate API documentation
  - Set up Sphinx for documentation generation
  - Configure autodoc to extract docstrings
  - Generate HTML documentation
  - Create architecture diagrams using Mermaid or similar
  - _Requirements: 1.3_

- [ ]* 32. Implement performance monitoring utilities
  - Create apgi_system/monitoring.py with PerformanceMetrics dataclass
  - Implement performance tracking for step execution time
  - Implement memory usage tracking
  - Add performance logging to APGISystem
  - _Requirements: 9.1, 9.2, 9.4_

- [ ]* 33. Implement extended analysis capabilities
  - Create apgi_system/analysis.py with AnalysisResults dataclass
  - Implement ignition statistics computation (rate, duration, intervals)
  - Implement energy budget summary (total consumed, average per step)
  - Implement somatic marker statistics (count, retrieval accuracy)
  - Implement coherence metrics computation
  - _Requirements: 12.2_

- [ ]* 34. Add configuration validation tools
  - Create apgi_system/config_validator.py
  - Implement parameter range validation for all config sections
  - Implement config schema validation
  - Add helpful error messages for common config mistakes
  - _Requirements: 11.1, 10.3_

- [ ]* 35. Implement debugging and diagnostic utilities
  - Create apgi_system/diagnostics.py
  - Implement state snapshot functionality
  - Implement subsystem health checks
  - Add diagnostic logging with configurable verbosity
  - _Requirements: 10.2_

- [ ] 36. Final checkpoint - Comprehensive test run
  - Run full test suite with coverage report
  - Verify 80% coverage target achieved
  - Run mypy and ensure no type errors
  - Run linters (black, flake8) and fix any issues
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 37. Create usage examples and tutorials
  - Create examples/testing_guide.py demonstrating test usage
  - Create examples/property_testing_guide.py with Hypothesis examples
  - Update README.md with testing instructions
  - Add troubleshooting guide for common issues
  - _Requirements: 1.3_
