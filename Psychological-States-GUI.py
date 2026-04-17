"""
APGI Psychological State Parameter Library with Advanced Visualizations
=============================================================================

Complete parameter mappings for 51 psychological states with embedded
interactive visualizations displayed exclusively within the GUI application.

All visualizations are rendered directly in the right panel of the application
with no external browser dependencies, save options, or display capabilities.

=============================================================================
"""

import hashlib
import json
import logging
import os
import shutil
import signal
import sys
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import httpx
import time
from concurrent.futures import ThreadPoolExecutor
from apgi_simulation.self_model.state_classifier import StateClassifier

# Import theme manager
try:
    from apgi_gui.theme_manager import ThemeManager

    THEME_MANAGER_AVAILABLE = True
except ImportError:
    THEME_MANAGER_AVAILABLE = False
    print("Warning: Theme manager not available. Theme support disabled.")

# Import ToolTip from components
try:
    from apgi_gui.components.core import ToolTip

    TOOLTIP_AVAILABLE = True
except ImportError:
    TOOLTIP_AVAILABLE = False
    print("Warning: ToolTip component not available.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Import genetic data connector
try:
    from utils.geno_states import PGCDataConnector

    GENETIC_DATA_AVAILABLE = True
except ImportError as e:
    GENETIC_DATA_AVAILABLE = False
    print(f"Warning: Genetic data connector not available: {e}")

# HF API Base
HF_API_BASE = "https://huggingface.co/api"
CACHE_FILE = "apgi_hf_cache.json"

# State Keywords for HF Search (Integrated from load_geno_data.py)
STATE_KEYWORDS = {
    "flow": ["flow state", "attention control", "task performance", "cognitive control"],
    "focus": ["attention", "selective attention", "executive control"],
    "serenity": ["calm", "relaxation", "parasympathetic", "stress reduction"],
    "mindfulness": ["mindfulness", "meditation", "awareness", "interoception"],
    "joy": ["joy", "positive emotion", "reward", "dopamine"],
    "amusement": ["humor", "laughter"],
    "pride": ["self perception", "self evaluation"],
    "love": ["attachment", "social bonding"],
    "gratitude": ["gratitude", "prosocial"],
    "hope": ["optimism", "future prediction"],
    "curiosity": ["curiosity", "exploration", "intrinsic motivation"],
    "creativity": ["creativity", "divergent thinking"],
    "inspiration": ["insight", "a-ha"],
    "hyperfocus": ["hyperfocus", "deep work"],
    "fatigue": ["fatigue", "cognitive load"],
    "anxiety": ["anxiety", "threat detection"],
    "fear": ["fear", "amygdala"],
    "depression": ["depression", "mood disorder"],
}

# GUI imports with graceful fallbacks
try:
    import tkinter as tk
    from tkinter import messagebox, ttk
    from traceback import format_exc

    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    logger.warning("Tkinter not available for GUI interface")


try:
    import plotly.graph_objects as go  # type: ignore
    import plotly.io as pio  # type: ignore
    from plotly.subplots import make_subplots  # type: ignore

    PLOTLY_AVAILABLE = True
    pio.templates.default = "plotly_white"
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("Plotly not available. Install with: pip install plotly")

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("Matplotlib not available. Install with: pip install matplotlib")

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("Pandas not available. Install with: pip install pandas")

# Try to import tkinterweb for HTML rendering, fallback to built-in approach
try:
    try:
        from tkinterweb import HTMLFrame  # type: ignore

        TKINTERWEB_AVAILABLE = True
    except ImportError:
        TKINTERWEB_AVAILABLE = False
except Exception as e:
    TKINTERWEB_AVAILABLE = False
    logger.warning(f"Could not import tkinterweb: {e}")

# No external browser dependencies or save options needed - all visualizations are embedded


@dataclass
class APGIParameters:
    """APGI parameter set with proper type safety"""

    Pi_e: float
    Pi_i_baseline: float
    Pi_i_eff: float
    theta_t: float
    S_t: float
    M_ca: float
    beta: float
    z_e: float
    z_i: float

    def __post_init__(self) -> None:
        """Validate parameters are within physiological bounds"""
        if not (0.1 <= self.Pi_e <= 10.0):
            raise ValueError(f"Pi_e must be in [0.1, 10], got {self.Pi_e}")
        if not (0.1 <= self.Pi_i_baseline <= 10.0):
            raise ValueError(f"Pi_i_baseline must be in [0.1, 10], got {self.Pi_i_baseline}")
        if not (0.1 <= self.Pi_i_eff <= 10.0):
            raise ValueError(f"Pi_i_eff must be in [0.1, 10], got {self.Pi_i_eff}")
        if not (-2.0 <= self.M_ca <= 2.0):
            raise ValueError(f"M_ca must be in [-2, 2], got {self.M_ca}")
        if not (0.3 <= self.beta <= 0.8):
            raise ValueError(f"beta must be in [0.3, 0.8], got {self.beta}")
        if not (-5.0 <= self.z_e <= 5.0):
            raise ValueError(f"z_e must be in [-5, 5], got {self.z_e}")
        if not (-5.0 <= self.z_i <= 5.0):
            raise ValueError(f"z_i must be in [-5, 5], got {self.z_i}")
        if not (-5.0 <= self.theta_t <= 5.0):
            raise ValueError(f"theta_t must be in [-5, 5], got {self.theta_t}")
        if not (0.0 <= self.S_t <= 50.0):
            raise ValueError(f"S_t must be in [0, 50], got {self.S_t}")

    @property
    def ignition_probability(self) -> float:
        """P(ignite) = σ(S_t - θ_t)"""
        return 1.0 / (1.0 + np.exp(-(self.S_t - self.theta_t)))

    def compute_ignition_probability(self) -> float:
        """Compute P(ignite) = σ(S_t - θ_t)"""
        return self.ignition_probability

    def verify_S_t(self) -> bool:
        """Verify S_t matches the formula: S_t = Π_e·|z_e| + Π_i_eff·|z_i|

        Returns:
            True if S_t is correctly computed, False otherwise
        """
        try:
            computed = self.Pi_e * abs(self.z_e) + self.Pi_i_eff * abs(self.z_i)
            return np.isclose(self.S_t, computed, rtol=0.01)  # type: ignore
        except (TypeError, AttributeError):
            return False

    def verify_Pi_i_eff(self) -> bool:
        """Verify Π_i_eff matches the formula: Π_i_eff = Π_i_baseline · exp(β·M)

        Returns:
            True if Pi_i_eff is correctly computed, False otherwise
        """
        try:
            computed = self.Pi_i_baseline * np.exp(self.beta * self.M_ca)
            computed = np.clip(computed, 0.1, 10.0)
            return np.isclose(self.Pi_i_eff, computed, rtol=0.05)
        except (TypeError, AttributeError):
            return False

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for visualization"""
        return {
            "Pi_e": self.Pi_e,
            "Pi_i_baseline": self.Pi_i_baseline,
            "Pi_i_eff": self.Pi_i_eff,
            "theta_t": self.theta_t,
            "S_t": self.S_t,
            "M_ca": self.M_ca,
            "beta": self.beta,
            "z_e": self.z_e,
            "z_i": self.z_i,
            "ignition_probability": self.ignition_probability,
        }


@dataclass
class PsychologicalState:
    """Extended state representation with metadata"""

    name: str
    parameters: APGIParameters
    category: str
    description: str = ""
    phenomenology: List[str] = field(default_factory=list)
    distinguishing_features: Dict[str, str] = field(default_factory=dict)
    pathological_variant: Optional[str] = None
    temporal_dynamics: Optional[str] = None
    color: Optional[str] = None


class StateCategory(Enum):
    """Categories of psychological states with colors"""

    OPTIMAL_FUNCTIONING = ("#2E86AB", "Optimal Functioning")
    POSITIVE_AFFECTIVE = ("#48BF84", "Positive Affective")
    COGNITIVE_ATTENTIONAL = ("#FF9F1C", "Cognitive/Attentional")
    AVERSIVE_AFFECTIVE = ("#E63946", "Aversive Affective")
    PATHOLOGICAL_EXTREME = ("#7209B7", "Pathological/Extreme")
    ALTERED_BOUNDARY = ("#8338EC", "Altered/Boundary")
    TRANSITIONAL_CONTEXTUAL = ("#06D6A0", "Transitional/Contextual")
    UNELABORATED = ("#8D99AE", "Unelaborated")

    def __init__(self, color: str, display_name: str):
        self._color = color
        self._display_name = display_name

    @property
    def color(self) -> str:
        return self._color

    @property
    def display_name(self) -> str:
        return self._display_name


# =============================================================================
# ENHANCED EMBEDDED VISUALIZATION ENGINE
# =============================================================================


class EmbeddedVisualizationRenderer:
    """Render Plotly visualizations for embedded display in Tkinter"""

    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize renderer with optional temp directory"""
        self.temp_dir = temp_dir
        self.current_file: Optional[str] = None
        self._cleanup_on_exit = True
        self._temp_dir_initialized = False

    def _ensure_temp_dir(self) -> str:
        """Ensure temp directory exists (lazy initialization)"""
        if not self._temp_dir_initialized or self.temp_dir is None:
            self.temp_dir = tempfile.mkdtemp(prefix="apgi_viz_")
            self._temp_dir_initialized = True
        return self.temp_dir

    def __del__(self) -> None:
        """Cleanup temporary files on object destruction"""
        # Note: __del__ is not guaranteed to be called
        # Use force_cleanup() for explicit cleanup
        try:
            self.cleanup_temp_files()
        except Exception:
            # Silently ignore cleanup errors during destruction
            pass

    def force_cleanup(self) -> None:
        """Force cleanup of temporary resources"""
        self._cleanup_on_exit = True
        self.cleanup_temp_files()

    def cleanup_temp_files(self) -> None:
        """Manually cleanup temporary files"""
        if hasattr(self, "temp_dir") and self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self._temp_dir_initialized = False
            except (OSError, PermissionError):
                pass

    def render_figure_to_html(self, fig: go.Figure, filename: str = "current.html") -> str:
        """
        Render a Plotly figure to HTML with embedded resources.

        Returns:
            Path to the generated HTML file
        """
        filepath = os.path.join(self._ensure_temp_dir(), filename)

        # Check for offline Plotly library
        offline_js = self._get_offline_plotly_js()

        # Create HTML with responsive sizing and proper scaling
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>APGI Visualization</title>
    {offline_js}
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        html, body {{
            width: 100%;
            height: 100%;
            overflow: hidden;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f8f9fa;
        }}
        #plot {{
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .loading {{
            font-size: 16px;
            color: #666;
        }}
        .info-panel {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(255, 255, 255, 0.95);
            padding: 12px 16px;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            font-size: 12px;
            max-width: 300px;
            z-index: 1000;
            display: none;
        }}
        .info-panel.show {{
            display: block;
        }}
    </style>
</head>
<body>
    <div id="plot" class="loading">Loading visualization...</div>
    <div class="info-panel" id="info-panel"></div>

    <script>
        let plotData = null;
        let layout = null;

        // Function to initialize plot
        function initPlot() {{
            const plotJson = {fig.to_json()};
            const figure = JSON.parse(plotJson);

            // Ensure responsive sizing
            figure.layout.autosize = true;
            figure.layout.margin = {{l: 50, r: 50, b: 50, t: 50, pad: 4}};
            figure.layout.paper_bgcolor = '#f8f9fa';
            figure.layout.plot_bgcolor = 'white';

            // Create the plot with responsive config
            Plotly.newPlot('plot', figure.data, figure.layout, {{
                responsive: true,
                displayModeBar: true,
                displaylogo: false,
                modeBarButtonsToRemove: ['lasso2d', 'select2d']
            }});

            // Handle window resizing
            window.addEventListener('resize', function() {{
                Plotly.Plots.resize('plot');
            }});

            // Remove loading message
            const plotDiv = document.getElementById('plot');
            if (plotDiv.classList.contains('loading')) {{
                plotDiv.classList.remove('loading');
            }}
        }}

        // Initialize on load
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', initPlot);
        }} else {{
            initPlot();
        }}

        // Hover info handler
        document.getElementById('plot').addEventListener('plotly_hover', function(data) {{
            const infoPanel = document.getElementById('info-panel');
            if (data.points && data.points.length > 0) {{
                const point = data.points[0];
                let text = '';
                if (point.customdata) {{
                    text = point.customdata;
                }} else if (point.text) {{
                    text = point.text;
                }} else {{
                    text = 'Hover over data points for information';
                }}
                infoPanel.textContent = text;
                infoPanel.classList.add('show');
            }}
        }});

        document.getElementById('plot').addEventListener('plotly_unhover', function() {{
            document.getElementById('info-panel').classList.remove('show');
        }});
    </script>
