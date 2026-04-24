"""Configuration constants for the APGI Framework.

This module contains all hardcoded values extracted from the codebase
to improve maintainability and make configuration more explicit.
"""


# GUI Layout Constants
class GUIConstants:
    """Constants for GUI layout and styling."""

    # Window dimensions
    DEFAULT_WINDOW_WIDTH = 1200
    DEFAULT_WINDOW_HEIGHT = 800
    MIN_WINDOW_WIDTH = 800
    MIN_WINDOW_HEIGHT = 600

    # Padding and spacing
    DEFAULT_PADDING = 10
    SMALL_PADDING = 5
    LARGE_PADDING = 20

    # Font sizes
    TITLE_FONT_SIZE = 16
    HEADER_FONT_SIZE = 14
    DEFAULT_FONT_SIZE = 12
    SMALL_FONT_SIZE = 10

    # Widget dimensions
    DEFAULT_ENTRY_WIDTH = 30
    LARGE_ENTRY_WIDTH = 40
    TEXT_WIDGET_HEIGHT = 10
    SMALL_TEXT_HEIGHT = 3

    # Grid spacing
    GRID_PADDING_X = 5
    GRID_PADDING_Y = 5

    # Thread and performance settings
    THREAD_POOL_SIZE = 4
    PLOT_DPI = 100
    EXPORT_DPI = 300
    CONSOLE_MAX_LINES = 1000
    VALIDATION_TIMEOUT = 5.0

    # Window layout ratios
    WINDOW_WIDTH_RATIO = 0.8
    WINDOW_HEIGHT_RATIO = 0.8
    MAX_WINDOW_WIDTH = 2000
    MAX_WINDOW_HEIGHT = 1200
    SIDEBAR_WIDTH = 350
    STATUS_BAR_HEIGHT = 30
    MAX_ERROR_DISPLAY = 5

    # Color schemes
    SIDEBAR_BG = "#f0f0f0"
    MAIN_BG = "white"
    STATUS_BAR_BG = "#e0e0e0"
    SUCCESS_COLOR = "#2E8B57"
    WARNING_COLOR = "#FFA500"
    ERROR_COLOR = "#DC143C"
    INFO_COLOR = "#4682B4"

    # Default parameter values
    DEFAULT_EXTEROCEPTIVE_PRECISION = 1.0
    DEFAULT_INTEROCEPTIVE_PRECISION = 1.0
    DEFAULT_SOMATIC_GAIN = 1.0
    DEFAULT_THRESHOLD = 1.0
    DEFAULT_STEEPNESS = 1.0
    DEFAULT_NUM_TRIALS = 100
    DEFAULT_N_PARTICIPANTS = 10
    DEFAULT_SESSION_DURATION = 60.0


# Timing Constants
class TimingConstants:
    """Constants for timing and delays."""

    # Sleep durations (seconds)
    SHORT_DELAY = 0.1
    MEDIUM_DELAY = 0.5
    LONG_DELAY = 1.0
    GUI_LOAD_DELAY = 2.0
    SIMULATION_DELAY = 3.0

    # Timeouts
    DEFAULT_TIMEOUT = 30
    LONG_TIMEOUT = 60

    # Update intervals
    STATUS_UPDATE_INTERVAL = 1000  # milliseconds
    PROGRESS_UPDATE_INTERVAL = 100  # milliseconds


# Data Processing Constants
class DataConstants:
    """Constants for data processing and analysis."""

    # Queue sizes
    DEFAULT_QUEUE_SIZE = 1000
    LARGE_QUEUE_SIZE = 5000

    # Sample rates
    DEFAULT_SAMPLE_RATE = 1000  # Hz
    MIN_SAMPLE_RATE = 125  # Hz
    MAX_SAMPLE_RATE = 2000  # Hz

    # Analysis parameters
    DEFAULT_EPOCH_DURATION = 2.0  # seconds
    MIN_EPOCH_DURATION = 0.1  # seconds
    MAX_EPOCH_DURATION = 10.0  # seconds

    DEFAULT_BASELINE_DURATION = 0.5  # seconds
    MIN_BASELINE_DURATION = 0.1  # seconds
    MAX_BASELINE_DURATION = 2.0  # seconds


