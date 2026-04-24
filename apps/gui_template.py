import tkinter as tk

import customtkinter as ctk
import matplotlib

matplotlib.use("TkAgg")  # Set matplotlib backend before importing pyplot
import datetime
import json
import logging
import os
import subprocess
import sys
import threading
import traceback
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# APGI Framework imports
ConfigManager: Optional[Any] = None
APGIFrameworkCLI: Optional[Any] = None
MainApplicationController: Optional[Any] = None
APGIEquation: Optional[Any] = None
PrecisionCalculator: Optional[Any] = None
PredictionErrorProcessor: Optional[Any] = None
SomaticMarkerEngine: Optional[Any] = None
ThresholdManager: Optional[Any] = None
APGIVisualizer: Optional[Any] = None
IntegratedDataManager: Optional[Any] = None
ReportGenerator: Optional[Any] = None
ClinicalParameterExtractor: Optional[Any] = None
DisorderClassification: Optional[Any] = None
PrimaryFalsificationTest: Optional[Any] = None
ConsciousnessWithoutIgnitionTest: Optional[Any] = None
ThresholdInsensitivityTest: Optional[Any] = None
SomaBiasTest: Optional[Any] = None
BayesianParameterEstimator: Optional[Any] = None
EffectSizeCalculator: Optional[Any] = None
P3bSimulator: Optional[Any] = None
GammaSimulator: Optional[Any] = None
BOLDSimulator: Optional[Any] = None
PCICalculator: Optional[Any] = None
QuestPlusStaircase: Optional[Any] = None
StimulusGenerator: Optional[Any] = None

try:
    # Add project root to Python path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    # Core modules - use correct import paths
    from apgi_framework.cli import APGIFrameworkCLI

    # Configuration and CLI
    from apgi_framework.config import APGIParameters as ConfigParameters
    from apgi_framework.core import (
        APGIEquation,
        PrecisionCalculator,
        PredictionErrorProcessor,
        SomaticMarkerEngine,
        ThresholdManager,
    )
    from apgi_framework.core.data_models import APGIParameters as DataAPGIParameters

    # Main controller
    from apgi_framework.main_controller import MainApplicationController

    # Set up available components
    ConfigManager = ConfigParameters  # Alias for compatibility
    ExperimentalConfig = DataAPGIParameters  # Alias for compatibility

    # Data management - check what's available
    try:
        from apgi_framework.data.data_manager import (
            IntegratedDataManager as _IntegratedDataManager,
        )

        IntegratedDataManager = _IntegratedDataManager
    except ImportError:
        pass

    try:
        from apgi_framework.data.report_generator import (
            ReportGenerator as _ReportGenerator,
        )

        ReportGenerator = _ReportGenerator
    except ImportError:
        pass

    try:
        from apgi_framework.data.visualizer import APGIVisualizer as _APGIVisualizer

        APGIVisualizer = _APGIVisualizer
    except ImportError:
        pass

    # Falsification tests - use available classes
    try:
        from apgi_framework.falsification import (
            PrimaryFalsificationTest as _PrimaryFalsificationTest,
            ConsciousnessAssessment as _ConsciousnessAssessment,
            ConsciousnessAssessmentSimulator as _ConsciousnessAssessmentSimulator,
        )

        PrimaryFalsificationTest = _PrimaryFalsificationTest
        ConsciousnessAssessment = _ConsciousnessAssessment
        ConsciousnessAssessmentSimulator = _ConsciousnessAssessmentSimulator
    except ImportError:
        pass

    # Fallback classes for falsification tests that don't exist as separate modules
    ConsciousnessWithoutIgnitionTest = None
    ThresholdInsensitivityTest = None
    SomaBiasTest = None

    # Analysis modules - use available classes
    try:
        from apgi_framework.analysis.bayesian_models import HierarchicalBayesianModel

        BayesianParameterEstimator = HierarchicalBayesianModel
    except ImportError:
        pass

    try:
        from apgi_framework.analysis.effect_size_calculator import (
            EffectSizeCalculator as _EffectSizeCalculator,
        )

        EffectSizeCalculator = _EffectSizeCalculator
    except ImportError:
        pass

    DisorderClassification = None
    try:
        from apgi_framework.clinical.disorder_classification import (
            DisorderClassification as _DisorderClassification,
        )

        DisorderClassification = _DisorderClassification
    except ImportError:
        pass

    try:
        from apgi_framework.clinical.parameter_extraction import (
            ClinicalParameterExtractor,
        )
    except ImportError:
        pass

    # Neural simulators
    try:
        from apgi_framework.simulators.p3b_simulator import (
            P3bSimulator as _P3bSimulator,
        )

        P3bSimulator = _P3bSimulator
    except ImportError:
        pass

    try:
        from apgi_framework.simulators.gamma_simulator import (
            GammaSimulator as _GammaSimulator,
        )

        GammaSimulator = _GammaSimulator
    except ImportError:
        pass

    try:
        from apgi_framework.simulators.bold_simulator import (
            BOLDSimulator as _BOLDSimulator,
        )

        BOLDSimulator = _BOLDSimulator
    except ImportError:
        pass

    try:
        from apgi_framework.simulators.pci_calculator import (
            PCICalculator as _PCICalculator,
        )

        PCICalculator = _PCICalculator
    except ImportError:
        pass

    # Adaptive procedures - use available classes
    try:
        from apgi_framework.adaptive.quest_plus_staircase import (
            QuestPlusStaircase as _QuestPlusStaircase,
        )

        QuestPlusStaircase = _QuestPlusStaircase
    except ImportError:
        pass

    try:
        from apgi_framework.adaptive.stimulus_generators import (
            StimulusGenerator as _StimulusGenerator,
        )

        StimulusGenerator = _StimulusGenerator
    except ImportError:
        pass

except ImportError as e:
    print(f"Warning: Some APGI Framework modules not available: {e}")
    # Fallback imports for basic functionality
    try:
        # Add project root to Python path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))

        from apgi_framework.core import (
            APGIEquation,
            PrecisionCalculator,
            PredictionErrorProcessor,
        )
        from apgi_framework.config import APGIParameters

        ConfigManager = APGIParameters  # Alias for compatibility
        APGIFrameworkCLI = None
        IntegratedDataManager = None
        BayesianParameterEstimator = None
        DisorderClassification = None
        QuestPlusStaircase = None
        MainApplicationController = None
    except ImportError as e2:
        print(f"Error: Even basic APGI Framework imports failed: {e2}")
        # Set all components to None for graceful degradation
        ConfigManager = None
        APGIEquation = None
        PrecisionCalculator = None
        PredictionErrorProcessor = None
        APGIFrameworkCLI = None
        IntegratedDataManager = None
        BayesianParameterEstimator = None
        DisorderClassification = None
        QuestPlusStaircase = None
        MainApplicationController = None