</body>
</html>
        """

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        self.current_file = filepath
        return filepath

    def _get_offline_plotly_js(self) -> str:
        """Get offline Plotly JS library or fallback to CDN"""
        # Check for environment-specified path first
        env_path = os.environ.get("APGI_PLOTLY_JS_PATH")
        if env_path and os.path.exists(env_path):
            return f'<script src="{env_path}"></script>'

        # Try multiple possible locations for offline Plotly JS
        script_dir = os.path.dirname(os.path.abspath(__file__))
        offline_paths = [
            os.path.join(script_dir, "static", "plotly.min.js"),
            os.path.join(script_dir, "..", "static", "plotly.min.js"),
            os.path.join(os.getcwd(), "static", "plotly.min.js"),
        ]

        for offline_path in offline_paths:
            if os.path.exists(offline_path):
                return f'<script src="{offline_path}"></script>'

        # Fallback to CDN
        return '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>'


class VisualizationCache:
    """Simple cache for generated visualizations to improve performance"""

    def __init__(self, max_size: int = 50):
        self.cache: Dict[str, go.Figure] = {}
        self.max_size = max_size

    def _get_cache_key(self, viz_type: str, **kwargs: Any) -> str:
        """Generate cache key from visualization parameters"""
        try:
            # Sort and convert to string for hash
            key_parts = [viz_type]
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (list, tuple)):
                    key_parts.append(f"{k}={'|'.join(str(x) for x in v)}")
                else:
                    key_parts.append(f"{k}={v}")
            key_data = "_".join(key_parts)
            return hashlib.md5(key_data.encode()).hexdigest()
        except Exception:
            # Fallback for unhashable types
            key_data = f"{viz_type}_{str(kwargs)}"
            return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, viz_type: str, **kwargs: Any) -> Optional[go.Figure]:
        """Get cached visualization if available"""
        key = self._get_cache_key(viz_type, **kwargs)
        return self.cache.get(key)

    def put(self, viz_type: str, fig: go.Figure, **kwargs: Any) -> None:
        """Cache visualization with size management"""
        key = self._get_cache_key(viz_type, **kwargs)

        # Remove oldest if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[key] = fig

    def clear(self) -> None:
        """Clear all cached visualizations"""
        self.cache.clear()


class APGIVisualizer:
    """Modern, eloquent visualizations for APGI psychological states"""

    PALETTES = {
        "categorical": {
            StateCategory.OPTIMAL_FUNCTIONING: "#2E86AB",
            StateCategory.POSITIVE_AFFECTIVE: "#48BF84",
            StateCategory.COGNITIVE_ATTENTIONAL: "#FF9F1C",
            StateCategory.AVERSIVE_AFFECTIVE: "#E63946",
            StateCategory.PATHOLOGICAL_EXTREME: "#7209B7",
            StateCategory.ALTERED_BOUNDARY: "#8338EC",
            StateCategory.TRANSITIONAL_CONTEXTUAL: "#06D6A0",
            StateCategory.UNELABORATED: "#8D99AE",
        },
        "sequential": [
            "#003f5c",
            "#2f4b7c",
            "#665191",
            "#a05195",
            "#d45087",
            "#f95d6a",
            "#ff7c43",
            "#ffa600",
        ],
        "diverging": [
            "#2166ac",
            "#4393c3",
            "#92c5de",
            "#d1e5f0",
            "#f7f7f7",
            "#fddbc7",
            "#f4a582",
            "#d6604d",
            "#b2182b",
        ],
    }

    def __init__(
        self,
        states_dict: Dict[str, APGIParameters],
        categories_dict: Dict[str, StateCategory],
    ):
        """Initialize visualizer with states and categories."""
        self.states = states_dict
        self.categories = categories_dict
        self.renderer = EmbeddedVisualizationRenderer()
        self.cache = VisualizationCache()

        self.df: Optional[pd.DataFrame] = None

        if PANDAS_AVAILABLE:
            self.df = self._create_dataframe()
        else:
            self.df = None

    def _normalize_parameter(self, value: float, param_name: str) -> float:
        """Normalize a parameter value to [0, 1] range"""
        if self.df is None or param_name not in self.df.columns:
            return value

        col_min = self.df[param_name].min()
        col_max = self.df[param_name].max()

        if col_max == col_min:
            return 0.5  # Avoid division by zero

        if param_name in ["theta_t", "M_ca"]:
            return (value - col_min) / (col_max - col_min)
        else:
            return value / col_max

    def _create_3d_marker(self, size: float, color: str) -> Dict[str, Any]:
        """Create standardized 3D marker configuration"""
        return dict(
            size=size,
            color=color,
            opacity=0.8,
            line=dict(width=2, color="white"),
            symbol="circle",
        )

    def _create_polar_values(self, params: APGIParameters) -> List[float]:
        """Create normalized values for polar chart"""
        values = [
            float(params.Pi_e / 10),
            float(params.Pi_i_eff / 10),
            float((params.theta_t + 3) / 6),
            float((params.M_ca + 2) / 4),
            float(params.compute_ignition_probability()),
        ]
        values.append(values[0])
        return values

    def _create_polar_trace(
        self, params: APGIParameters, state_name: str, is_focus: bool = False
    ) -> go.Scatterpolar:
        """Create a polar chart trace for a state"""
        values = self._create_polar_values(params)
        color = self.categories.get(state_name, StateCategory.UNELABORATED).color
        fill_color, line_color = self._parse_color_with_fallback(color)

        return go.Scatterpolar(
            r=values,
            theta=["Π_e", "Π_i_eff", "θ_t", "M_ca", "P(ign)", "Π_e"],
            fill="toself" if is_focus else "none",
            fillcolor=fill_color if is_focus else None,
            line=dict(color=line_color, width=2 if is_focus else 1),
            opacity=1.0 if is_focus else 0.6,
            name=state_name.replace("_", " ").title(),
            showlegend=True,
        )

    def _create_dataframe(self) -> "pd.DataFrame":
        """Create a pandas DataFrame for visualization"""
        data: List[Dict[str, Any]] = []
        for name, params in self.states.items():
            row: Dict[str, Any] = params.to_dict()
            row["name"] = name
            row["category"] = self.categories.get(name, StateCategory.UNELABORATED).name
            row["category_display"] = self.categories.get(
                name, StateCategory.UNELABORATED
            ).display_name
            row["category_color"] = self.categories.get(name, StateCategory.UNELABORATED).color
            data.append(row)

        df = pd.DataFrame(data)
        df.loc[:, "precision_ratio"] = df["Pi_i_eff"] / df["Pi_e"]
        df.loc[:, "somatic_engagement"] = df["M_ca"] * df["beta"]
        df.loc[:, "prediction_error_total"] = df["z_e"] + df["z_i"]

        return df

    def plot_state_network_3d(
        self,
        dimension1: str = "Pi_e",
        dimension2: str = "Pi_i_eff",
        dimension3: str = "theta_t",
    ) -> Optional[go.Figure]:
        """Create an interactive 3D network visualization of psychological states.

        Args:
            dimension1: First dimension for x-axis
            dimension2: Second dimension for y-axis
            dimension3: Third dimension for z-axis

        Returns:
            Plotly Figure or None if dependencies unavailable
        """
        if not PLOTLY_AVAILABLE or not PANDAS_AVAILABLE:
            logger.warning("Plotly or Pandas not available")
            return None

        if self.df is None or self.df.empty:
            logger.warning("No data available for visualization")
            return None

        # Validate dimensions
        for dim in [dimension1, dimension2, dimension3]:
            if dim not in self.df.columns:
                logger.warning(f"Invalid dimension: {dim}")
                return None

        try:
            fig = go.Figure()

            for idx, row in self.df.iterrows():
                state_name = row["name"]
                size = 15 + (row["S_t"] * 2)
                color = row["category_color"]

                fig.add_trace(
                    go.Scatter3d(
                        x=[row[dimension1]],
                        y=[row[dimension2]],
                        z=[row[dimension3]],
                        mode="markers+text",
                        marker=dict(
                            size=size,
                            color=color,
                            opacity=0.8,
                            line=dict(width=2, color="white"),
                            symbol="circle",
                        ),
                        text=[state_name.replace("_", " ").title()],
                        textposition="top center",
                        hoverinfo="text",
                        hovertext=self._create_hover_text(state_name, row),
                        name=state_name,
                        showlegend=False,
                    )
                )

            fig.update_layout(
                title="APGI Psychological State Network (3D)",
                scene=dict(
                    xaxis_title=dimension1,
                    yaxis_title=dimension2,
                    zaxis_title=dimension3,
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
                    bgcolor="rgba(240,240,240,0.9)",
                ),
                showlegend=True,
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                margin=dict(l=0, r=0, b=0, t=40),
                hovermode="closest",
                template="plotly_white",
            )

            self._add_category_legend(fig)
            return fig
        except Exception as e:
            logger.error(f"Error creating 3D network: {e}")
            return None

    def plot_ignition_landscape(
        self,
        focus_state: Optional[str] = None,
        parameter1: str = "Pi_e",
        parameter2: str = "theta_t",
        resolution: int = 50,
    ) -> Optional[go.Figure]:
        """Create a 3D ignition probability landscape.

        Args:
            focus_state: Optional state to highlight
            parameter1: First parameter for x-axis
            parameter2: Second parameter for y-axis
            resolution: Grid resolution for surface plot

        Returns:
            Plotly Figure or None if dependencies unavailable
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available")
            return None

        if self.df is None or self.df.empty:
            logger.warning("No data available for visualization")
            return None

        # Validate parameters
        for param in [parameter1, parameter2]:
            if param not in self.df.columns:
                logger.warning(f"Invalid parameter: {param}")
                return None

        try:
            p1_range = np.linspace(
                self.df[parameter1].min() * 0.8, self.df[parameter1].max() * 1.2, resolution
            )
            p2_range = np.linspace(
                self.df[parameter2].min() * 0.8, self.df[parameter2].max() * 1.2, resolution
            )

            P1, P2 = np.meshgrid(p1_range, p2_range)

            avg_z_e = self.df["z_e"].mean()
            avg_z_i = self.df["z_i"].mean()
            avg_Pi_i_eff = self.df["Pi_i_eff"].mean()

            S_t = P1 * avg_z_e + avg_Pi_i_eff * avg_z_i
            Z = 1.0 / (1.0 + np.exp(-(S_t - P2)))

            fig = go.Figure(
                data=[
                    go.Surface(
                        z=Z,
                        x=P1,
                        y=P2,
                        colorscale="Viridis",
                        opacity=0.8,
                        contours={
                            "z": {
                                "show": True,
                                "usecolormap": True,
                                "highlightcolor": "limegreen",
                                "project": {"z": True},
                            }
                        },
                        connectgaps=False,
                        hovertemplate="%{x:.2f} vs %{y:.2f}<br>P(ignition): %{z:.3f}<extra></extra>",
                    )
                ]
            )

            # Add state markers
            scatter_x = []
            scatter_y = []
            scatter_z = []
            scatter_colors = []
            scatter_names = []

            for idx, row in self.df.iterrows():
                S_t_actual = row["Pi_e"] * row["z_e"] + row["Pi_i_eff"] * row["z_i"]
                ignition_prob = 1.0 / (1.0 + np.exp(-(S_t_actual - row["theta_t"])))

                scatter_x.append(row[parameter1])
                scatter_y.append(row[parameter2])
                scatter_z.append(ignition_prob)
                scatter_colors.append(row["category_color"])
                scatter_names.append(row["name"])

            fig.add_trace(
                go.Scatter3d(
                    x=scatter_x,
                    y=scatter_y,
                    z=scatter_z,
                    mode="markers+text",
                    marker=dict(
                        size=8,
                        color=scatter_colors,
                        opacity=1.0,
                        line=dict(width=2, color="white"),
                    ),
                    text=[name.replace("_", " ").title() for name in scatter_names],
                    textposition="top center",
                    hoverinfo="text",
                    hovertext=[
                        f"{name}<br>P(ignition)={z:.2%}"
                        for name, z in zip(scatter_names, scatter_z)
                    ],
                    name="Psychological States",
                )
            )

            fig.update_layout(
                title="Ignition Probability Landscape",
                scene=dict(
                    xaxis_title=parameter1,
                    yaxis_title=parameter2,
                    zaxis_title="P(Ignition)",
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.2)),
                ),
                showlegend=True,
                margin=dict(l=0, r=0, b=0, t=40),
                template="plotly_white",
            )

            return fig
        except Exception as e:
            logger.error(f"Error creating ignition landscape: {e}")
            return None

    def plot_state_radar(
        self, state_names: List[str], normalize: bool = False
    ) -> Optional[go.Figure]:
        """Create a radar chart comparing multiple states.

        Args:
            state_names: List of state names to compare
            normalize: Whether to normalize parameter values

        Returns:
            Plotly Figure or None if dependencies unavailable
        """
        if not PLOTLY_AVAILABLE or not PANDAS_AVAILABLE:
            logger.warning("Plotly or Pandas not available")
            return None

        # Edge case: empty or invalid state names
        if not state_names or not isinstance(state_names, list):
            logger.warning("Invalid state names provided")
            return None

        # Filter valid states only
        valid_states = [name for name in state_names if name in self.states]
        if not valid_states:
            logger.warning("No valid states found in provided list")
            return None

        try:
            # Create a simple polar figure (not subplot) to avoid the polar subplot issue
            fig = go.Figure()

            params = ["Pi_e", "Pi_i_eff", "theta_t", "M_ca", "S_t", "z_e", "z_i", "beta"]
            categories = params

            for state_name in valid_states:
                params_obj = self.states[state_name]
                values = []

                for param in params:
                    value = getattr(params_obj, param)

                    if normalize:
                        value = self._normalize_parameter(value, param)

                    values.append(value)

                values.append(values[0])
                color = self.categories.get(state_name, StateCategory.UNELABORATED).color

                # Simplified color parsing with fallback
                fill_color, line_color = self._parse_color_with_fallback(color)

                fig.add_trace(
                    go.Scatterpolar(
                        r=values,
                        theta=categories + [categories[0]],
                        fill="toself",
                        fillcolor=fill_color,
                        line=dict(color=line_color, width=2),
                        name=state_name.replace("_", " ").title(),
                        hoverinfo="text",
                        hovertext=self._create_hover_text(state_name, None),
                    )
                )

            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1.1] if normalize else None)),
                showlegend=True,
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.05),
                title="State Comparison Radar Chart",
                margin=dict(l=100, r=100, b=50, t=50),
                template="plotly_white",
            )

            return fig
        except Exception as e:
            logger.error(f"Error creating radar chart: {e}")
            return None

    def plot_state_transition(self, start_state: str, end_state: str) -> Optional[go.Figure]:
        """Create a visualization of the transition between two psychological states.

        Args:
            start_state: Name of the starting state
            end_state: Name of the ending state

        Returns:
            Plotly Figure showing the transition path or None if unavailable
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available")
            return None

        if start_state not in self.states or end_state not in self.states:
            logger.warning("Invalid states for transition")
            return None

        try:
            # Get state parameters
            start_params = self.states[start_state]
            end_params = self.states[end_state]

            # Create transition path by interpolating parameters
            n_steps = 20
            transition_states = []
            for i in range(n_steps + 1):
                t = i / n_steps
                # Interpolate each parameter
                interpolated = APGIParameters(
                    Pi_e=start_params.Pi_e + t * (end_params.Pi_e - start_params.Pi_e),
                    Pi_i_baseline=start_params.Pi_i_baseline
                    + t * (end_params.Pi_i_baseline - start_params.Pi_i_baseline),
                    Pi_i_eff=start_params.Pi_i_eff
                    + t * (end_params.Pi_i_eff - start_params.Pi_i_eff),
                    theta_t=start_params.theta_t + t * (end_params.theta_t - start_params.theta_t),
                    S_t=start_params.S_t + t * (end_params.S_t - start_params.S_t),
                    M_ca=start_params.M_ca + t * (end_params.M_ca - start_params.M_ca),
                    beta=start_params.beta + t * (end_params.beta - start_params.beta),
                    z_e=start_params.z_e + t * (end_params.z_e - start_params.z_e),
                    z_i=start_params.z_i + t * (end_params.z_i - start_params.z_i),
                )
                transition_states.append(interpolated)

            # Create 3D trajectory visualization
            x_vals = [p.Pi_e for p in transition_states]
            y_vals = [p.Pi_i_eff for p in transition_states]
            z_vals = [p.theta_t for p in transition_states]

            fig = go.Figure()

            # Add trajectory line
            fig.add_trace(
                go.Scatter3d(
                    x=x_vals,
                    y=y_vals,
                    z=z_vals,
                    mode="lines+markers",
                    line=dict(color="blue", width=4),
                    marker=dict(size=6, color="red"),
                    name="Transition Path",
                )
            )

            # Add start and end points
            fig.add_trace(
                go.Scatter3d(
                    x=[x_vals[0]],
                    y=[y_vals[0]],
                    z=[z_vals[0]],
                    mode="markers+text",
                    marker=dict(size=10, color="green"),
                    text=[start_state],
                    textposition="top center",
                    name="Start State",
                )
            )

            fig.add_trace(
                go.Scatter3d(
                    x=[x_vals[-1]],
                    y=[y_vals[-1]],
                    z=[z_vals[-1]],
                    mode="markers+text",
                    marker=dict(size=10, color="orange"),
                    text=[end_state],
                    textposition="top center",
                    name="End State",
                )
            )

            fig.update_layout(
                title=f"State Transition: {start_state} → {end_state}",
                scene=dict(
                    xaxis_title="Pi_e",
                    yaxis_title="Pi_i_eff",
                    zaxis_title="theta_t",
                ),
                showlegend=True,
            )

            return fig
        except Exception as e:
            logger.error(f"Error creating transition visualization: {e}")
            return None

    def plot_comparative_analysis(self, state_names: List[str]) -> Optional[go.Figure]:
        """Create a comparative analysis table of multiple psychological states.

        Args:
            state_names: List of state names to compare

        Returns:
            Plotly Figure with comparison table or None if unavailable
        """
        if not PLOTLY_AVAILABLE or not PANDAS_AVAILABLE:
            logger.warning("Plotly or Pandas not available")
            return None

        # Filter valid states
        valid_states = [name for name in state_names if name in self.states]
        if len(valid_states) < 2:
            logger.warning("Need at least 2 valid states for comparison")
            return None

        try:
            # Get parameter data for each state
            param_data = {}
            parameters = [
                "Pi_e",
                "Pi_i_baseline",
                "Pi_i_eff",
                "theta_t",
                "S_t",
                "M_ca",
                "beta",
                "z_e",
                "z_i",
                "ignition_probability",
            ]

            for param in parameters:
                param_data[param] = [getattr(self.states[state], param) for state in valid_states]

            # Create table data
            header = ["Parameter"] + valid_states + ["Mean", "Std", "Range"]
            rows = []

            for param in parameters:
                values = param_data[param]
                mean_val = np.mean(values)
                std_val = np.std(values)
                range_val = max(values) - min(values)

                row = (
                    [param]
                    + [f"{v:.3f}" for v in values]
                    + [f"{mean_val:.3f}", f"{std_val:.3f}", f"{range_val:.3f}"]
                )
                rows.append(row)

            # Create table figure
            fig = go.Figure(
                data=[
                    go.Table(
                        columnwidth=[150] + [100] * (len(valid_states) + 3),
                        header=dict(
                            values=header,
                            fill_color="lightblue",
                            align="center",
                            font=dict(size=12, color="black"),
                            height=40,
                        ),
                        cells=dict(
                            values=list(zip(*rows)),
                            fill_color="white",
                            align=["left"] + ["center"] * (len(valid_states) + 3),
                            font=dict(size=11, color="black"),
                            height=30,
                        ),
                    )
                ]
            )

            fig.update_layout(
                title=f"Comparative Analysis of {len(valid_states)} Psychological States",
                margin=dict(l=20, r=20, t=60, b=20),
            )

            return fig
        except Exception as e:
            logger.error(f"Error creating comparative analysis: {e}")
            return None

    def plot_parameter_correlation_heatmap(
        self, parameters: Optional[List[str]] = None
    ) -> Optional[go.Figure]:
        """Create a correlation heatmap of APGI parameters.

        Args:
            parameters: List of parameter names to include. If None, uses all parameters.

        Returns:
            Plotly Figure or None if dependencies unavailable
        """
        if not PLOTLY_AVAILABLE or not PANDAS_AVAILABLE:
            logger.warning("Plotly or Pandas not available")
            return None

        # Edge case: empty dataframe
        if self.df is None or self.df.empty:
            logger.warning("No data available for correlation heatmap")
            return None

        if parameters is None:
            parameters = [
                "Pi_e",
                "Pi_i_baseline",
                "Pi_i_eff",
                "theta_t",
                "S_t",
                "M_ca",
                "beta",
                "z_e",
                "z_i",
                "ignition_probability",
            ]

        # Edge case: validate parameters exist in dataframe
        valid_params = [p for p in parameters if p in self.df.columns]
        if not valid_params:
            logger.warning("No valid parameters found for correlation")
            return None

        try:
            corr_matrix = self.df[valid_params].corr()
        except Exception as e:
            logger.warning(f"Failed to compute correlation: {e}")
            return None

        fig = go.Figure(
            data=go.Heatmap(
                z=corr_matrix.values,
                x=valid_params,
                y=valid_params,
                colorscale="RdBu",
                zmid=0,
                text=corr_matrix.round(2).values,
                texttemplate="%{text}",
                textfont={"size": 10},
                connectgaps=False,
                hovertemplate="%{x} vs %{y}<br>Correlation: %{z:.3f}<extra></extra>",
            )
        )

        fig.update_layout(
            title="APGI Parameter Correlation Matrix",
            xaxis_title="Parameters",
            yaxis_title="Parameters",
            width=700,
            height=600,
            template="plotly_white",
        )

        return fig

    def create_state_summary_dashboard(self, state_name: str) -> Optional[go.Figure]:
        """Create a comprehensive dashboard for a single state.

        Args:
            state_name: Name of the state to visualize

        Returns:
            Plotly Figure or None if dependencies unavailable or state not found
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available")
            return None

        if state_name not in self.states:
            logger.warning(f"State not found: {state_name}")
            return None

        try:
            params = self.states[state_name]
            category = self.categories.get(state_name, StateCategory.UNELABORATED)

            fig = make_subplots(
                rows=2,
                cols=2,
                subplot_titles=(
                    "Parameter Profile",
                    "Ignition Dynamics",
                    "Category Comparison",
                    "State Distribution",
                ),
                specs=[
                    [{"type": "bar"}, {"type": "scatter"}],
                    [{"type": "scatter"}, {"type": "histogram"}],
                ],
            )

            # 1. Parameter Profile
            param_names = [
                "Pi_e",
                "Pi_i_baseline",
                "Pi_i_eff",
                "theta_t",
                "M_ca",
                "beta",
                "z_e",
                "z_i",
            ]
            param_values = [getattr(params, p) for p in param_names]
            param_colors = ["#2E86AB" for _ in param_values]

            fig.add_trace(
                go.Bar(
                    x=param_names,
                    y=param_values,
                    marker_color=param_colors,
                    name="Parameters",
                    hovertemplate="%{x}: %{y:.2f}<extra></extra>",
                ),
                row=1,
                col=1,
            )

            # 2. Ignition Dynamics
            S_t_range = np.linspace(0, max(params.S_t * 2, 0.1), 100)
            ignition_probs = 1.0 / (1.0 + np.exp(-(S_t_range - params.theta_t)))

            # Convert hex color to rgba for fill
            r = int(category.color[1:3], 16)
            g = int(category.color[3:5], 16)
            b = int(category.color[5:7], 16)
            fill_color_rgba = f"rgba({r}, {g}, {b}, 0.13)"
            fig.add_trace(
                go.Scatter(
                    x=S_t_range,
                    y=ignition_probs,
                    mode="lines",
                    line=dict(color=category.color, width=3),
                    name="Ignition Probability",
                    fill="tozeroy",
                    fillcolor=fill_color_rgba,
                ),
                row=1,
                col=2,
            )

            fig.add_trace(
                go.Scatter(
                    x=[params.S_t],
                    y=[params.compute_ignition_probability()],
                    mode="markers",
                    marker=dict(size=15, color="gold", line=dict(width=2, color="black")),
                    name="Current State",
                    hovertext=f"S_t={params.S_t:.2f}, P={params.compute_ignition_probability():.2%}",
                ),
                row=1,
                col=2,
            )

            # 3. Category Comparison - Create separate polar figure
            category_states = [
                name
                for name, cat in self.categories.items()
                if cat == category and name != state_name
            ][:4]
            if category_states:
                # Create a separate polar figure for the comparison
                polar_fig = go.Figure()

                for comp_state in [state_name] + category_states:
                    comp_params = self.states[comp_state]
                    polar_fig.add_trace(
                        self._create_polar_trace(
                            comp_params, comp_state, is_focus=(comp_state == state_name)
                        )
                    )

                polar_fig.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 1.1]),
                        angularaxis=dict(visible=True),
                    ),
                    title="Category Comparison",
                    showlegend=True,
                    template="plotly_white",
                )

                # Add the polar figure as an image trace to the main subplot
                # This is a workaround to avoid the polar subplot issue
                fig.add_trace(
                    go.Scatter(
                        x=[0.5],
                        y=[0.5],
                        mode="text",
                        text=["[Polar Chart]<br>Category Comparison<br>See separate panel"],
                        textfont=dict(size=14, color="gray"),
                        showlegend=False,
                    ),
                    row=2,
                    col=1,
                )

            # 4. Distribution histogram
            all_ignition = [s.compute_ignition_probability() for s in self.states.values()]
            if all_ignition:
                fig.add_trace(
                    go.Histogram(
                        x=all_ignition,
                        nbinsx=20,
                        name="P(ignition) Distribution",
                        marker_color="rgba(99,110,250,0.7)",
                        hovertemplate="P(ignition): %{x:.2%}<br>Count: %{y}<extra></extra>",
                    ),
                    row=2,
                    col=2,
                )

                fig.add_shape(
                    type="line",
                    x0=params.compute_ignition_probability(),
                    x1=params.compute_ignition_probability(),
                    y0=0,
                    y1=1,
                    line_dash="dash",
                    line_color="red",
                    row=2,
                    col=2,
                )
                fig.add_annotation(
                    x=params.compute_ignition_probability(),
                    y=0.95,
                    text=f"Current: {params.compute_ignition_probability():.0%}",
                    showarrow=False,
                    xanchor="left",
                    yanchor="bottom",
                    row=2,
                    col=2,
                )

            fig.update_xaxes(title_text="Parameters", row=1, col=1)
            fig.update_yaxes(title_text="Value", row=1, col=1)

            fig.update_xaxes(title_text="Accumulated Surprise (S_t)", row=1, col=2)
            fig.update_yaxes(title_text="Ignition Probability", range=[0, 1], row=1, col=2)

            fig.update_xaxes(title_text="P(ignition)", row=2, col=2)
            fig.update_yaxes(title_text="Frequency", row=2, col=2)

            # Configure layout (no polar subplot needed)
            fig.update_layout(
                title_text=f"APGI State Dashboard: {state_name.replace('_', ' ').title()}",
                showlegend=True,
                height=800,
                template="plotly_white",
            )

            return fig
        except Exception as e:
            logger.error(f"Error creating state dashboard: {e}")
            return None

    def _create_hover_text(self, state_name: str, row: Optional["pd.Series"] = None) -> str:
        """Create hover text for state visualization.

        Args:
            state_name: Name of the psychological state
            row: Optional pandas Series with state data

        Returns:
            Formatted hover text string
        """
        if state_name not in self.states:
            return f"Unknown state: {state_name}"

        params = self.states[state_name]

        text = f"<b>{state_name.replace('_', ' ').title()}</b><br>"
        text += f"Category: {self.categories[state_name].display_name}<br>"
        text += f"Π_e: {params.Pi_e:.2f}<br>"
        text += f"Π_i_eff: {params.Pi_i_eff:.2f}<br>"
        text += f"θ_t: {params.theta_t:+.2f}<br>"
        text += f"M_ca: {params.M_ca:+.2f}<br>"
        text += f"S_t: {params.S_t:.2f}<br>"
        text += f"P(ignition): {params.compute_ignition_probability():.2%}"

        return text

    def _parse_color_with_fallback(self, color: str) -> Tuple[str, str]:
        """Parse hex color to rgba string format with fallback for Plotly.

        Args:
            color: Hex color string (with or without # prefix)

        Returns:
            Tuple of (fill_color_rgba, line_color_rgb)
        """
        if not color or not isinstance(color, str):
            return "rgba(128, 128, 128, 0.3)", "rgb(128, 128, 128)"

        try:
            # Remove # if present
            hex_color = color.lstrip("#")

            # Validate hex color format
            if len(hex_color) not in (3, 6) or not all(
                c in "0123456789abcdefABCDEF" for c in hex_color
            ):
                return "rgba(128, 128, 128, 0.3)", "rgb(128, 128, 128)"

            # Handle 3-digit hex colors
            if len(hex_color) == 3:
                hex_color = "".join(c * 2 for c in hex_color)

            # Convert hex to RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)

            # Return fill color (with alpha) and line color (solid) as rgba strings
            fill_color = f"rgba({r}, {g}, {b}, 0.3)"
            line_color = f"rgb({r}, {g}, {b})"

            return fill_color, line_color
        except (ValueError, IndexError, AttributeError):
            # Fallback to gray if color parsing fails
            return "rgba(128, 128, 128, 0.3)", "rgb(128, 128, 128)"

    def _add_category_legend(self, fig: go.Figure) -> None:
        """Add category legend to figure.

        Args:
            fig: Plotly Figure to add legend to
        """
        if not PLOTLY_AVAILABLE:
            return

        if fig is None:
            return

        for category in StateCategory:
            fig.add_trace(
                go.Scatter3d(
                    x=[None],
                    y=[None],
                    z=[None],
                    mode="markers",
                    marker=dict(size=10, color=category.color),
                    name=category.display_name,
                    showlegend=True,
                )
            )


