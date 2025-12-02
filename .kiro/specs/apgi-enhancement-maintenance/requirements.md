# Requirements Document

## Introduction

This document specifies requirements for enhancing, maintaining, and comprehensively testing the APGI (Allostatic Precision-Gated Ignition) System - a computational consciousness framework. The APGI system integrates active inference, predictive processing, allostatic regulation, ignition dynamics, and self-modeling to simulate consciousness phenomena. The system includes a GUI application for real-time visualization and interaction, experimental task implementations, and multi-scale neural dynamics.

The enhancement plan focuses on three key areas:
1. **Code Quality & Maintainability**: Improving code structure, documentation, and maintainability
2. **Testing Infrastructure**: Establishing comprehensive unit and property-based testing
3. **Feature Enhancements**: Adding new capabilities while preserving existing functionality

## Glossary

- **APGI System**: The Allostatic Precision-Gated Ignition framework - the complete consciousness modeling system
- **Active Inference**: Variational free energy minimization and Bayesian inference mechanism
- **Predictive Processing**: Hierarchical prediction error minimization system
- **Allostatic Regulation**: Interoceptive predictive processing and homeostatic control
- **Ignition Event**: Threshold-based global workspace broadcasting event representing conscious access
- **Free Energy**: Measure of prediction error magnitude in the system
- **Precision Weighting**: Confidence-based weighting of prediction errors
- **Somatic Markers**: Learned associations between contexts, actions, and outcomes
- **Global Workspace**: Broadcasting mechanism for conscious access to information
- **Interoceptive Input**: Body state information (heart rate, cortisol, etc.)
- **Exteroceptive Input**: External sensory information
- **Property-Based Test**: Test that verifies a universal property holds across many randomly generated inputs
- **Unit Test**: Test that verifies specific examples and edge cases work correctly

## Requirements

### Requirement 1: Code Quality and Documentation

**User Story:** As a developer, I want well-documented, maintainable code with clear structure, so that I can understand, modify, and extend the system effectively.

#### Acceptance Criteria

1. WHEN a developer reads any module THEN the system SHALL provide comprehensive docstrings following NumPy/Google style for all public classes and methods
2. WHEN a developer examines the codebase THEN the system SHALL include type hints for all function parameters and return values
3. WHEN a developer needs to understand system architecture THEN the system SHALL provide architecture documentation with component interaction diagrams
4. WHEN code complexity exceeds reasonable limits THEN the system SHALL refactor complex methods into smaller, focused functions
5. WHEN a developer reviews the code THEN the system SHALL follow consistent naming conventions and code style throughout

### Requirement 2: Core System Testing

**User Story:** As a developer, I want comprehensive tests for core system components, so that I can verify correctness and catch regressions early.

#### Acceptance Criteria

1. WHEN the active inference engine processes observations THEN the system SHALL compute valid free energy values that decrease over time with learning
2. WHEN precision weighting updates with error variance THEN the system SHALL produce precision values that inversely correlate with prediction error variance
3. WHEN the hierarchical predictor processes inputs THEN the system SHALL generate predictions at multiple hierarchical levels with decreasing error over time
4. WHEN the system performs a complete step THEN the system SHALL maintain internal consistency across all subsystem states
5. WHEN the body model updates THEN the system SHALL produce physiologically plausible interoceptive signals within valid ranges

### Requirement 3: Ignition Dynamics Testing

**User Story:** As a researcher, I want to verify ignition dynamics behave correctly, so that I can trust the consciousness modeling results.

#### Acceptance Criteria

1. WHEN precision-weighted prediction errors exceed threshold THEN the system SHALL trigger an ignition event
2. WHEN an ignition event occurs THEN the system SHALL broadcast to the global workspace for 300-500ms duration
3. WHEN metabolic reserves are depleted THEN the system SHALL increase the ignition threshold proportionally
4. WHEN allostatic load is high THEN the system SHALL modulate ignition threshold to reflect increased stress
5. WHEN somatic markers provide strong signals THEN the system SHALL incorporate marker gain into ignition computation

### Requirement 4: Interoception and Allostasis Testing

**User Story:** As a researcher, I want to verify interoceptive processing and allostatic regulation work correctly, so that I can model body-brain interactions accurately.

#### Acceptance Criteria

1. WHEN the body model updates over time THEN the system SHALL maintain homeostatic variables within physiological bounds
2. WHEN allostatic load accumulates THEN the system SHALL track cumulative deviation from homeostatic setpoints
3. WHEN somatic markers are learned THEN the system SHALL store context-action-outcome associations with timestamps
4. WHEN somatic markers are retrieved THEN the system SHALL return markers matching the current context with appropriate gain values
5. WHEN body state deviates from predictions THEN the system SHALL generate interoceptive prediction errors

### Requirement 5: Property-Based Testing for Core Invariants

**User Story:** As a developer, I want property-based tests that verify system invariants hold across many inputs, so that I can catch edge cases and ensure robustness.

#### Acceptance Criteria