# Validation Constants
class ValidationConstants:
    """Constants for validation and testing."""

    # Test parameters
    MIN_TEST_PARTICIPANTS = 1
    DEFAULT_TEST_PARTICIPANTS = 5
    MAX_TEST_PARTICIPANTS = 100

    MIN_TEST_TRIALS = 5
    DEFAULT_TEST_TRIALS = 100
    MAX_TEST_TRIALS = 1000

    # Validation thresholds
    MIN_CONTOUR_CORNERS = 4
    MAX_CONTOUR_CORNERS = 6

    # Screenshot limits
    MAX_SCREENSHOTS = 18
    MAX_WINDOW_FIND_ATTEMPTS = 3


# Model Parameters Constants
class ModelConstants:
    """Constants for APGI model parameters."""

    # Default parameter values
    DEFAULT_LEARNING_RATE = 0.01
    DEFAULT_PRECISION_WEIGHT = 1.0
    DEFAULT_PREDICTION_ERROR_THRESHOLD = 0.5
    DEFAULT_INTEROCEPTIVE_GAIN = 1.0
    DEFAULT_SOMATIC_BIAS = 0.0
    DEFAULT_IGNITION_THRESHOLD = 2.0
    DEFAULT_MAX_SIGMOID_INPUT = 500.0  # Prevent overflow in sigmoid calculations

    # Parameter ranges
    LEARNING_RATE_RANGE = (0.0001, 1.0)
    PRECISION_WEIGHT_RANGE = (0.1, 10.0)
    PREDICTION_ERROR_RANGE = (0.01, 2.0)
    INTEROCEPTIVE_GAIN_RANGE = (0.1, 5.0)
    SOMATIC_BIAS_RANGE = (-2.0, 2.0)
    IGNITION_THRESHOLD_RANGE = (0.5, 5.0)
    MAX_SIGMOID_INPUT_RANGE = (
        100.0,
        1000.0,
    )  # Reasonable range for numerical stability


# File and Path Constants
class PathConstants:
    """Constants for file paths and directories."""

    # Default directories
    DEFAULT_DATA_DIR = "data"
    DEFAULT_LOGS_DIR = "logs"
    DEFAULT_RESULTS_DIR = "results"
    DEFAULT_CONFIG_DIR = "config"

    # File extensions
    DATA_FILE_EXTENSION = ".csv"
    CONFIG_FILE_EXTENSION = ".json"
    LOG_FILE_EXTENSION = ".log"

    # Screenshot settings
    SCREENSHOT_DIR = "screenshots"
    REPORTS_DIR = "reports"


# Network Constants
class NetworkConstants:
    """Constants for network and communication."""

    # Default ports
    DEFAULT_WEB_PORT = 8080
    DEFAULT_WEBSOCKET_PORT = 8081

    # Connection settings
    DEFAULT_HOST = "localhost"
    CONNECTION_RETRY_ATTEMPTS = 3
    CONNECTION_TIMEOUT = 10  # seconds


# Performance Constants
class PerformanceConstants:
    """Constants for performance monitoring and limits."""

    # Memory limits
    DEFAULT_MEMORY_LIMIT_MB = 1024
    WARNING_MEMORY_THRESHOLD_MB = 512

    # Processing limits
    MAX_CONCURRENT_PROCESSES = 4
    DEFAULT_BATCH_SIZE = 100

    # Plot settings
    DEFAULT_LINE_WIDTH = 2
    THIN_LINE_WIDTH = 1
    PLOT_ALPHA = 0.7


# Visualization Constants
class VisualizationConstants:
    """Constants for data visualization and plotting."""

    # Plot dimensions
    DEFAULT_PLOT_HEIGHT = 800
    DEFAULT_PLOT_WIDTH = 1200
    SMALL_PLOT_HEIGHT = 400
    LARGE_PLOT_HEIGHT = 1000

    # Histogram settings
    DEFAULT_HISTOGRAM_BINS = 30
    MIN_HISTOGRAM_BINS = 10
    MAX_HISTOGRAM_BINS = 100

    # Marker and line settings
    DEFAULT_MARKER_SIZE = 8
    SMALL_MARKER_SIZE = 4
    LARGE_MARKER_SIZE = 12
    DEFAULT_LINE_WIDTH = 2
    THIN_LINE_WIDTH = 1
    THICK_LINE_WIDTH = 3

    # Statistical thresholds for visualization
    SIGNIFICANCE_THRESHOLD = 0.05
    EFFECT_SIZE_THRESHOLD = 0.5

    # Color settings
    DEFAULT_ALPHA = 0.7
    HIGHLIGHT_ALPHA = 0.9
    BACKGROUND_ALPHA = 0.3

    # Template settings
    DEFAULT_TEMPLATE = "plotly_white"
    DARK_TEMPLATE = "plotly_dark"