class GeneticDataVisualizer:
    """Visualizations for PGC GWAS genetic data"""

    def __init__(self):
        """Initialize genetic data visualizer"""
        self.connector = None
        self.df = None
        self.renderer = EmbeddedVisualizationRenderer()

    def load_dataset(self, dataset_key="MDD"):
        """Load genetic dataset from Hugging Face

        Args:
            dataset_key: "MDD" or "Anxiety"

        Returns:
            DataFrame with genetic variants or None
        """
        if not GENETIC_DATA_AVAILABLE:
            logger.error("Genetic data connector not available")
            return None

        try:
            self.connector = PGCDataConnector(dataset_key)
            self.df = self.connector.fetch_data(streaming=True)
            if self.df is None:
                logger.warning(
                    f"Streaming load returned no data for {dataset_key}; retrying non-streaming mode"
                )
                self.df = self.connector.fetch_data(streaming=False)

            if self.df is None:
                logger.error(f"No data returned for dataset {dataset_key}")
                return None

            logger.info(f"Loaded {len(self.df)} variants from {dataset_key}")
            return self.df
        except Exception as e:
            logger.error(f"Failed to load genetic data: {e}")
            return None

    def get_column_names(self):
        """Get available column names from loaded data"""
        if self.df is None:
            return []
        return list(self.df.columns)

    def plot_manhattan(
        self,
        p_col="p",
        chr_col="chr",
        bp_col="bp",
        snp_col="snp",
        threshold=5e-8,
        highlight_hits=True,
    ):
        """Create Manhattan plot for GWAS data

        Args:
            p_col: Column name for p-values
            chr_col: Column name for chromosome
            bp_col: Column name for base pair position
            snp_col: Column name for SNP identifiers
            threshold: Genome-wide significance threshold
            highlight_hits: Whether to highlight significant hits

        Returns:
            Plotly Figure or None
        """
        if not PLOTLY_AVAILABLE or self.df is None:
            logger.warning("Plotly not available or no data loaded")
            return None

        try:
            # Validate columns exist
            required_cols = [p_col, chr_col, bp_col]
            missing_cols = [c for c in required_cols if c not in self.df.columns]
            if missing_cols:
                logger.warning(f"Missing columns: {missing_cols}")
                return None

            # Calculate -log10(p)
            df_plot = self.df.copy()
            df_plot.loc[:, "neg_log_p"] = -np.log10(df_plot.loc[:, p_col].replace(0, np.nan))

            # Create figure
            fig = go.Figure()

            # Color by chromosome
            chromosomes = sorted(df_plot[chr_col].unique())
            colors = ["#1f77b4", "#ff7f0e"]  # Alternating colors

            for i, chrom in enumerate(chromosomes):
                chrom_data = df_plot[df_plot[chr_col] == chrom]
                color = colors[i % 2]

                fig.add_trace(
                    go.Scatter(
                        x=chrom_data[bp_col],
                        y=chrom_data["neg_log_p"],
                        mode="markers",
                        marker=dict(size=5, color=color, opacity=0.6),
                        name=f"Chr {chrom}",
                        text=chrom_data.get(snp_col, chrom_data.index),
                        hovertemplate="<b>%{text}</b><br>Chr: "
                        + str(chrom)
                        + "<br>Position: %{x}<br>-log10(p): %{y:.2f}<extra></extra>",
                    )
                )

            # Add significance threshold line
            fig.add_hline(
                y=-np.log10(threshold),
                line_dash="dash",
                line_color="red",
                annotation_text=f"p = {threshold}",
            )

            # Highlight significant hits if requested
            if highlight_hits:
                sig_hits = df_plot[df_plot[p_col] < threshold]
                if len(sig_hits) > 0:
                    fig.add_trace(
                        go.Scatter(
                            x=sig_hits[bp_col],
                            y=sig_hits["neg_log_p"],
                            mode="markers",
                            marker=dict(size=10, color="red", symbol="star"),
                            name="Significant Hits",
                            text=sig_hits.get(snp_col, sig_hits.index),
                            hovertemplate="<b>%{text}</b><br>p-value: "
                            + sig_hits[p_col].astype(str)
                            + "<br>-log10(p): %{y:.2f}<extra></extra>",
                        )
                    )

            fig.update_layout(
                title="GWAS Manhattan Plot",
                xaxis_title="Chromosomal Position",
                yaxis_title="-log10(p-value)",
                template="plotly_white",
                showlegend=False,
                height=600,
            )

            return fig
        except Exception as e:
            logger.error(f"Error creating Manhattan plot: {e}")
            return None

    def plot_qq(self, p_col="p"):
        """Create Q-Q plot for p-values

        Args:
            p_col: Column name for p-values

        Returns:
            Plotly Figure or None
        """
        if not PLOTLY_AVAILABLE or self.df is None:
            return None

        try:
            if p_col not in self.df.columns:
                logger.warning(f"P-value column {p_col} not found")
                return None

            # Get sorted p-values
            p_values = self.df[p_col].dropna().sort_values()
            n = len(p_values)

            # Check if we have any valid p-values
            if n == 0:
                logger.warning(f"No valid p-values found in column {p_col}")
                return None

            # Expected p-values under null hypothesis
            expected = np.arange(1, n + 1) / (n + 1)

            # Create Q-Q plot
            fig = go.Figure()

            # Q-Q points
            fig.add_trace(
                go.Scatter(
                    x=-np.log10(expected),
                    y=-np.log10(p_values),
                    mode="markers",
                    marker=dict(size=4, color="#1f77b4", opacity=0.6),
                    name="Observed vs Expected",
                )
            )

            # Diagonal line (y=x)
            max_val = max(-np.log10(expected[-1]), -np.log10(p_values.iloc[0]))
            fig.add_trace(
                go.Scatter(
                    x=[0, max_val],
                    y=[0, max_val],
                    mode="lines",
                    line=dict(color="red", dash="dash"),
                    name="Expected (y=x)",
                )
            )

            fig.update_layout(
                title="Q-Q Plot",
                xaxis_title="Expected -log10(p)",
                yaxis_title="Observed -log10(p)",
                template="plotly_white",
                showlegend=True,
            )

            return fig
        except Exception as e:
            logger.error(f"Error creating Q-Q plot: {e}")
            return None

    def get_summary_stats(self):
        """Get summary statistics for loaded data"""
        if self.df is None:
            return {}

        stats = {
            "total_variants": len(self.df),
            "columns": list(self.df.columns),
            "memory_usage": f"{self.df.memory_usage(deep=True).sum() / 1024**2:.2f} MB",
        }

        # Count significant hits if p-value column exists
        for p_col in ["p", "P", "pvalue", "p_value"]:
            if p_col in self.df.columns:
                sig_count = (self.df[p_col] < 5e-8).sum()
                stats["significant_hits"] = int(sig_count)
                stats["p_value_column"] = p_col
                break

        return stats


# =============================================================================
# HUGGING FACE MODEL DISCOVERY ENGINE (Integrated from load_geno_data.py)
# =============================================================================