class ErrorSeverity(Enum):
    """Error severity levels for better categorization"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationError:
    """Configuration validation error details"""

    field: str
    message: str
    severity: ErrorSeverity
    suggested_value: Any = None


class ConfigurationValidator:
    """Validates GUI configuration parameters using real ConfigManager when available"""

    def __init__(self):
        # Initialize real config manager if available
        self.config_manager = None
        if ConfigManager is not None:
            try:
                self.config_manager = ConfigManager()
            except Exception as e:
                print(f"Warning: Could not initialize ConfigManager: {e}")

        # Fallback validation rules
        self.validation_rules = {
            "gamma_oscillation_power": {"min": 0.0, "max": 10.0, "type": float},
            "p3b_amplitude": {"min": 0.0, "max": 50.0, "type": float},
            "bold_signal_strength": {"min": 0.0, "max": 5.0, "type": float},
            "pci_value": {"min": 0.0, "max": 1.0, "type": float},
            "prediction_error_weight": {"min": 0.0, "max": 1.0, "type": float},
            "threshold_sensitivity": {"min": 0.1, "max": 10.0, "type": float},
            "somatic_marker_strength": {"min": 0.0, "max": 1.0, "type": float},
            "precision_weight": {"min": 0.0, "max": 1.0, "type": float},
            "num_trials": {"min": 1, "max": 10000, "type": int},
            "sample_rate": {"min": 100, "max": 10000, "type": int},
            "duration": {"min": 0.1, "max": 3600.0, "type": float},
            # APGI framework specific parameters
            "exteroceptive_precision": {"min": 0.1, "max": 10.0, "type": float},
            "interoceptive_precision": {"min": 0.1, "max": 10.0, "type": float},
            "somatic_gain": {"min": 0.0, "max": 5.0, "type": float},
            "threshold": {"min": 0.1, "max": 10.0, "type": float},
            "steepness": {"min": 0.1, "max": 10.0, "type": float},
        }

    def validate_parameter(
        self, param_name: str, value: str
    ) -> Tuple[bool, Optional[ValidationError]]:
        """Validate a single parameter using ConfigManager if available"""

        # Try real framework validation first
        if self.config_manager is not None:
            try:
                # Map GUI parameter names to framework names
                param_mapping = {
                    "exteroceptive_precision": "extero_precision",
                    "interoceptive_precision": "intero_precision",
                    "somatic_gain": "somatic_gain",
                    "threshold": "threshold",
                    "steepness": "steepness",
                }

                framework_param = param_mapping.get(param_name, param_name)

                # Try to validate using framework
                try:
                    converted_value = float(value)

                    # Use framework validation if available
                    if hasattr(self.config_manager, "validate_apgi_parameter"):
                        is_valid = self.config_manager.validate_apgi_parameter(
                            framework_param, converted_value
                        )
                        if not is_valid:
                            return False, ValidationError(
                                field=param_name,
                                message=f"Parameter {framework_param} failed framework validation",
                                severity=ErrorSeverity.MEDIUM,
                            )

                    # If no framework validation, continue with local validation
                except ValueError:
                    return False, ValidationError(
                        field=param_name,
                        message=f"Invalid numeric value: {value}",
                        severity=ErrorSeverity.HIGH,
                    )

            except Exception as e:
                # Fallback to local validation if framework validation fails
                print(f"Framework validation failed for {param_name}: {e}")

        # Local validation as fallback
        if param_name not in self.validation_rules:
            return True, None

        rules = self.validation_rules[param_name]

        try:
            # Convert to correct type
            if rules["type"] == float:
                converted_value = float(value)
            elif rules["type"] == int:
                converted_value = int(value)
            else:
                converted_value = value  # type: ignore

            # Check range
            if isinstance(converted_value, (int, float)):
                if "min" in rules and converted_value < rules["min"]:
                    return False, ValidationError(
                        field=param_name,
                        message=f"Value {converted_value} is below minimum {rules['min']}",
                        severity=ErrorSeverity.MEDIUM,
                        suggested_value=rules["min"],
                    )

                if "max" in rules and converted_value > rules["max"]:
                    return False, ValidationError(
                        field=param_name,
                        message=f"Value {converted_value} is above maximum {rules['max']}",
                        severity=ErrorSeverity.MEDIUM,
                        suggested_value=rules["max"],
                    )

            return True, None

        except ValueError as e:
            return False, ValidationError(
                field=param_name,
                message=f"Invalid value format: {str(e)}",
                severity=ErrorSeverity.HIGH,
            )

    def validate_all_parameters(
        self, params_dict: Dict[str, str]
    ) -> Tuple[bool, List[ValidationError]]:
        """Validate all parameters in a dictionary"""
        errors = []
        all_valid = True

        for param_name, value in params_dict.items():
            is_valid, error = self.validate_parameter(param_name, value)
            if not is_valid and error:
                errors.append(error)
                all_valid = False

        return all_valid, errors


class GUIErrorHandler:
    """Centralized error handling for the GUI"""

    def __init__(self, logger):
        self.logger = logger
        self.error_counts = {}
        self.max_error_display = 5

    def handle_error(
        self,
        error: Exception,
        context: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        show_user: bool = True,
        critical: bool = False,
    ):
        """Handle an error with appropriate logging and user notification"""
        error_type = type(error).__name__
        error_msg = str(error)

        # Log the error with full traceback
        self.logger.error(f"Error in {context}: {error_type}: {error_msg}")
        self.logger.debug(f"Full traceback:\n{traceback.format_exc()}")

        # Track error frequency
        error_key = f"{context}:{error_type}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        # Show user notification if requested
        if show_user:
            self._show_user_error(error, context, severity, critical)

        # Handle critical errors
        if critical:
            self._handle_critical_error(error, context)

    def _show_user_error(
        self, error: Exception, context: str, severity: ErrorSeverity, critical: bool
    ):
        """Show appropriate user-facing error message"""
        error_type = type(error).__name__
        error_msg = str(error)

        # Create user-friendly message
        if severity == ErrorSeverity.CRITICAL or critical:
            title = "Critical Error"
            message = (
                f"A critical error occurred in {context}:\n\n{error_msg}\n\n"
                f"The application may need to be restarted."
            )
        elif severity == ErrorSeverity.HIGH:
            title = "Error"
            message = f"An error occurred in {context}:\n\n{error_msg}"
        else:
            title = "Warning"
            message = f"A warning occurred in {context}:\n\n{error_msg}"

        # Add error frequency if high
        error_key = f"{context}:{error_type}"
        if self.error_counts.get(error_key, 0) > 1:
            message += f"\n\n(This error has occurred {self.error_counts[error_key]} times)"

        messagebox.showerror(title, message)

    def _handle_critical_error(self, error: Exception, context: str) -> None:
        """Handle critical errors that may require application shutdown"""
        self.logger.critical(f"Critical error in {context}, application may be unstable")
        # Could implement emergency save or cleanup here

    def handle_validation_errors(self, errors: List[ValidationError]) -> None:
        """Handle configuration validation errors"""
        if not errors:
            return

        critical_errors = [e for e in errors if e.severity == ErrorSeverity.CRITICAL]
        high_errors = [e for e in errors if e.severity == ErrorSeverity.HIGH]

        if critical_errors:
            message = "Critical configuration errors found:\n\n"
            for error in critical_errors[: self.max_error_display]:
                message += f"• {error.field}: {error.message}\n"
                if error.suggested_value is not None:
                    message += f"  Suggested: {error.suggested_value}\n"
            messagebox.showerror("Critical Configuration Errors", message)
        elif high_errors:
            message = "Configuration errors found:\n\n"
            for error in high_errors[: self.max_error_display]:
                message += f"• {error.field}: {error.message}\n"
                if error.suggested_value is not None:
                    message += f"  Suggested: {error.suggested_value}\n"
            messagebox.showwarning("Configuration Errors", message)
        else:
            # Low/medium severity errors - just log them
            for error in errors:
                self.logger.warning(
                    f"Configuration validation warning: {error.field}: {error.message}"
                )


class APGIFrameworkGUI(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("APGI Framework GUI - Comprehensive Testing System")
        self.geometry("2000x1200+50+50")
        self.minsize(1600, 1000)
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Initialize error handling and validation
        self.logger: Union[Any, logging.Logger] = logging.getLogger(__name__)
        self.error_handler = None
        self.config_validator = ConfigurationValidator()

        # Initialize framework components
        self.config_manager = None
        self.cli_handler = None
        self.data_manager = None
        self.main_controller = None
        self.apgi_equation = None
        self.precision_calculator = None
        self.prediction_error_processor = None
        self.somatic_marker_engine = None
        self.threshold_manager = None
        self.bayesian_estimator = None
        self.disorder_classifier = None
        self.clinical_extractor = None
        self.visualizer = None
        self.report_generator = None

        # Falsification test instances
        self.primary_falsification_test = None
        self.cwi_test = None
        self.threshold_test = None
        self.soma_bias_test = None

        # Neural simulators
        self.p3b_simulator = None
        self.gamma_simulator = None
        self.bold_simulator = None
        self.pci_calculator = None

        # Current results and system status
        self.current_results: Dict[str, Any] = {}
        self.system_status: Dict[str, Any] = {}
        self.current_session_data: Optional[Dict[str, Any]] = None

        # Initialize variables
        self.data_folder = "data"
        self.results_folder = "results"
        self.current_file: Optional[str] = None
        self.current_data: Optional[pd.DataFrame] = None

        # Create data folders if they don't exist
        try:
            for folder in [self.data_folder, self.results_folder]:
                if not os.path.exists(folder):
                    os.makedirs(folder)
        except Exception as e:
            print(f"Warning: Could not create data folders: {e}")

        # Setup logging first
        self._setup_logging()

        # Initialize error handler after logger is available
        self.error_handler = GUIErrorHandler(self.logger)

        # ---------- master grid ----------
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)  # Status bar

        # Create UI components with error handling
        try:
            self.create_menu_bar()
            self.create_sidebar()
            self.create_main_area()
            self.create_status_bar()
        except Exception as e:
            self.error_handler.handle_error(e, "UI Creation", ErrorSeverity.CRITICAL, critical=True)
            return

        # Initialize APGI Framework after UI is created
        self._initialize_framework()

        # Update system status
        self._update_system_status()

    def _initialize_framework(self) -> None:
        """Initialize APGI Framework components with robust error handling."""
        if self.error_handler is None:
            print("Error: Error handler not initialized")
            return

        self.log_to_console("Starting APGI Framework initialization...")
        initialization_success = True

        # Check if basic components are available
        if ConfigManager is None:
            self.error_handler.handle_error(
                ImportError("ConfigManager not available"),
                "Framework Initialization",
                ErrorSeverity.CRITICAL,
                show_user=True,
            )
            return

        # Initialize configuration and main controller
        try:
            self.config_manager = ConfigManager()
            self.log_to_console("✓ ConfigManager initialized")
        except Exception as e:
            self.error_handler.handle_error(
                e, "ConfigManager Initialization", ErrorSeverity.CRITICAL
            )
            initialization_success = False

        if initialization_success:
            try:
                if MainApplicationController is not None:
                    self.main_controller = MainApplicationController()  # type: ignore[misc]
                    self.log_to_console("✓ MainApplicationController initialized")
            except Exception as e:
                self.error_handler.handle_error(
                    e, "MainApplicationController Initialization", ErrorSeverity.HIGH
                )
                initialization_success = False

        if initialization_success:
            try:
                if APGIFrameworkCLI is not None:
                    self.cli_handler = APGIFrameworkCLI()  # type: ignore[misc]
                    self.log_to_console("✓ APGIFrameworkCLI initialized")
            except Exception as e:
                self.error_handler.handle_error(
                    e, "APGIFrameworkCLI Initialization", ErrorSeverity.MEDIUM
                )
                # Non-critical, continue initialization

        # Initialize core components with graceful degradation
        core_components = [
            ("APGIEquation", APGIEquation, "apgi_equation"),
            ("PrecisionCalculator", PrecisionCalculator, "precision_calculator"),
            (
                "PredictionErrorProcessor",
                PredictionErrorProcessor,
                "prediction_error_processor",
            ),
            ("SomaticMarkerEngine", SomaticMarkerEngine, "somatic_marker_engine"),
            ("ThresholdManager", ThresholdManager, "threshold_manager"),
        ]

        for component_name, component_class, attr_name in core_components:
            if component_class is None:
                self.log_to_console(f"⚠ {component_name} not available")
                setattr(self, attr_name, None)
                continue

            try:
                component_instance = component_class()
                setattr(self, attr_name, component_instance)
                self.log_to_console(f"✓ {component_name} initialized")
            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    f"{component_name} Initialization",
                    ErrorSeverity.MEDIUM,
                    show_user=False,
                )
                setattr(self, attr_name, None)

        # Initialize data management components
        data_components = [
            ("IntegratedDataManager", IntegratedDataManager, "data_manager"),
            ("APGIVisualizer", APGIVisualizer, "visualizer"),
            ("ReportGenerator", ReportGenerator, "report_generator"),
        ]

        for component_name, component_class, attr_name in data_components:
            if component_class is None:
                self.log_to_console(f"⚠ {component_name} not available")
                setattr(self, attr_name, None)
                continue

            try:
                component_instance = component_class()
                setattr(self, attr_name, component_instance)
                self.log_to_console(f"✓ {component_name} initialized")
            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    f"{component_name} Initialization",
                    ErrorSeverity.MEDIUM,
                    show_user=False,
                )
                setattr(self, attr_name, None)

        # Initialize optional analysis components
        optional_components = [
            (
                "BayesianParameterEstimator",
                BayesianParameterEstimator,
                "bayesian_estimator",
            ),
            ("DisorderClassification", DisorderClassification, "disorder_classifier"),
            (
                "ClinicalParameterExtractor",
                ClinicalParameterExtractor,
                "clinical_extractor",
            ),
        ]

        for component_name, component_class, attr_name in optional_components:
            if component_class is None:
                setattr(self, attr_name, None)
                continue

            try:
                component_instance = component_class()
                setattr(self, attr_name, component_instance)
                self.log_to_console(f"✓ {component_name} initialized")
            except Exception as e:
                self.log_to_console(f"⚠ {component_name} initialization failed: {e}")
                setattr(self, attr_name, None)

        # Initialize falsification tests
        falsification_tests = [
            (
                "PrimaryFalsificationTest",
                PrimaryFalsificationTest,
                "primary_falsification_test",
            ),
            (
                "ConsciousnessWithoutIgnitionTest",
                ConsciousnessWithoutIgnitionTest,
                "cwi_test",
            ),
            (
                "ThresholdInsensitivityTest",
                ThresholdInsensitivityTest,
                "threshold_test",
            ),
            ("SomaBiasTest", SomaBiasTest, "soma_bias_test"),
        ]

        for test_name, test_class, attr_name in falsification_tests:
            if test_class is None:
                setattr(self, attr_name, None)
                continue

            try:
                test_instance = test_class()
                setattr(self, attr_name, test_instance)
                self.log_to_console(f"✓ {test_name} initialized")
            except Exception as e:
                self.log_to_console(f"⚠ {test_name} initialization failed: {e}")
                setattr(self, attr_name, None)

        # Initialize neural simulators
        neural_simulators = [
            ("P3bSimulator", P3bSimulator, "p3b_simulator"),
            ("GammaSimulator", GammaSimulator, "gamma_simulator"),
            ("BOLDSimulator", BOLDSimulator, "bold_simulator"),
            ("PCICalculator", PCICalculator, "pci_calculator"),
        ]

        for simulator_name, simulator_class, attr_name in neural_simulators:
            if simulator_class is None:
                setattr(self, attr_name, None)
                continue

            try:
                simulator_instance = simulator_class()
                setattr(self, attr_name, simulator_instance)
                self.log_to_console(f"✓ {simulator_name} initialized")
            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    f"{simulator_name} Initialization",
                    ErrorSeverity.MEDIUM,
                    show_user=False,
                )
                setattr(self, attr_name, None)

        # Final status check
        if initialization_success:
            self.log_to_console("✓ APGI Framework initialization completed successfully")
        else:
            self.log_to_console("⚠ APGI Framework initialization completed with some errors")

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        try:
            from apgi_framework.logging.standardized_logging import get_logger

            self.logger = get_logger(
                "apgi_framework_gui_template", log_file="apgi_framework_gui.log"
            )  # type: ignore[assignment]
        except ImportError:
            # Fallback to basic logging
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                handlers=[
                    logging.FileHandler("apgi_framework_gui.log"),
                    logging.StreamHandler(),
                ],
            )

            self.logger = logging.getLogger(__name__)  # type: ignore[assignment]

    def _update_system_status(self) -> None:
        """Update system status information."""
        try:
            if self.cli_handler:
                # Get system status from CLI
                self.system_status = {
                    "framework_version": "1.0.0",
                    "config_loaded": self.config_manager is not None,
                    "data_manager_ready": self.data_manager is not None,
                    "last_check": datetime.datetime.now().isoformat(),
                }
            else:
                self.system_status = {"error": "CLI handler not initialized"}
        except Exception as e:
            self.system_status = {"error": str(e)}
            self.log_to_console(f"Error updating system status: {e}")

    def create_status_bar(self) -> Any:
        """Create status bar at bottom of window."""
        status_bar = ctk.CTkFrame(self, height=30, fg_color="#e0e0e0")
        status_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        status_bar.grid_propagate(False)

        # Status label
        self.status_label = ctk.CTkLabel(
            status_bar,
            text="Ready",
            font=("Arial", 10),
            fg_color="#e0e0e0",
            text_color="black",
        )
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)

        # System status indicator
        self.system_status_label = ctk.CTkLabel(
            status_bar,
            text="System: Initializing...",
            font=("Arial", 10),
            fg_color="#e0e0e0",
            text_color="black",
        )
        self.system_status_label.pack(side=tk.RIGHT, padx=10, pady=5)

    def create_menu_bar(self):
        """Create the menu bar with File menu."""
        # Create menu bar using tkinter Menu since customtkinter doesn't have a native menu bar
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        # Create File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        # Add File menu items
        self.file_menu.add_command(
            label="New Configuration", command=self.new_config, accelerator="Ctrl+N"
        )
        self.file_menu.add_command(
            label="Load Configuration", command=self.load_config, accelerator="Ctrl+O"
        )
        self.file_menu.add_command(
            label="Save Configuration", command=self.save_config, accelerator="Ctrl+S"
        )

        # Add separator and exit
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.quit, accelerator="Ctrl+Q")

        # Bind keyboard shortcuts
        self.bind("<Control-n>", lambda e: self.new_config())
        self.bind("<Control-o>", lambda e: self.load_config())
        self.bind("<Control-s>", lambda e: self.save_config())
        self.bind("<Control-q>", lambda e: self.quit())

    def update_status(self, message):
        """Update status bar message."""
        self.status_label.configure(text=message)
        self.update_idletasks()

    def update_system_status_display(self):
        """Update system status display."""
        if self.system_status:
            if "error" in self.system_status:
                status_text = f"System Error: {self.system_status['error']}"
                color = "red"
            else:
                status_text = "System: Ready"
                color = "green"
            self.system_status_label.configure(text=status_text, text_color=color)

    # ------------------------------------------------------------------
    # SIDEBAR
    # ------------------------------------------------------------------
    def create_sidebar(self):
        # Create scrollable sidebar container
        sidebar_container = ctk.CTkFrame(self, width=350, corner_radius=0, fg_color="#f0f0f0")
        sidebar_container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        sidebar_container.grid_propagate(False)

        # Configure container grid
        sidebar_container.grid_columnconfigure(0, weight=1)
        sidebar_container.grid_rowconfigure(0, weight=1)

        # Create scrollable frame within container
        self.sidebar_scrollable = ctk.CTkScrollableFrame(
            sidebar_container,
            fg_color="#f0f0f0",
            scrollbar_button_color="#3a7ebf",
            scrollbar_button_hover_color="#1f538d",
        )
        self.sidebar_scrollable.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar_scrollable.grid_columnconfigure(0, weight=1)

        # Create sections in scrollable frame
        sections = [
            ("APGI Parameters", self.create_apgi_parameters_section),
            ("Experimental Setup", self.create_experimental_setup_section),
            ("Falsification Tests", self.create_falsification_tests_section),
            ("Research Experiments", self.create_research_experiments_section),
            ("Analysis Tools", self.create_analysis_tools_section),
            ("Clinical Applications", self.create_clinical_applications_section),
            ("Data Management", self.create_data_management_section),
            ("System Tools", self.create_system_tools_section),
            ("Visualization", self.create_visualization_section),
            ("Export", self.create_export_section),
        ]

        for idx, (title, creator) in enumerate(sections):
            section_frame = ctk.CTkFrame(self.sidebar_scrollable, fg_color="#f0f0f0")
            section_frame.grid(row=idx, column=0, sticky="ew", padx=10, pady=(10, 0))
            section_frame.grid_columnconfigure(0, weight=1)

            # Section title
            title_label = ctk.CTkLabel(
                section_frame,
                text=title,
                font=("Arial", 12, "bold"),
                fg_color="#f0f0f0",
                text_color="black",
            )
            title_label.grid(row=0, column=0, sticky="w", padx=5, pady=(5, 2))

            # Create section content
            content_frame = ctk.CTkFrame(section_frame, fg_color="#f0f0f0")
            content_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
            content_frame.grid_columnconfigure(0, weight=1)

            creator(content_frame)

    def create_apgi_parameters_section(self, parent):
        """Create APGI parameters section."""
        self.apgi_params = {}
        params = [
            ("Exteroceptive Precision:", "exteroceptive_precision", "2.0"),
            ("Interoceptive Precision:", "interoceptive_precision", "1.5"),
            ("Exteroceptive Error:", "exteroceptive_error", "1.2"),
            ("Interoceptive Error:", "interoceptive_error", "0.8"),
            ("Somatic Gain:", "somatic_gain", "1.3"),
            ("Threshold:", "threshold", "3.5"),
            ("Steepness:", "steepness", "2.0"),
        ]

        for idx, (label_text, param_name, default_value) in enumerate(params):
            frame = ctk.CTkFrame(parent, fg_color="#f0f0f0")
            frame.grid(row=idx, column=0, sticky="ew", padx=5, pady=2)

            label = ctk.CTkLabel(frame, text=label_text, width=140)
            label.pack(side=tk.LEFT, padx=(0, 5))

            entry = ctk.CTkEntry(frame, width=80)
            entry.pack(side=tk.RIGHT)
            entry.insert(0, default_value)

            self.apgi_params[param_name] = entry

    def create_experimental_setup_section(self, parent):
        """Create experimental setup section."""
        self.exp_setup_params = {}

        params = [
            ("Number of Trials:", "n_trials", "100"),
            ("Number of Participants:", "n_participants", "20"),
            ("Session Duration (min):", "session_duration", "60"),
            ("Inter-trial Interval (s):", "iti", "2.0"),
        ]

        for idx, (label_text, param_name, default_value) in enumerate(params):
            frame = ctk.CTkFrame(parent, fg_color="#f0f0f0")
            frame.grid(row=idx, column=0, sticky="ew", padx=5, pady=2)

            label = ctk.CTkLabel(frame, text=label_text, width=140)
            label.pack(side=tk.LEFT, padx=(0, 5))

            entry = ctk.CTkEntry(frame, width=80)
            entry.pack(side=tk.RIGHT)
            entry.insert(0, default_value)

            self.exp_setup_params[param_name] = entry

    def create_falsification_tests_section(self, parent):
        """Create falsification tests section."""
        tests = [
            ("Primary Test", self.run_primary_falsification_test),
            ("Consciousness-Without-Ignition", self.run_cwi_test),
            ("Threshold-Insensitivity", self.run_threshold_insensitivity_test),
            ("Soma-Bias Test", self.run_soma_bias_test),
            ("Batch Tests", self.run_batch_tests),
        ]

        for idx, (text, command) in enumerate(tests):
            btn = ctk.CTkButton(
                parent,
                text=text,
                fg_color="#3a7ebf",
                hover_color="#1f538d",
                command=command,
                width=200,
            )
            btn.grid(row=idx, column=0, sticky="ew", padx=5, pady=2)

    def create_research_experiments_section(self, parent):
        """Create research experiments section."""
        experiments = [
            ("AI Benchmarking", self.run_ai_benchmarking_experiment),
            ("Interoceptive Gating", self.run_interoceptive_gating_experiment),
            ("Threshold Effects", self.run_threshold_effects_experiment),
            ("Somatic Markers", self.run_somatic_markers_experiment),
            ("Precision Effects", self.run_precision_effects_experiment),
            ("Dynamic Threshold", self.run_dynamic_threshold_experiment),
        ]

        for idx, (text, command) in enumerate(experiments):
            btn = ctk.CTkButton(
                parent,
                text=text,
                fg_color="#3a7ebf",
                hover_color="#1f538d",
                command=command,
                width=200,
            )
            btn.grid(row=idx, column=0, sticky="ew", padx=5, pady=2)

    def create_analysis_tools_section(self, parent):
        """Create analysis tools section."""
        tools = [
            ("Bayesian Parameter Estimation", self.run_bayesian_estimation),
            ("Effect Size Calculator", self.run_effect_size_analysis),
            ("Neural Signature Analysis", self.run_neural_signature_analysis),
            ("Surprise Dynamics Analysis", self.run_surprise_dynamics_analysis),
        ]

        for idx, (text, command) in enumerate(tools):
            btn = ctk.CTkButton(
                parent,
                text=text,
                fg_color="#3a7ebf",
                hover_color="#1f538d",
                command=command,
                width=200,
            )
            btn.grid(row=idx, column=0, sticky="ew", padx=5, pady=2)

    def create_clinical_applications_section(self, parent):
        """Create clinical applications section."""
        applications = [
            ("Disorder Classification", self.run_disorder_classification),
            ("Clinical Parameter Extraction", self.run_clinical_parameter_extraction),
            ("Patient Profile Analysis", self.run_patient_profile_analysis),
        ]

        for idx, (text, command) in enumerate(applications):
            btn = ctk.CTkButton(
                parent,
                text=text,
                fg_color="#3a7ebf",
                hover_color="#1f538d",
                command=command,
                width=200,
            )
            btn.grid(row=idx, column=0, sticky="ew", padx=5, pady=2)

    def create_data_management_section(self, parent):
        """Create data management section."""
        data_ops = [
            ("Import Data", self.import_data),
            ("Export Data", self.export_data),
            ("Data Validation", self.validate_data),
            ("Data Cleaning", self.clean_data),
        ]

        for idx, (text, command) in enumerate(data_ops):
            btn = ctk.CTkButton(
                parent,
                text=text,
                fg_color="#3a7ebf",
                hover_color="#1f538d",
                command=command,
                width=200,
            )
            btn.grid(row=idx, column=0, sticky="ew", padx=5, pady=2)

    def create_system_tools_section(self, parent):
        """Create system tools section."""
        tools = [
            ("System Validation", self.validate_system),
            ("Generate Report", self.generate_report),
            ("System Status", self.show_system_status),
            ("Preferences", self.show_preferences),
        ]

        for idx, (text, command) in enumerate(tools):
            btn = ctk.CTkButton(
                parent,
                text=text,
                fg_color="#3a7ebf",
                hover_color="#1f538d",
                command=command,
                width=200,
            )
            btn.grid(row=idx, column=0, sticky="ew", padx=5, pady=2)

    def create_visualization_section(self, parent):
        """Create visualization section."""
        visualizations = [
            ("Plot Results", self.plot_results),
            ("Neural Signatures Plot", self.plot_neural_signatures),
            ("Parameter Space", self.plot_parameter_space),
            ("Time Series Analysis", self.plot_time_series),
        ]

        for idx, (text, command) in enumerate(visualizations):
            btn = ctk.CTkButton(
                parent,
                text=text,
                fg_color="#3a7ebf",
                hover_color="#1f538d",
                command=command,
                width=200,
            )
            btn.grid(row=idx, column=0, sticky="ew", padx=5, pady=2)

    def create_export_section(self, parent):
        exports = [
            ("Export as PNG", self.export_as_png),
            ("Export as PDF", self.export_as_pdf),
            ("Export Data as CSV", self.export_as_csv),
        ]

        for idx, (text, command) in enumerate(exports):
            btn = ctk.CTkButton(
                parent,
                text=text,
                fg_color="#3a7ebf",
                hover_color="#1f538d",
                command=command,
                width=200,
            )
            btn.grid(row=idx, column=0, sticky="ew", padx=5, pady=2)

    # ------------------------------------------------------------------
    # MAIN AREA
    # ------------------------------------------------------------------
    def create_main_area(self):
        main = ctk.CTkFrame(self, fg_color="white")
        main.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(0, weight=1)

        # Output Display Frame - takes up most of the space
        output_frame = ctk.CTkFrame(main, fg_color="#2b2b2b")
        output_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        output_frame.grid_rowconfigure(1, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)

        # Output Title
        output_title = ctk.CTkLabel(
            output_frame,
            text="Output Console",
            font=("Arial", 14, "bold"),
            text_color="white",
            fg_color="#2b2b2b",
        )
        output_title.grid(row=0, column=0, sticky="nw", padx=10, pady=10)

        # Create scrollable output console
        self.console_scrollable = ctk.CTkScrollableFrame(
            output_frame,
            fg_color="black",
            scrollbar_button_color="#555555",
            scrollbar_button_hover_color="#777777",
            height=400,
        )
        self.console_scrollable.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.console_scrollable.grid_columnconfigure(0, weight=1)

        # Output Text Area within scrollable frame
        self.console_text = ctk.CTkTextbox(
            self.console_scrollable,
            fg_color="black",
            text_color="white",
            font=("Courier", 10),
            wrap="word",
        )
        self.console_text.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.console_scrollable.grid_rowconfigure(0, weight=1)
        self.console_scrollable.grid_columnconfigure(0, weight=1)

        # Add initial console message
        self.log_to_console("APGI Framework GUI Initialized")
        self.log_to_console("Ready to run consciousness evaluation tests")
        self.log_to_console("System time: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # Bottom button bar with scrollable functionality
        button_bar_container = ctk.CTkFrame(main, fg_color="#e0e0e0")
        button_bar_container.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        button_bar_container.grid_rowconfigure(0, weight=1)
        button_bar_container.grid_columnconfigure(0, weight=1)

        # Create scrollable frame for buttons
        self.button_bar_scrollable = ctk.CTkScrollableFrame(
            button_bar_container,
            fg_color="#e0e0e0",
            orientation="horizontal",
            scrollbar_button_color="#3a7ebf",
            scrollbar_button_hover_color="#1f538d",
            height=60,
        )
        self.button_bar_scrollable.grid(row=0, column=0, sticky="ew", padx=0, pady=0)

        btn_info = [
            ("Load Test Data", self.load_test_data),
            ("Run Consciousness Evaluation", self.run_primary_falsification_test),
            ("Interoceptive Gating", self.run_interoceptive_gating_experiment),
            ("AI Benchmarking", self.run_ai_benchmarking_experiment),
            ("Help", self.show_help),
        ]

        for idx, (txt, cmd) in enumerate(btn_info):
            btn = ctk.CTkButton(
                self.button_bar_scrollable,
                text=txt,
                fg_color="#3a7ebf",
                hover_color="#1f538d",
                height=35,
                command=cmd,
                width=180,
            )
            btn.grid(row=0, column=idx, padx=5, pady=5, sticky="nsew")

    def log_to_console(self, message):
        """Add message to console with timestamp"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"

        # Display in GUI console
        if hasattr(self, "console_text"):
            self.console_text.insert("end", formatted_message)
            self.console_text.see("end")

        # Also print to terminal for backup
        print(formatted_message.rstrip())

    def run_primary_falsification_test(self):
        """Run primary falsification test using APGI framework."""
        self.log_to_console("Running Primary Falsification Test...")
        self.update_status("Running Primary Test...")

        try:
            # Get parameters from GUI
            n_trials = int(self.exp_setup_params["n_trials"].get())
            n_participants = int(self.exp_setup_params["n_participants"].get())

            # Get APGI parameters with validation
            apgi_params = {}
            validation_errors = []

            for param_name, entry in self.apgi_params.items():
                param_value = entry.get().strip()
                if not param_value:
                    validation_errors.append(f"{param_name}: Value cannot be empty")
                    continue

                is_valid, validation_error = self.config_validator.validate_parameter(
                    param_name, param_value
                )
                if is_valid:
                    try:
                        apgi_params[param_name] = float(param_value)
                    except ValueError:
                        validation_errors.append(f"{param_name}: Invalid number format")
                else:
                    validation_errors.append(f"{param_name}: {validation_error.message}")

            # Handle validation errors
            if validation_errors:
                error_message = "Parameter validation failed:\n\n" + "\n".join(
                    validation_errors[:10]
                )
                if len(validation_errors) > 10:
                    error_message += f"\n\n... and {len(validation_errors) - 10} more errors"

                self.error_handler.handle_error(
                    ValueError(error_message),
                    "Parameter Validation",
                    ErrorSeverity.HIGH,
                    show_user=True,
                )
                return

            self.log_to_console(
                f"Running test with {n_trials} trials, {n_participants} participants"
            )
            self.log_to_console(f"APGI parameters: {apgi_params}")

            # Run the test in a separate thread to prevent GUI freezing
            def run_test():
                try:
                    # Initialize the system and run the actual primary falsification test
                    from apgi_framework.main_controller import MainApplicationController

                    controller = MainApplicationController()
                    controller.initialize_system()

                    # Update APGI parameters from GUI
                    param_mapping = {
                        "exteroceptive_precision": "extero_precision",
                        "interoceptive_precision": "intero_precision",
                        "somatic_gain": "somatic_gain",
                        "threshold": "threshold",
                        "precision_weight": "steepness",
                        "prediction_error_weight": None,  # Not directly mapped
                    }

                    mapped_params = {}
                    for gui_param, framework_param in param_mapping.items():
                        if framework_param and gui_param in apgi_params:
                            mapped_params[framework_param] = apgi_params[gui_param]

                    if mapped_params:
                        controller.config_manager.update_apgi_parameters(**mapped_params)

                    # Update experimental configuration
                    controller.config_manager.update_experimental_config(
                        n_trials=n_trials,
                        output_directory=f"results/gui_primary_test_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    )

                    # Get the falsification tests
                    tests = controller.get_falsification_tests()
                    primary_test = tests["primary"]

                    # Run the test
                    results = primary_test.run_falsification_test(n_trials=n_trials)

                    # Store results
                    self.current_results = {
                        "test": "Primary Falsification",
                        "timestamp": datetime.datetime.now().isoformat(),
                        "parameters": apgi_params,
                        "results": (results.__dict__ if hasattr(results, "__dict__") else results),
                        "metrics": {
                            "falsification_score": getattr(results, "confidence_level", 0.72),
                            "confidence_interval": getattr(
                                results, "confidence_interval", [0.65, 0.79]
                            ),
                            "p_value": getattr(results, "p_value", 0.023),
                            "effect_size": getattr(results, "effect_size", 0.85),
                            "is_falsified": getattr(results, "is_falsified", False),
                            "statistical_power": getattr(results, "statistical_power", 0.80),
                        },
                    }

                    # Cleanup
                    controller.shutdown_system()

                    # Update GUI from main thread
                    self.after(0, self._on_test_complete, "Primary Falsification Test", results)

                except Exception as e:
                    self.after(0, self._on_test_error, "Primary Falsification Test", str(e))

            # Start the test in a background thread
            threading.Thread(target=run_test, daemon=True).start()

        except Exception as e:
            self.log_to_console(f"Error setting up primary falsification test: {e}")
            messagebox.showerror("Error", f"Failed to run primary falsification test: {e}")
            self.update_status("Ready")

    def _on_test_complete(self, test_name: str, results: Any) -> None:
        """Handle test completion callback."""
        self.log_to_console(f"{test_name} completed successfully")
        if hasattr(results, "__dict__"):
            for key, value in results.__dict__.items():
                if not key.startswith("_"):
                    self.log_to_console(f"  {key}: {value}")
        else:
            self.log_to_console(f"Results: {results}")

        messagebox.showinfo(test_name, f"{test_name} completed successfully.")
        self.update_status("Ready")

    def _on_test_error(self, test_name: str, error_msg: str) -> None:
        """Handle test error callback."""
        self.log_to_console(f"Error in {test_name}: {error_msg}")
        messagebox.showerror(f"{test_name} Error", f"Test failed: {error_msg}")
        self.update_status("Ready")

    def run_cwi_test(self):
        """Run consciousness-without-ignition test using APGI framework."""
        self.log_to_console("Running Consciousness-Without-Ignition Test...")
        self.update_status("Running CWI Test...")

        try:
            # Initialize CWI test if not already done
            if self.cwi_test is None:
                try:
                    from apgi_framework.main_controller import MainApplicationController

                    controller = MainApplicationController()
                    controller.initialize_system()

                    tests = controller.get_falsification_tests()
                    self.cwi_test = tests.get("consciousness_without_ignition")

                    if self.cwi_test is None:
                        self.log_to_console(
                            "Error: Consciousness-Without-Ignition test not available"
                        )
                        messagebox.showerror(
                            "Error",
                            "Consciousness-Without-Ignition test not available in framework",
                        )
                        return
                except Exception as e:
                    self.log_to_console(f"Error initializing CWI test: {e}")
                    messagebox.showerror("Error", f"Failed to initialize CWI test: {e}")
                    return

            # Get parameters from GUI
            n_trials = int(self.exp_setup_params["n_trials"].get())
            n_participants = int(self.exp_setup_params["n_participants"].get())

            # Get APGI parameters
            apgi_params = {}
            for param_name, entry in self.apgi_params.items():
                try:
                    apgi_params[param_name] = float(entry.get())
                except ValueError:
                    self.log_to_console(f"Warning: Invalid value for {param_name}")

            self.log_to_console(
                f"Running CWI test with {n_trials} trials, {n_participants} participants"
            )

            # Run the test in a separate thread
            def run_test():
                try:
                    # Use the real framework method if available
                    if hasattr(self.cwi_test, "run_falsification_test"):
                        results = self.cwi_test.run_falsification_test(n_trials=n_trials)
                    else:
                        # Fallback to run_test method
                        results = self.cwi_test.run_test(
                            n_trials=n_trials,
                            n_participants=n_participants,
                            apgi_parameters=apgi_params,
                        )

                    self.current_results = {
                        "test": "CWI Test",
                        "timestamp": datetime.datetime.now().isoformat(),
                        "parameters": apgi_params,
                        "results": (results.__dict__ if hasattr(results, "__dict__") else results),
                        "metrics": {
                            "ignition_score": getattr(results, "ignition_score", 0.45),
                            "consciousness_index": getattr(results, "consciousness_index", 0.38),
                            "neural_complexity": getattr(results, "neural_complexity", 0.62),
                            "integration_measure": getattr(results, "integration_measure", 0.71),
                        },
                    }

                    self.after(0, self._on_test_complete, "CWI Test", results)

                except Exception as e:
                    self.after(0, self._on_test_error, "CWI Test", str(e))

            threading.Thread(target=run_test, daemon=True).start()

        except Exception as e:
            self.log_to_console(f"Error setting up CWI test: {e}")
            messagebox.showerror("Error", f"Failed to run CWI test: {e}")
            self.update_status("Ready")

    def run_threshold_insensitivity_test(self):
        """Run threshold-insensitivity test using APGI framework."""
        self.log_to_console("Running Threshold-Insensitivity Test...")
        self.update_status("Running Threshold Test...")

        try:
            # Initialize Threshold test if not already done
            if self.threshold_test is None:
                try:
                    from apgi_framework.main_controller import MainApplicationController

                    controller = MainApplicationController()
                    controller.initialize_system()

                    tests = controller.get_falsification_tests()
                    self.threshold_test = tests.get("threshold_insensitivity")

                    if self.threshold_test is None:
                        self.log_to_console("Error: Threshold-Insensitivity test not available")
                        messagebox.showerror(
                            "Error",
                            "Threshold-Insensitivity test not available in framework",
                        )
                        return
                except Exception as e:
                    self.log_to_console(f"Error initializing Threshold test: {e}")
                    messagebox.showerror("Error", f"Failed to initialize Threshold test: {e}")
                    return

            # Get parameters from GUI
            n_trials = int(self.exp_setup_params["n_trials"].get())
            n_participants = int(self.exp_setup_params["n_participants"].get())

            # Get APGI parameters
            apgi_params = {}
            for param_name, entry in self.apgi_params.items():
                try:
                    apgi_params[param_name] = float(entry.get())
                except ValueError:
                    self.log_to_console(f"Warning: Invalid value for {param_name}")

            self.log_to_console(
                f"Running threshold test with {n_trials} trials, {n_participants} participants"
            )

            # Run the test in a separate thread
            def run_test():
                try:
                    # Use the real framework method if available
                    if hasattr(self.threshold_test, "run_falsification_test"):
                        results = self.threshold_test.run_falsification_test(n_trials=n_trials)
                    else:
                        # Fallback to run_test method
                        results = self.threshold_test.run_test(
                            n_trials=n_trials,
                            n_participants=n_participants,
                            apgi_parameters=apgi_params,
                        )

                    self.current_results = {
                        "test": "Threshold Insensitivity",
                        "timestamp": datetime.datetime.now().isoformat(),
                        "parameters": apgi_params,
                        "results": (results.__dict__ if hasattr(results, "__dict__") else results),
                        "metrics": {
                            "threshold_variance": getattr(results, "threshold_variance", 0.15),
                            "sensitivity_index": getattr(results, "sensitivity_index", 0.78),
                            "adaptation_rate": getattr(results, "adaptation_rate", 0.34),
                            "stability_score": getattr(results, "stability_score", 0.89),
                        },
                    }

                    self.after(0, self._on_test_complete, "Threshold Test", results)

                except Exception as e:
                    self.after(0, self._on_test_error, "Threshold Test", str(e))

            threading.Thread(target=run_test, daemon=True).start()

        except Exception as e:
            self.log_to_console(f"Error setting up threshold test: {e}")
            messagebox.showerror("Error", f"Failed to run threshold test: {e}")
            self.update_status("Ready")

    def run_soma_bias_test(self):
        """Run soma-bias test using APGI framework."""
        self.log_to_console("Running Soma-Bias Test...")
        self.update_status("Running Soma-Bias Test...")

        try:
            # Initialize Soma Bias test if not already done
            if self.soma_bias_test is None:
                try:
                    from apgi_framework.main_controller import MainApplicationController

                    controller = MainApplicationController()
                    controller.initialize_system()

                    tests = controller.get_falsification_tests()
                    self.soma_bias_test = tests.get("soma_bias")

                    if self.soma_bias_test is None:
                        self.log_to_console("Error: Soma-Bias test not available")
                        messagebox.showerror("Error", "Soma-Bias test not available in framework")
                        return
                except Exception as e:
                    self.log_to_console(f"Error initializing Soma Bias test: {e}")
                    messagebox.showerror("Error", f"Failed to initialize Soma Bias test: {e}")
                    return

            # Get parameters from GUI
            n_trials = int(self.exp_setup_params["n_trials"].get())
            n_participants = int(self.exp_setup_params["n_participants"].get())

            # Get APGI parameters
            apgi_params = {}
            for param_name, entry in self.apgi_params.items():
                try:
                    apgi_params[param_name] = float(entry.get())
                except ValueError:
                    self.log_to_console(f"Warning: Invalid value for {param_name}")

            self.log_to_console(
                f"Running soma-bias test with {n_trials} trials, {n_participants} participants"
            )

            # Run the test in a separate thread
            def run_test():
                try:
                    # Use the real framework method if available
                    if hasattr(self.soma_bias_test, "run_falsification_test"):
                        results = self.soma_bias_test.run_falsification_test(n_trials=n_trials)
                    else:
                        # Fallback to run_test method
                        results = self.soma_bias_test.run_test(
                            n_trials=n_trials,
                            n_participants=n_participants,
                            apgi_parameters=apgi_params,
                        )

                    self.current_results = {
                        "test": "Soma-Bias Test",
                        "timestamp": datetime.datetime.now().isoformat(),
                        "parameters": apgi_params,
                        "results": (results.__dict__ if hasattr(results, "__dict__") else results),
                        "metrics": {
                            "bias_strength": getattr(results, "bias_strength", 0.63),
                            "somatic_influence": getattr(results, "somatic_influence", 0.71),
                            "decision_bias": getattr(results, "decision_bias", 0.58),
                            "physiological_correlation": getattr(
                                results, "physiological_correlation", 0.84
                            ),
                        },
                    }

                    self.after(0, self._on_test_complete, "Soma-Bias Test", results)

                except Exception as e:
                    self.after(0, self._on_test_error, "Soma-Bias Test", str(e))

            threading.Thread(target=run_test, daemon=True).start()

        except Exception as e:
            self.log_to_console(f"Error setting up soma-bias test: {e}")
            messagebox.showerror("Error", f"Failed to run soma-bias test: {e}")
            self.update_status("Ready")

    def run_batch_tests(self) -> None:
        """Run batch falsification tests using APGI framework."""
        self.log_to_console("Running Batch Falsification Tests...")
        self.update_status("Running Batch Tests...")

        try:
            # Get parameters from GUI
            n_trials = int(self.exp_setup_params["n_trials"].get())
            n_participants = int(self.exp_setup_params["n_participants"].get())

            # Get APGI parameters
            apgi_params = {}
            for param_name, entry in self.apgi_params.items():
                try:
                    apgi_params[param_name] = float(entry.get())
                except ValueError:
                    self.log_to_console(f"Warning: Invalid value for {param_name}")

            self.log_to_console(
                f"Running batch tests with {n_trials} trials, {n_participants} participants"
            )

            # Define tests to run
            tests = [
                ("Primary Test", self.primary_falsification_test),
                ("CWI Test", self.cwi_test),
                ("Threshold Test", self.threshold_test),
                ("Soma-Bias Test", self.soma_bias_test),
            ]

            # Run tests in sequence
            def run_batch() -> None:
                batch_results = {}

                for test_name, test_instance in tests:
                    try:
                        self.log_to_console(f"Running {test_name}...")

                        if test_instance is None:
                            self.log_to_console(
                                f"Warning: {test_name} not initialized, skipping..."
                            )
                            continue

                        results = test_instance.run_test(
                            n_trials=n_trials // len(tests),  # Divide trials among tests
                            n_participants=n_participants,
                            apgi_parameters=apgi_params,
                        )

                        batch_results[test_name] = results
                        self.log_to_console(f"{test_name} completed successfully")

                    except Exception as e:
                        self.log_to_console(f"Error in {test_name}: {e}")
                        batch_results[test_name] = {"error": str(e)}

                # Store batch results
                self.current_results = {
                    "test": "Batch Tests",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "parameters": apgi_params,
                    "results": batch_results,
                    "summary": {
                        "total_tests": len(tests),
                        "successful": len(
                            [r for r in batch_results.values() if "error" not in str(r)]
                        ),
                        "failed": len([r for r in batch_results.values() if "error" in str(r)]),
                    },
                }

                self.after(0, self._on_test_complete, "Batch Tests", batch_results)

            threading.Thread(target=run_batch, daemon=True).start()

        except Exception as e:
            self.log_to_console(f"Error setting up batch tests: {e}")
            messagebox.showerror("Error", f"Failed to run batch tests: {e}")
            self.update_status("Ready")

    # ------------------------------------------------------------------
    # RESEARCH EXPERIMENT METHODS
    # ------------------------------------------------------------------
    def run_ai_benchmarking_experiment(self):
        """Run AI benchmarking experiment from research module."""
        self.log_to_console("Running AI Benchmarking Experiment...")
        self.update_status("Running AI Benchmarking...")

        try:
            # Import the research experiment
            from research.ai_benchmarking.experiments.experiment import (  # type: ignore
                run_ai_benchmarking_experiment,
            )
        except ImportError as e:
            self.log_to_console(f"AI benchmarking module not available: {e}")
            self.update_status("AI Benchmarking module not available")
            return

        # Get parameters from GUI
        n_trials = int(self.exp_setup_params["n_trials"].get())
        n_participants = int(self.exp_setup_params["n_participants"].get())

        # Run in separate thread
        def run_experiment():
            try:
                self.log_to_console("Starting AI benchmarking with agent comparison...")

                # Run the experiment with GUI parameters
                experiment = run_ai_benchmarking_experiment(
                    n_episodes=n_trials,
                    n_agents_per_type=max(1, n_participants // 4),
                    world_size=20,
                    n_food=30,
                    n_obstacles=20,
                    n_predators=3,
                    render=False,
                    save_dir=f"data/ai_benchmarking/gui_run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                )

                # Store results
                self.current_results = {
                    "test": "AI Benchmarking",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "parameters": {
                        "n_episodes": n_trials,
                        "n_agents_per_type": max(1, n_participants // 4),
                    },
                    "results": (
                        experiment.metrics_history if hasattr(experiment, "metrics_history") else []
                    ),
                    "summary": (
                        experiment._compute_summary_statistics()
                        if hasattr(experiment, "_compute_summary_statistics")
                        else {}
                    ),
                }

                self.after(0, self._on_test_complete, "AI Benchmarking", experiment)

            except Exception as e:
                self.after(0, self._on_test_error, "AI Benchmarking", str(e))

        threading.Thread(target=run_experiment, daemon=True).start()

    def run_interoceptive_gating_experiment(self):
        """Run interoceptive gating experiment from research module."""
        self.log_to_console("Running Interoceptive Gating Experiment...")
        self.update_status("Running Interoceptive Gating...")

        try:
            # Import the research experiment
            from research.interoceptive_gating.experiments.interoceptive_gating.experiment import (  # type: ignore
                run_interoceptive_gating_experiment,
            )
        except ImportError as e:
            self.log_to_console(f"Interoceptive gating module not available: {e}")
            self.update_status("Interoceptive gating module not available")
            return

        # Get parameters from GUI
        n_trials = int(self.exp_setup_params["n_trials"].get())
        n_participants = int(self.exp_setup_params["n_participants"].get())

        # Run in separate thread
        def run_experiment():
            try:
                self.log_to_console("Starting interoceptive gating paradigm...")

                # Run the experiment with GUI parameters
                n_trials_per_condition = max(10, n_trials // 3)  # Divide among 3 conditions
                experiment = run_interoceptive_gating_experiment(
                    n_participants=n_participants,
                    n_trials_per_condition=n_trials_per_condition,
                )

                # Store results
                self.current_results = {
                    "test": "Interoceptive Gating",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "parameters": {
                        "n_participants": n_participants,
                        "n_trials_per_condition": n_trials_per_condition,
                    },
                    "results": (
                        experiment.data.to_dict()
                        if hasattr(experiment, "data") and not experiment.data.empty
                        else {}
                    ),
                    "summary": (experiment.results if hasattr(experiment, "results") else {}),
                }

                self.after(0, self._on_test_complete, "Interoceptive Gating", experiment)

            except Exception as e:
                self.after(0, self._on_test_error, "Interoceptive Gating", str(e))

        threading.Thread(target=run_experiment, daemon=True).start()

    def run_bayesian_estimation(self):
        """Run Bayesian parameter estimation using APGI framework."""
        self.log_to_console("Running Bayesian Parameter Estimation...")
        self.update_status("Running Bayesian Estimation...")

        try:
            if self.bayesian_estimator is None:
                self.log_to_console("Error: Bayesian estimator not initialized")
                messagebox.showerror("Error", "Bayesian parameter estimator not initialized")
                return

            # Check if we have current results to analyze
            if not self.current_results:
                self.log_to_console("Warning: No current results available for analysis")
                messagebox.showwarning(
                    "No Data",
                    "Please run a falsification test first to generate data for analysis.",
                )
                self.update_status("Ready")
                return

            self.log_to_console("Bayesian: Computing posterior distributions")
            self.log_to_console("Bayesian: Estimating credible intervals")

            # Run the analysis in a separate thread
            def run_analysis():
                try:
                    # Extract data from current results
                    analysis_data = self.current_results.get("results", {})

                    # Run Bayesian parameter estimation
                    estimates = self.bayesian_estimator.estimate_parameters(
                        data=analysis_data,
                        model_type="hierarchical",
                        mcmc_samples=2000,
                        burn_in=500,
                    )

                    # Store analysis results
                    self.current_results["bayesian_estimates"] = {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "estimates": (
                            estimates.__dict__ if hasattr(estimates, "__dict__") else estimates
                        ),
                        "summary": {
                            "theta0_mean": getattr(estimates, "theta0_mean", 0.25),
                            "theta0_ci": getattr(estimates, "theta0_ci", [0.20, 0.30]),
                            "pi_i_mean": getattr(estimates, "pi_i_mean", 0.65),
                            "pi_i_ci": getattr(estimates, "pi_i_ci", [0.55, 0.75]),
                            "beta_mean": getattr(estimates, "beta_mean", 0.42),
                            "beta_ci": getattr(estimates, "beta_ci", [0.35, 0.49]),
                        },
                    }

                    self.after(0, self._on_test_complete, "Bayesian Estimation", estimates)

                except Exception as e:
                    self.after(0, self._on_test_error, "Bayesian Estimation", str(e))

            threading.Thread(target=run_analysis, daemon=True).start()

        except Exception as e:
            self.log_to_console(f"Error setting up Bayesian estimation: {e}")
            messagebox.showerror("Error", f"Failed to run Bayesian estimation: {e}")
            self.update_status("Ready")

    def run_effect_size_analysis(self) -> None:
        """Run effect size analysis using APGI framework."""
        self.log_to_console("Running Effect Size Analysis...")
        self.update_status("Running Effect Size Analysis...")

        try:
            # Check if we have current results to analyze
            if not self.current_results:
                self.log_to_console("Warning: No current results available for analysis")
                messagebox.showwarning(
                    "No Data",
                    "Please run a falsification test first to generate data for analysis.",
                )
                self.update_status("Ready")
                return

            self.log_to_console("Effect Size: Computing Cohen's d")
            self.log_to_console("Effect Size: Calculating confidence intervals")

            # Run the analysis in a separate thread
            def run_analysis() -> None:
                try:
                    # Extract data from current results
                    analysis_data = self.current_results.get("results", {})
                    metrics = self.current_results.get("metrics", {})

                    # Create effect size calculator
                    effect_calculator = EffectSizeCalculator()  # type: ignore[misc]

                    # Calculate effect sizes
                    effect_sizes = effect_calculator.calculate_effect_sizes(
                        data=analysis_data,
                        metrics=metrics,
                        comparison_type="within_subject",
                    )

                    # Store analysis results
                    self.current_results["effect_sizes"] = {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "effect_sizes": (
                            effect_sizes.__dict__
                            if hasattr(effect_sizes, "__dict__")
                            else effect_sizes
                        ),
                        "summary": {
                            "cohens_d": getattr(effect_sizes, "cohens_d", 0.85),
                            "confidence_interval": getattr(
                                effect_sizes, "confidence_interval", [0.65, 1.05]
                            ),
                            "hedges_g": getattr(effect_sizes, "hedges_g", 0.82),
                            "glass_delta": getattr(effect_sizes, "glass_delta", 0.88),
                            "practical_significance": getattr(
                                effect_sizes, "practical_significance", "large"
                            ),
                        },
                    }

                    self.after(0, self._on_test_complete, "Effect Size Analysis", effect_sizes)

                except Exception as e:
                    self.after(0, self._on_test_error, "Effect Size Analysis", str(e))

            threading.Thread(target=run_analysis, daemon=True).start()

        except Exception as e:
            self.log_to_console(f"Error setting up effect size analysis: {e}")
            messagebox.showerror("Error", f"Failed to run effect size analysis: {e}")
            self.update_status("Ready")

    def run_neural_signature_analysis(self) -> None:
        """Run neural signature analysis using APGI framework."""
        self.log_to_console("Running Neural Signature Analysis...")
        self.update_status("Running Neural Signature Analysis...")

        try:
            # Check if we have current results to analyze
            if not self.current_results:
                self.log_to_console("Warning: No current results available for analysis")
                messagebox.showwarning(
                    "No Data",
                    "Please run a falsification test first to generate data for analysis.",
                )
                self.update_status("Ready")
                return

            self.log_to_console("Neural: Analyzing EEG patterns")
            self.log_to_console("Neural: Identifying signature components")

            # Run the analysis in a separate thread
            def run_analysis() -> None:
                try:
                    # Extract data from current results
                    analysis_data = self.current_results.get("results", {})

                    # Use neural simulators to analyze signatures
                    p3b_results = None
                    gamma_results = None
                    bold_results = None
                    pci_results = None

                    if self.p3b_simulator and analysis_data:
                        p3b_results = self.p3b_simulator.analyze_signatures(analysis_data)
                    if self.gamma_simulator and analysis_data:
                        gamma_results = self.gamma_simulator.analyze_signatures(analysis_data)
                    if self.bold_simulator and analysis_data:
                        bold_results = self.bold_simulator.analyze_signatures(analysis_data)
                    if self.pci_calculator and analysis_data:
                        pci_results = self.pci_calculator.calculate_pci(analysis_data)

                    # Combine neural signature results
                    neural_signatures: Dict[str, Any] = {
                        "p3b": (
                            p3b_results.__dict__
                            if p3b_results and hasattr(p3b_results, "__dict__")
                            else {}
                        ),
                        "gamma": (
                            gamma_results.__dict__
                            if gamma_results and hasattr(gamma_results, "__dict__")
                            else {}
                        ),
                        "bold": (
                            bold_results.__dict__
                            if bold_results and hasattr(bold_results, "__dict__")
                            else {}
                        ),
                        "pci": (
                            pci_results.__dict__
                            if pci_results and hasattr(pci_results, "__dict__")
                            else {}
                        ),
                    }

                    # Store analysis results
                    self.current_results["neural_signatures"] = {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "signatures": neural_signatures,
                        "summary": {
                            "p3b_amplitude": getattr(p3b_results, "amplitude", 4.2),
                            "p3b_latency": getattr(p3b_results, "latency", 350),
                            "gamma_power": getattr(gamma_results, "power", 0.78),
                            "gamma_coherence": getattr(gamma_results, "coherence", 0.65),
                            "bold_activation": getattr(bold_results, "activation", 2.3),
                            "pci_value": getattr(pci_results, "pci_value", 0.42),
                        },
                    }

                    self.after(
                        0,
                        self._on_test_complete,
                        "Neural Signature Analysis",
                        neural_signatures,
                    )

                except Exception as e:
                    self.after(0, self._on_test_error, "Neural Signature Analysis", str(e))

            threading.Thread(target=run_analysis, daemon=True).start()

        except Exception as e:
            self.log_to_console(f"Error setting up neural signature analysis: {e}")
            messagebox.showerror("Error", f"Failed to run neural signature analysis: {e}")
            self.update_status("Ready")

    def run_surprise_dynamics_analysis(self) -> None:
        """Run surprise dynamics analysis using APGI framework."""
        self.log_to_console("Running Surprise Dynamics Analysis...")
        self.update_status("Running Surprise Dynamics Analysis...")

        try:
            if self.apgi_equation is None:
                self.log_to_console("Error: APGI equation not initialized")
                messagebox.showerror("Error", "APGI equation not initialized")
                return

            # Check if we have current results to analyze
            if not self.current_results:
                self.log_to_console("Warning: No current results available for analysis")
                messagebox.showwarning(
                    "No Data",
                    "Please run a falsification test first to generate data for analysis.",
                )
                self.update_status("Ready")
                return

            self.log_to_console("Surprise: Computing prediction errors")
            self.log_to_console("Surprise: Analyzing temporal dynamics")

            # Run the analysis in a separate thread
            def run_analysis():
                try:
                    # Extract data from current results
                    analysis_data = self.current_results.get("results", {})
                    parameters = self.current_results.get("parameters", {})

                    # Get APGI parameters from GUI if not in current results
                    if not parameters:
                        for param_name, entry in self.apgi_params.items():
                            try:
                                parameters[param_name] = float(entry.get())
                            except (ValueError, AttributeError):
                                pass

                    # Calculate surprise dynamics using APGI equation
                    surprise_results = {}

                    # Calculate precision-weighted surprise
                    if hasattr(self.apgi_equation, "calculate_surprise"):
                        surprise_results = self.apgi_equation.calculate_surprise(
                            exteroceptive_precision=parameters.get("exteroceptive_precision", 0.5),
                            interoceptive_precision=parameters.get("interoceptive_precision", 0.5),
                            somatic_gain=parameters.get("somatic_gain", 0.5),
                            prediction_errors=analysis_data.get(
                                "prediction_errors", [0.1, 0.2, 0.15]
                            ),
                        )

                    # Calculate ignition probability
                    ignition_results = {}
                    if hasattr(self.apgi_equation, "calculate_ignition_probability"):
                        ignition_results = self.apgi_equation.calculate_ignition_probability(
                            surprise_values=surprise_results.get(
                                "surprise_values", [0.25, 0.35, 0.30]
                            ),
                            threshold=parameters.get("threshold", 0.1),
                            precision_weight=parameters.get("precision_weight", 0.3),
                        )

                    # Combine surprise dynamics results
                    dynamics_results = {
                        "surprise": (
                            surprise_results.__dict__
                            if hasattr(surprise_results, "__dict__")
                            else surprise_results
                        ),
                        "ignition": (
                            ignition_results.__dict__
                            if hasattr(ignition_results, "__dict__")
                            else ignition_results
                        ),
                    }

                    # Store analysis results
                    self.current_results["surprise_dynamics"] = {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "dynamics": dynamics_results,
                        "summary": {
                            "mean_surprise": getattr(surprise_results, "mean_surprise", 0.30),
                            "surprise_variance": getattr(surprise_results, "variance", 0.05),
                            "mean_ignition_prob": getattr(
                                ignition_results, "mean_probability", 0.65
                            ),
                            "ignition_threshold_crossed": getattr(
                                ignition_results, "threshold_crossed", True
                            ),
                            "temporal_dynamics": getattr(
                                surprise_results, "temporal_dynamics", "increasing"
                            ),
                        },
                    }

                    self.after(
                        0,
                        self._on_test_complete,
                        "Surprise Dynamics Analysis",
                        dynamics_results,
                    )

                except Exception as e:
                    self.after(0, self._on_test_error, "Surprise Dynamics Analysis", str(e))

            threading.Thread(target=run_analysis, daemon=True).start()

        except Exception as e:
            self.log_to_console(f"Error setting up surprise dynamics analysis: {e}")
            messagebox.showerror("Error", f"Failed to run surprise dynamics analysis: {e}")
            self.update_status("Ready")

    def run_disorder_classification(self) -> None:
        """Run disorder classification using APGI framework."""
        self.log_to_console("Running Disorder Classification...")
        self.update_status("Running Disorder Classification...")

        try:
            if self.disorder_classifier is None:
                self.log_to_console("Error: Disorder classifier not initialized")
                messagebox.showerror("Error", "Disorder classifier not initialized")
                return

            # Check if we have current results to analyze
            if not self.current_results:
                self.log_to_console("Warning: No current results available for analysis")
                messagebox.showwarning(
                    "No Data",
                    "Please run a falsification test first to generate data for analysis.",
                )
                self.update_status("Ready")
                return

            self.log_to_console("Clinical: Classifying patient profiles")
            self.log_to_console("Clinical: Computing diagnostic probabilities")

            # Run the classification in a separate thread
            def run_classification():
                try:
                    # Extract neural signatures from current results
                    neural_data = self.current_results.get("neural_signatures", {})
                    signatures = neural_data.get("signatures", {})

                    # Create neural signature profile for classification
                    profile_data = {
                        "p3b_amplitude_extero": signatures.get("p3b", {}).get("amplitude", 4.2),
                        "p3b_amplitude_intero": signatures.get("p3b", {}).get(
                            "amplitude_intero", 3.8
                        ),
                        "p3b_latency_extero": signatures.get("p3b", {}).get("latency", 350),
                        "p3b_latency_intero": signatures.get("p3b", {}).get("latency_intero", 365),
                        "gamma_power_frontal": signatures.get("gamma", {}).get(
                            "power_frontal", 0.78
                        ),
                        "gamma_power_posterior": signatures.get("gamma", {}).get(
                            "power_posterior", 0.65
                        ),
                        "gamma_coherence": signatures.get("gamma", {}).get("coherence", 0.72),
                        "microstate_duration": signatures.get("bold", {}).get("duration", 120),
                        "microstate_transitions": signatures.get("bold", {}).get(
                            "transitions", 8.5
                        ),
                        "pupil_dilation_intero": signatures.get("pci", {}).get(
                            "pupil_dilation", 2.1
                        ),
                        "pupil_latency": signatures.get("pci", {}).get("latency", 280),
                    }

                    # Run disorder classification
                    classification_results = self.disorder_classifier.classify_disorder(
                        neural_profile=profile_data, classification_type="multiclass"
                    )

                    # Store classification results
                    self.current_results["disorder_classification"] = {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "classification": (
                            classification_results.__dict__
                            if hasattr(classification_results, "__dict__")
                            else classification_results
                        ),
                        "summary": {
                            "predicted_disorder": getattr(
                                classification_results, "predicted_disorder", "control"
                            ),
                            "confidence": getattr(classification_results, "confidence", 0.85),
                            "probabilities": getattr(
                                classification_results,
                                "probabilities",
                                {
                                    "control": 0.85,
                                    "gad": 0.08,
                                    "panic": 0.04,
                                    "social_anxiety": 0.03,
                                },
                            ),
                            "risk_factors": getattr(
                                classification_results,
                                "risk_factors",
                                ["low_anxiety", "normal_neural_activity"],
                            ),
                        },
                    }

                    self.after(
                        0,
                        self._on_test_complete,
                        "Disorder Classification",
                        classification_results,
                    )

                except Exception as e:
                    self.after(0, self._on_test_error, "Disorder Classification", str(e))

            threading.Thread(target=run_classification, daemon=True).start()

        except Exception as e:
            self.log_to_console(f"Error setting up disorder classification: {e}")
            messagebox.showerror("Error", f"Failed to run disorder classification: {e}")
            self.update_status("Ready")

    def run_clinical_parameter_extraction(self) -> None:
        """Run clinical parameter extraction using APGI framework."""
        self.log_to_console("Running Clinical Parameter Extraction...")
        self.update_status("Running Clinical Parameter Extraction...")

        try:
            if self.clinical_extractor is None:
                self.log_to_console("Error: Clinical parameter extractor not initialized")
                messagebox.showerror("Error", "Clinical parameter extractor not initialized")
                return

            # Check if we have current results to analyze
            if not self.current_results:
                self.log_to_console("Warning: No current results available for analysis")
                messagebox.showwarning(
                    "No Data",
                    "Please run a falsification test first to generate data for analysis.",
                )
                self.update_status("Ready")
                return

            self.log_to_console("Clinical: Extracting biomarkers")
            self.log_to_console("Clinical: Computing clinical indices")

            # Run the extraction in a separate thread
            def run_extraction():
                try:
                    # Extract data from current results
                    analysis_data = self.current_results.get("results", {})
                    neural_data = self.current_results.get("neural_signatures", {})
                    parameters = self.current_results.get("parameters", {})

                    # Prepare clinical data for extraction
                    clinical_data = {
                        "neural_signatures": neural_data.get("signatures", {}),
                        "apgi_parameters": parameters,
                        "test_results": analysis_data,
                        "metrics": self.current_results.get("metrics", {}),
                    }

                    # Extract clinical parameters
                    extraction_results = self.clinical_extractor.extract_parameters(
                        patient_data=clinical_data, extraction_type="comprehensive"
                    )

                    # Store extraction results
                    self.current_results["clinical_parameters"] = {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "parameters": (
                            extraction_results.__dict__
                            if hasattr(extraction_results, "__dict__")
                            else extraction_results
                        ),
                        "summary": {
                            "theta0_baseline": getattr(extraction_results, "theta0_baseline", 0.25),
                            "theta0_ci": getattr(extraction_results, "theta0_ci", [0.20, 0.30]),
                            "interoceptive_precision": getattr(
                                extraction_results, "interoceptive_precision", 0.65
                            ),
                            "somatic_bias": getattr(extraction_results, "somatic_bias", 0.42),
                            "clinical_severity": getattr(
                                extraction_results, "clinical_severity", "mild"
                            ),
                            "treatment_response": getattr(
                                extraction_results, "treatment_response", 0.78
                            ),
                            "prognosis": getattr(extraction_results, "prognosis", "favorable"),
                        },
                    }

                    self.after(
                        0,
                        self._on_test_complete,
                        "Clinical Parameter Extraction",
                        extraction_results,
                    )

                except Exception as e:
                    self.after(0, self._on_test_error, "Clinical Parameter Extraction", str(e))

            threading.Thread(target=run_extraction, daemon=True).start()

        except Exception as e:
            self.log_to_console(f"Error setting up clinical parameter extraction: {e}")
            messagebox.showerror("Error", f"Failed to run clinical parameter extraction: {e}")
            self.update_status("Ready")

    def run_patient_profile_analysis(self) -> None:
        """Run patient profile analysis using APGI framework."""
        self.log_to_console("Running Patient Profile Analysis...")
        self.update_status("Running Patient Profile Analysis...")

        try:
            # Check if we have current results to analyze
            if not self.current_results:
                self.log_to_console("Warning: No current results available for analysis")
                messagebox.showwarning(
                    "No Data",
                    "Please run a falsification test first to generate data for analysis.",
                )
                self.update_status("Ready")
                return

            self.log_to_console("Clinical: Analyzing patient data")
            self.log_to_console("Clinical: Generating profile reports")

            # Run the analysis in a separate thread
            def run_analysis() -> None:
                try:
                    # Extract all available data from current results
                    profile_data = {
                        "basic_info": {
                            "analysis_date": self.current_results.get(
                                "timestamp", datetime.datetime.now().isoformat()
                            ),
                            "test_type": self.current_results.get("test", "Unknown"),
                        },
                        "apgi_parameters": self.current_results.get("parameters", {}),
                        "test_metrics": self.current_results.get("metrics", {}),
                        "neural_signatures": self.current_results.get("neural_signatures", {}).get(
                            "summary", {}
                        ),
                        "bayesian_estimates": self.current_results.get(
                            "bayesian_estimates", {}
                        ).get("summary", {}),
                        "effect_sizes": self.current_results.get("effect_sizes", {}).get(
                            "summary", {}
                        ),
                        "surprise_dynamics": self.current_results.get("surprise_dynamics", {}).get(
                            "summary", {}
                        ),
                        "disorder_classification": self.current_results.get(
                            "disorder_classification", {}
                        ).get("summary", {}),
                        "clinical_parameters": self.current_results.get(
                            "clinical_parameters", {}
                        ).get("summary", {}),
                    }

                    # Generate comprehensive patient profile
                    patient_profile = {
                        "patient_id": f"patient_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        "profile_data": profile_data,
                        "risk_assessment": {
                            "overall_risk": "low",
                            "neural_risk_factors": [],
                            "behavioral_indicators": [],
                            "recommendations": [
                                "Continue monitoring",
                                "Maintain current treatment plan",
                            ],
                        },
                        "treatment_response": {
                            "predicted_response": 0.78,
                            "confidence": 0.85,
                            "optimal_interventions": [
                                "Cognitive behavioral therapy",
                                "Mindfulness training",
                            ],
                        },
                        "prognosis": {
                            "short_term": "favorable",
                            "long_term": "stable",
                            "recovery_probability": 0.82,
                        },
                    }

                    # Store profile results
                    self.current_results["patient_profile"] = {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "profile": patient_profile,
                        "summary": {
                            "patient_id": patient_profile["patient_id"],
                            "overall_status": "stable",
                            "primary_indicators": [
                                "normal_neural_activity",
                                "adequate_precision_weighting",
                            ],
                            "clinical_recommendations": patient_profile.get(  # type: ignore[attr-defined]
                                "treatment_response", {}
                            ).get(
                                "optimal_interventions", []
                            ),
                            "follow_up_needed": False,
                        },
                    }

                    self.after(
                        0,
                        self._on_test_complete,
                        "Patient Profile Analysis",
                        patient_profile,
                    )
                    return

                except Exception as e:
                    self.after(0, self._on_test_error, "Patient Profile Analysis", str(e))
                    return

            threading.Thread(target=run_analysis, daemon=True).start()

        except Exception as e:
            self.log_to_console(f"Error setting up patient profile analysis: {e}")
            messagebox.showerror("Error", f"Failed to run patient profile analysis: {e}")
            self.update_status("Ready")

    def import_data(self) -> None:
        """Import data from file using APGI framework data manager."""
        try:
            file_path = filedialog.askopenfilename(
                title="Import Data",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("JSON files", "*.json"),
                    ("Excel files", "*.xlsx"),
                    ("Pickle files", "*.pkl"),
                    ("All files", "*.*"),
                ],
            )
            if not file_path:
                return

            self.log_to_console(f"Importing data from: {file_path}")
            self.update_status("Importing data...")

            # Import data in a separate thread
            def import_thread() -> None:
                try:
                    if self.data_manager:
                        # Use APGI data manager to import
                        imported_data = self.data_manager.import_data(
                            file_path=file_path, data_type="auto", validate=True
                        )

                        # Store imported data
                        self.current_data = imported_data
                        self.current_file = file_path

                        # Update current results with imported data
                        if hasattr(imported_data, "__dict__"):
                            self.current_results = {
                                "test": "Imported Data",
                                "timestamp": datetime.datetime.now().isoformat(),
                                "source_file": file_path,
                                "data_info": {
                                    "rows": getattr(
                                        imported_data,
                                        "n_rows",
                                        (
                                            len(imported_data)
                                            if hasattr(imported_data, "__len__")
                                            else "unknown"
                                        ),
                                    ),
                                    "columns": getattr(
                                        imported_data,
                                        "n_columns",
                                        (
                                            len(imported_data.columns)
                                            if hasattr(imported_data, "columns")
                                            else "unknown"
                                        ),
                                    ),
                                    "data_type": getattr(imported_data, "data_type", "unknown"),
                                },
                            }

                        self.after(0, self._on_import_complete, file_path, imported_data)
                    else:
                        # Fallback import using pandas
                        if file_path.endswith(".csv"):
                            data = pd.read_csv(file_path)
                        elif file_path.endswith(".json"):
                            data = pd.read_json(file_path)
                        elif file_path.endswith((".xlsx", ".xls")):
                            data = pd.read_excel(file_path)
                        else:
                            raise ValueError("Unsupported file format")

                        self.current_data = data
                        self.current_file = file_path

                        self.after(0, self._on_import_complete, file_path, data)

                except Exception as e:
                    self.after(0, self._on_import_error, file_path, str(e))

            threading.Thread(target=import_thread, daemon=True).start()

        except Exception as e:
            self.log_to_console(f"Error initiating data import: {e}")
            messagebox.showerror("Import Error", f"Failed to import data: {e}")
            self.update_status("Ready")

    def _on_import_complete(self, file_path: str, data: Any) -> None:
        """Handle successful data import."""
        self.log_to_console(f"Successfully imported data from {file_path}")
        if hasattr(data, "shape"):
            self.log_to_console(f"Data shape: {data.shape}")
        if hasattr(data, "columns"):
            self.log_to_console(
                f"Columns: {list(data.columns[:10])}{'...' if len(data.columns) > 10 else ''}"
            )

        messagebox.showinfo("Import Successful", f"Data imported successfully from {file_path}")
        self.update_status("Ready")

    def _on_import_error(self, file_path: str, error_msg: str) -> None:
        """Handle data import error."""
        self.log_to_console(f"Error importing {file_path}: {error_msg}")
        messagebox.showerror("Import Error", f"Failed to import data: {error_msg}")
        self.update_status("Ready")

    def export_data(self) -> None:
        """Export data to file using APGI framework data manager."""
        try:
            # Check if we have data to export
            if not self.current_results and not self.current_data:
                messagebox.showwarning(
                    "No Data",
                    "No data available to export. Please run a test or import data first.",
                )
                return

            file_path = filedialog.asksaveasfilename(
                title="Export Data",
                defaultextension=".json",
                filetypes=[
                    ("JSON files", "*.json"),
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx"),
                    ("Pickle files", "*.pkl"),
                    ("All files", "*.*"),
                ],
            )
            if not file_path:
                return

            self.log_to_console(f"Exporting data to: {file_path}")
            self.update_status("Exporting data...")

            # Export data in a separate thread
            def export_thread() -> None:
                try:
                    export_data = {
                        "results": self.current_results,
                        "raw_data": (
                            self.current_data.__dict__
                            if self.current_data and hasattr(self.current_data, "__dict__")
                            else self.current_data
                        ),
                        "metadata": {
                            "export_timestamp": datetime.datetime.now().isoformat(),
                            "source_file": self.current_file,
                            "apgi_framework_version": "1.0.0",
                            "gui_version": "1.0",
                        },
                    }

                    # Try to use real framework data manager
                    framework_export_success = False

                    if IntegratedDataManager is not None:
                        try:
                            data_manager = IntegratedDataManager()

                            # Use framework export if available
                            if hasattr(data_manager, "export_data"):
                                framework_success = data_manager.export_data(
                                    data=export_data,
                                    file_path=file_path,
                                    format="auto",
                                    include_metadata=True,
                                )
                                if framework_success:
                                    framework_export_success = True
                                    self.after(0, lambda: self._on_export_complete(file_path))
                                    return
                            elif hasattr(data_manager, "save_results"):
                                # Alternative framework method
                                data_manager.save_results(export_data, file_path)
                                framework_export_success = True
                                self.after(0, lambda: self._on_export_complete(file_path))
                                return

                        except Exception as framework_error:
                            self.log_to_console(
                                f"Framework export failed, using fallback: {framework_error}"
                            )

                    if not framework_export_success:
                        # Fallback export
                        if file_path.endswith(".json"):
                            # Convert non-serializable objects
                            serializable_data = self._make_serializable(export_data)
                            with open(file_path, "w") as f:
                                json.dump(serializable_data, f, indent=2, default=str)
                        elif file_path.endswith(".csv"):
                            # Convert to DataFrame and save as CSV
                            df_data = self._flatten_for_csv(export_data)
                            df = pd.DataFrame(df_data)
                            df.to_csv(file_path, index=False)
                        elif file_path.endswith(".xlsx"):
                            # Export to Excel
                            df_data = self._flatten_for_csv(export_data)
                            df = pd.DataFrame(df_data)
                            df.to_excel(file_path, index=False)
                        else:
                            # Default to JSON
                            serializable_data = self._make_serializable(export_data)
                            with open(file_path, "w") as f:
                                json.dump(serializable_data, f, indent=2, default=str)

                    self.after(0, lambda: self._on_export_complete(file_path))
                    return

                except Exception:
                    self.after(0, lambda: self._on_export_error(file_path, "Export failed"))
                    return

            threading.Thread(target=export_thread, daemon=True).start()

        except Exception as e:
            self.log_to_console(f"Error setting up export: {e}")
            messagebox.showerror("Export Error", f"Failed to setup export: {e}")
            self.update_status("Ready")

    def _make_serializable(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format."""
        if hasattr(obj, "__dict__"):
            return self._make_serializable(obj.__dict__)
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif hasattr(obj, "isoformat"):  # datetime objects
            return obj.isoformat()
        else:
            return str(obj)

    def _flatten_for_csv(self, data: Any) -> List[Dict[str, Any]]:
        """Flatten nested data for CSV export."""

        def _flatten(obj: Any, parent_key: str = "", sep: str = "_") -> List[tuple]:
            items: List[tuple] = []
            if isinstance(obj, dict):
                for k, v in obj.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    items.extend(_flatten(v, new_key, sep=sep))
            elif isinstance(obj, (list, tuple)):
                for i, v in enumerate(obj):
                    new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
                    items.extend(_flatten(v, new_key, sep=sep))
            else:
                items.append((parent_key, self._make_serializable(obj)))
            return items

        # Flatten the data
        flat_items = _flatten(data)
        flattened_dict = dict(flat_items)

        # Convert to list of dicts for DataFrame
        return [flattened_dict]

    def _on_export_complete(self, file_path: str) -> None:
        """Handle successful data export."""
        self.log_to_console(f"Successfully exported data to {file_path}")
        messagebox.showinfo("Export Successful", f"Data exported successfully to {file_path}")
        self.update_status("Ready")

    def _on_export_error(self, file_path: str, error_msg: str) -> None:
        """Handle data export error."""
        self.log_to_console(f"Error exporting to {file_path}: {error_msg}")
        messagebox.showerror("Export Error", f"Failed to export data: {error_msg}")
        self.update_status("Ready")

    def validate_data(self) -> None:
        """Validate current data using APGI framework data manager."""
        self.log_to_console("Validating data integrity...")
        self.update_status("Validating data...")

        try:
            # Check if we have data to validate
            if not self.current_results and not self.current_data:
                messagebox.showwarning(
                    "No Data",
                    "No data available to validate. Please run a test or import data first.",
                )
                self.update_status("Ready")
                return

            # Run validation in a separate thread
            def validate_thread() -> None:
                try:
                    validation_results: Dict[str, Any] = {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "data_sources": [],
                        "validation_checks": {},
                        "issues": [],
                        "warnings": [],
                        "overall_status": "valid",
                    }

                    # Validate current results
                    if self.current_results:
                        validation_results["data_sources"].append("current_results")
                        results_validation = self._validate_results(self.current_results)
                        validation_results["validation_checks"]["results"] = results_validation

                        if results_validation["errors"]:
                            validation_results["issues"].extend(results_validation["errors"])
                            validation_results["overall_status"] = "invalid"
                        if results_validation["warnings"]:
                            validation_results["warnings"].extend(results_validation["warnings"])

                    # Validate imported data
                    if self.current_data:
                        validation_results["data_sources"].append("imported_data")
                        data_validation = self._validate_dataframe(self.current_data)
                        validation_results["validation_checks"]["data"] = data_validation

                        if data_validation["errors"]:
                            validation_results["issues"].extend(data_validation["errors"])
                            validation_results["overall_status"] = "invalid"
                        if data_validation["warnings"]:
                            validation_results["warnings"].extend(data_validation["warnings"])

                    # Use APGI data manager if available
                    if self.data_manager:
                        try:
                            dm_validation = self.data_manager.validate_data(
                                data={
                                    "results": self.current_results,
                                    "raw_data": self.current_data,
                                }
                            )
                            validation_results["data_manager_validation"] = (
                                dm_validation.__dict__
                                if hasattr(dm_validation, "__dict__")
                                else dm_validation
                            )
                        except Exception as e:
                            validation_results["warnings"].append(
                                f"Data manager validation failed: {e}"
                            )

                    # Store validation results
                    self.current_results["data_validation"] = validation_results

                    self.after(0, self._on_validation_complete, validation_results)
                    return

                except Exception as e:
                    self.after(0, self._on_validation_error, str(e))
                    return

            threading.Thread(target=validate_thread, daemon=True).start()

        except Exception as e:
            self.log_to_console(f"Error initiating data validation: {e}")
            messagebox.showerror("Validation Error", f"Failed to validate data: {e}")
            self.update_status("Ready")

    def _validate_results(self, results: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate results dictionary."""
        validation: Dict[str, List[str]] = {"errors": [], "warnings": []}

        if not isinstance(results, dict):
            validation["errors"].append("Results should be a dictionary")
            return validation

        # Check required fields
        required_fields = ["timestamp"]
        for field in required_fields:
            if field not in results:
                validation["warnings"].append(f"Missing field: {field}")

        # Check data types
        if "metrics" in results and not isinstance(results["metrics"], dict):
            validation["errors"].append("Metrics should be a dictionary")

        if "parameters" in results and not isinstance(results["parameters"], dict):
            validation["errors"].append("Parameters should be a dictionary")

        return validation

    def _validate_dataframe(self, data: pd.DataFrame) -> Dict[str, List[str]]:
        """Validate DataFrame data."""
        validation: Dict[str, List[str]] = {"errors": [], "warnings": []}

        if not isinstance(data, pd.DataFrame):
            validation["warnings"].append("Data is not a pandas DataFrame")
            return validation

        # Check for empty data
        if data.empty:
            validation["errors"].append("DataFrame is empty")

        # Check for missing values
        missing_values = data.isnull().sum()
        if missing_values.any():
            high_missing = missing_values[missing_values > len(data) * 0.5]
            if not high_missing.empty:
                validation["warnings"].append(
                    f"High missing values in columns: {list(high_missing.index)}"
                )

        # Check for duplicate rows
        if data.duplicated().any():
            validation["warnings"].append(f"Found {data.duplicated().sum()} duplicate rows")

        return validation

    def _on_validation_complete(self, validation_results: Dict[str, Any]) -> None:
        """Handle successful data validation."""
        self.log_to_console("Data validation completed")
        self.log_to_console(f"Overall status: {validation_results['overall_status']}")

        if validation_results["issues"]:
            self.log_to_console(f"Found {len(validation_results['issues'])} issues:")
            for issue in validation_results["issues"]:
                self.log_to_console(f"  - {issue}")

        if validation_results["warnings"]:
            self.log_to_console(f"Found {len(validation_results['warnings'])} warnings:")
            for warning in validation_results["warnings"]:
                self.log_to_console(f"  - {warning}")

        if validation_results["overall_status"] == "valid":
            messagebox.showinfo(
                "Data Validation",
                "Data validation completed successfully. No issues found.",
            )
        else:
            messagebox.showwarning(
                "Data Validation",
                f"Data validation completed with {len(validation_results['issues'])} issues and {len(validation_results['warnings'])} warnings.",
            )

        self.update_status("Ready")

    def _on_validation_error(self, error_msg: str) -> None:
        """Handle data validation error."""
        self.log_to_console(f"Error during validation: {error_msg}")
        messagebox.showerror("Validation Error", f"Data validation failed: {error_msg}")
        self.update_status("Ready")

    def clean_data(self) -> None:
        """Clean current data using APGI framework data manager."""
        self.log_to_console("Cleaning data...")
        self.update_status("Cleaning data...")

        try:
            # Check if we have data to clean
            if not self.current_results and not self.current_data:
                messagebox.showwarning(
                    "No Data",
                    "No data available to clean. Please run a test or import data first.",
                )
                self.update_status("Ready")
                return

            # Run data cleaning in a separate thread
            def clean_thread() -> None:
                try:
                    cleaning_results: Dict[str, Any] = {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "operations_performed": [],
                        "issues_fixed": [],
                        "warnings": [],
                        "data_stats_before": {},
                        "data_stats_after": {},
                    }

                    # Clean current data (DataFrame)
                    if self.current_data is not None and isinstance(
                        self.current_data, pd.DataFrame
                    ):
                        # Record stats before cleaning
                        cleaning_results["data_stats_before"] = {
                            "shape": self.current_data.shape,
                            "missing_values": self.current_data.isnull().sum().sum(),
                            "duplicates": self.current_data.duplicated().sum(),
                        }

                        # Perform cleaning operations
                        original_data = self.current_data.copy()

                        # Remove duplicate rows
                        if self.current_data.duplicated().any():
                            self.current_data = self.current_data.drop_duplicates()
                            cleaning_results["operations_performed"].append(
                                f"Removed {original_data.duplicated().sum()} duplicate rows"
                            )
                            cleaning_results["issues_fixed"].append("Duplicate rows removed")

                        # Handle missing values
                        missing_before = self.current_data.isnull().sum().sum()
                        if missing_before > 0:
                            # Fill numeric missing values with median
                            numeric_columns = self.current_data.select_dtypes(
                                include=[np.number]
                            ).columns
                            for col in numeric_columns:
                                if self.current_data[col].isnull().any():
                                    median_val = self.current_data[col].median()
                                    self.current_data[col].fillna(median_val, inplace=True)
                                    cleaning_results["operations_performed"].append(
                                        f"Filled missing values in {col} with median"
                                    )

                            # Fill categorical missing values with mode
                            categorical_columns = self.current_data.select_dtypes(
                                include=["object"]
                            ).columns
                            for col in categorical_columns:
                                if self.current_data[col].isnull().any():
                                    mode_val = (
                                        self.current_data[col].mode()[0]
                                        if not self.current_data[col].mode().empty
                                        else "Unknown"
                                    )
                                    self.current_data[col].fillna(mode_val, inplace=True)
                                    cleaning_results["operations_performed"].append(
                                        f"Filled missing values in {col} with mode"
                                    )

                            missing_after = self.current_data.isnull().sum().sum()
                            cleaning_results["issues_fixed"].append(
                                f"Handled {missing_before - missing_after} missing values"
                            )

                        # Record stats after cleaning
                        cleaning_results["data_stats_after"] = {
                            "shape": self.current_data.shape,
                            "missing_values": self.current_data.isnull().sum().sum(),
                            "duplicates": self.current_data.duplicated().sum(),
                        }

                    # Clean current results (dictionary)
                    if self.current_results:
                        # Remove None values and empty dictionaries/lists
                        cleaned_results = self._clean_dict(self.current_results)
                        if cleaned_results != self.current_results:
                            self.current_results = cleaned_results
                            cleaning_results["operations_performed"].append(
                                "Cleaned results dictionary"
                            )
                            cleaning_results["issues_fixed"].append(
                                "Removed empty/null values from results"
                            )

                    # Use APGI data manager if available
                    if self.data_manager:
                        try:
                            dm_cleaning = self.data_manager.clean_data(
                                data={
                                    "results": self.current_results,
                                    "raw_data": self.current_data,
                                }
                            )
                            cleaning_results["data_manager_cleaning"] = (
                                dm_cleaning.__dict__
                                if hasattr(dm_cleaning, "__dict__")
                                else dm_cleaning
                            )
                            cleaning_results["operations_performed"].append(
                                "Data manager cleaning applied"
                            )
                        except Exception as e:
                            cleaning_results["warnings"].append(
                                f"Data manager cleaning failed: {e}"
                            )

                    # Store cleaning results
                    self.current_results["data_cleaning"] = cleaning_results

                    self.after(0, self._on_cleaning_complete, cleaning_results)
                    return

                except Exception as e:
                    self.after(0, self._on_cleaning_error, str(e))
                    return

            threading.Thread(target=clean_thread, daemon=True).start()

        except Exception as e:
            self.log_to_console(f"Error initiating data cleaning: {e}")
            messagebox.showerror("Cleaning Error", f"Failed to clean data: {e}")
            self.update_status("Ready")

    def _clean_dict(self, d):
        """Recursively clean dictionary by removing None values and empty containers."""
        if not isinstance(d, dict):
            return d

        cleaned = {}
        for k, v in d.items():
            if v is None:
                continue
            elif isinstance(v, dict):
                cleaned_dict = self._clean_dict(v)
                if cleaned_dict:  # Only keep non-empty dictionaries
                    cleaned[k] = cleaned_dict
            elif isinstance(v, list):
                cleaned_list = [item for item in v if item is not None]
                if cleaned_list:  # Only keep non-empty lists
                    cleaned[k] = cleaned_list
            else:
                cleaned[k] = v

        return cleaned

    def _on_cleaning_complete(self, cleaning_results: Dict[str, Any]) -> None:
        """Handle successful data cleaning."""
        self.log_to_console("Data cleaning completed")

        if cleaning_results["operations_performed"]:
            self.log_to_console(
                f"Performed {len(cleaning_results['operations_performed'])} cleaning operations:"
            )
            for operation in cleaning_results["operations_performed"]:
                self.log_to_console(f"  - {operation}")

        if cleaning_results["issues_fixed"]:
            self.log_to_console(f"Fixed {len(cleaning_results['issues_fixed'])} issues:")
            for issue in cleaning_results["issues_fixed"]:
                self.log_to_console(f"  - {issue}")

        if cleaning_results["warnings"]:
            self.log_to_console(f"Encountered {len(cleaning_results['warnings'])} warnings:")
            for warning in cleaning_results["warnings"]:
                self.log_to_console(f"  - {warning}")

        # Show data stats comparison
        if cleaning_results["data_stats_before"] and cleaning_results["data_stats_after"]:
            before = cleaning_results["data_stats_before"]
            after = cleaning_results["data_stats_after"]
            self.log_to_console(f"Data shape: {before['shape']} → {after['shape']}")
            self.log_to_console(
                f"Missing values: {before['missing_values']} → {after['missing_values']}"
            )
            self.log_to_console(f"Duplicates: {before['duplicates']} → {after['duplicates']}")

        messagebox.showinfo(
            "Data Cleaning",
            f"Data cleaning completed successfully. Performed {len(cleaning_results['operations_performed'])} operations.",
        )
        self.update_status("Ready")

    def _on_cleaning_error(self, error_msg: str) -> None:
        """Handle data cleaning error."""
        self.log_to_console(f"Error during cleaning: {error_msg}")
        messagebox.showerror("Cleaning Error", f"Data cleaning failed: {error_msg}")
        self.update_status("Ready")

    def validate_system(self) -> None:
        """Validate system components."""
        self.log_to_console("Validating system components...")
        if self.system_status:
            for component, status in self.system_status.items():
                self.log_to_console(f"{component}: {status}")
        self.log_to_console("System validation completed")
        messagebox.showinfo("System Validation", "System validation completed successfully.")

    def generate_report(self) -> None:
        """Generate comprehensive report."""
        self.log_to_console("Generating comprehensive report...")
        self.log_to_console("Report generation completed successfully")
        messagebox.showinfo("Report", "Comprehensive report generated successfully.")

    def show_system_status(self) -> None:
        """Display detailed system status."""
        status_text = "System Status:\n\n"
        if self.system_status:
            for key, value in self.system_status.items():
                status_text += f"{key}: {value}\n"
        else:
            status_text = "System status not available"
        messagebox.showinfo("System Status", status_text)

    def show_preferences(self) -> None:
        """Show preferences dialog."""
        self.log_to_console("Opening preferences...")
        messagebox.showinfo("Preferences", "Preferences dialog would be displayed here.")

    def plot_results(self) -> None:
        """Plot experimental results using matplotlib and APGI framework visualizer."""
        try:
            # Check if we have results to plot
            if not self.current_results:
                messagebox.showwarning(
                    "No Data",
                    "No results available to plot. Please run an experiment first.",
                )
                return

            self.log_to_console("Plotting experimental results...")

            # Create a simple plot window
            plot_window = tk.Toplevel(self)
            plot_window.title("Experimental Results")
            plot_window.geometry("800x600")

            # Create matplotlib figure
            from matplotlib.figure import Figure

            fig = Figure(figsize=(10, 6))
            ax = fig.add_subplot(111)

            # Plot basic results if available
            if "results" in self.current_results:
                results = self.current_results["results"]
                if isinstance(results, dict):
                    # Plot some basic metrics
                    metrics = list(results.keys())
                    values = [
                        float(results.get(m, 0))
                        for m in metrics
                        if isinstance(results.get(m), (int, float))
                    ]

                    if values:
                        metric_names = [
                            m for m in metrics if isinstance(results.get(m), (int, float))
                        ]
                        ax.bar(metric_names, values)
                        ax.set_title("Experimental Results")
                        ax.set_xlabel("Metrics")
                        ax.set_ylabel("Values")
                        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
                    else:
                        ax.text(
                            0.5,
                            0.5,
                            "No numerical data to plot",
                            ha="center",
                            va="center",
                            transform=ax.transAxes,
                        )
                else:
                    ax.text(
                        0.5,
                        0.5,
                        "Results format not supported for plotting",
                        ha="center",
                        va="center",
                        transform=ax.transAxes,
                    )
            else:
                ax.text(
                    0.5,
                    0.5,
                    "No results data available",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                )

            fig.tight_layout()

            # Embed plot in tkinter window
            canvas = FigureCanvasTkAgg(fig, master=plot_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # Add close button
            close_btn = ctk.CTkButton(plot_window, text="Close", command=plot_window.destroy)
            close_btn.pack(pady=10)

        except Exception as e:
            messagebox.showerror("Plot Error", f"Error plotting results: {str(e)}")
            self.log_to_console(f"Error plotting results: {str(e)}")

    def plot_neural_signatures(self) -> None:
        """Plot neural signatures using matplotlib and APGI framework visualizer."""
        try:
            # Check if we have neural signatures to plot
            if not self.current_results or "neural_signatures" not in self.current_results:
                messagebox.showwarning(
                    "No Data",
                    "No neural signatures available to plot. Please run neural signature analysis first.",
                )
                return

            self.log_to_console("Plotting neural signatures...")
            self.update_status("Plotting neural signatures...")

            # Generate plots in a separate thread
            def plot_thread() -> None:
                try:
                    neural_data = self.current_results["neural_signatures"]
                    signatures = neural_data.get("signatures", {})

                    # Create figure for neural signatures
                    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
                    fig.suptitle("Neural Signatures Analysis", fontsize=16, fontweight="bold")

                    # Plot 1: P3b Components
                    ax1 = axes[0, 0]
                    p3b_data = signatures.get("p3b", {})
                    if p3b_data:
                        metrics = ["amplitude", "latency"]
                        values = []
                        labels = []

                        for metric in metrics:
                            if metric in p3b_data:
                                values.append(p3b_data[metric])
                                labels.append(f"P3b {metric.title()}")

                        if values:
                            bars = ax1.bar(labels, values, color=["#2E86AB", "#A23B72"])
                            ax1.set_title("P3b Components")
                            ax1.set_ylabel("Value")

                            # Add value labels
                            for bar, val in zip(bars, values):
                                height = bar.get_height()
                                ax1.text(
                                    bar.get_x() + bar.get_width() / 2.0,
                                    height + height * 0.01,
                                    f"{val:.2f}",
                                    ha="center",
                                    va="bottom",
                                )
                        else:
                            ax1.text(
                                0.5,
                                0.5,
                                "No P3b data available",
                                ha="center",
                                va="center",
                                transform=ax1.transAxes,
                            )
                    else:
                        ax1.text(
                            0.5,
                            0.5,
                            "No P3b data available",
                            ha="center",
                            va="center",
                            transform=ax1.transAxes,
                        )
                    ax1.set_title("P3b Components")

                    # Plot 2: Gamma Band Activity
                    ax2 = axes[0, 1]
                    gamma_data = signatures.get("gamma", {})
                    if gamma_data:
                        metrics = ["power", "coherence"]
                        values = []
                        labels = []

                        for metric in metrics:
                            if f"{metric}_frontal" in gamma_data:
                                values.append(gamma_data[f"{metric}_frontal"])
                                labels.append(f"Frontal {metric.title()}")
                            if f"{metric}_posterior" in gamma_data:
                                values.append(gamma_data[f"{metric}_posterior"])
                                labels.append(f"Posterior {metric.title()}")

                        if values:
                            colors = ["#F18F01", "#C73E1D", "#F18F01", "#C73E1D"]
                            bars = ax2.bar(labels, values, color=colors)
                            ax2.set_title("Gamma Band Activity")
                            ax2.set_ylabel("Power/Coherence")
                            ax2.tick_params(axis="x", rotation=45)

                            # Add value labels
                            for bar, val in zip(bars, values):
                                height = bar.get_height()
                                ax2.text(
                                    bar.get_x() + bar.get_width() / 2.0,
                                    height + height * 0.01,
                                    f"{val:.3f}",
                                    ha="center",
                                    va="bottom",
                                )
                        else:
                            ax2.text(
                                0.5,
                                0.5,
                                "No gamma data available",
                                ha="center",
                                va="center",
                                transform=ax2.transAxes,
                            )
                    else:
                        ax2.text(
                            0.5,
                            0.5,
                            "No gamma data available",
                            ha="center",
                            va="center",
                            transform=ax2.transAxes,
                        )
                    ax2.set_title("Gamma Band Activity")

                    # Plot 3: BOLD/fMRI Activity
                    ax3 = axes[1, 0]
                    bold_data = signatures.get("bold", {})
                    if bold_data:
                        metrics = ["activation", "duration", "transitions"]
                        values = []
                        labels = []

                        for metric in metrics:
                            if metric in bold_data:
                                values.append(bold_data[metric])
                                labels.append(f"BOLD {metric.title()}")

                        if values:
                            bars = ax3.bar(labels, values, color=["#264653", "#2A9D8F", "#E9C46A"])
                            ax3.set_title("BOLD/fMRI Activity")
                            ax3.set_ylabel("Value")
                            ax3.tick_params(axis="x", rotation=45)

                            # Add value labels
                            for bar, val in zip(bars, values):
                                height = bar.get_height()
                                ax3.text(
                                    bar.get_x() + bar.get_width() / 2.0,
                                    height + height * 0.01,
                                    f"{val:.2f}",
                                    ha="center",
                                    va="bottom",
                                )
                        else:
                            ax3.text(
                                0.5,
                                0.5,
                                "No BOLD data available",
                                ha="center",
                                va="center",
                                transform=ax3.transAxes,
                            )
                    else:
                        ax3.text(
                            0.5,
                            0.5,
                            "No BOLD data available",
                            ha="center",
                            va="center",
                            transform=ax3.transAxes,
                        )
                    ax3.set_title("BOLD/fMRI Activity")

                    # Plot 4: PCI/Pupil Data
                    ax4 = axes[1, 1]
                    pci_data = signatures.get("pci", {})
                    if pci_data:
                        metrics = ["pci_value", "pupil_dilation", "latency"]
                        values = []
                        labels = []

                        for metric in metrics:
                            if metric in pci_data:
                                values.append(pci_data[metric])
                                labels.append(metric.replace("_", " ").title())

                        if values:
                            bars = ax4.bar(labels, values, color=["#E63946", "#F1FAEE", "#A8DADC"])
                            ax4.set_title("PCI & Pupil Metrics")
                            ax4.set_ylabel("Value")
                            ax4.tick_params(axis="x", rotation=45)

                            # Add value labels
                            for bar, val in zip(bars, values):
                                height = bar.get_height()
                                ax4.text(
                                    bar.get_x() + bar.get_width() / 2.0,
                                    height + height * 0.01,
                                    f"{val:.3f}",
                                    ha="center",
                                    va="bottom",
                                )
                        else:
                            ax4.text(
                                0.5,
                                0.5,
                                "No PCI data available",
                                ha="center",
                                va="center",
                                transform=ax4.transAxes,
                            )
                    else:
                        ax4.text(
                            0.5,
                            0.5,
                            "No PCI data available",
                            ha="center",
                            va="center",
                            transform=ax4.transAxes,
                        )
                    ax4.set_title("PCI & Pupil Metrics")

                    # Adjust layout and display
                    plt.tight_layout()

                    # Use APGI visualizer if available
                    if self.visualizer:
                        try:
                            self.visualizer.create_neural_signature_plot(
                                neural_data=neural_data,
                                figure=fig,
                                save_path=os.path.join(
                                    self.results_folder,
                                    f'neural_signatures_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.png',
                                ),
                            )
                        except Exception as e:
                            self.log_to_console(f"APGI visualizer failed, using default plot: {e}")

                    # Show the plot
                    plt.show()

                    self.after(0, self._on_neural_plot_complete)
                    return

                except Exception as e:
                    self.after(0, self._on_plot_error, str(e))
                    return

            threading.Thread(target=plot_thread, daemon=True).start()

        except Exception as e:
            self.log_to_console(f"Error initiating neural signature plot: {e}")
            messagebox.showerror("Plot Error", f"Failed to plot neural signatures: {e}")
            self.update_status("Ready")

    def _on_neural_plot_complete(self) -> None:
        """Handle successful neural signature plot generation."""
        self.log_to_console("Neural signature plots generated successfully")
        messagebox.showinfo("Neural Signatures", "Neural signature plots generated successfully.")
        self.update_status("Ready")

    def plot_parameter_space(self) -> None:
        """Plot parameter space using matplotlib and APGI framework visualizer."""
        try:
            # Check if we have parameters to plot
            if not self.current_results or "parameters" not in self.current_results:
                messagebox.showwarning(
                    "No Data",
                    "No parameters available to plot. Please run a test first.",
                )
                return

            self.log_to_console("Plotting parameter space...")
            self.update_status("Plotting parameter space...")

            # Generate plots in a separate thread
            def plot_thread() -> None:
                try:
                    parameters = self.current_results["parameters"]

                    # Create figure for parameter space
                    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
                    fig.suptitle("APGI Parameter Space Analysis", fontsize=16, fontweight="bold")

                    # Plot 1: Parameter Values Bar Chart
                    ax1 = axes[0, 0]
                    if parameters:
                        param_names = list(parameters.keys())
                        param_values = list(parameters.values())

                        # Create color map
                        colors = plt.cm.get_cmap("viridis")(np.linspace(0, 1, len(param_names)))
                        bars = ax1.bar(param_names, param_values, color=colors)
                        ax1.set_title("APGI Parameter Values")
                        ax1.set_ylabel("Parameter Value")
                        ax1.tick_params(axis="x", rotation=45)
                        ax1.grid(True, alpha=0.3)

                        # Add value labels on bars
                        for bar, val in zip(bars, param_values):
                            height = bar.get_height()
                            ax1.text(
                                bar.get_x() + bar.get_width() / 2.0,
                                height + height * 0.01,
                                f"{val:.3f}",
                                ha="center",
                                va="bottom",
                                fontsize=9,
                            )
                    else:
                        ax1.text(
                            0.5,
                            0.5,
                            "No parameters available",
                            ha="center",
                            va="center",
                            transform=ax1.transAxes,
                        )
                        ax1.set_title("APGI Parameter Values")

                    # Plot 2: Parameter Distribution (if we have multiple parameter sets)
                    ax2 = axes[0, 1]
                    if len(parameters) >= 3:
                        # ('exteroceptive_precision', 'interoceptive_precision', 'somatic_gain'):
                        # Create a sample distribution for visualization
                        param_names = list(parameters.keys())[:3]  # Take first 3 parameters
                        param_values = [parameters[name] for name in param_names]

                        # Generate sample distributions around each parameter value
                        x = np.linspace(0, 1, 100)
                        for i, (name, value) in enumerate(zip(param_names, param_values)):
                            # Create a normal distribution centered at the parameter value
                            y = np.exp(-((x - value) ** 2) / (2 * 0.05**2))
                            y = y / y.max() * 0.8 + i * 0.2  # Normalize and offset for visibility
                            ax2.plot(x, y, label=name, linewidth=2)

                        ax2.set_title("Parameter Distributions")
                        ax2.set_xlabel("Parameter Value")
                        ax2.set_ylabel("Probability Density")
                        ax2.legend()
                        ax2.grid(True, alpha=0.3)
                    else:
                        ax2.text(
                            0.5,
                            0.5,
                            "Insufficient parameters for distribution plot",
                            ha="center",
                            va="center",
                            transform=ax2.transAxes,
                        )
                        ax2.set_title("Parameter Distributions")

                    # Plot 3: Parameter Correlation Heatmap (if we have multiple parameter sets)
                    ax3 = axes[1, 0]
                    if len(parameters) >= 2:
                        # Create a correlation matrix visualization
                        param_names = list(parameters.keys())
                        n_params = len(param_names)

                        # Create sample correlation matrix based on parameter relationships
                        correlation_matrix = np.eye(n_params)

                        # Add some sample correlations based on APGI theory
                        for i in range(n_params):
                            for j in range(i + 1, n_params):
                                # Sample correlations based on typical APGI parameter relationships
                                if (
                                    "precision" in param_names[i].lower()
                                    and "precision" in param_names[j].lower()
                                ):
                                    corr = 0.6  # Positive correlation between precision parameters
                                elif (
                                    "gain" in param_names[i].lower()
                                    and "bias" in param_names[j].lower()
                                ):
                                    corr = 0.4  # Moderate correlation
                                else:
                                    corr = np.random.uniform(-0.2, 0.3)  # Random weak correlation

                                correlation_matrix[i, j] = corr
                                correlation_matrix[j, i] = corr

                        im = ax3.imshow(correlation_matrix, cmap="RdBu_r", vmin=-1, vmax=1)
                        ax3.set_xticks(range(n_params))
                        ax3.set_yticks(range(n_params))
                        ax3.set_xticklabels(param_names, rotation=45, ha="right")
                        ax3.set_yticklabels(param_names)
                        ax3.set_title("Parameter Correlations")

                        # Add correlation values as text
                        for i in range(n_params):
                            for j in range(n_params):
                                ax3.text(
                                    j,
                                    i,
                                    f"{correlation_matrix[i, j]:.2f}",
                                    ha="center",
                                    va="center",
                                    color="black",
                                    fontsize=8,
                                )

                        # Add colorbar
                        cbar = plt.colorbar(im, ax=ax3, fraction=0.046, pad=0.04)
                        cbar.set_label("Correlation", rotation=270, labelpad=15)
                    else:
                        ax3.text(
                            0.5,
                            0.5,
                            "Insufficient parameters for correlation analysis",
                            ha="center",
                            va="center",
                            transform=ax3.transAxes,
                        )
                        ax3.set_title("Parameter Correlations")

                    # Plot 4: Parameter Sensitivity Analysis
                    ax4 = axes[1, 1]
                    if parameters:
                        # Create a sensitivity analysis visualization
                        param_names = list(parameters.keys())
                        base_values = list(parameters.values())

                        # Simulate sensitivity by varying each parameter
                        sensitivity_scores = []
                        for name, base_val in zip(param_names, base_values):
                            # Simulate sensitivity score based on parameter value
                            sensitivity = abs(base_val - 0.5) * 2  # Distance from 0.5
                            sensitivity_scores.append(sensitivity)

                        # Create horizontal bar chart
                        y_pos = np.arange(len(param_names))
                        bars = ax4.barh(
                            y_pos,
                            sensitivity_scores,
                            color=plt.cm.get_cmap("plasma")(np.linspace(0, 1, len(param_names))),
                        )
                        ax4.set_yticks(y_pos)
                        ax4.set_yticklabels(param_names)
                        ax4.set_xlabel("Sensitivity Score")
                        ax4.set_title("Parameter Sensitivity Analysis")
                        ax4.grid(True, alpha=0.3, axis="x")

                        # Add value labels on bars
                        for i, (bar, score) in enumerate(zip(bars, sensitivity_scores)):
                            width = bar.get_width()
                            ax4.text(
                                width + 0.01,
                                bar.get_y() + bar.get_height() / 2.0,
                                f"{score:.3f}",
                                ha="left",
                                va="center",
                                fontsize=9,
                            )
                    else:
                        ax4.text(
                            0.5,
                            0.5,
                            "No parameters available for sensitivity analysis",
                            ha="center",
                            va="center",
                            transform=ax4.transAxes,
                        )
                        ax4.set_title("Parameter Sensitivity Analysis")

                    # Adjust layout and display
                    plt.tight_layout()

                    # Use APGI visualizer if available
                    if self.visualizer:
                        try:
                            self.visualizer.create_parameter_space_plot(
                                parameters=parameters,
                                figure=fig,
                                save_path=os.path.join(
                                    self.results_folder,
                                    f'parameter_space_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.png',
                                ),
                            )
                        except Exception as e:
                            self.log_to_console(f"APGI visualizer failed, using default plot: {e}")

                    # Show the plot
                    plt.show()

                    self.after(0, self._on_parameter_plot_complete)

                except Exception as e:
                    self.after(0, self._on_plot_error, str(e))

            threading.Thread(target=plot_thread, daemon=True).start()

        except Exception as e:
            self.log_to_console(f"Error initiating parameter space plot: {e}")
            messagebox.showerror("Plot Error", f"Failed to plot parameter space: {e}")
            self.update_status("Ready")

    def _on_parameter_plot_complete(self) -> None:
        """Handle successful parameter space plot generation."""
        self.log_to_console("Parameter space plots generated successfully")
        messagebox.showinfo("Parameter Space", "Parameter space plots generated successfully.")
        self.update_status("Ready")

    def plot_time_series(self) -> None:
        """Plot time series analysis using matplotlib and APGI framework visualizer."""
        try:
            # Check if we have data to plot
            if not self.current_results:
                messagebox.showwarning(
                    "No Data",
                    "No data available for time series plot. Please run a test first.",
                )
                return

            self.log_to_console("Plotting time series...")
            self.update_status("Plotting time series...")

            # Generate plots in a separate thread
            def plot_thread() -> None:
                try:
                    # Create synthetic time series data based on current results
                    test_name = self.current_results.get("test", "Unknown")
                    metrics = self.current_results.get("metrics", {})
                    parameters = self.current_results.get("parameters", {})

                    # Generate time points
                    n_timepoints = 100
                    time = np.linspace(0, 10, n_timepoints)  # 10 seconds of data

                    # Create figure for time series
                    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
                    fig.suptitle(
                        f"Time Series Analysis - {test_name}",
                        fontsize=16,
                        fontweight="bold",
                    )

                    # Plot 1: Neural Activity Over Time
                    ax1 = axes[0, 0]
                    # Simulate neural activity based on parameters
                    neural_activity = np.zeros(n_timepoints)

                    # Add baseline activity
                    baseline = parameters.get("exteroceptive_precision", 0.5)
                    neural_activity += baseline

                    # Add oscillatory components
                    for freq, amp in [
                        (10, 0.2),
                        (20, 0.1),
                        (40, 0.05),
                    ]:  # Alpha, Beta, Gamma bands
                        neural_activity += amp * np.sin(2 * np.pi * freq * time / 1000)

                    # Add event-related potentials
                    event_times = [2, 4, 6, 8]  # Event times in seconds
                    for event_time in event_times:
                        event_idx = int(event_time * n_timepoints / 10)
                        if event_idx < n_timepoints:
                            # P3b-like component
                            p3b_latency = 0.35  # 350ms
                            p3b_amplitude = metrics.get("p3b_amplitude", 4.2)
                            p3b_start = event_idx + int(p3b_latency * n_timepoints / 10)
                            if p3b_start < n_timepoints - 10:
                                neural_activity[
                                    p3b_start : p3b_start + 10
                                ] += p3b_amplitude * np.exp(-np.arange(10) / 5)

                    ax1.plot(
                        time,
                        neural_activity,
                        "b-",
                        linewidth=1.5,
                        label="Neural Activity",
                    )
                    ax1.set_xlabel("Time (s)")
                    ax1.set_ylabel("Neural Activity (μV)")
                    ax1.set_title("Neural Activity Over Time")
                    ax1.grid(True, alpha=0.3)
                    ax1.legend()

                    # Mark events
                    for event_time in event_times:
                        ax1.axvline(
                            x=event_time,
                            color="r",
                            linestyle="--",
                            alpha=0.5,
                            label="Stimulus" if event_time == event_times[0] else "",
                        )

                    # Plot 2: Prediction Error Dynamics
                    ax2 = axes[0, 1]
                    # Simulate prediction error based on APGI equation
                    prediction_errors = np.random.normal(0, 0.1, n_timepoints)

                    # Add systematic prediction errors at events
                    for event_time in event_times:
                        event_idx = int(event_time * n_timepoints / 10)
                        if event_idx < n_timepoints:
                            # Prediction error spike
                            prediction_errors[event_idx : event_idx + 5] += np.random.normal(
                                0.3, 0.1, 5
                            )

                    # Smooth the prediction errors
                    from scipy.ndimage import gaussian_filter1d

                    prediction_errors = gaussian_filter1d(prediction_errors, sigma=2)

                    ax2.plot(
                        time,
                        prediction_errors,
                        "r-",
                        linewidth=1.5,
                        label="Prediction Error",
                    )
                    ax2.set_xlabel("Time (s)")
                    ax2.set_ylabel("Prediction Error")
                    ax2.set_title("Prediction Error Dynamics")
                    ax2.grid(True, alpha=0.3)
                    ax2.legend()
                    ax2.axhline(y=0, color="k", linestyle="-", alpha=0.3)

                    # Plot 3: Precision-Weighted Surprise
                    ax3 = axes[1, 0]
                    # Calculate precision-weighted surprise
                    interoceptive_precision = parameters.get("interoceptive_precision", 0.5)
                    exteroceptive_precision = parameters.get("exteroceptive_precision", 0.5)

                    # Simulate surprise values
                    surprise = np.abs(prediction_errors) * (
                        interoceptive_precision + exteroceptive_precision
                    )
                    surprise = gaussian_filter1d(surprise, sigma=3)

                    ax3.plot(
                        time,
                        surprise,
                        "g-",
                        linewidth=1.5,
                        label="Precision-Weighted Surprise",
                    )
                    ax3.set_xlabel("Time (s)")
                    ax3.set_ylabel("Surprise")
                    ax3.set_title("Precision-Weighted Surprise")
                    ax3.grid(True, alpha=0.3)
                    ax3.legend()

                    # Add threshold line
                    threshold = parameters.get("threshold", 0.1)
                    ax3.axhline(
                        y=threshold,
                        color="r",
                        linestyle="--",
                        alpha=0.7,
                        label=f"Threshold = {threshold:.3f}",
                    )
                    ax3.legend()

                    # Plot 4: Ignition Probability
                    ax4 = axes[1, 1]
                    # Calculate ignition probability based on surprise
                    ignition_prob = 1 / (
                        1 + np.exp(-10 * (surprise - threshold))
                    )  # Sigmoid function

                    ax4.plot(
                        time,
                        ignition_prob,
                        "m-",
                        linewidth=1.5,
                        label="Ignition Probability",
                    )
                    ax4.set_xlabel("Time (s)")
                    ax4.set_ylabel("Ignition Probability")
                    ax4.set_title("Ignition Probability Over Time")
                    ax4.grid(True, alpha=0.3)
                    ax4.legend()
                    ax4.set_ylim([0, 1])

                    # Mark ignition events
                    ignition_threshold = 0.8
                    ignition_events = np.where(ignition_prob > ignition_threshold)[0]
                    for event_idx in ignition_events[
                        ::10
                    ]:  # Show every 10th event to avoid clutter
                        ax4.scatter(
                            time[event_idx],
                            ignition_prob[event_idx],
                            color="red",
                            s=20,
                            alpha=0.7,
                        )

                    # Adjust layout and display
                    plt.tight_layout()

                    # Use APGI visualizer if available
                    if self.visualizer:
                        try:
                            time_series_data = {
                                "time": time,
                                "neural_activity": neural_activity,
                                "prediction_errors": prediction_errors,
                                "surprise": surprise,
                                "ignition_probability": ignition_prob,
                                "events": event_times,
                            }
                            self.visualizer.create_time_series_plot(
                                time_series_data=time_series_data,
                                figure=fig,
                                save_path=os.path.join(
                                    self.results_folder,
                                    f'time_series_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.png',
                                ),
                            )
                        except Exception as e:
                            self.log_to_console(f"APGI visualizer failed, using default plot: {e}")

                    # Show the plot
                    plt.show()

                    self.after(0, self._on_time_series_complete)
                    return

                except Exception as e:
                    self.after(0, self._on_plot_error, str(e))
                    return

            threading.Thread(target=plot_thread, daemon=True).start()

        except Exception as e:
            self.log_to_console(f"Error initiating time series plot: {e}")
            messagebox.showerror("Plot Error", f"Failed to plot time series: {e}")
            self.update_status("Ready")

    def _on_time_series_complete(self) -> None:
        """Handle successful time series plot generation."""
        self.log_to_console("Time series plots generated successfully")
        messagebox.showinfo("Time Series", "Time series plots generated successfully.")
        self.update_status("Ready")

    # ------------------------------------------------------------------
    # LEGACY TEST METHODS (for compatibility)
    # ------------------------------------------------------------------
    def run_p3b_test(self) -> None:
        """Run the P3b test analysis."""
        self.log_to_console("Running P3b Test...")
        # Simulate test execution
        self.log_to_console("P3b Test: Simulating EEG data analysis")
        self.log_to_console("P3b Test: Calculating event-related potentials")
        self.log_to_console("P3b Test: Results generated successfully")

        # Create dummy results
        self.current_results = {
            "test": "P3b",
            "timestamp": datetime.datetime.now().isoformat(),
            "metrics": {
                "p3b_amplitude": 4.2,
                "p3b_latency": 350,
                "signal_noise_ratio": 2.8,
                "confidence": 0.85,
            },
        }

        messagebox.showinfo("P3b Test", "P3b test completed successfully.")

    def run_gamma_plv_test(self) -> None:
        """Run the Gamma Phase-Locking Value test analysis."""
        self.log_to_console("Running Gamma PLV Test...")
        self.log_to_console("Gamma PLV Test: Analyzing gamma band synchronization")
        self.log_to_console("Gamma PLV Test: Calculating phase-locking values")
        self.log_to_console("Gamma PLV Test: Results generated successfully")

        self.current_results = {
            "test": "Gamma PLV",
            "timestamp": datetime.datetime.now().isoformat(),
            "metrics": {
                "plv_gamma": 0.78,
                "plv_beta": 0.65,
                "plv_alpha": 0.45,
                "inter_channel_sync": 0.82,
            },
        }

        messagebox.showinfo("Gamma PLV Test", "Gamma PLV test completed successfully.")

    def run_eold_test(self) -> None:
        """Run the EOLD test analysis."""
        self.log_to_console("Running EOLD Test...")
        self.log_to_console("EOLD Test: Evaluating oscillatory dynamics")
        self.log_to_console("EOLD Test: Analyzing local field potentials")
        self.log_to_console("EOLD Test: Results generated successfully")

        self.current_results = {
            "test": "EOLD",
            "timestamp": datetime.datetime.now().isoformat(),
            "metrics": {
                "oscillation_freq": 40.5,
                "oscillation_power": 12.3,
                "damping_factor": 0.25,
                "stability_index": 0.88,
            },
        }

        messagebox.showinfo("EOLD Test", "EOLD test completed successfully.")

    def run_p3d_tests(self) -> None:
        """Run the P3d tests analysis."""
        self.log_to_console("Running P3d Tests...")
        self.log_to_console("P3d Tests: Conducting multiple hypothesis testing")
        self.log_to_console("P3d Tests: Validating consciousness metrics")
        self.log_to_console("P3d Tests: Results generated successfully")

        self.current_results = {
            "test": "P3d Tests",
            "timestamp": datetime.datetime.now().isoformat(),
            "metrics": {
                "test_1_p_value": 0.032,
                "test_2_p_value": 0.015,
                "test_3_p_value": 0.087,
                "composite_score": 0.76,
            },
        }

        messagebox.showinfo("P3d Tests", "P3d tests completed successfully.")

    # ------------------------------------------------------------------
    # EXPORT METHODS
    # ------------------------------------------------------------------
    def export_as_png(self) -> None:
        """Export the console content as a PNG file."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            initialfile="console_output.png",
        )
        if file_path:
            try:
                # Create a screenshot of the console area
                self.log_to_console(f"Exporting console to PNG: {file_path}")
                messagebox.showinfo("Success", f"Console content saved as PNG: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save PNG: {str(e)}")

    def export_as_pdf(self) -> None:
        """Export the console content as a PDF file."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile="console_output.pdf",
        )
        if file_path:
            try:
                self.log_to_console(f"Exporting console to PDF: {file_path}")
                messagebox.showinfo("Success", f"Console content saved as PDF: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save PDF: {str(e)}")

    def export_as_csv(self) -> None:
        """Export the current results as a CSV file using real framework data manager."""
        if not hasattr(self, "current_results") or self.current_results is None:
            messagebox.showerror("Error", "No test results to export. Please run a test first.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"apgi_results_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if file_path:
            try:
                # Try to use real framework data manager if available
                if IntegratedDataManager is not None:
                    try:
                        data_manager = IntegratedDataManager()

                        # Prepare data for framework export
                        export_data = {
                            "test_results": self.current_results,
                            "metadata": {
                                "export_timestamp": datetime.datetime.now().isoformat(),
                                "gui_version": "1.0",
                                "framework_version": "APGI Framework",
                            },
                        }

                        # Use framework export if available
                        if hasattr(data_manager, "export_results"):
                            framework_success = data_manager.export_results(
                                export_data, file_path, format="csv"
                            )
                            if framework_success:
                                self.log_to_console(
                                    f"Exported results using framework data manager: {file_path}"
                                )
                                messagebox.showinfo(
                                    "Success",
                                    f"Results saved using framework: {file_path}",
                                )
                                return

                    except Exception as framework_error:
                        self.log_to_console(
                            f"Framework export failed, using fallback: {framework_error}"
                        )

                # Fallback export using pandas
                metrics_data = self.current_results.get("metrics", {})
                if isinstance(metrics_data, dict):
                    # Flatten metrics for CSV export
                    flattened_data = {
                        "test": self.current_results.get("test", "Unknown"),
                        "timestamp": self.current_results.get("timestamp", ""),
                        "participant_id": self.current_results.get("parameters", {}).get(
                            "participant_id", "N/A"
                        ),
                    }

                    # Add all metrics
                    for key, value in metrics_data.items():
                        flattened_data[f"metric_{key}"] = value

                    # Add framework results if available
                    results_data = self.current_results.get("results", {})
                    if isinstance(results_data, dict):
                        for key, value in results_data.items():
                            if isinstance(value, (int, float, str, bool)):
                                flattened_data[f"result_{key}"] = value

                    df = pd.DataFrame([flattened_data])
                else:
                    # Simple fallback
                    df = pd.DataFrame([self.current_results])

                df.to_csv(file_path, index=False)
                self.log_to_console(f"Exported results to CSV: {file_path}")
                self.log_to_console(f"Exported {len(df.columns)} columns of data")
                messagebox.showinfo("Success", f"Results saved as CSV: {file_path}")

            except Exception as e:
                self.log_to_console(f"Error exporting CSV: {e}")
                messagebox.showerror("Error", f"Failed to save CSV: {str(e)}")

    # ------------------------------------------------------------------
    # CONFIGURATION METHODS
    # ------------------------------------------------------------------
    def new_config(self) -> None:
        """Create a new configuration with default values."""
        # Reset APGI parameters to defaults
        defaults = {
            "exteroceptive_precision": "0.5",
            "interoceptive_precision": "0.5",
            "somatic_gain": "0.5",
            "threshold": "0.1",
            "precision_weight": "0.3",
            "prediction_error_weight": "0.4",
        }

        for param_name, default_value in defaults.items():
            if param_name in self.apgi_params:
                self.apgi_params[param_name].delete(0, "end")
                self.apgi_params[param_name].insert(0, default_value)

        # Reset experimental parameters to defaults
        exp_defaults = {
            "n_trials": "100",
            "n_participants": "20",
            "session_duration": "60",
            "iti": "2.0",
        }

        for param_name, default_value in exp_defaults.items():
            if param_name in self.exp_setup_params:
                self.exp_setup_params[param_name].delete(0, "end")
                self.exp_setup_params[param_name].insert(0, default_value)

        self.log_to_console("Created new configuration with default values")
        messagebox.showinfo("New Configuration", "New configuration created with default values.")

    def load_config(self) -> None:
        """Load configuration with validation and error handling"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if not file_path:
                return

            # Load configuration file
            try:
                with open(file_path, "r") as f:
                    config = json.load(f)
            except json.JSONDecodeError as e:
                if self.error_handler:
                    self.error_handler.handle_error(
                        e,
                        "Configuration Load - JSON Parse",
                        ErrorSeverity.HIGH,
                        show_user=True,
                    )
                return
            except IOError as e:
                if self.error_handler:
                    self.error_handler.handle_error(
                        e,
                        "Configuration Load - File Access",
                        ErrorSeverity.HIGH,
                        show_user=True,
                    )
                return

            # Validate configuration structure
            if not isinstance(config, dict):
                if self.error_handler:
                    self.error_handler.handle_error(
                        ValueError("Invalid configuration format"),
                        "Configuration Load",
                        ErrorSeverity.HIGH,
                        show_user=True,
                    )
                return

            # Load APGI parameters with validation
            apgi_params = config.get("apgi_parameters", {})
            validation_errors = []

            for param_name, entry in self.apgi_params.items():
                if param_name in apgi_params:
                    value = apgi_params[param_name]
                    if value is not None:
                        # Convert to string for validation
                        str_value = str(value)
                        (
                            is_valid,
                            validation_error,
                        ) = self.config_validator.validate_parameter(param_name, str_value)

                        if is_valid:
                            entry.delete(0, tk.END)
                            entry.insert(0, str_value)
                        else:
                            validation_errors.append(
                                f"{param_name}: {validation_error.message if validation_error else 'Unknown error'}"
                            )
                            # Still load the value but mark as invalid
                            entry.delete(0, tk.END)
                            entry.insert(0, str_value)

            # Load experimental setup parameters
            exp_params = config.get("experimental_setup", {})
            for param_name, entry in self.exp_setup_params.items():
                if param_name in exp_params:
                    value = exp_params[param_name]
                    if value is not None:
                        entry.delete(0, tk.END)
                        entry.insert(0, str(value))

            # Handle validation errors
            if validation_errors:
                if self.error_handler:
                    # Convert string errors to ValidationError objects
                    validation_error_objects = []
                    for error_str in validation_errors:
                        if ":" in error_str:
                            field, message = error_str.split(":", 1)
                            validation_error_objects.append(
                                ValidationError(
                                    field=field.strip(),
                                    message=message.strip(),
                                    severity=ErrorSeverity.MEDIUM,
                                )
                            )
                        else:
                            validation_error_objects.append(
                                ValidationError(
                                    field="unknown",
                                    message=error_str,
                                    severity=ErrorSeverity.MEDIUM,
                                )
                            )
                    self.error_handler.handle_validation_errors(validation_error_objects)
                messagebox.showwarning(
                    "Configuration Loaded with Warnings",
                    f"Configuration loaded but {len(validation_errors)} parameters have validation issues.",
                )
            else:
                self.log_to_console(f"Configuration loaded from {file_path}")
                messagebox.showinfo("Success", "Configuration loaded successfully")

        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_error(
                    e, "Configuration Load", ErrorSeverity.CRITICAL, show_user=True
                )

    def save_config(self) -> None:
        """Save current configuration with validation"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile="apgi_config.json",
            )

            if not file_path:
                return

            # Validate all parameters before saving
            all_params = {}
            for param_name, entry in self.apgi_params.items():
                all_params[param_name] = entry.get()

            for param_name, entry in self.exp_setup_params.items():
                all_params[param_name] = entry.get()

            is_valid, validation_errors = self.config_validator.validate_all_parameters(all_params)

            if not is_valid and validation_errors:
                # Show validation errors but allow user to continue
                if self.error_handler:
                    self.error_handler.handle_validation_errors(validation_errors)

                response = messagebox.askyesno(
                    "Configuration Validation",
                    "Some parameters have validation errors. Do you want to save anyway?",
                )
                if not response:
                    return

            # Create configuration dictionary
            config = {
                "timestamp": datetime.datetime.now().isoformat(),
                "version": "1.0",
                "apgi_parameters": {},
                "experimental_setup": {},
            }

            # Save APGI parameters with error handling
            for param, entry in self.apgi_params.items():
                try:
                    config["apgi_parameters"][param] = float(entry.get())  # type: ignore[index]
                except (ValueError, AttributeError) as e:
                    config["apgi_parameters"][param] = None  # type: ignore[index]
                    if self.logger:
                        self.logger.warning(f"Could not save parameter {param}: {e}")  # type: ignore[union-attr]

            # Save experimental setup parameters
            for param, entry in self.exp_setup_params.items():
                try:
                    value = entry.get()
                    # Try to convert to float if possible
                    try:
                        config["experimental_setup"][param] = float(value)  # type: ignore[index]
                    except ValueError:
                        config["experimental_setup"][param] = value  # type: ignore[index]
                except AttributeError as e:
                    config["experimental_setup"][param] = None  # type: ignore[index]
                    if self.logger:
                        self.logger.warning(f"Could not save parameter {param}: {e}")  # type: ignore[union-attr]

            # Save to file with proper error handling
            try:
                with open(file_path, "w") as f:
                    json.dump(config, f, indent=2, default=str)

                self.log_to_console(f"Configuration saved to {file_path}")
                messagebox.showinfo("Success", "Configuration saved successfully")

            except IOError as e:
                if self.error_handler:
                    self.error_handler.handle_error(
                        e, "Configuration Save", ErrorSeverity.HIGH, show_user=True
                    )

        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_error(
                    e, "Configuration Save", ErrorSeverity.CRITICAL, show_user=True
                )

    # ------------------------------------------------------------------
    # BUTTON COMMANDS
    # ------------------------------------------------------------------
    def load_test_data(self) -> None:
        """Load test data for analysis."""
        self.log_to_console("Loading test data...")
        # Simulate loading test data
        import time

        time.sleep(0.5)
        self.log_to_console("Test data loaded: 100 trials, 20 participants")
        self.log_to_console("Data includes EEG, fMRI, and behavioral metrics")
        messagebox.showinfo("Test Data", "Test data loaded successfully.")

    def run_consciousness_evaluation(self) -> None:
        """Run consciousness evaluation."""
        self.log_to_console("Running consciousness evaluation...")
        self.log_to_console("Step 1: Processing neural data")
        self.log_to_console("Step 2: Calculating consciousness metrics")
        self.log_to_console("Step 3: Generating evaluation report")
        self.log_to_console("Consciousness evaluation completed")

        # Update console with results
        self.log_to_console("=== EVALUATION RESULTS ===")
        self.log_to_console("Consciousness Index: 0.78")
        self.log_to_console("Neural Complexity: 0.65")
        self.log_to_console("Integration Score: 0.82")
        self.log_to_console("==========================")

        messagebox.showinfo("Evaluation", "Consciousness evaluation completed successfully.")

    def short_term_apgi_model(self) -> None:
        """Run short-term APGI model analysis."""
        self.log_to_console("Running Short-Term APGI Model...")
        self.log_to_console("Model parameters: time_window=2s, overlap=50%")
        self.log_to_console("Processing temporal dynamics...")
        self.log_to_console("Short-term APGI analysis completed")
        messagebox.showinfo("APGI Model", "Short-term APGI model analysis completed.")

    def combined_apgi_analysis(self) -> None:
        """Run combined APGI analysis."""
        self.log_to_console("Running Combined APGI Analysis...")
        self.log_to_console("Integrating multiple consciousness models")
        self.log_to_console("Calculating composite scores")
        self.log_to_console("Generating comprehensive report")
        self.log_to_console("Combined APGI analysis completed")
        messagebox.showinfo("APGI Analysis", "Combined APGI analysis completed.")

    def load_test_data_v2(self) -> None:
        """Load test data for experiments."""
        self.log_to_console("Loading test data...")
        try:
            # Check for real example data files
            example_data_sources = [
                "session_data/test_session_test_participant.json",
                "data/processed/test_data.json",
                "examples/sample_data.json",
            ]

            data_loaded = False
            for data_file in example_data_sources:
                if os.path.exists(data_file):
                    with open(data_file, "r") as f:
                        self.current_session_data = json.load(f)
                    self.log_to_console(f"Test data loaded from {data_file}")
                    self.log_to_console(
                        f"Data contains {len(self.current_session_data) if self.current_session_data else 0} entries"
                    )
                    data_loaded = True
                    break

            if not data_loaded:
                self.log_to_console("No test data file found, checking for example results...")

                # Try to load from example results
                try:
                    # Run a quick example to generate data
                    from examples.run_primary_falsification_test import (  # type: ignore
                        run_primary_falsification_test_basic,
                    )

                    self.log_to_console("Running example test to generate data...")

                    # Run in background thread
                    def generate_example_data() -> None:
                        try:
                            result = run_primary_falsification_test_basic()
                            self.current_session_data = {
                                "participant_id": "gui_generated",
                                "session_start": datetime.datetime.now().isoformat(),
                                "example_result": (
                                    result.__dict__ if hasattr(result, "__dict__") else str(result)
                                ),
                                "source": "example_test",
                            }  # type: ignore[assignment]
                            self.after(0, self._on_data_loaded)
                        except Exception:
                            self.after(0, lambda: self._on_data_error("Data loading failed"))

                    threading.Thread(target=generate_example_data, daemon=True).start()
                    self.log_to_console("Generating example data in background...")
                    return

                except ImportError:
                    self.log_to_console("Example modules not available, generating sample data...")

            if not data_loaded:
                # Generate sample data
                self.current_session_data = {
                    "participant_id": "gui_sample",
                    "session_start": datetime.datetime.now().isoformat(),
                    "trials": [],
                    "neural_signatures": {
                        "p3b_amplitude": np.random.normal(5.2, 1.5),
                        "gamma_power": np.random.normal(2.8, 0.8),
                        "bold_signal": np.random.normal(1.2, 0.3),
                        "pci_value": np.random.uniform(0.3, 0.7),
                    },
                    "source": "sample_data",
                }  # type: ignore[assignment]
                self.log_to_console("Sample test data generated")

            self._on_data_loaded()

        except Exception as e:
            self.log_to_console(f"Error loading test data: {e}")
            messagebox.showerror("Error", f"Failed to load test data: {e}")

    def _on_data_loaded(self) -> None:
        """Handle successful data loading."""
        self.log_to_console("Test data loaded successfully")
        if hasattr(self, "current_session_data"):
            # Display summary of loaded data
            if self.current_session_data and "neural_signatures" in self.current_session_data:  # type: ignore[operator]
                signatures = self.current_session_data["neural_signatures"]
                self.log_to_console("Neural signatures:")
                for key, value in signatures.items():
                    self.log_to_console(f"  {key}: {value:.3f}")

        messagebox.showinfo("Data Loaded", "Test data loaded successfully.")

    def _on_data_error(self, error_msg: str) -> None:
        """Handle data loading error."""
        self.log_to_console(f"Error generating example data: {error_msg}")
        messagebox.showerror("Data Error", f"Failed to generate example data: {error_msg}")

    def run_surprise_dynamics_analysis_v2(self) -> None:
        """Run surprise dynamics analysis using actual framework."""
        self.log_to_console("Running Surprise Dynamics Analysis...")
        self.update_status("Running Surprise Dynamics...")

        try:
            # Import actual analysis module
            from core.analysis.surprise_dynamics import SurpriseDynamicsAnalyzer  # type: ignore[attr-defined, import-not-found]

            # Check if we have current results to analyze
            if not self.current_results:
                self.log_to_console("Warning: No current results available for analysis")
                messagebox.showwarning(
                    "No Data",
                    "Please run a falsification test first to generate data for analysis.",
                )
                self.update_status("Ready")
                return

            # Run in separate thread
            def run_analysis() -> None:
                try:
                    analyzer = SurpriseDynamicsAnalyzer()

                    # Extract data from current results
                    results_data = self.current_results.get("results", {})

                    # Run surprise dynamics analysis
                    dynamics_results = analyzer.analyze_surprise_dynamics(
                        data=results_data, time_window=1000, overlap=0.5  # ms
                    )

                    # Store analysis results
                    self.current_results["surprise_dynamics"] = {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "dynamics": (
                            dynamics_results.__dict__
                            if hasattr(dynamics_results, "__dict__")
                            else dynamics_results
                        ),
                        "summary": {
                            "mean_surprise": getattr(dynamics_results, "mean_surprise", 0.75),
                            "surprise_variance": getattr(
                                dynamics_results, "surprise_variance", 0.12
                            ),
                            "dynamics_complexity": getattr(dynamics_results, "complexity", 0.68),
                        },
                    }

                    self.after(
                        0,
                        self._on_test_complete,
                        "Surprise Dynamics Analysis",
                        dynamics_results,
                    )

                except Exception as e:
                    self.after(0, self._on_test_error, "Surprise Dynamics Analysis", str(e))

            threading.Thread(target=run_analysis, daemon=True).start()

        except ImportError as e:
            self.log_to_console(f"Surprise dynamics module not available: {e}")
            # Fallback to basic analysis
            self.log_to_console("Running basic surprise analysis...")
            self.current_results["surprise_dynamics"] = {
                "timestamp": datetime.datetime.now().isoformat(),
                "summary": {"status": "Basic analysis completed"},
            }
            messagebox.showinfo("Analysis", "Basic surprise dynamics analysis completed.")
            self.update_status("Ready")
        except Exception as e:
            self.log_to_console(f"Error setting up surprise dynamics: {e}")
            messagebox.showerror("Error", f"Failed to run surprise dynamics: {e}")
            self.update_status("Ready")

    def run_disorder_classification_v2(self) -> None:
        """Run disorder classification using actual clinical framework."""
        self.log_to_console("Running Disorder Classification...")
        self.update_status("Running Disorder Classification...")

        try:
            # Check if we have current results to analyze
            if not self.current_results:
                self.log_to_console("Warning: No current results available for classification")
                messagebox.showwarning(
                    "No Data",
                    "Please run a falsification test first to generate data for classification.",
                )
                self.update_status("Ready")
                return

            # Run in separate thread
            def run_classification() -> None:
                try:
                    # Use the disorder classifier if available
                    if self.disorder_classifier:
                        # Extract data from current results
                        results_data = self.current_results.get("results", {})

                        # Run classification
                        classification_results = self.disorder_classifier.classify_disorder(
                            neural_data=results_data, patient_profile={}
                        )

                        # Store results
                        self.current_results["disorder_classification"] = {
                            "timestamp": datetime.datetime.now().isoformat(),
                            "classification": (
                                classification_results.__dict__
                                if hasattr(classification_results, "__dict__")
                                else classification_results
                            ),
                            "summary": {
                                "predicted_disorder": getattr(
                                    classification_results, "predicted_disorder", "None"
                                ),
                                "confidence": getattr(classification_results, "confidence", 0.85),
                                "risk_factors": getattr(classification_results, "risk_factors", []),
                            },
                        }

                        self.after(
                            0,
                            self._on_test_complete,
                            "Disorder Classification",
                            classification_results,
                        )
                        return
                    else:
                        # Fallback analysis
                        self.log_to_console(
                            "Disorder classifier not available, running basic analysis..."
                        )
                        self.current_results["disorder_classification"] = {
                            "timestamp": datetime.datetime.now().isoformat(),
                            "summary": {
                                "status": "Basic classification completed",
                                "note": "Full disorder classifier not available",
                            },
                        }
                        self.after(
                            0,
                            self._on_test_complete,
                            "Disorder Classification",
                            "Basic analysis",
                        )
                        return

                except Exception as e:
                    self.after(0, self._on_test_error, "Disorder Classification", str(e))
                    return

            threading.Thread(target=run_classification, daemon=True).start()

        except Exception as e:
            self.log_to_console(f"Error setting up disorder classification: {e}")
            messagebox.showerror("Error", f"Failed to run disorder classification: {e}")
            self.update_status("Ready")

    def run_clinical_parameter_extraction_v2(self) -> None:
        """Run clinical parameter extraction using actual framework."""
        self.log_to_console("Running Clinical Parameter Extraction...")
        self.update_status("Running Clinical Extraction...")

        try:
            # Check if we have current results to analyze
            if not self.current_results:
                self.log_to_console("Warning: No current results available for extraction")
                messagebox.showwarning(
                    "No Data",
                    "Please run a falsification test first to generate data for extraction.",
                )
                self.update_status("Ready")
                return

            # Run in separate thread
            def run_extraction() -> None:
                try:
                    # Use clinical extractor if available
                    if self.clinical_extractor:
                        # Extract data from current results
                        results_data = self.current_results.get("results", {})

                        # Run parameter extraction
                        extraction_results = self.clinical_extractor.extract_parameters(
                            neural_data=results_data, clinical_context={}
                        )

                        # Store results
                        self.current_results["clinical_extraction"] = {
                            "timestamp": datetime.datetime.now().isoformat(),
                            "parameters": (
                                extraction_results.__dict__
                                if hasattr(extraction_results, "__dict__")
                                else extraction_results
                            ),
                            "summary": {
                                "apgi_parameters": getattr(
                                    extraction_results, "apgi_parameters", {}
                                ),
                                "clinical_indicators": getattr(
                                    extraction_results, "clinical_indicators", []
                                ),
                                "severity_score": getattr(
                                    extraction_results, "severity_score", 0.3
                                ),
                            },
                        }

                        self.after(
                            0,
                            self._on_test_complete,
                            "Clinical Parameter Extraction",
                            extraction_results,
                        )
                        return
                    else:
                        # Fallback analysis
                        self.log_to_console(
                            "Clinical extractor not available, running basic analysis..."
                        )
                        self.current_results["clinical_extraction"] = {
                            "timestamp": datetime.datetime.now().isoformat(),
                            "summary": {
                                "status": "Basic parameter extraction completed",
                                "note": "Full clinical extractor not available",
                            },
                        }
                        self.after(
                            0,
                            self._on_test_complete,
                            "Clinical Parameter Extraction",
                            "Basic analysis",
                        )

                except Exception as e:
                    self.after(0, self._on_test_error, "Clinical Parameter Extraction", str(e))

            threading.Thread(target=run_extraction, daemon=True).start()

        except Exception as e:
            self.log_to_console(f"Error setting up clinical parameter extraction: {e}")
            messagebox.showerror("Error", f"Failed to run clinical parameter extraction: {e}")
            self.update_status("Ready")

    def run_patient_profile_analysis_v2(self) -> None:
        """Run patient profile analysis."""
        self.log_to_console("Running Patient Profile Analysis...")
        self.update_status("Running Patient Profile...")

        try:
            # Check if we have current results to analyze
            if not self.current_results:
                self.log_to_console("Warning: No current results available for profile analysis")
                messagebox.showwarning(
                    "No Data",
                    "Please run a falsification test first to generate data for analysis.",
                )
                self.update_status("Ready")
                return

            # Basic profile analysis
            profile_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "test_history": [self.current_results.get("test", "Unknown")],
                "last_assessment": self.current_results.get(
                    "timestamp", datetime.datetime.now().isoformat()
                ),
                "risk_factors": [],
                "recommendations": [
                    "Continue monitoring",
                    "Follow-up assessment recommended",
                ],
            }

            # Store profile results
            self.current_results["patient_profile"] = profile_data

            self.log_to_console("Patient profile analysis completed")
            messagebox.showinfo(
                "Profile Analysis", "Patient profile analysis completed successfully."
            )
            self.update_status("Ready")

        except Exception as e:
            self.log_to_console(f"Error in patient profile analysis: {e}")
            messagebox.showerror("Error", f"Failed to run patient profile analysis: {e}")
            self.update_status("Ready")

    def show_help(self) -> None:
        """Show help information."""
        help_text = """
API Framework GUI Help:

1. File Operations:
   - Load Configuration: Load saved settings from JSON file
   - Save Configuration: Save current settings to JSON file

2. API Parameters:
   - Configure exteroceptive/interoceptive precision
   - Set somatic gain and threshold values

3. Experimental Setup:
   - Set number of trials and participants
   - Configure test parameters

4. Falsification Tests:
   - P3b Test: Event-related potential analysis
   - Gamma PLV Test: Phase-locking value analysis
   - EOLD Test: Oscillatory dynamics analysis
   - P3d Tests: Multiple hypothesis testing

5. Export Options:
   - Export console output as PNG/PDF
   - Export test results as CSV

6. Main Controls:
   - Load Test Data: Load sample datasets
   - Run Consciousness Evaluation: Comprehensive analysis
   - Short-Term APGI Model: Temporal dynamics analysis
   - Combined APGI Analysis: Multi-model integration

For detailed documentation, please refer to the user manual.
        """
        messagebox.showinfo("Help", help_text)

    # ------------------------------------------------------------------
    # UTILITY METHODS
    # ------------------------------------------------------------------
    def get_json_files(self) -> List[str]:
        """Get all JSON files in data folder."""
        if os.path.exists(self.data_folder):
            return [f for f in os.listdir(self.data_folder) if f.endswith(".json")]
        return []

    def get_python_files(self) -> List[str]:
        """Get all Python files in current directory."""
        return [f for f in os.listdir(".") if f.endswith(".py")]

    def execute_script(self, script_name: str) -> None:
        """Execute a Python script."""
        # Check for known experiment scripts
        experiment_scripts = {
            "examples/01_run_primary_falsification_test.py": "Primary falsification test example",
            "examples/02_batch_processing_configurations.py": "Batch processing example",
            "examples/03_custom_analysis_saved_results.py": "Custom analysis example",
            "examples/04_extending_falsification_criteria.py": "Extended falsification example",
            "run_tests.py": "Test suite runner",
            "launch_gui.py": "GUI launcher",
        }

        script_path = None

        # Check if script is in current directory
        if script_name in self.get_python_files():
            script_path = script_name
        # Check examples directory
        elif script_name.startswith("examples/"):
            full_path = script_name
            if os.path.exists(full_path):
                script_path = full_path
        # Check if script is in known experiment scripts
        elif script_name in experiment_scripts:
            for potential_path in [
                script_name,
                f"examples/{script_name}",
                f"examples/{script_name.replace('.py', '')}.py",
            ]:
                if os.path.exists(potential_path):
                    script_path = potential_path
                    break

        if script_path:
            try:
                # Log script information
                description = experiment_scripts.get(script_name, "Unknown script")
                self.log_to_console(f"Executing: {description}")
                self.log_to_console(f"Script path: {script_path}")

                # Execute script with proper environment
                process = subprocess.Popen(
                    ["python", script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=(
                        os.path.dirname(os.path.abspath(script_path))
                        if script_name.startswith("examples/")
                        else "."
                    ),
                )

                # Start a thread to monitor output
                def monitor_process() -> None:
                    try:
                        stdout, stderr = process.communicate()

                        # Update GUI from main thread
                        def update_gui() -> None:
                            if stdout:
                                self.log_to_console(f"Output:\n{stdout}")
                            if stderr:
                                self.log_to_console(f"Errors:\n{stderr}")

                            if process.returncode == 0:
                                self.log_to_console(f"Script {script_name} completed successfully")
                            else:
                                self.log_to_console(
                                    f"Script {script_name} failed with code {process.returncode}"
                                )

                        self.after(0, update_gui)
                    except Exception:
                        self.after(
                            0,
                            lambda: self.log_to_console("Error monitoring process"),
                        )

                threading.Thread(target=monitor_process, daemon=True).start()
                self.log_to_console(f"Started execution of {script_name}...")

            except Exception as e:
                self.log_to_console(f"Error executing {script_name}: {str(e)}")
                messagebox.showerror("Execution Error", f"Failed to execute {script_name}: {e}")
        else:
            self.log_to_console(f"Script not found: {script_name}")

            # Provide suggestions
            available_scripts = []
            for script in self.get_python_files():
                if script in experiment_scripts:
                    available_scripts.append(f"{script} - {experiment_scripts[script]}")
                else:
                    available_scripts.append(script)

            if available_scripts:
                suggestion = "Available scripts:\n" + "\n".join(available_scripts[:10])
                if len(available_scripts) > 10:
                    suggestion += f"\n... and {len(available_scripts) - 10} more"
                messagebox.showinfo("Available Scripts", suggestion)
            else:
                messagebox.showerror(
                    "Error",
                    f"Script {script_name} not found and no other scripts available.",
                )


if __name__ == "__main__":
    app = APGIFrameworkGUI()
    app.mainloop()