1. WHEN the system processes any valid input sequence THEN the system SHALL maintain non-negative free energy values
2. WHEN precision values are updated with any valid error variance THEN the system SHALL produce finite, positive precision weights
3. WHEN the system runs for any duration THEN the system SHALL maintain metabolic reserves between 0 and maximum capacity
4. WHEN ignition events occur THEN the system SHALL deplete metabolic reserves by a consistent percentage per event
5. WHEN the system resets THEN the system SHALL restore all subsystems to initial state regardless of previous history

### Requirement 6: GUI Application Testing

**User Story:** As a user, I want a reliable GUI application, so that I can visualize and interact with the system without crashes or errors.

#### Acceptance Criteria

1. WHEN the GUI launches THEN the system SHALL initialize all visualization panels without errors
2. WHEN simulation parameters are adjusted via sliders THEN the system SHALL apply changes to the running system immediately
3. WHEN the user exports data THEN the system SHALL save complete simulation history in the specified format (CSV or JSON)
4. WHEN the simulation runs THEN the system SHALL update all plots at the specified refresh rate without blocking
5. WHEN the user triggers manual interventions THEN the system SHALL apply the intervention and reflect changes in real-time

### Requirement 7: Experimental Task Validation

**User Story:** As a researcher, I want validated experimental task implementations, so that I can reproduce known consciousness phenomena.

#### Acceptance Criteria

1. WHEN the Iowa Gambling Task runs THEN the system SHALL demonstrate learning to prefer advantageous decks over time
2. WHEN the Masking Paradigm runs with varying SOAs THEN the system SHALL show reduced ignition probability at short SOAs
3. WHEN the Attentional Blink task runs THEN the system SHALL show reduced detection of T2 targets at 200-500ms lag
4. WHEN any experimental task completes THEN the system SHALL generate results matching expected consciousness phenomena patterns
5. WHEN task results are saved THEN the system SHALL include all trial data, ignition events, and performance metrics

### Requirement 8: System Integration and Consistency

**User Story:** As a developer, I want to ensure all subsystems integrate correctly, so that the complete system behaves coherently.

#### Acceptance Criteria

1. WHEN the system performs a step THEN the system SHALL update all subsystems in the correct dependency order
2. WHEN subsystem states are accessed THEN the system SHALL provide consistent state information across all components
3. WHEN the system runs for extended duration THEN the system SHALL maintain numerical stability without overflow or underflow
4. WHEN multiple subsystems interact THEN the system SHALL preserve causal relationships and temporal ordering
5. WHEN the system state is queried THEN the system SHALL return complete state information including all subsystem metrics

### Requirement 9: Performance and Scalability

**User Story:** As a user, I want the system to run efficiently, so that I can perform long simulations and real-time interactions.

#### Acceptance Criteria

1. WHEN the system performs a single step THEN the system SHALL complete within 10ms on standard hardware
2. WHEN the GUI updates visualizations THEN the system SHALL maintain at least 10 FPS during active simulation
3. WHEN simulation history grows large THEN the system SHALL manage memory efficiently using bounded buffers
4. WHEN the system runs for extended periods THEN the system SHALL maintain consistent performance without degradation
5. WHEN multiple experimental tasks run sequentially THEN the system SHALL properly clean up resources between tasks

### Requirement 10: Error Handling and Robustness

**User Story:** As a user, I want the system to handle errors gracefully, so that I can recover from issues without losing work.

#### Acceptance Criteria

1. WHEN invalid input is provided THEN the system SHALL validate inputs and raise informative error messages
2. WHEN numerical instability is detected THEN the system SHALL log warnings and attempt recovery or graceful degradation
3. WHEN configuration files are malformed THEN the system SHALL report specific configuration errors with line numbers
4. WHEN the GUI encounters errors THEN the system SHALL display error messages to the user without crashing
5. WHEN system resources are exhausted THEN the system SHALL handle resource limits gracefully and inform the user

### Requirement 11: Configuration and Extensibility

**User Story:** As a researcher, I want to easily configure and extend the system, so that I can adapt it to new experiments and research questions.

#### Acceptance Criteria

1. WHEN configuration parameters are modified THEN the system SHALL validate parameter ranges and apply changes correctly
2. WHEN new subsystems are added THEN the system SHALL provide clear integration points and interfaces
3. WHEN custom experimental tasks are created THEN the system SHALL support task registration and execution through standard interfaces
4. WHEN the system is extended THEN the system SHALL maintain backward compatibility with existing configurations
5. WHEN researchers need custom metrics THEN the system SHALL provide hooks for adding custom state tracking and analysis

### Requirement 12: Data Export and Analysis

**User Story:** As a researcher, I want comprehensive data export and analysis capabilities, so that I can analyze simulation results effectively.

#### Acceptance Criteria

1. WHEN simulation data is exported THEN the system SHALL include timestamps, all subsystem states, and event markers
2. WHEN analysis reports are generated THEN the system SHALL compute summary statistics for ignition events, free energy, and metabolic costs
3. WHEN data is saved in CSV format THEN the system SHALL use consistent column ordering and include headers
4. WHEN data is saved in JSON format THEN the system SHALL preserve nested structure and data types
5. WHEN large datasets are exported THEN the system SHALL handle export efficiently without memory overflow