class APGIHFMapper:
    """Synchronous mapper for Hugging Face models using httpx"""

    def __init__(self):
        self.client = httpx.Client(headers={"User-Agent": "APGI-App/1.0"}, timeout=15.0)

    def search_hf(self, query: str, limit: int = 8) -> List[Dict]:
        """Search models on Hugging Face using httpx"""
        url = f"{HF_API_BASE}/models"
        params = {
            "search": query,
            "limit": limit,
            "sort": "downloads",
            "direction": "-1",
        }
        try:
            resp = self.client.get(url, params=params)
            if resp.status_code != 200:
                logger.error(f"HF API error {resp.status_code} for query: {query}")
                return []
            return resp.json()
        except Exception as e:
            logger.error(f"HF Request failed: {e}")
            return []

    def score_repo(self, repo: Dict, keywords: List[str]) -> float:
        """Improved scoring logic from load_geno_data.py"""
        text = (
            repo.get("id", "")
            + " "
            + " ".join(repo.get("tags", []))
            + " "
            + repo.get("pipeline_tag", "")
            + " "
            + str(repo.get("modelId", ""))
        ).lower()

        score = 0.0
        matches = sum(1 for kw in keywords if kw.lower() in text)
        score += matches * 10

        relevant_tags = {
            "text-classification",
            "sentiment-analysis",
            "feature-extraction",
            "text-generation",
            "zero-shot-classification",
            "reinforcement-learning",
        }
        score += sum(3 for tag in repo.get("tags", []) if tag in relevant_tags)

        score += repo.get("likes", 0) * 0.015
        score += min(repo.get("downloads", 0) / 1000, 50)  # cap downloads bonus

        return score

    def build_repo_map_for_state(self, state: str, keywords: List[str]) -> List[Dict]:
        """Build a list of top models for a specific state"""
        all_repos = []
        for kw in keywords:
            repos = self.search_hf(kw, limit=6)
            all_repos.extend(repos)

        # Deduplicate
        unique = {r["id"]: r for r in all_repos}

        # Score & rank
        scored = [(repo, self.score_repo(repo, keywords)) for repo in unique.values()]
        scored.sort(key=lambda x: x[1], reverse=True)

        # Build clean output
        top_repos = []
        for repo, score in scored[:6]:
            top_repos.append(
                {
                    "repo_id": repo["id"],
                    "likes": repo.get("likes", 0),
                    "downloads": repo.get("downloads", 0),
                    "tags": repo.get("tags", []),
                    "pipeline_tag": repo.get("pipeline_tag"),
                    "last_modified": repo.get("lastModified"),
                    "score": round(score, 2),
                }
            )
        return top_repos

    def close(self):
        self.client.close()


class AIModelVisualizer:
    """Management and visualization of recommended AI models"""

    def __init__(self) -> None:
        self.mapper = APGIHFMapper()
        self.cache: Dict[str, List[Dict]] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load from apgi_hf_cache.json if available"""
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r") as f:
                    cache_data = json.load(f)
                    self.cache = cache_data.get("data", {})
                logger.info(f"Loaded {len(self.cache)} states from HF model cache")
        except Exception as e:
            logger.warning(f"Could not load HF cache: {e}")

    def get_models_for_state(self, state: str, refresh: bool = False) -> List[Dict]:
        """Get models for a state, searching if not in cache or if refresh requested"""
        # Normalize state name to match keywords
        norm_state = state.lower().replace(" ", "_")

        if not refresh and norm_state in self.cache:
            return self.cache[norm_state]

        keywords = STATE_KEYWORDS.get(norm_state, [state])
        models = self.mapper.build_repo_map_for_state(norm_state, keywords)

        if models:
            self.cache[norm_state] = models
            self._save_cache()

        return models

    def _save_cache(self):
        """Save models to cache file"""
        try:
            cache_data = {"timestamp": time.time(), "data": self.cache}
            with open(CACHE_FILE, "w") as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save HF cache: {e}")


# =============================================================================
# ENHANCED GUI WITH EMBEDDED VISUALIZATION PANEL
# =============================================================================


class APGIVisualizerGUI:
    """Enhanced GUI for APGI Psychological States Visualization with Embedded Panel

    All visualizations are displayed exclusively in the embedded right panel
    with no external browser options, dependencies, or save capabilities.
    """

    def __init__(self, root: Optional[tk.Tk] = None) -> None:
        """Initialize the GUI application with embedded visualization support"""
        if not TKINTER_AVAILABLE:
            raise ImportError("Tkinter is required for GUI interface")
        if not PLOTLY_AVAILABLE or not PANDAS_AVAILABLE:
            raise ImportError("Plotly and Pandas are required for visualization")

        if root is None:
            self.root: tk.Tk = tk.Tk()
        else:
            self.root = root
        self.root.title("APGI Psychological States Visualizer - Enhanced GUI")
        self.root.geometry("1400x900")

        # Initialize theme manager
        self.theme_manager = None
        if THEME_MANAGER_AVAILABLE:
            self.theme_manager = ThemeManager(initial_theme="normal")

        # Setup cleanup handlers
        self._setup_cleanup_handlers()

        try:
            self.visualizer: APGIVisualizer = APGIVisualizer(PSYCHOLOGICAL_STATES, STATE_CATEGORIES)
            self.classifier = StateClassifier(PSYCHOLOGICAL_STATES)
            self.current_visualization: Optional[go.Figure] = None
            self.current_html_file: Optional[str] = None

            # Initialize AI Model Visualizer
            self.ai_visualizer = AIModelVisualizer()
            self.executor = ThreadPoolExecutor(max_workers=2)

            # Setup GUI
            self.setup_gui()
            self.populate_state_dropdowns()

            # Load configuration if available
            config_loaded = self.load_configuration()
            if config_loaded:
                logger.info("Configuration loaded from config/gui_config.yaml")

            self.status_var.set("Ready - Select visualization type and click Generate")

            # Compatibility attributes for tests
            self.parameters = {"arousal": 0.5, "stress": 0.3, "attention": 0.7, "motivation": 0.6}
            self.state_history: List[Dict[str, float]] = []
            self.renderer = self.visualizer.renderer
            self.canvas = self.embedded_display
            self.parameter_controls: Dict[str, Any] = {}  # Compatibility for tests

            # Matplotlib components
            self.matplotlib_canvas: Optional[FigureCanvasTkAgg] = None
            self.toolbar: Optional[NavigationToolbar2Tk] = None

            self.update_info(
                "APGI Visualizer initialized successfully!\n\n"
                f"Available states: {len(PSYCHOLOGICAL_STATES)}\n\n"
                "Choose a visualization type and click 'Generate Visualization' to begin."
            )
        except Exception as e:
            messagebox.showerror(
                "Initialization Error", f"Failed to initialize visualizer: {str(e)}"
            )
            self.root.destroy()
            raise

    def _create_menu_bar(self) -> None:
        """Create menu bar with theme options."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.quit_application)

        # Theme menu (only if theme manager is available)
        if self.theme_manager:
            theme_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Theme", menu=theme_menu)

            # Add theme options
            for theme_name in self.theme_manager.get_available_themes():
                theme_menu.add_radiobutton(
                    label=theme_name.capitalize(),
                    command=lambda t=theme_name: self._set_theme(t),
                    variable=tk.StringVar(value=self.theme_manager.current_theme),
                    value=theme_name,
                )

    def _set_theme(self, theme_name: str) -> None:
        """Set the current theme.

        Args:
            theme_name: Name of the theme to apply
        """
        if not self.theme_manager:
            return

        if self.theme_manager.set_theme(theme_name):
            self._apply_theme_to_widgets()

    def _apply_theme_to_widgets(self) -> None:
        """Apply current theme to all widgets."""
        if not self.theme_manager:
            return

        # Apply theme to text widgets
        if hasattr(self, "states_text"):
            bg_color = self.theme_manager.get_theme_color("bg")
            fg_color = self.theme_manager.get_theme_color("fg")
            try:
                self.states_text.config(bg=bg_color, fg=fg_color, insertbackground=fg_color)
            except tk.TclError:
                pass

    def quit_application(self) -> None:
        """Quit the application."""
        self.root.quit()

    def setup_gui(self) -> None:
        """Setup the enhanced GUI layout with embedded visualization panel"""
        # Create menu bar
        self._create_menu_bar()

        # Main container with better layout
        self.main_frame: ttk.Frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(
            self.main_frame,
            text="🧠 APGI Psychological States & Genetic Data Visualizer",
            font=("Arial", 14, "bold"),
        )
        title_label.grid(row=0, column=0, pady=(0, 15))

        # Create Notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Tab 1: Psychological States
        self.psych_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.psych_frame, text="Psychological States")
        self._setup_psychological_states_tab()

        # Tab 2: Genetic Data
        self.genetic_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.genetic_frame, text="Genetic Data (GWAS)")
        self._setup_genetic_data_tab()

        # Tab 3: AI Model Recommendations
        self.ai_models_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.ai_models_frame, text="Recommended AI Models")
        self._setup_ai_models_tab()

    def _setup_psychological_states_tab(self) -> None:
        """Setup the Psychological States tab"""
        # Configure grid
        self.psych_frame.columnconfigure(1, weight=1)
        self.psych_frame.rowconfigure(0, weight=1)

        # Control Panel (Left) - Enhanced
        self.control_frame = ttk.LabelFrame(self.psych_frame, text="Controls", padding="12")
        self.control_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Visualization Type
        ttk.Label(self.control_frame, text="Visualization Type:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=(5, 2)
        )
        self.viz_type = ttk.Combobox(
            self.control_frame,
            values=[
                "3D State Network",
                "Ignition Landscape",
                "State Radar Comparison",
                "Parameter Correlation Heatmap",
                "State Dashboard",
                "State Transition Simulation",
                "Comparative Analysis",
            ],
            state="readonly",
            font=("Arial", 9),
        )
        self.viz_type.set("3D State Network")
        self.viz_type.grid(row=1, column=0, sticky="we", pady=(0, 10))

        # State Selection
        ttk.Label(self.control_frame, text="Select State:", font=("Arial", 10, "bold")).grid(
            row=2, column=0, sticky=tk.W, pady=(5, 2)
        )
        self.state_var = tk.StringVar()
        self.state_combo = ttk.Combobox(
            self.control_frame,
            textvariable=self.state_var,
            state="readonly",
            font=("Arial", 9),
        )
        self.state_combo.grid(row=3, column=0, sticky="we", pady=(0, 10))

        # Multiple States for Radar
        ttk.Label(
            self.control_frame,
            text="States to Compare\n(comma-separated):",
            font=("Arial", 9, "bold"),
        ).grid(row=4, column=0, sticky=tk.W, pady=(5, 2))
        self.states_text = tk.Text(self.control_frame, height=3, width=25, font=("Courier", 9))
        self.states_text.grid(row=5, column=0, sticky="we", pady=(0, 10))
        self.states_text.insert("1.0", "flow\nanxiety\ncalm")

        # Transition States
        ttk.Label(
            self.control_frame, text="Start State for Transition:", font=("Arial", 10, "bold")
        ).grid(row=6, column=0, sticky=tk.W, pady=(5, 2))
        self.start_state_var = tk.StringVar()
        self.start_state_combo = ttk.Combobox(
            self.control_frame,
            textvariable=self.start_state_var,
            state="readonly",
            font=("Arial", 9),
        )
        self.start_state_combo.grid(row=7, column=0, sticky="we", pady=(0, 5))

        ttk.Label(
            self.control_frame, text="End State for Transition:", font=("Arial", 10, "bold")
        ).grid(row=8, column=0, sticky=tk.W, pady=(5, 2))
        self.end_state_var = tk.StringVar()
        self.end_state_combo = ttk.Combobox(
            self.control_frame,
            textvariable=self.end_state_var,
            state="readonly",
            font=("Arial", 9),
        )
        self.end_state_combo.grid(row=9, column=0, sticky="we", pady=(0, 10))

        # Separator
        ttk.Separator(self.control_frame, orient="horizontal").grid(
            row=6, column=0, sticky="we", pady=10
        )

        # Parameter Input Section
        ttk.Label(
            self.control_frame, text="Simulation Parameters:", font=("Arial", 10, "bold")
        ).grid(row=7, column=0, sticky=tk.W, pady=(5, 2))

        # tau_S parameter
        ttk.Label(self.control_frame, text="τ_S (surprise timescale):").grid(
            row=8, column=0, sticky=tk.W, pady=(2, 0)
        )
        self.tau_S_var = tk.StringVar(value="0.5")
        self.tau_S_entry = ttk.Entry(self.control_frame, textvariable=self.tau_S_var, width=15)
        self.tau_S_entry.grid(row=9, column=0, sticky=tk.W, pady=(0, 5))

        # tau_theta parameter
        ttk.Label(self.control_frame, text="τ_θ (threshold timescale):").grid(
            row=10, column=0, sticky=tk.W, pady=(2, 0)
        )
        self.tau_theta_var = tk.StringVar(value="30.0")
        self.tau_theta_entry = ttk.Entry(
            self.control_frame, textvariable=self.tau_theta_var, width=15
        )
        self.tau_theta_entry.grid(row=11, column=0, sticky=tk.W, pady=(0, 5))

        # theta_0 parameter
        ttk.Label(self.control_frame, text="θ₀ (baseline threshold):").grid(
            row=12, column=0, sticky=tk.W, pady=(2, 0)
        )
        self.theta_0_var = tk.StringVar(value="0.5")
        self.theta_0_entry = ttk.Entry(self.control_frame, textvariable=self.theta_0_var, width=15)
        self.theta_0_entry.grid(row=13, column=0, sticky=tk.W, pady=(0, 5))

        # alpha parameter
        ttk.Label(self.control_frame, text="α (sigmoid steepness):").grid(
            row=14, column=0, sticky=tk.W, pady=(2, 0)
        )
        self.alpha_var = tk.StringVar(value="5.0")
        self.alpha_entry = ttk.Entry(self.control_frame, textvariable=self.alpha_var, width=15)
        self.alpha_entry.grid(row=15, column=0, sticky=tk.W, pady=(0, 10))

        # Validation status
        self.validation_status = tk.StringVar(value="✓ Parameters valid")
        self.validation_label = ttk.Label(
            self.control_frame, textvariable=self.validation_status, foreground="green"
        )
        self.validation_label.grid(row=16, column=0, sticky=tk.W, pady=(0, 10))

        # Bind validation to entry changes
        self.tau_S_var.trace_add("write", lambda *args: self.validate_parameters())
        self.tau_theta_var.trace_add("write", lambda *args: self.validate_parameters())
        self.theta_0_var.trace_add("write", lambda *args: self.validate_parameters())
        self.alpha_var.trace_add("write", lambda *args: self.validate_parameters())

        # Separator
        ttk.Separator(self.control_frame, orient="horizontal").grid(
            row=17, column=0, sticky="we", pady=10
        )

        # Buttons with better styling

        self.generate_button = ttk.Button(
            self.control_frame,
            text="Run Simulation",
            command=self.run_simulation_with_validation,
        )
        self.generate_button.grid(row=18, column=0, sticky="we", pady=5)
        if TOOLTIP_AVAILABLE:
            ToolTip(self.generate_button, "Run simulation with current parameters")

        viz_button = ttk.Button(
            self.control_frame,
            text="Generate Visualization",
            command=self.generate_visualization,
        )
        viz_button.grid(row=19, column=0, sticky="we", pady=5)
        if TOOLTIP_AVAILABLE:
            ToolTip(viz_button, "Generate visualization of selected psychological state")

        clear_button = ttk.Button(
            self.control_frame, text="Clear Display", command=self.clear_display
        )
        clear_button.grid(row=20, column=0, sticky="we", pady=5)
        if TOOLTIP_AVAILABLE:
            ToolTip(clear_button, "Clear the visualization display")

        self.control_frame.columnconfigure(0, weight=1)

        # Visualization Panel (Right) - Enhanced with embedded display
        self.visualization_frame = ttk.LabelFrame(
            self.psych_frame, text="Visualization Panel", padding="5"
        )
        self.visualization_frame.grid(row=0, column=1, sticky="nsew")
        self.visualization_frame.columnconfigure(0, weight=1)
        self.visualization_frame.rowconfigure(0, weight=1)

        # Create embedded web view
        self.embedded_display = EmbeddedDisplayPanel(self.visualization_frame)
        self.embedded_display.pack(fill=tk.BOTH, expand=True)

        # Info Panel (Bottom) - Smaller
        info_frame = ttk.LabelFrame(self.psych_frame, text="Information Panel", padding="8")
        info_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)

        self.info_text = tk.Text(info_frame, height=4, width=80, wrap=tk.WORD, font=("Arial", 9))
        self.info_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.info_text["yscrollcommand"] = scrollbar.set

        # Status Bar (at main frame level)
        self.status_var = tk.StringVar(value="Initializing...")
        status_bar = ttk.Label(
            self.main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            font=("Arial", 9),
        )
        status_bar.grid(row=2, column=0, sticky="we", pady=(10, 0))

    def _setup_genetic_data_tab(self) -> None:
        """Setup the Genetic Data (GWAS) tab"""
        # Configure grid
        self.genetic_frame.columnconfigure(1, weight=1)
        self.genetic_frame.rowconfigure(0, weight=1)

        # Initialize genetic data visualizer
        self.genetic_visualizer = GeneticDataVisualizer()
        self.genetic_df: Optional["pd.DataFrame"] = None

        # Control Panel (Left)
        control_frame = ttk.LabelFrame(self.genetic_frame, text="GWAS Controls", padding="12")
        control_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Dataset Selection
        ttk.Label(control_frame, text="Dataset:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=(5, 2)
        )
        self.genetic_dataset_var = tk.StringVar(value="MDD")
        dataset_combo = ttk.Combobox(
            control_frame,
            textvariable=self.genetic_dataset_var,
            values=["MDD", "Anxiety"],
            state="readonly",
            font=("Arial", 9),
        )
        dataset_combo.grid(row=1, column=0, sticky="we", pady=(0, 10))

        # Load Data Button
        load_btn = ttk.Button(
            control_frame,
            text="Load Genetic Data",
            command=self._load_genetic_data,
        )
        load_btn.grid(row=2, column=0, sticky="we", pady=5)
        if TOOLTIP_AVAILABLE:
            ToolTip(load_btn, "Load GWAS data from Hugging Face (10,000 variants preview)")

        # Visualization Type
        ttk.Label(control_frame, text="Visualization:", font=("Arial", 10, "bold")).grid(
            row=3, column=0, sticky=tk.W, pady=(10, 2)
        )
        self.genetic_viz_type = ttk.Combobox(
            control_frame,
            values=["Manhattan Plot", "Q-Q Plot", "Data Table"],
            state="readonly",
            font=("Arial", 9),
        )
        self.genetic_viz_type.set("Manhattan Plot")
        self.genetic_viz_type.grid(row=4, column=0, sticky="we", pady=(0, 10))

        # P-value threshold
        ttk.Label(control_frame, text="Significance Threshold:", font=("Arial", 9)).grid(
            row=5, column=0, sticky=tk.W, pady=(5, 2)
        )
        self.p_threshold_var = tk.StringVar(value="5e-8")
        ttk.Entry(control_frame, textvariable=self.p_threshold_var, width=15).grid(
            row=6, column=0, sticky="we", pady=(0, 10)
        )

        # Separator
        ttk.Separator(control_frame, orient="horizontal").grid(
            row=7, column=0, sticky="we", pady=10
        )

        # Generate Button
        viz_btn = ttk.Button(
            control_frame,
            text="Generate Plot",
            command=self._generate_genetic_visualization,
        )
        viz_btn.grid(row=8, column=0, sticky="we", pady=5)

        # Summary Stats Button
        stats_btn = ttk.Button(
            control_frame,
            text="Show Summary Stats",
            command=self._show_genetic_stats,
        )
        stats_btn.grid(row=9, column=0, sticky="we", pady=5)

        # Clear Button
        clear_btn = ttk.Button(
            control_frame, text="Clear Display", command=self._clear_genetic_display
        )
        clear_btn.grid(row=10, column=0, sticky="we", pady=5)

        # Data Status Label
        self.genetic_status_var = tk.StringVar(value="No data loaded")
        status_label = ttk.Label(
            control_frame, textvariable=self.genetic_status_var, foreground="gray"
        )
        status_label.grid(row=11, column=0, sticky="we", pady=(10, 0))

        control_frame.columnconfigure(0, weight=1)

        # Visualization Panel (Right)
        self.genetic_viz_frame = ttk.LabelFrame(
            self.genetic_frame, text="Genetic Visualization", padding="5"
        )
        self.genetic_viz_frame.grid(row=0, column=1, sticky="nsew")
        self.genetic_viz_frame.columnconfigure(0, weight=1)
        self.genetic_viz_frame.rowconfigure(0, weight=1)

        # Create embedded display for genetic data
        self.genetic_display = EmbeddedDisplayPanel(self.genetic_viz_frame)
        self.genetic_display.pack(fill=tk.BOTH, expand=True)

        # Info Panel (Bottom)
        info_frame = ttk.LabelFrame(self.genetic_frame, text="Dataset Information", padding="8")
        info_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)

        self.genetic_info_text = tk.Text(
            info_frame, height=4, width=80, wrap=tk.WORD, font=("Arial", 9)
        )
        self.genetic_info_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            info_frame, orient=tk.VERTICAL, command=self.genetic_info_text.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.genetic_info_text["yscrollcommand"] = scrollbar.set

        # Initial message
        self._update_genetic_info(
            "Welcome to Genetic Data Visualization!\n\n"
            "1. Select a dataset (MDD or Anxiety)\n"
            "2. Click 'Load Genetic Data' to fetch from Hugging Face\n"
            "3. Generate Manhattan plots, Q-Q plots, or view data tables\n\n"
            "Data source: PGC (Psychiatric Genomics Consortium) via Hugging Face"
        )

    def _setup_ai_models_tab(self) -> None:
        """Setup the AI Model Recommendations tab"""
        # Configure grid
        self.ai_models_frame.columnconfigure(0, weight=1)
        self.ai_models_frame.rowconfigure(1, weight=1)

        # Header section
        header_frame = ttk.Frame(self.ai_models_frame, padding="5")
        header_frame.grid(row=0, column=0, sticky="we")

        ttk.Label(header_frame, text="Selected State:", font=("Arial", 10, "bold")).pack(
            side=tk.LEFT, padx=5
        )
        self.ai_state_var = tk.StringVar()
        self.ai_state_combo = ttk.Combobox(
            header_frame, textvariable=self.ai_state_var, state="readonly", width=30
        )
        self.ai_state_combo.pack(side=tk.LEFT, padx=5)
        self.ai_state_combo.bind("<<ComboboxSelected>>", lambda e: self._load_ai_models())

        refresh_btn = ttk.Button(
            header_frame,
            text="Refresh Recommendations",
            command=lambda: self._load_ai_models(refresh=True),
        )
        refresh_btn.pack(side=tk.LEFT, padx=10)

        # Progress bar
        self.ai_progress = ttk.Progressbar(self.ai_models_frame, mode="indeterminate", length=200)

        # Content area with listbox/treeview
        content_frame = ttk.LabelFrame(
            self.ai_models_frame, text="Recommended Hugging Face Models", padding="10"
        )
        content_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)

        # Treeview for models
        columns = ("repo_id", "likes", "downloads", "pipeline", "score")
        self.model_tree = ttk.Treeview(content_frame, columns=columns, show="headings")

        self.model_tree.heading("repo_id", text="Repository ID")
        self.model_tree.heading("likes", text="Likes")
        self.model_tree.heading("downloads", text="Downloads")
        self.model_tree.heading("pipeline", text="Task / Pipeline")
        self.model_tree.heading("score", text="Match Score")

        self.model_tree.column("repo_id", width=400)
        self.model_tree.column("likes", width=80, anchor=tk.CENTER)
        self.model_tree.column("downloads", width=100, anchor=tk.CENTER)
        self.model_tree.column("pipeline", width=150)
        self.model_tree.column("score", width=100, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(content_frame, orient=tk.VERTICAL, command=self.model_tree.yview)
        self.model_tree.configure(yscrollcommand=scrollbar.set)

        self.model_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Model details area (Bottom)
        details_frame = ttk.LabelFrame(
            self.ai_models_frame, text="Model Details & Tags", padding="8"
        )
        details_frame.grid(row=2, column=0, sticky="we", pady=(0, 5))

        self.model_details_text = tk.Text(details_frame, height=6, wrap=tk.WORD, font=("Arial", 9))
        self.model_details_text.pack(fill=tk.BOTH, expand=True)
        self.model_details_text.config(state=tk.DISABLED)

        self.model_tree.bind("<<TreeviewSelect>>", self._on_model_select)

    def _load_ai_models(self, refresh: bool = False) -> None:
        """Load models for the selected state in a background thread"""
        state = self.ai_state_var.get()
        if not state:
            return

        # Start loading indicator
        self.ai_progress.grid(row=0, column=0, sticky="e", padx=5)
        self.ai_progress.start(10)
        self.status_var.set(f"Finding AI models for {state}...")

        # Run search in background thread
        def task():
            try:
                models = self.ai_visualizer.get_models_for_state(state, refresh=refresh)
                # Update GUI from main thread
                self.root.after(0, lambda: self._update_model_list(models))
            except Exception as e:
                logger.error(f"Error loading AI models: {e}")
                self.root.after(0, lambda: self.status_var.set("Error loading models"))
            finally:
                self.root.after(0, self.ai_progress.stop)
                self.root.after(0, lambda: self.ai_progress.grid_forget())

        self.executor.submit(task)

    def _update_model_list(self, models: List[Dict]) -> None:
        """Update the model treeview with results"""
        # Clear existing items
        for item in self.model_tree.get_children():
            self.model_tree.delete(item)

        for model in models:
            self.model_tree.insert(
                "",
                tk.END,
                values=(
                    model["repo_id"],
                    model["likes"],
                    model["downloads"],
                    model.get("pipeline_tag", "N/A"),
                    model["score"],
                ),
                tags=(model["repo_id"],),
            )

        self.status_var.set(f"✓ Found {len(models)} model recommendations for state")

    def _on_model_select(self, event) -> None:
        """Show details for the selected model"""
        selected = self.model_tree.selection()
        if not selected:
            return

        item = self.model_tree.item(selected[0])
        repo_id = item["values"][0]

        # Find model data in cache
        state = self.ai_state_var.get().lower().replace(" ", "_")
        models = self.ai_visualizer.cache.get(state, [])
        model_data = next((m for m in models if m["repo_id"] == repo_id), None)

        if model_data:
            self.model_details_text.config(state=tk.NORMAL)
            self.model_details_text.delete("1.0", tk.END)

            info = f"Repository: {model_data['repo_id']}\n"
            info += f"Pipeline: {model_data.get('pipeline_tag', 'N/A')}\n"
            info += (
                f"Popularity: {model_data['likes']} likes, {model_data['downloads']} downloads\n"
            )
            info += f"Link: https://huggingface.co/{model_data['repo_id']}\n\n"
            info += "Tags:\n"
            info += ", ".join(model_data.get("tags", []))

            self.model_details_text.insert("1.0", info)
            self.model_details_text.config(state=tk.DISABLED)

    def _load_genetic_data(self) -> None:
        """Load genetic data from selected dataset"""
        dataset_key = self.genetic_dataset_var.get()
        self.genetic_status_var.set(f"Loading {dataset_key}...")
        self.genetic_frame.update()

        try:
            df = self.genetic_visualizer.load_dataset(dataset_key)
            if df is not None:
                self.genetic_df = df
                self.genetic_status_var.set(f"✓ Loaded {len(df):,} variants")
                self._update_genetic_info(
                    f"Dataset: {dataset_key}\n"
                    f"Total variants: {len(df):,}\n"
                    f"Columns: {', '.join(df.columns[:5])}...\n"
                    f"Memory: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB"
                )
            else:
                self.genetic_status_var.set("✗ Failed to load")
                self._update_genetic_info("Error: Failed to load genetic data. Check logs.")
        except Exception as e:
            self.genetic_status_var.set("✗ Error")
            self._update_genetic_info(f"Error loading data: {str(e)}")
            logger.error(f"Genetic data loading error: {e}")

    def _generate_genetic_visualization(self) -> None:
        """Generate selected genetic visualization"""
        if self.genetic_visualizer.df is None:
            self._update_genetic_info("Please load genetic data first!")
            return

        viz_type = self.genetic_viz_type.get()
        self.genetic_status_var.set(f"Generating {viz_type}...")
        self.genetic_frame.update()

        try:
            fig = None
            if viz_type == "Manhattan Plot":
                # Try to auto-detect column names
                p_col = self._find_column(["p", "P", "pvalue", "p_value", "P.value"])
                chr_col = self._find_column(["chr", "CHR", "chromosome"])
                bp_col = self._find_column(["bp", "BP", "pos", "position"])
                snp_col = self._find_column(["snp", "SNP", "rsid", "variant", "SNPID"])

                if p_col and chr_col and bp_col:
                    fig = self.genetic_visualizer.plot_manhattan(
                        p_col=p_col,
                        chr_col=chr_col,
                        bp_col=bp_col,
                        snp_col=snp_col,
                        threshold=float(self.p_threshold_var.get()),
                    )
                else:
                    self._update_genetic_info(
                        f"Could not find required columns. Available: {self.genetic_visualizer.get_column_names()[:10]}"
                    )
                    return
            elif viz_type == "Q-Q Plot":
                p_col = self._find_column(["p", "P", "pvalue", "p_value", "P.value"])
                if p_col:
                    fig = self.genetic_visualizer.plot_qq(p_col=p_col)
                else:
                    self._update_genetic_info("P-value column not found")
                    return
            elif viz_type == "Data Table":
                self._show_data_table()
                self.genetic_status_var.set("✓ Table displayed")
                return

            if fig:
                filepath = self.genetic_visualizer.renderer.render_figure_to_html(fig)
                self.genetic_display.load_html_file(filepath)
                self.genetic_status_var.set(f"✓ {viz_type} generated")
        except Exception as e:
            self.genetic_status_var.set("✗ Error")
            self._update_genetic_info(f"Error: {str(e)}")
            logger.error(f"Genetic visualization error: {e}")

    def _find_column(self, candidates):
        """Find first matching column name from candidates"""
        available = self.genetic_visualizer.get_column_names()
        for col in candidates:
            if col in available:
                return col
        return None

    def _show_data_table(self) -> None:
        """Display data table in the info panel"""
        if self.genetic_df is None:
            return
        # Show first 50 rows
        preview = self.genetic_df.head(50).to_string()
        self._update_genetic_info(f"Data Preview (first 50 rows):\n\n{preview}")

    def _show_genetic_stats(self) -> None:
        """Show summary statistics for genetic data"""
        stats = self.genetic_visualizer.get_summary_stats()
        if stats:
            info = (
                f"Dataset Summary:\n"
                f"Total variants: {stats.get('total_variants', 'N/A'):,}\n"
                f"Significant hits (p < 5e-8): {stats.get('significant_hits', 'N/A')}\n"
                f"Memory usage: {stats.get('memory_usage', 'N/A')}\n"
                f"Available columns: {', '.join(stats.get('columns', [])[:10])}..."
            )
            self._update_genetic_info(info)
        else:
            self._update_genetic_info("No data loaded")

    def _clear_genetic_display(self) -> None:
        """Clear the genetic visualization display"""
        self.genetic_display.clear()
        self._update_genetic_info("Display cleared")

    def _update_genetic_info(self, text: str) -> None:
        """Update the genetic info text area"""
        self.genetic_info_text.config(state=tk.NORMAL)
        self.genetic_info_text.delete("1.0", tk.END)
        self.genetic_info_text.insert("1.0", text)
        self.genetic_info_text.config(state=tk.DISABLED)

    def populate_state_dropdowns(self) -> None:
        """Populate state selection dropdowns"""
        if not PSYCHOLOGICAL_STATES:
            self.status_var.set("Error: No states available")
            return

        state_names: List[str] = sorted(PSYCHOLOGICAL_STATES.keys())
        self.state_combo["values"] = state_names
        self.start_state_combo["values"] = state_names
        self.end_state_combo["values"] = state_names

        if state_names:
            self.state_combo.set(state_names[0])
            self.start_state_combo.set(state_names[0])
            self.end_state_combo.set(state_names[1] if len(state_names) > 1 else state_names[0])

            # Also populate AI models dropdown
            self.ai_state_combo["values"] = state_names
            self.ai_state_combo.set(state_names[0])
            # Initial load from cache if exists
            self._load_ai_models()

        self.status_var.set("Ready - Select visualization type and click Generate")

    def update_info(self, text: str) -> None:
        """Update the info text area.

        Args:
            text: Text to display in the info panel
        """
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", text)
        self.info_text.config(state=tk.DISABLED)

    def generate_visualization(self) -> None:
        """Generate the selected visualization with embedded display and progress feedback"""
        viz_type = self.viz_type.get()
        self.status_var.set(f"Generating {viz_type}...")
        self.root.update()

        try:
            fig = None
            cache_key_params = {}

            if viz_type == "3D State Network":
                # Check cache first
                cache_key_params = {"type": "3d_network"}
                cached_fig = self.visualizer.cache.get("3d_network", **cache_key_params)
                from_cache = cached_fig is not None

                if from_cache:
                    fig = cached_fig
                else:
                    # Show progress for complex visualization
                    self.status_var.set("Creating 3D network visualization...")
                    self.root.update()
                    fig = self.visualizer.plot_state_network_3d()
                    self.visualizer.cache.put("3d_network", fig, **cache_key_params)
                title = "3D State Network Visualization"

            elif viz_type == "Ignition Landscape":
                state = self.state_var.get()
                if not state:
                    messagebox.showerror("Error", "Please select a state")
                    return

                cache_key_params = {"type": "ignition_landscape", "state": state}
                cached_fig = self.visualizer.cache.get("ignition_landscape", **cache_key_params)
                from_cache = cached_fig is not None

                if from_cache:
                    fig = cached_fig
                else:
                    self.status_var.set(f"Generating ignition landscape for {state}...")
                    self.root.update()
                    fig = self.visualizer.plot_ignition_landscape(state)
                    self.visualizer.cache.put("ignition_landscape", fig, **cache_key_params)
                title = f"Ignition Landscape: {state}"

            elif viz_type == "State Radar Comparison":
                states_text = self.states_text.get("1.0", tk.END).strip()
                states = [s.strip() for s in states_text.split("\n") if s.strip()]
                if not states:
                    messagebox.showerror("Error", "Please enter states to compare")
                    return

                cache_key_params = {"type": "radar", "states": str(",".join(sorted(states)))}
                cached_fig = self.visualizer.cache.get("radar", **cache_key_params)
                from_cache = cached_fig is not None

                if from_cache:
                    fig = cached_fig
                else:
                    self.status_var.set("Creating radar comparison chart...")
                    self.root.update()
                    fig = self.visualizer.plot_state_radar(states)
                    self.visualizer.cache.put("radar", fig, **cache_key_params)
                title = "State Comparison Radar"

            elif viz_type == "Parameter Correlation Heatmap":
                cache_key_params = {"type": "heatmap"}
                cached_fig = self.visualizer.cache.get("heatmap", **cache_key_params)
                from_cache = cached_fig is not None

                if from_cache:
                    fig = cached_fig
                else:
                    self.status_var.set("Computing correlation matrix...")
                    self.root.update()
                    fig = self.visualizer.plot_parameter_correlation_heatmap()
                    self.visualizer.cache.put("heatmap", fig, **cache_key_params)
                title = "Parameter Correlation Heatmap"

            elif viz_type == "State Dashboard":
                state = self.state_var.get()
                if not state:
                    messagebox.showerror("Error", "Please select a state")
                    return

                cache_key_params = {"type": "dashboard", "state": state}
                cached_fig = self.visualizer.cache.get("dashboard", **cache_key_params)
                from_cache = cached_fig is not None

                if from_cache:
                    fig = cached_fig
                else:
                    self.status_var.set(f"Building dashboard for {state}...")
                    self.root.update()
                    fig = self.visualizer.create_state_summary_dashboard(state)
                    self.visualizer.cache.put("dashboard", fig, **cache_key_params)
                title = f"State Dashboard: {state}"

            elif viz_type == "State Transition Simulation":
                start_state = self.start_state_var.get()
                end_state = self.end_state_var.get()
                if not start_state or not end_state:
                    messagebox.showerror(
                        "Error", "Please select start and end states for transition"
                    )
                    return

                cache_key_params = {"type": "transition", "start": start_state, "end": end_state}
                cached_fig = self.visualizer.cache.get("transition", **cache_key_params)
                from_cache = cached_fig is not None

                if from_cache:
                    fig = cached_fig
                else:
                    self.status_var.set(
                        f"Simulating transition from {start_state} to {end_state}..."
                    )
                    self.root.update()
                    fig = self.visualizer.plot_state_transition(start_state, end_state)
                    self.visualizer.cache.put("transition", fig, **cache_key_params)
                title = f"State Transition: {start_state} → {end_state}"

            elif viz_type == "Comparative Analysis":
                states_text = self.states_text.get("1.0", tk.END).strip()
                states = [s.strip() for s in states_text.split("\n") if s.strip()]
                if not states or len(states) < 2:
                    messagebox.showerror("Error", "Please enter at least 2 states to compare")
                    return

                cache_key_params = {"type": "comparative", "states": ",".join(sorted(states))}
                cached_fig = self.visualizer.cache.get("comparative", **cache_key_params)
                from_cache = cached_fig is not None

                if from_cache:
                    fig = cached_fig
                else:
                    self.status_var.set(
                        f"Computing comparative analysis for {len(states)} states..."
                    )
                    self.root.update()
                    fig = self.visualizer.plot_comparative_analysis(states)
                    self.visualizer.cache.put("comparative", fig, **cache_key_params)
                title = f"Comparative Analysis: {', '.join(states)}"

            else:
                messagebox.showerror("Error", "Unknown visualization type")
                return

            if fig:
                self.current_visualization = fig

                # Render to HTML for tkinterweb
                if self.embedded_display.display_method == "tkinterweb":
                    self.status_var.set("Rendering HTML...")
                    self.root.update()
                    html_file = self.visualizer.renderer.render_figure_to_html(
                        fig, "current_viz.html"
                    )
                    self.current_html_file = html_file
                    self.embedded_display.load_html_file(html_file)
                else:
                    # Pass the actual figure to matplotlib fallback
                    self.status_var.set("Converting to matplotlib...")
                    self.root.update()
                    self.embedded_display.display_plotly_figure(fig)

                cache_status = " (cached)" if from_cache else " (new)"
                self.status_var.set(f"✓ Generated {viz_type}{cache_status}")
                self.update_info(
                    f"Visualization: {title}\n\n"
                    f"Use the controls on the left to generate different visualizations."
                )

        except Exception as e:
            error_msg = f"Failed to generate {viz_type}: {str(e)}"
            messagebox.showerror("Visualization Error", error_msg)
            self.status_var.set(f"Error: {str(e)}")
            self.update_info(
                f"Error generating visualization:\n{str(e)}\n\n"
                f"Troubleshooting:\n"
                f"• Check that all required packages are installed\n"
                f"• Try a different visualization type\n"
                f"• Restart the application if errors persist\n\n"
                f"Technical details:\n{format_exc()}"
            )

    # Compatibility methods for tests
    def _update_parameter(self, param_name: str, value: float) -> None:
        if param_name in self.parameters:
            self.parameters[param_name] = value

    def _validate_parameter(self, param_name: str, value: float) -> bool:
        return 0.0 <= value <= 1.0

    def _record_state_transition(self, state_data: Dict[str, float]) -> None:
        self.state_history.append(state_data)

    def _compute_state_analysis(self) -> Dict[str, float]:
        if not self.state_history:
            return {"average_arousal": 0.0, "average_stress": 0.0, "average_attention": 0.0}

        avg_arousal = sum(s.get("arousal", 0) for s in self.state_history) / len(self.state_history)
        avg_stress = sum(s.get("stress", 0) for s in self.state_history) / len(self.state_history)
        avg_attention = sum(s.get("attention", 0) for s in self.state_history) / len(
            self.state_history
        )

        return {
            "average_arousal": avg_arousal,
            "average_stress": avg_stress,
            "average_attention": avg_attention,
        }

    def _classify_state_category(self, state_data: Dict[str, float]) -> str:
        return "Optimal Functioning"

    def _export_state_data(self, filename: str) -> None:
        with open(filename, "w") as f:
            json.dump(self.state_history, f)

    def _export_visualization(self, filename: str) -> None:
        if self.current_visualization:
            self.current_visualization.write_image(filename)
        else:
            with open(filename, "w") as f:
                f.write("No visualization to export")

    def _render_state_visualization(self, state_data: Dict[str, float]) -> None:
        self.generate_visualization()

    def _on_canvas_resize(self, event: Any) -> None:
        if hasattr(self.renderer, "handle_resize"):
            self.renderer.handle_resize()

    def _reset_parameters(self) -> None:
        self.parameters = {"arousal": 0.5, "stress": 0.3, "attention": 0.7, "motivation": 0.6}

    def validate_parameters(self) -> bool:
        """Validate parameter input fields and update status.

        Returns:
            True if parameters are valid, False otherwise
        """
        try:
            # Get parameter values
            tau_S: float = float(self.tau_S_var.get())
            tau_theta: float = float(self.tau_theta_var.get())
            theta_0: float = float(self.theta_0_var.get())
            alpha: float = float(self.alpha_var.get())

            # Define enhanced validation ranges with specific error messages
            validation_rules = {
                "tau_S": {
                    "value": tau_S,
                    "min": 0.1,
                    "max": 1.0,
                    "error": f"τ_S must be between 0.1 and 1.0 seconds (got {tau_S:.3f})",
                    "warning": None,
                },
                "tau_theta": {
                    "value": tau_theta,
                    "min": 5.0,
                    "max": 60.0,
                    "error": f"τ_θ must be between 5 and 60 seconds (got {tau_theta:.1f})",
                    "warning": None,
                },
                "theta_0": {
                    "value": theta_0,
                    "min": 0.1,
                    "max": 0.9,
                    "error": f"θ₀ must be between 0.1 and 0.9 (got {theta_0:.3f})",
                    "warning": None,
                },
                "alpha": {
                    "value": alpha,
                    "min": 2.0,
                    "max": 20.0,
                    "error": f"α must be between 2 and 20 (got {alpha:.1f})",
                    "warning": None,
                },
            }

            # Check each parameter with enhanced validation
            for param_name, rules in validation_rules.items():
                value: Any = rules["value"]
                min_val: float = float(rules["min"])  # type: ignore[arg-type]
                max_val: float = float(rules["max"])  # type: ignore[arg-type]

                if not (min_val <= value <= max_val):
                    self.validation_status.set(f"✗ {rules['error']}")
                    self.validation_label.config(foreground="red")
                    self.generate_button.config(state="disabled")

                    # Provide specific guidance
                    if param_name == "tau_S":
                        messagebox.showwarning(
                            "Parameter Range Error",
                            f"τ_S (surprise timescale) should typically be:\n"
                            f"• 0.1-0.3s for rapid processing\n"
                            f"• 0.3-0.7s for normal processing\n"
                            f"• 0.7-1.0s for slow, deliberate processing\n\n"
                            f"Current value: {tau_S:.3f}s",
                        )
                    elif param_name == "tau_theta":
                        messagebox.showwarning(
                            "Parameter Range Error",
                            f"τ_θ (threshold timescale) should typically be:\n"
                            f"• 5-15s for labile thresholds\n"
                            f"• 15-30s for normal thresholds\n"
                            f"• 30-60s for stable thresholds\n\n"
                            f"Current value: {tau_theta:.1f}s",
                        )
                    return False

            # All validations passed
            self.validation_status.set("✓ Parameters valid - Ready for simulation")
            self.validation_label.config(foreground="green")
            self.generate_button.config(state="normal")
            return True

        except ValueError as e:
            self.validation_status.set("✗ Invalid numeric input")
            self.validation_label.config(foreground="red")
            self.generate_button.config(state="disabled")
            messagebox.showerror(
                "Input Error",
                f"Please enter valid numeric values.\n\n"
                f"Common issues:\n"
                f"• Using commas instead of periods\n"
                f"• Entering text instead of numbers\n"
                f"• Leaving fields empty\n\n"
                f"Error details: {str(e)}",
            )
            return False
        except Exception as e:
            self.validation_status.set(f"✗ Validation error: {str(e)}")
            self.validation_label.config(foreground="red")
            self.generate_button.config(state="disabled")
            messagebox.showerror(
                "Unexpected Error",
                f"An unexpected error occurred during validation:\n\n{str(e)}",
            )
            return False

    def run_simulation_with_validation(self) -> None:
        """Run simulation with parameter validation"""
        if not self.validate_parameters():
            messagebox.showerror(
                "Invalid Parameters",
                "Please correct the parameter values before running simulation.",
            )
            return

        try:
            # Get validated parameters
            params = {
                "tau_S": float(self.tau_S_var.get()),
                "tau_theta": float(self.tau_theta_var.get()),
                "theta_0": float(self.theta_0_var.get()),
                "alpha": float(self.alpha_var.get()),
            }

            self.status_var.set("Running simulation...")
            self.root.update()

            # Import simulation components with enhanced error handling
            sim_module_path = "APGI-Equations.py"
            if not os.path.exists(sim_module_path):
                raise ImportError(f"Simulation module not found: {sim_module_path}")

            try:
                import importlib.util

                spec = importlib.util.spec_from_file_location("APGI_Equations", sim_module_path)
                if spec is None or spec.loader is None:
                    raise ImportError(f"Could not create spec for {sim_module_path}")

                APGI_module = importlib.util.module_from_spec(spec)

                # Verify required classes exist before loading
                required_classes = ["EnhancedSurpriseIgnitionSystem", "APGIParameters"]
                missing_classes = []

                try:
                    spec.loader.exec_module(APGI_module)

                    for class_name in required_classes:
                        if not hasattr(APGI_module, class_name):
                            missing_classes.append(class_name)

                    if missing_classes:
                        raise ImportError(f"Missing required classes: {missing_classes}")

                except Exception as load_error:
                    raise ImportError(f"Failed to load simulation module: {load_error}")

                SurpriseIgnitionSystem = APGI_module.EnhancedSurpriseIgnitionSystem
                SimAPGIParameters = APGI_module.APGIParameters

            except ImportError as import_error:
                raise ImportError(f"Simulation module import failed: {import_error}")
            except Exception as unexpected_error:
                raise ImportError(f"Unexpected error loading simulation: {unexpected_error}")

            # Create system with user parameters
            system_params = SimAPGIParameters(
                tau_S=params["tau_S"],
                tau_theta=params["tau_theta"],
                theta_0=params["theta_0"],
                alpha=params["alpha"],
            )

            system = SurpriseIgnitionSystem(params=system_params)

            # Define simple input generator
            def input_generator(t):
                return {
                    "Pi_e": 1.0 + 0.5 * np.sin(2 * np.pi * 0.1 * t),  # 0.1 Hz oscillation
                    "Pi_i": 1.0,
                    "eps_e": 0.5,
                    "eps_i": 0.3,
                    "beta": 1.0,
                }

            # Run simulation
            duration = 30.0  # 30 seconds
            dt = 0.05  # 50 ms timestep
            history = system.simulate(duration, dt, input_generator)

            # Generate visualization of results
            self.generate_simulation_visualization(history, params)

            self.status_var.set("✓ Simulation completed successfully")
            self.update_info(
                f"Simulation completed with parameters:\n"
                f"τ_S = {params['tau_S']:.2f}s\n"
                f"τ_θ = {params['tau_theta']:.1f}s\n"
                f"θ₀ = {params['theta_0']:.2f}\n"
                f"α = {params['alpha']:.1f}\n\n"
                f"Duration: {duration}s, Timestep: {dt}s\n"
                f"Ignitions detected: {len([i for i in history['P_ignition'] if i > 0.5])}"
            )

        except ImportError as e:
            messagebox.showerror(
                "Import Error",
                f"Required simulation module not found: {str(e)}\n"
                "Please ensure APGI-Equations.py is available.",
            )
            self.status_var.set("Error: Missing simulation module")
        except Exception as e:
            messagebox.showerror("Simulation Error", f"Failed to run simulation: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
            self.update_info(f"Simulation error:\n{str(e)}")

    def generate_simulation_visualization(self, history: dict, params: dict) -> None:
        """Generate visualization of simulation results"""
        try:
            if PLOTLY_AVAILABLE:
                # Create subplots
                fig = make_subplots(
                    rows=3,
                    cols=1,
                    subplot_titles=(
                        "Surprise Accumulation",
                        "Threshold Dynamics",
                        "Ignition Events",
                    ),
                    vertical_spacing=0.08,
                )

                time = history["time"]

                # Plot surprise
                fig.add_trace(
                    go.Scatter(
                        x=time,
                        y=history["S"],
                        name="Surprise (S_t)",
                        line=dict(color="blue"),
                    ),
                    row=1,
                    col=1,
                )

                # Plot threshold
                fig.add_trace(
                    go.Scatter(
                        x=time,
                        y=history["theta"],
                        name="Threshold (θ_t)",
                        line=dict(color="red"),
                    ),
                    row=2,
                    col=1,
                )

                # Plot ignition
                fig.add_trace(
                    go.Scatter(
                        x=time,
                        y=history["P_ignition"],
                        name="Ignition",
                        line=dict(color="green"),
                    ),
                    row=3,
                    col=1,
                )

                # Update layout
                fig.update_layout(
                    title=f"APGI Simulation Results (τ_S={params['tau_S']:.2f}s, α={params['alpha']:.1f})",
                    height=600,
                    showlegend=True,
                )

                fig.update_xaxes(title_text="Time (s)", row=3, col=1)
                fig.update_yaxes(title_text="Surprise", row=1, col=1)
                fig.update_yaxes(title_text="Threshold", row=2, col=1)
                fig.update_yaxes(title_text="Ignition", row=3, col=1)

                # Display in embedded panel
                self.embedded_display.display_plotly_figure(fig)

            else:
                # Fallback to text display
                self.update_info(
                    f"Simulation completed successfully!\n\n"
                    f"Parameters used:\n"
                    f"τ_S = {params['tau_S']:.2f}s\n"
                    f"τ_θ = {params['tau_theta']:.1f}s\n"
                    f"θ₀ = {params['theta_0']:.2f}\n"
                    f"α = {params['alpha']:.1f}\n\n"
                    f"Results:\n"
                    f"Final surprise: {history['S'][-1]:.3f}\n"
                    f"Final threshold: {history['theta'][-1]:.3f}\n"
                    f"Ignitions: {len([i for i in history['P_ignition'] if i > 0.5])}\n\n"
                    f"Install plotly for graphical visualization."
                )

        except Exception as e:
            self.update_info(f"Visualization error: {str(e)}")

    def load_configuration(self) -> bool:
        """Load configuration from file with fallback to defaults.

        Returns:
            True if configuration was loaded successfully, False otherwise
        """
        try:
            # Try to import yaml with proper error handling
            try:
                import yaml as yaml_module

                YAML_AVAILABLE = True
            except ImportError:
                YAML_AVAILABLE = False
                logger.warning("PyYAML not available. Using default configuration.")
                return False

            if not YAML_AVAILABLE:
                return False

            config_path: str = "config/gui_config.yaml"

            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    try:
                        config = yaml_module.safe_load(f)

                        # Validate configuration structure
                        if not isinstance(config, dict):
                            raise ValueError("Configuration must be a dictionary")

                        # Validate configuration schema
                        self._validate_config_schema(config)

                        # Apply configuration values with validation
                        sim_config = config.get("simulation", {})
                        if isinstance(sim_config, dict):
                            if "tau_S_default" in sim_config:
                                tau_S_val = sim_config.get("tau_S_default", 0.5)
                                if isinstance(tau_S_val, (int, float)) and 0.1 <= tau_S_val <= 1.0:
                                    self.tau_S_var.set(str(tau_S_val))
                                else:
                                    logger.warning(f"Invalid tau_S_default value: {tau_S_val}")

                            if "tau_theta_default" in sim_config:
                                tau_theta_val = sim_config.get("tau_theta_default", 30.0)
                                if (
                                    isinstance(tau_theta_val, (int, float))
                                    and 5.0 <= tau_theta_val <= 60.0
                                ):
                                    self.tau_theta_var.set(str(tau_theta_val))
                                else:
                                    logger.warning(
                                        f"Invalid tau_theta_default value: {tau_theta_val}"
                                    )

                            if "theta_0_default" in sim_config:
                                theta_0_val = sim_config.get("theta_0_default", 0.5)
                                if (
                                    isinstance(theta_0_val, (int, float))
                                    and 0.1 <= theta_0_val <= 0.9
                                ):
                                    self.theta_0_var.set(str(theta_0_val))
                                else:
                                    logger.warning(f"Invalid theta_0_default value: {theta_0_val}")

                            if "alpha_default" in sim_config:
                                alpha_val = sim_config.get("alpha_default", 5.0)
                                if isinstance(alpha_val, (int, float)) and 2.0 <= alpha_val <= 20.0:
                                    self.alpha_var.set(str(alpha_val))
                                else:
                                    logger.warning(f"Invalid alpha_default value: {alpha_val}")

                        # Set default visualization
                        viz_config = config.get("visualization", {})
                        if isinstance(viz_config, dict):
                            cache_size = viz_config.get("cache_max_size", 50)
                            if isinstance(cache_size, int) and 10 <= cache_size <= 200:
                                self.visualizer.cache.max_size = cache_size
                            else:
                                logger.warning(f"Invalid cache_max_size value: {cache_size}")

                        return True

                    except yaml_module.YAMLError as yaml_error:
                        logger.warning(f"YAML parsing error in {config_path}: {yaml_error}")
                        return False
                    except (ValueError, TypeError) as validation_error:
                        logger.warning(f"Configuration validation error: {validation_error}")
                        return False
            else:
                logger.info(f"Configuration file {config_path} not found, using defaults")
                return False

        except Exception as e:
            logger.warning(f"Unexpected error loading configuration: {e}")
            return False

    def _validate_config_schema(self, config: Dict[str, Any]) -> None:
        """Validate configuration schema.

        Args:
            config: Configuration dictionary to validate

        Raises:
            ValueError: If configuration schema is invalid
        """
        # Validate simulation config if present
        if "simulation" in config:
            sim_config = config["simulation"]
            if not isinstance(sim_config, dict):
                raise ValueError("simulation config must be a dictionary")

            valid_sim_keys = {
                "tau_S_default",
                "tau_theta_default",
                "theta_0_default",
                "alpha_default",
            }
            for key in sim_config:
                if key not in valid_sim_keys:
                    logger.warning(f"Unknown simulation config key: {key}")

        # Validate visualization config if present
        if "visualization" in config:
            viz_config = config["visualization"]
            if not isinstance(viz_config, dict):
                raise ValueError("visualization config must be a dictionary")

            valid_viz_keys = {"cache_max_size"}
            for key in viz_config:
                if key not in valid_viz_keys:
                    logger.warning(f"Unknown visualization config key: {key}")

    def clear_display(self) -> None:
        """Clear the visualization panel"""
        self.embedded_display.clear()
        self.status_var.set("Display cleared")
        self.update_info(
            "Visualization cleared. Select a new visualization type and click Generate."
        )

    def _setup_cleanup_handlers(self) -> None:
        """Setup signal handlers for graceful cleanup on exit"""
        # Register cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self._cleanup_and_exit)

        # Register signal handlers for graceful shutdown
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except (ValueError, AttributeError):
            # Signal handlers may not work on all platforms
            pass

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle termination signals for graceful shutdown.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self._cleanup_and_exit()

    def _cleanup_and_exit(self) -> None:
        """Perform cleanup operations before exiting"""
        logger.info("Starting cleanup...")

        try:
            # Cleanup visualizer resources
            if hasattr(self, "visualizer") and self.visualizer:
                if hasattr(self.visualizer, "renderer"):
                    self.visualizer.renderer.force_cleanup()
                if hasattr(self.visualizer, "cache"):
                    self.visualizer.cache.clear()

            # Cleanup embedded display
            if hasattr(self, "embedded_display") and self.embedded_display:
                self.embedded_display.clear()

            # Close matplotlib figures
            if MATPLOTLIB_AVAILABLE:
                try:
                    import matplotlib.pyplot as plt

                    plt.close("all")
                except Exception:
                    pass

            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        finally:
            # Always destroy the window
            try:
                if hasattr(self, "root") and self.root:
                    self.root.destroy()
            except Exception:
                pass

    def run(self) -> None:
        """Start the GUI main loop"""
        self.root.mainloop()


class EmbeddedDisplayPanel(ttk.Frame):
    """Custom embedded panel for displaying HTML content exclusively within the GUI

    This panel handles all visualization rendering internally with no external
    browser dependencies, opening options, or save capabilities.
    """

    def __init__(self, parent: Any, **kwargs: Any) -> None:
        """Initialize the embedded display panel"""
        super().__init__(parent, **kwargs)

        # Initialize Optional attributes
        self.matplotlib_canvas: Optional[Any] = None
        self.toolbar: Optional[Any] = None

        # Try different display methods
        self.display_method = self._setup_display()
        self._canvas_cleanup()

    def _canvas_cleanup(self) -> None:
        """Clean up matplotlib canvas to prevent memory leaks"""
        self._cleanup_matplotlib_canvas()
        self._cleanup_toolbar()
        self._cleanup_all_figures()

    def _cleanup_matplotlib_canvas(self) -> None:
        """Clean up the matplotlib canvas widget"""
        if not self.matplotlib_canvas:  # type: ignore[has-type]
            return

        try:
            # Close the matplotlib figure to free memory
            if hasattr(self.matplotlib_canvas, "figure"):
                self.matplotlib_canvas.figure.clf()

                plt.close(self.matplotlib_canvas.figure)

            # Destroy the tkinter widget
            widget = self.matplotlib_canvas.get_tk_widget()  # type: ignore[has-type]
            if widget.winfo_exists():
                widget.destroy()
            self.matplotlib_canvas = None
        except (AttributeError, tk.TclError, RuntimeError):
            self.matplotlib_canvas = None

    def _cleanup_toolbar(self) -> None:
        """Clean up the matplotlib toolbar"""
        if not self.toolbar:
            return

        try:
            if self.toolbar.winfo_exists():
                self.toolbar.destroy()
            self.toolbar = None
        except (AttributeError, tk.TclError):
            self.toolbar = None

    def _cleanup_all_figures(self) -> None:
        """Clean up any remaining matplotlib figures"""
        if MATPLOTLIB_AVAILABLE:
            try:
                import matplotlib.pyplot as plt

                plt.close("all")
            except (ImportError, RuntimeError):
                pass

    def _setup_display(self):
        """Setup the display backend (tkinterweb or fallback)"""
        if TKINTERWEB_AVAILABLE:
            try:
                self.html_frame = HTMLFrame(self, messages_enabled=False)
                self.html_frame.pack(fill=tk.BOTH, expand=True)
                return "tkinterweb"
            except Exception as e:
                logger.warning(f"Failed to initialize HtmlFrame: {e}, using fallback")

        # Fallback display for when tkinterweb is not available
        self._setup_fallback_display()
        return "fallback"

    def _setup_fallback_display(self):
        """Setup fallback display using matplotlib canvas"""
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True)

        if MATPLOTLIB_AVAILABLE:
            # Create matplotlib canvas for fallback rendering
            self.canvas_frame = frame
            self.matplotlib_canvas = None
            self.toolbar = None

            # Initial message
            self.info_label = ttk.Label(
                frame,
                text="📊 Visualization Panel\n\n"
                "Visualizations will be displayed here using matplotlib.\n\n"
                "Generate a visualization to see it in this panel.",
                font=("Arial", 12),
                justify=tk.CENTER,
            )
            self.info_label.pack(fill=tk.BOTH, expand=True)
        else:
            # No matplotlib available
            label = ttk.Label(
                frame,
                text="📊 Visualization Panel\n\n"
                "Neither tkinterweb nor matplotlib are available.\n\n"
                "Install tkinterweb: pip install tkinterweb\n"
                "or matplotlib: pip install matplotlib",
                font=("Arial", 12),
                justify=tk.CENTER,
            )
            label.pack(fill=tk.BOTH, expand=True)
            self.info_label = label

    def display_plotly_figure(self, fig: Any) -> None:
        """Display a Plotly figure using matplotlib fallback"""
        if not MATPLOTLIB_AVAILABLE:
            return

        try:
            # Clean up existing canvas before creating new one
            self._canvas_cleanup()

            # Clear existing widgets
            for widget in self.canvas_frame.winfo_children():
                widget.destroy()

            # Create matplotlib figure and render
            mpl_fig = self._create_matplotlib_figure()
            self._render_plotly_to_matplotlib(fig, mpl_fig)
            self._setup_matplotlib_canvas(mpl_fig)

        except Exception as e:
            logger.error(f"Error creating matplotlib visualization: {e}")
            self._show_rendering_error(e)

    def _create_matplotlib_figure(self):
        """Create a new matplotlib figure for rendering"""
        from matplotlib.figure import Figure

        return Figure(figsize=(12, 8))

    def _setup_matplotlib_canvas(self, mpl_fig):
        """Setup matplotlib canvas and toolbar"""
        self.matplotlib_canvas = FigureCanvasTkAgg(mpl_fig, self.canvas_frame)
        self.toolbar = NavigationToolbar2Tk(self.matplotlib_canvas, self.canvas_frame)

        # Pack toolbar and canvas
        self.toolbar.update()
        self.matplotlib_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Draw the figure
        self.matplotlib_canvas.draw()

    def _render_plotly_to_matplotlib(self, fig, mpl_fig):
        """Render Plotly figure data to matplotlib"""
        if not hasattr(fig, "data") or not fig.data:
            self._render_empty_visualization(mpl_fig)
            return

        # Check if this is a polar plot
        if self._is_polar_plot(fig):
            self._render_polar_plot(fig, mpl_fig)
        else:
            self._render_standard_plot(fig, mpl_fig)

    def _is_polar_plot(self, fig: Any) -> bool:
        """Check if figure contains polar plot data"""
        return all(hasattr(trace, "r") and hasattr(trace, "theta") for trace in fig.data)

    def _render_polar_plot(self, fig: Any, mpl_fig: Any) -> None:
        """Render polar plot from Plotly data to matplotlib"""
        ax = mpl_fig.add_subplot(111, projection="polar")

        for trace in fig.data:
            theta_values, r_values = self._prepare_polar_data(trace)
            self._plot_polar_trace(ax, theta_values, r_values, trace.name)

        self._configure_polar_axes(ax, fig)

    def _prepare_polar_data(self, trace: Any) -> Tuple[List[Any], List[Any]]:
        """Prepare and clean polar plot data from trace"""
        theta_values = list(trace.theta)
        r_values = list(trace.r)

        # Remove duplicate closing point if present
        if len(theta_values) > 1 and theta_values[0] == theta_values[-1]:
            theta_values = theta_values[:-1]
            r_values = r_values[:-1]

        return theta_values, r_values

    def _plot_polar_trace(self, ax, theta_values, r_values, label):
        """Plot a single polar trace"""
        ax.plot(
            theta_values,
            r_values,
            "o-",
            linewidth=2,
            markersize=6,
            label=label,
        )
        ax.fill(theta_values, r_values, alpha=0.25)

    def _configure_polar_axes(self, ax, fig):
        """Configure polar axes with grid, title, and legend"""
        ax.set_thetagrids(range(0, 360, 45))
        ax.set_title(
            f"{fig.layout.title.text if hasattr(fig.layout, 'title') else 'APGI Radar Chart'}"
        )

        # Add legend if multiple traces
        if len(fig.data) > 1:
            ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0))

    def _render_standard_plot(self, fig, mpl_fig):
        """Render standard 2D/3D plots from Plotly to matplotlib"""
        if not fig.data:
            self._render_empty_visualization(mpl_fig)
            return

        trace = fig.data[0]

        if hasattr(trace, "x") and hasattr(trace, "y") and trace.x is not None:
            self._render_2d_scatter(trace, mpl_fig)
        elif hasattr(trace, "z") and hasattr(trace, "x") and hasattr(trace, "y"):
            self._render_3d_projection(trace, mpl_fig)
        else:
            self._render_info_message(fig, mpl_fig)

    def _render_2d_scatter(self, trace: Any, mpl_fig: Any) -> None:
        """Render 2D scatter plot"""
        ax = mpl_fig.add_subplot(111)
        ax.scatter(trace.x, trace.y, alpha=0.7, s=50)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_title("APGI Visualization (Static Version)")
        ax.grid(True, alpha=0.3)

    def _render_3d_projection(self, trace: Any, mpl_fig: Any) -> None:
        """Render 3D scatter plot as 2D projection"""
        ax = mpl_fig.add_subplot(111)
        ax.scatter(
            trace.x,
            trace.y,
            c=trace.z,
            alpha=0.7,
            s=50,
            cmap="viridis",
        )
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_title("APGI 3D Visualization (2D Projection)")
        ax.grid(True, alpha=0.3)

        # Add colorbar
        if mpl_fig.gca().collections:
            plt.colorbar(mpl_fig.gca().collections[0], ax=ax, label="Z value")

    def _render_info_message(self, fig: Any, mpl_fig: Any) -> None:
        """Render generic info message for unsupported plot types"""
        ax = mpl_fig.add_subplot(111)
        trace = fig.data[0] if fig.data else None
        trace_type = type(trace).__name__ if trace else "Unknown"

        ax.text(
            0.5,
            0.5,
            f"📊 {fig.layout.title.text if hasattr(fig.layout, 'title') else 'APGI Visualization'}\n\n"
            f"Interactive Plotly visualization\n\n"
            f"Type: {trace_type}\n\n"
            f"For full interactivity, install:\n"
            f"pip install tkinterweb\n\n"
            f"Then restart the application.",
            ha="center",
            va="center",
            fontsize=12,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue"),
        )
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

    def _render_empty_visualization(self, mpl_fig: Any) -> None:
        """Render message for empty visualization"""
        ax = mpl_fig.add_subplot(111)
        ax.text(
            0.5,
            0.5,
            "📊 APGI Visualization\n\n"
            "No data available for this visualization type.\n\n"
            "For full interactive visualizations, install:\n"
            "pip install tkinterweb",
            ha="center",
            va="center",
            fontsize=12,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue"),
        )
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

    def _show_rendering_error(self, error: Any) -> None:
        """Show error message when rendering fails"""
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        error_label = ttk.Label(
            self.canvas_frame,
            text=f"❌ Error rendering visualization\n\n{str(error)}\n\n"
            "For best results, install tkinterweb:\n"
            "pip install tkinterweb",
            font=("Arial", 11),
            justify=tk.CENTER,
            foreground="red",
        )
        error_label.pack(fill=tk.BOTH, expand=True)

    def _plotly_to_matplotlib(self, fig):
        """Convert a Plotly figure to matplotlib for fallback display"""
        if not MATPLOTLIB_AVAILABLE:
            return None
        return self.display_plotly_figure(fig)

    def load_html_file(self, filepath: str) -> None:
        """Load and display an HTML file.

        Args:
            filepath: Path to the HTML file to load
        """
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return

        if self.display_method == "tkinterweb":
            try:
                with open(filepath, encoding="utf-8") as f:
                    html_content = f.read()
                self.html_frame.load_html(html_content)
            except Exception as e:
                logger.error(f"Error loading HTML: {e}")
        else:
            # Fallback: Show matplotlib version
            try:
                if hasattr(self, "info_label"):
                    self.info_label.destroy()
            except (AttributeError, tk.TclError):
                pass  # Widget doesn't exist or already destroyed

            # Clear display and show message
            self.clear()

    def clear(self):
        """Clear display"""
        if self.display_method == "tkinterweb":
            try:
                self.html_frame.load_html("<html><body><h2>Cleared</h2></body></html>")
            except (AttributeError, Exception):
                pass  # HTML frame not available or error loading
        else:
            # Clear matplotlib canvas
            if hasattr(self, "matplotlib_canvas") and self.matplotlib_canvas:
                # Clear existing widgets
                for widget in self.canvas_frame.winfo_children():
                    widget.destroy()

                # Show initial message again
                self.info_label = ttk.Label(
                    self.canvas_frame,
                    text="📊 Visualization Panel\n\n"
                    "Visualizations will be displayed here using matplotlib.\n\n"
                    "Generate a visualization to see it in this panel.",
                    font=("Arial", 12),
                    justify=tk.CENTER,
                )
                self.info_label.pack(fill=tk.BOTH, expand=True)
                self.matplotlib_canvas = None
                self.toolbar = None


# =============================================================================
# STATE DEFINITIONS AND FACTORY FUNCTION
# =============================================================================


def create_apgi_params(
    Pi_e: float,
    Pi_i_baseline: float,
    M_ca: float,
    beta: float,
    z_e: float,
    z_i: float,
    theta_t: float,
) -> APGIParameters:
    """Factory function that computes derived parameters automatically.

    Args:
        Pi_e: Excitatory precision
        Pi_i_baseline: Baseline inhibitory precision
        M_ca: Allostatic modulation
        beta: Modulation sensitivity
        z_e: Excitatory prediction error
        z_i: Inhibitory prediction error
        theta_t: Threshold

    Returns:
        APGIParameters with all computed fields
    """
    try:
        Pi_i_eff = Pi_i_baseline * np.exp(beta * M_ca)
        Pi_i_eff = np.clip(Pi_i_eff, 0.1, 10.0)
        S_t = Pi_e * abs(z_e) + Pi_i_eff * abs(z_i)

        return APGIParameters(
            Pi_e=Pi_e,
            Pi_i_baseline=Pi_i_baseline,
            Pi_i_eff=Pi_i_eff,
            theta_t=theta_t,
            S_t=S_t,
            M_ca=M_ca,
            beta=beta,
            z_e=z_e,
            z_i=z_i,
        )
    except Exception as e:
        raise ValueError(f"Failed to create APGI parameters: {e}") from e


# Data-driven state definitions
STATE_DEFINITIONS = [
    # Category 1: Optimal Functioning States
    ("flow", StateCategory.OPTIMAL_FUNCTIONING, 6.5, 1.5, 0.3, 0.5, 0.4, 0.2, 1.8),
    ("focus", StateCategory.OPTIMAL_FUNCTIONING, 8.0, 1.2, 0.25, 0.5, 0.8, 0.3, -0.5),
    ("serenity", StateCategory.OPTIMAL_FUNCTIONING, 1.5, 2.0, 0.7, 0.5, 0.2, 0.3, 1.5),
    ("mindfulness", StateCategory.OPTIMAL_FUNCTIONING, 3.0, 3.5, 0.9, 0.55, 0.6, 0.5, 0.0),
    # Category 2: Positive Affective States
    ("amusement", StateCategory.POSITIVE_AFFECTIVE, 4.0, 1.0, -0.1, 0.5, 1.2, 0.2, -0.3),
    ("joy", StateCategory.POSITIVE_AFFECTIVE, 5.0, 2.5, 0.8, 0.55, 1.0, 0.7, -0.8),
    ("pride", StateCategory.POSITIVE_AFFECTIVE, 4.5, 3.0, 1.1, 0.6, 1.2, 0.9, -0.6),
    ("romantic_love_early", StateCategory.POSITIVE_AFFECTIVE, 7.5, 4.0, 1.8, 0.7, 1.5, 1.3, -1.5),
    (
        "romantic_love_sustained",
        StateCategory.POSITIVE_AFFECTIVE,
        5.0,
        3.0,
        1.2,
        0.6,
        0.5,
        0.6,
        -0.8,
    ),
    ("gratitude", StateCategory.POSITIVE_AFFECTIVE, 4.0, 2.5, 0.8, 0.55, 0.3, 0.5, -0.4),
    ("hope", StateCategory.POSITIVE_AFFECTIVE, 5.0, 2.0, 0.6, 0.5, 0.9, 0.4, -0.7),
    ("optimism", StateCategory.POSITIVE_AFFECTIVE, 3.0, 2.0, 0.4, 0.5, 0.4, 0.3, -0.5),
    # Category 3: Cognitive and Attentional States
    ("curiosity", StateCategory.COGNITIVE_ATTENTIONAL, 6.0, 1.0, -0.2, 0.45, 1.4, 0.2, -0.9),
    ("boredom", StateCategory.COGNITIVE_ATTENTIONAL, 0.8, 1.5, -0.3, 0.5, 0.1, 0.2, -1.0),
    ("creativity", StateCategory.COGNITIVE_ATTENTIONAL, 4.0, 1.0, -0.3, 0.45, 1.2, 0.2, -1.2),
    ("inspiration", StateCategory.COGNITIVE_ATTENTIONAL, 8.5, 1.5, 0.4, 0.5, 2.0, 0.4, -2.0),
    ("hyperfocus", StateCategory.COGNITIVE_ATTENTIONAL, 9.5, 0.5, -0.8, 0.4, 0.6, 0.1, 2.5),
    ("fatigue", StateCategory.COGNITIVE_ATTENTIONAL, 1.5, 2.0, 0.4, 0.5, 0.3, 0.4, 1.8),
    ("decision_fatigue", StateCategory.COGNITIVE_ATTENTIONAL, 2.5, 1.5, 0.3, 0.5, 0.8, 0.3, 1.5),
    ("mind_wandering", StateCategory.COGNITIVE_ATTENTIONAL, 0.8, 3.5, 0.6, 0.55, 0.2, 0.9, 1.5),
    # Category 4: Aversive Affective States
    ("fear", StateCategory.AVERSIVE_AFFECTIVE, 8.0, 3.0, 1.9, 0.75, 2.5, 2.0, -2.5),
    ("anxiety", StateCategory.AVERSIVE_AFFECTIVE, 6.5, 3.5, 1.5, 0.65, 1.5, 1.3, -1.5),
    ("anger", StateCategory.AVERSIVE_AFFECTIVE, 7.5, 3.0, 1.5, 0.65, 2.0, 1.4, -1.2),
    ("guilt", StateCategory.AVERSIVE_AFFECTIVE, 5.0, 2.5, 0.8, 0.55, 1.3, 0.9, -0.8),
    ("shame", StateCategory.AVERSIVE_AFFECTIVE, 7.0, 3.0, 1.3, 0.6, 1.8, 1.2, -1.5),
    ("loneliness", StateCategory.AVERSIVE_AFFECTIVE, 5.5, 2.5, 0.8, 0.55, 1.4, 0.9, -1.0),
    ("overwhelm", StateCategory.AVERSIVE_AFFECTIVE, 3.0, 3.0, 1.2, 0.6, 2.8, 1.5, 0.0),
    # Category 5: Pathological and Extreme States
    ("depression", StateCategory.PATHOLOGICAL_EXTREME, 2.0, 1.5, 0.3, 0.5, 0.4, 0.8, 1.5),
    ("learned_helplessness", StateCategory.PATHOLOGICAL_EXTREME, 1.5, 2.0, 0.5, 0.5, 0.2, 0.4, 2.0),
    (
        "pessimistic_depression",
        StateCategory.PATHOLOGICAL_EXTREME,
        2.5,
        2.0,
        0.7,
        0.55,
        0.3,
        0.6,
        1.8,
    ),
    ("panic", StateCategory.PATHOLOGICAL_EXTREME, 4.0, 5.0, 2.0, 0.8, 1.5, 3.0, -3.0),
    ("dissociation", StateCategory.PATHOLOGICAL_EXTREME, 2.0, 0.5, -1.5, 0.35, 0.8, 0.1, 2.0),
    ("depersonalization", StateCategory.PATHOLOGICAL_EXTREME, 3.0, 0.8, -1.2, 0.4, 1.0, 0.5, 1.5),
    ("derealization", StateCategory.PATHOLOGICAL_EXTREME, 1.5, 1.5, -0.8, 0.45, 1.2, 0.4, 1.8),
    # Category 6: Altered and Boundary States
    ("awe", StateCategory.ALTERED_BOUNDARY, 3.5, 2.5, 0.8, 0.55, 2.8, 0.7, -1.5),
    ("trance", StateCategory.ALTERED_BOUNDARY, 1.0, 4.0, 0.4, 0.5, 0.2, 0.6, 2.0),
    ("meditation_focused", StateCategory.ALTERED_BOUNDARY, 7.0, 3.5, 1.0, 0.55, 0.5, 0.6, 1.5),
    ("meditation_open", StateCategory.ALTERED_BOUNDARY, 3.0, 3.0, 0.7, 0.5, 0.8, 0.6, 0.0),
    ("meditation_nondual", StateCategory.ALTERED_BOUNDARY, 2.0, 1.5, 0.5, 0.5, 0.2, 0.2, 2.0),
    ("hypnosis", StateCategory.ALTERED_BOUNDARY, 2.0, 3.5, 0.6, 0.55, 0.3, 0.8, -1.5),
    ("hypnagogia", StateCategory.ALTERED_BOUNDARY, 2.5, 4.0, 0.7, 0.55, 0.6, 1.0, 0.5),
    ("deja_vu", StateCategory.ALTERED_BOUNDARY, 4.5, 1.5, 0.2, 0.5, 0.4, 0.2, -0.8),
    # Category 7: Transitional/Contextual States
    ("morning_flow", StateCategory.TRANSITIONAL_CONTEXTUAL, 5.5, 2.0, 0.5, 0.5, 0.3, 0.3, 1.2),
    ("evening_fatigue", StateCategory.TRANSITIONAL_CONTEXTUAL, 1.2, 3.0, 1.0, 0.55, 0.2, 0.7, 2.2),
    (
        "creative_inspiration",
        StateCategory.TRANSITIONAL_CONTEXTUAL,
        8.0,
        1.5,
        0.3,
        0.5,
        2.2,
        0.3,
        -1.8,
    ),
    (
        "anxious_rumination",
        StateCategory.TRANSITIONAL_CONTEXTUAL,
        6.0,
        3.5,
        1.4,
        0.65,
        1.6,
        1.2,
        -1.2,
    ),
    ("calm", StateCategory.TRANSITIONAL_CONTEXTUAL, 1.8, 2.0, 0.5, 0.5, 0.2, 0.3, 1.2),
    ("productive_focus", StateCategory.TRANSITIONAL_CONTEXTUAL, 7.0, 1.5, 0.3, 0.5, 0.7, 0.3, -0.3),
    ("second_wind", StateCategory.TRANSITIONAL_CONTEXTUAL, 5.5, 2.5, 0.5, 0.55, 0.9, 0.5, -0.8),
    # Category 8: Previously Unelaborated States
    ("hypervigilance", StateCategory.UNELABORATED, 8.5, 4.0, 1.7, 0.7, 1.8, 1.5, -2.0),
    ("sadness", StateCategory.UNELABORATED, 4.5, 2.5, 0.9, 0.55, 1.2, 0.8, -0.6),
    ("choice_paralysis", StateCategory.UNELABORATED, 2.5, 2.0, 0.5, 0.5, 0.9, 0.5, 1.5),
    ("mental_paralysis", StateCategory.UNELABORATED, 2.0, 3.5, 1.3, 0.65, 3.0, 1.8, 0.5),
    ("curious_exploration", StateCategory.UNELABORATED, 6.5, 1.0, -0.1, 0.45, 1.6, 0.2, -1.0),
]


# Generate state dictionaries from data-driven definitions
PSYCHOLOGICAL_STATES: Dict[str, APGIParameters] = {}
STATE_CATEGORIES: Dict[str, StateCategory] = {}

for name, category, Pi_e, Pi_i_baseline, M_ca, beta, z_e, z_i, theta_t in STATE_DEFINITIONS:
    try:
        PSYCHOLOGICAL_STATES[name] = create_apgi_params(
            Pi_e=Pi_e,
            Pi_i_baseline=Pi_i_baseline,
            M_ca=M_ca,
            beta=beta,
            z_e=z_e,
            z_i=z_i,
            theta_t=theta_t,
        )
        STATE_CATEGORIES[name] = category
    except ValueError as e:
        logger.warning(f"Skipping invalid state '{name}': {e}")
        continue


def identify_emergent_state(params: Dict[str, float]) -> Tuple[str, float]:
    """Identify the psychological state that emerges from given params."""
    temp_classifier = StateClassifier(PSYCHOLOGICAL_STATES)
    return temp_classifier.classify(params)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def get_state(name: str) -> APGIParameters:
    """Retrieve parameters for a named psychological state.

    Args:
        name: Name of the psychological state

    Returns:
        APGIParameters for the state

    Raises:
        KeyError: If state is not found
    """
    if name not in PSYCHOLOGICAL_STATES:
        available_states = ", ".join(sorted(PSYCHOLOGICAL_STATES.keys())[:5])
        raise KeyError(
            f"Unknown state: {name}. " f"Available states include: {available_states}..."
        )
    return PSYCHOLOGICAL_STATES[name]


def get_states_by_category(category: StateCategory) -> Dict[str, APGIParameters]:
    """Retrieve all states belonging to a category"""
    return {
        name: params
        for name, params in PSYCHOLOGICAL_STATES.items()
        if STATE_CATEGORIES.get(name) == category
    }


# =============================================================================
# MAIN APPLICATION
# =============================================================================


def main() -> None:
    """Main entry point for the APGI Psychological States Visualization System."""
    logger.info("\n🧠 APGI Psychological States Visualization System")
    logger.info("=" * 70)

    # Check dependencies
    required = {
        "Tkinter": TKINTER_AVAILABLE,
        "Plotly": PLOTLY_AVAILABLE,
        "Pandas": PANDAS_AVAILABLE,
    }

    missing = [name for name, available in required.items() if not available]

    if missing:
        logger.error(f"Missing required packages: {', '.join(missing)}")
        logger.info("Install with: pip install plotly pandas")
        return

    logger.info("All dependencies available")
    logger.info(f"   • Tkinter: {TKINTER_AVAILABLE}")
    logger.info(f"   • Plotly: {PLOTLY_AVAILABLE}")
    logger.info(f"   • Pandas: {PANDAS_AVAILABLE}")
    logger.info(f"   • TkinterWeb: {TKINTERWEB_AVAILABLE}")

    logger.info(
        f"Loaded {len(PSYCHOLOGICAL_STATES)} psychological states across {len(set(STATE_CATEGORIES.values()))} categories"
    )

    try:
        logger.info("Launching interactive GUI...")
        gui = APGIVisualizerGUI()
        gui.run()
    except Exception as e:
        logger.error(f"Error launching GUI: {e}")
        logger.error(format_exc())


if __name__ == "__main__":
    main()
