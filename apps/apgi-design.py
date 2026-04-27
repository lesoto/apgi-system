#!/usr/bin/env python3
"""
APGI Design Template & Interactive Visualization System
========================================================
A comprehensive design system for the APGI (Attention, Precision, Global workspace, Ignition)
framework with interactive parameter exploration, real-time visualization, and state tracking.

Features:
  - Visual identity system with APGI color palette
  - Interactive parameter sliders with real-time updates
  - Multi-panel visualization (radar, SDE trajectory, correlation heatmap)
  - State classification and clinical awareness
  - Session data export and audit logging
  - Responsive layout with proportional sizing
  - Accessibility-aware UI components

References:
  - Friston, K. (2010). The free-energy principle. Nat Rev Neurosci, 11, 127-138.
  - Barrett, L. F., & Simmons, W. K. (2015). Interoceptive predictions in the brain.
  - Dehaene, S., et al. (2014). Experimental and theoretical approaches to conscious processing.
"""

import csv
import json
import logging
import sys
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.figure import Figure
    from matplotlib.gridspec import GridSpec

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available. Visualization features disabled.")

import tkinter as tk
from tkinter import filedialog, messagebox

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================================================
# 1. VISUAL IDENTITY SYSTEM (apgi/colors.py & typography)
# ============================================================================
APGI_BLUE = "#00B4FF"  # Threshold (Bt)
APGI_RED = "#FF3366"  # Interoceptive Precision (PI)
APGI_YELLOW = "#FFCC00"  # Prediction Error (|epsilon|)
APGI_GREEN = "#00CC99"  # Neuromodulator Tone
APGI_PURPLE = "#9966FF"  # Global Workspace / Ignition
APGI_DARK = "#2C3E50"  # Background / Structure
APGI_BG = "#1A2634"  # Plot background
APGI_FG = "#E8F4FD"  # Light foreground
APGI_ACCENT = "#FF6633"  # Accent for alerts

# Light theme colors
APGI_LIGHT_BG = "#FFFFFF"
APGI_LIGHT_FG = "#2C3E50"
APGI_LIGHT_DARK = "#E8E8E8"

PARAM_COLORS = {
    "threshold": APGI_BLUE,
    "precision": APGI_RED,
    "prediction_error": APGI_YELLOW,
    "neuromodulator": APGI_GREEN,
    "ignition": APGI_PURPLE,
}

STATE_CATEGORY_COLORS = {
    1: APGI_PURPLE,  # Ignition / Peak
    2: APGI_BLUE,  # Heightened Awareness
    3: APGI_GREEN,  # Balanced / Regulated
    4: APGI_YELLOW,  # Caution / Transition
    5: APGI_ACCENT,  # Stress / Arousal
    6: APGI_RED,  # Anxiety / Hypervigilance
    7: "#7F8C8D",  # Dissociation
    8: "#8B0000",  # Pathological / Crisis
}

APGI_RCPARAMS = {
    "figure.facecolor": APGI_BG,
    "axes.facecolor": APGI_BG,
    "axes.edgecolor": APGI_DARK,
    "axes.labelcolor": "#E8F4FD",
    "xtick.color": "#E8F4FD",
    "ytick.color": "#E8F4FD",
    "text.color": "#E8F4FD",
    "grid.color": APGI_DARK,
    "grid.alpha": 0.4,
    "font.family": "sans-serif",
    "font.size": 10,
}

# UI Component specific colors (not Matplotlib rcParams)
APGI_UI_COLORS = {
    "session_dot.color": "#7F8C8D",
    "session_dot.active_color": APGI_GREEN,
    "warning.color": APGI_YELLOW,
    "error.color": APGI_RED,
}

# Advanced Clinical Metadata
CLINICAL_THRESHOLDS = {
    "hypervigilance": {"precision": 0.85, "error": 2.0},
    "crisis": {"signal_strength": 0.3},
    "stress": {"error": 3.0, "neuromodulator": 1.5},
}

APGI_DIVERGING_CMAP = LinearSegmentedColormap.from_list(
    "apgi_diverge", [APGI_BLUE, APGI_BG, APGI_RED], N=256
)


# Font fallback system
AVAILABLE_FONTS = {
    "sans": ["Inter", "Helvetica", "Arial", "DejaVu Sans", "sans-serif"],
    "mono": ["JetBrains Mono", "Consolas", "Monaco", "Courier New", "monospace"],
}


def get_font(font_type: str, size: int, bold: bool = False) -> Tuple[str, int, str]:
    """Get available font with fallback chain."""
    font_list = AVAILABLE_FONTS.get(font_type, ["sans-serif"])
    weight = "bold" if bold else "normal"

    for font_name in font_list:
        try:
            from tkinter import font as tkfont

            if font_name in tkfont.families():
                return (font_name, size, weight)
        except Exception:
            continue

    # Ultimate fallback
    return ("sans-serif" if font_type == "sans" else "monospace", size, weight)


def setup_apgi_fonts():
    """Initialize APGI font configuration at app startup."""
    try:
        from tkinter import font as tkfont

        tkfont.nametofont("TkDefaultFont")
        logger.info("Font system initialized successfully")
    except Exception as e:
        logger.warning(f"Font setup warning: {e}")


# ============================================================================
# 2. CORE MATHEMATICAL FUNCTIONS (apgi/core/*.py)
# ============================================================================
def calculate_threshold_crossing(
    prediction_error: float, precision_weight: float, broadcast_threshold: float
) -> Dict:
    """
    Determine whether precision-weighted prediction error exceeds
    the dynamic broadcast threshold, triggering global workspace ignition.

    APGI Parameters:
        prediction_error (epsilon): Z-score [0.0, 5.0].
            Exteroceptive and interoceptive channels standardized separately.
        precision_weight (PI): Inverse variance 1/sigma^2 [0.0, 1.0].
            CRITICAL: Must not be confused with prediction_error magnitude.
        broadcast_threshold (Bt): Dynamic ignition threshold [0.0, 10.0].
            Modulated by neuromodulator tone (beta parameter).

    Returns:
        dict with keys: 'ignition' (bool), 'signal_strength' (float),
                        'margin' (float, St - Bt)

    Mathematical basis:
        St = PI_e * |z_e| + PI_i_eff * |z_i|
        Ignition: St > Bt
        Euler-Maruyama: Xt+1 = Xt + mu*dt + sigma*sqrt(dt)*N(0,1)

    References:
        Friston, K. (2010). The free-energy principle. Nat Rev Neurosci, 11, 127-138.
        Barrett, L. F., & Simmons, W. K. (2015). Interoceptive predictions in the brain.
            Nat Rev Neurosci, 16, 419-429.
        Dehaene, S., et al. (2014). Experimental and theoretical approaches to conscious
            processing. Neuron, 70(2), 200-227.
    """
    # Validate inputs
    if not all(
        isinstance(v, (int, float))
        for v in [prediction_error, precision_weight, broadcast_threshold]
    ):
        raise ValueError("All parameters must be numeric")

    integrated_signal = precision_weight * abs(prediction_error)
    ignition = integrated_signal > broadcast_threshold
    return {
        "ignition": ignition,
        "signal_strength": integrated_signal,
        "margin": integrated_signal - broadcast_threshold,
    }


def integrate_euler_maruyama(
    st: float, mu: float = 0.1, sigma: float = 0.5, dt: float = 0.1
) -> float:
    """Single step of Euler-Maruyama SDE integration."""
    if sigma < 0:
        raise ValueError("Sigma must be non-negative")
    if dt <= 0:
        raise ValueError("dt must be positive")
    dW = np.sqrt(dt) * np.random.standard_normal()
    return float(st + mu * dt + sigma * dW)


def classify_system_state(
    signal_strength: float,
    threshold: float,
    precision: float,
    prediction_error: float,
    neuromodulator: float,
) -> Tuple[int, str, str]:
    """
    Classify the system state based on APGI parameters and clinical metadata.
    """
    st = max(0.0, min(10.0, signal_strength))
    bt = max(0.0, min(10.0, threshold))
    pi = max(0.0, min(1.0, precision))
    eps = max(0.0, min(5.0, prediction_error))
    beta = max(-3.0, min(3.0, neuromodulator))

    # Check against clinical thresholds
    if st < CLINICAL_THRESHOLDS["crisis"]["signal_strength"]:
        return 8, "Pathological / Crisis", "Critical system dysregulation"

    if (
        pi > CLINICAL_THRESHOLDS["hypervigilance"]["precision"]
        and eps > CLINICAL_THRESHOLDS["hypervigilance"]["error"]
    ):
        return 6, "Anxiety / Hypervigilance", "Pathological precision weighting"

    if (
        eps > CLINICAL_THRESHOLDS["stress"]["error"]
        and beta > CLINICAL_THRESHOLDS["stress"]["neuromodulator"]
    ):
        return 5, "Stress / Arousal", "Sympathetic somatic bias dominant"

    # Standard states
    if eps > 2.5 and pi < 0.4:
        return 7, "Dissociation", "Precision suppressed, error uncoupled"
    elif st > bt + 1.5 and pi > 0.7:
        return 2, "Heightened Awareness", f"High SNR ({st:.2f} > {bt:.1f})"
    elif st > bt and 0.3 <= eps <= 1.5:
        return 1, "Optimal / Flow", f"Smooth ignition at {st:.2f}"
    else:
        return 3, "Balanced / Regulated", "Homeostatic nominal state"


# ============================================================================
# 3. VISUALIZATION MODULES (apgi/visualization/*.py)
# ============================================================================
def plot_apgi_radar(
    ax, values: List[float], title: str = "APGI Signature", fill_alpha: float = 0.25
):
    """Plot APGI parameter radar chart."""
    RADAR_AXES = [
        ("Threshold\nSensitivity", APGI_BLUE),
        ("Interoceptive\nPrecision", APGI_RED),
        ("Prediction\nError", APGI_YELLOW),
        ("Neuromodulator\nTone", APGI_GREEN),
        ("Somatic\nBias", APGI_PURPLE),
    ]
    N = len(RADAR_AXES)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    values_plot = list(values) + [values[0]]
    ax.set_facecolor(APGI_BG)
    ax.plot(angles, values_plot, color=APGI_PURPLE, lw=2.0)
    ax.fill(angles, values_plot, color=APGI_PURPLE, alpha=fill_alpha)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([a[0] for a in RADAR_AXES], size=8, color="#E8F4FD")
    for i, (_, color) in enumerate(RADAR_AXES):
        ax.tick_params(axis="x", colors=color)
    ax.set_title(title, color="#E8F4FD", pad=20, fontsize=12)
    ax.figure.text(
        0.01,
        0.01,
        "APGI Framework — Friston 2010; Barrett 2017; Dehaene 2014",
        fontsize=6,
        color="#4A5568",
        alpha=0.7,
    )


def plot_sde_trajectory(
    ax,
    t: np.ndarray,
    S_t: np.ndarray,
    B_t: np.ndarray,
    ignition_events: Optional[List[float]] = None,
):
    """Plot SDE trajectory with threshold and ignition events."""
    ax.set_facecolor(APGI_BG)
    ax.plot(t, S_t, color=APGI_PURPLE, lw=2.0, label="St (Consciousness Signal)")
    ax.plot(t, B_t, color=APGI_BLUE, lw=1.5, ls="--", label="Bt (Threshold)")
    if ignition_events:
        for i, t_ign in enumerate(ignition_events):
            ax.axvline(
                x=t_ign,
                color=APGI_YELLOW,
                alpha=0.7,
                lw=1.0,
                ls=":",
                label="Ignition" if i == 0 else None,
            )
    ax.legend(loc="upper right", fontsize=8, facecolor=APGI_DARK, labelcolor="#E8F4FD")
    ax.set_xlabel("Time (s)", color="#E8F4FD")
    ax.set_ylabel("Signal Magnitude", color="#E8F4FD")
    ax.tick_params(colors="#E8F4FD")
    ax.figure.text(
        0.01,
        0.01,
        "SDE: Euler-Maruyama. Friston 2010; Barrett & Simmons 2015",
        fontsize=6,
        color="#4A5568",
        alpha=0.7,
    )


def plot_correlation_heatmap(ax, corr_matrix: np.ndarray):
    """Plot parameter correlation heatmap."""
    PARAM_LABELS = [
        "Bt Threshold",
        "PI Precision",
        "|eps| Pred.Error",
        "Neuromod.",
        "beta Somatic Bias",
    ]
    im = ax.imshow(corr_matrix, cmap=APGI_DIVERGING_CMAP, vmin=-1, vmax=1)
    ax.set_xticks(range(len(PARAM_LABELS)))
    ax.set_yticks(range(len(PARAM_LABELS)))
    ax.set_xticklabels(PARAM_LABELS, rotation=45, ha="right", fontsize=8, color="#E8F4FD")
    ax.set_yticklabels(PARAM_LABELS, fontsize=8, color="#E8F4FD")
    ax.figure.colorbar(im, ax=ax, label="Correlation")
    ax.figure.text(
        0.01,
        0.01,
        "Correlation matrix. Pearson r. See apgi.stats.correlate_parameters()",
        fontsize=6,
        color="#4A5568",
        alpha=0.7,
    )


# ============================================================================
# 4. PRESET CONFIGURATIONS
# ============================================================================
@dataclass
class ParameterPreset:
    """Data class for parameter presets."""

    name: str
    description: str
    threshold: float
    precision: float
    prediction_error: float
    neuromodulator: float
    category: int


PRESET_CONFIGURATIONS = {
    "Balanced": ParameterPreset(
        name="Balanced",
        description="Default resting state nominal",
        threshold=3.0,
        precision=0.5,
        prediction_error=1.5,
        neuromodulator=0.0,
        category=3,
    ),
    "Flow State": ParameterPreset(
        name="Flow State",
        description="Optimal conscious processing",
        threshold=2.5,
        precision=0.7,
        prediction_error=1.2,
        neuromodulator=0.5,
        category=1,
    ),
    "Anxiety": ParameterPreset(
        name="Anxiety",
        description="Hypersensitive precision, threshold mismatch",
        threshold=4.0,
        precision=0.9,
        prediction_error=2.0,
        neuromodulator=1.0,
        category=6,
    ),
    "Stress": ParameterPreset(
        name="Stress",
        description="Sympathetic somatic bias active",
        threshold=3.5,
        precision=0.6,
        prediction_error=3.5,
        neuromodulator=2.0,
        category=5,
    ),
    "Dissociation": ParameterPreset(
        name="Dissociation",
        description="Precision suppressed, error uncoupled",
        threshold=2.0,
        precision=0.3,
        prediction_error=3.0,
        neuromodulator=-1.0,
        category=7,
    ),
    "Heightened Awareness": ParameterPreset(
        name="Heightened Awareness",
        description="SNR elevated state",
        threshold=2.0,
        precision=0.8,
        prediction_error=1.8,
        neuromodulator=1.0,
        category=2,
    ),
}


# ============================================================================
# 5. THEME MANAGEMENT
# ============================================================================
class ThemeManager:
    """Manage application themes (dark/light)."""

    THEMES = {
        "dark": {
            "bg": APGI_BG,
            "fg": APGI_FG,
            "dark": APGI_DARK,
            "grid_alpha": 0.4,
        },
        "light": {
            "bg": APGI_LIGHT_BG,
            "fg": APGI_LIGHT_FG,
            "dark": APGI_LIGHT_DARK,
            "grid_alpha": 0.3,
        },
    }

    def __init__(self) -> None:
        self.current_theme: str = "dark"

    def get_theme(self, theme_name: Optional[str] = None) -> Dict:
        """Get theme colors."""
        theme_name = theme_name or self.current_theme
        return self.THEMES.get(theme_name, self.THEMES["dark"])

    def set_theme(self, theme_name: str):
        """Set current theme."""
        if theme_name in self.THEMES:
            self.current_theme = theme_name
            return True
        return False

    def toggle_theme(self) -> str:
        """Toggle between dark and light theme."""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        return self.current_theme


# ============================================================================
# 6. SESSION DATA MANAGEMENT
# ============================================================================
class SessionDataManager:
    """Manage session recording, export, and audit logging."""

    def __init__(self, session_dir: Optional[Path] = None):
        self.session_dir = session_dir or Path.home() / ".apgi" / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file = self.session_dir / f"session_{self.session_id}.csv"
        self.data_log: List[Dict] = []
        self.parameter_history: List[Dict] = []  # For undo functionality
        self._init_csv()
        logger.info(f"Session initialized: {self.session_id}")

    def _init_csv(self):
        """Initialize CSV file with headers."""
        headers = [
            "timestamp",
            "threshold",
            "precision",
            "prediction_error",
            "neuromodulator",
            "signal_strength",
            "ignition",
            "state_category",
            "state_name",
        ]
        try:
            with open(self.session_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
        except Exception as e:
            print(f"CSV initialization error: {e}")

    def log_frame(self, params: Dict, state_info: Tuple[int, str, str]):
        """Log a single frame of data."""
        st = params.get("precision", 0.5) * abs(params.get("prediction_error", 1.5))
        ignition = st > params.get("threshold", 3.0)

        record = {
            "timestamp": datetime.now().isoformat(),
            "threshold": params.get("threshold", 0),
            "precision": params.get("precision", 0),
            "prediction_error": params.get("prediction_error", 0),
            "neuromodulator": params.get("neuromodulator", 0),
            "signal_strength": st,
            "ignition": int(ignition),
            "state_category": state_info[0],
            "state_name": state_info[1],
        }
        self.data_log.append(record)

        # Store parameter history for undo (keep last 50 states)
        self.parameter_history.append(deepcopy(params))
        if len(self.parameter_history) > 50:
            self.parameter_history.pop(0)

        try:
            with open(self.session_file, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=record.keys())
                writer.writerow(record)
        except Exception as e:
            logger.error(f"Logging error: {e}")

    def undo_last_parameters(self) -> Optional[Dict]:
        """Undo to last parameter state."""
        if len(self.parameter_history) > 1:
            self.parameter_history.pop()  # Remove current
            return deepcopy(self.parameter_history[-1])
        return None

    def export_json(self, filepath: Optional[Path] = None) -> Optional[Path]:
        """Export session data as JSON."""
        if filepath is None:
            filepath = self.session_dir / f"session_{self.session_id}.json"

        try:
            with open(filepath, "w") as f:
                json.dump(
                    {
                        "session_id": self.session_id,
                        "created": datetime.now().isoformat(),
                        "frame_count": len(self.data_log),
                        "data": self.data_log,
                    },
                    f,
                    indent=2,
                )
            return filepath
        except Exception as e:
            logger.error(f"JSON export error: {e}")
            return None

    def import_session(self, filepath: Path) -> bool:
        """Import session data from a JSON file."""
        try:
            with open(filepath, "r") as f:
                content = json.load(f)
                if "data" in content:
                    self.data_log = content["data"]
                    # Reset parameter history to last imported state
                    if self.data_log:
                        last_frame = self.data_log[-1]
                        self.parameter_history = [
                            {
                                "threshold": last_frame["threshold"],
                                "precision": last_frame["precision"],
                                "prediction_error": last_frame["prediction_error"],
                                "neuromodulator": last_frame["neuromodulator"],
                            }
                        ]
                    logger.info(f"Imported session from {filepath}")
                    return True
        except Exception as e:
            logger.error(f"Import error: {e}")
        return False

    def get_statistics(self) -> Dict:
        """Compute session statistics."""
        if not self.data_log:
            return {}

        thresholds = [d["threshold"] for d in self.data_log]
        precisions = [d["precision"] for d in self.data_log]
        errors = [d["prediction_error"] for d in self.data_log]
        signals = [d["signal_strength"] for d in self.data_log]
        ignitions = [d["ignition"] for d in self.data_log]

        return {
            "frame_count": len(self.data_log),
            "duration_s": len(self.data_log) * 0.1,  # 10Hz sampling
            "threshold_mean": float(np.mean(thresholds)),
            "threshold_std": float(np.std(thresholds)),
            "precision_mean": float(np.mean(precisions)),
            "precision_std": float(np.std(precisions)),
            "error_mean": float(np.mean(errors)),
            "error_std": float(np.std(errors)),
            "signal_mean": float(np.mean(signals)),
            "signal_std": float(np.std(signals)),
            "ignition_count": int(sum(ignitions)),
            "ignition_rate": (float(sum(ignitions) / len(ignitions)) if ignitions else 0.0),
        }


class APGIParameterSlider(tk.Frame):
    def __init__(
        self,
        parent,
        param_name,
        label,
        symbol,
        min_val,
        max_val,
        default,
        step=0.01,
        citation="",
        theme_manager: Optional[ThemeManager] = None,
    ):
        super().__init__(parent)
        self.param_name = param_name
        self.label_text = label
        self.step = step
        self.citation = citation
        self.value_callback = None
        self.color = PARAM_COLORS.get(param_name, "#E8F4FD")
        self.theme_manager = theme_manager or ThemeManager()
        self._build_ui(label, symbol, min_val, max_val, default)

    def _build_ui(self, label, symbol, lo, hi, default):
        theme = self.theme_manager.get_theme()
        self.configure(bg=theme["bg"])

        # Get fonts
        sans_font = get_font("sans", 10)
        mono_font = get_font("mono", 10)

        # Label with symbol
        lbl = tk.Label(
            self,
            text=f"{symbol}  {label}",
            fg=self.color,
            bg=theme["bg"],
            font=sans_font,
        )
        lbl.grid(row=0, column=0, sticky="w", padx=2, pady=2)

        # Value variable
        self.value_var = tk.DoubleVar(value=default)

        # Scale (slider)
        self.scale = tk.Scale(
            self,
            from_=lo,
            to=hi,
            resolution=self.step,
            orient=tk.HORIZONTAL,
            variable=self.value_var,
            bg=theme["bg"],
            fg=theme["fg"],
            highlightthickness=0,
            troughcolor=theme["dark"],
            command=self._on_value_change,
        )
        self.scale.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        # Readout label
        self.readout = tk.Label(
            self,
            text=f"{default:.3f}",
            fg=self.color,
            bg=theme["bg"],
            font=mono_font,
        )
        self.readout.grid(row=0, column=2, padx=2, pady=2)

        # Configure grid weights
        self.columnconfigure(1, weight=1)

    def _on_value_change(self, value):
        val = float(value)
        self.readout.config(text=f"{val:.3f}")
        if self.value_callback:
            self.value_callback(self.param_name, val)

    def set_value_callback(self, callback):
        """Set callback for value changes: callback(name, value)"""
        self.value_callback = callback

    def set_value(self, v):
        self.value_var.set(v)
        self.readout.config(text=f"{v:.3f}")

    def get_value(self):
        return self.value_var.get()


class APGIStateBadge(tk.Frame):
    """Display current system state with color-coded category."""

    STATE_CATEGORY_COLORS = STATE_CATEGORY_COLORS

    def __init__(
        self,
        parent,
        state_name="Balanced / Regulated",
        category=3,
        param_config="System nominal",
        theme_manager: Optional[ThemeManager] = None,
    ):
        super().__init__(parent)
        self.state_name = state_name
        self.category = category
        self.param_config = param_config
        self.theme_manager = theme_manager or ThemeManager()
        theme = self.theme_manager.get_theme()
        self.configure(bg=theme["bg"])
        self._build_badge(state_name, category, param_config)

    def _show_clinical_flag(self):
        flag = tk.Label(
            self,
            text="⚠ This system configuration is outside normative ranges. "
            "This is a parameter description, not a clinical diagnosis. "
            "If distress persists, consult a qualified mental health professional.",
            fg="#FFCC00",
            bg="#2C1810",
            font=get_font("sans", 8),
            wraplength=300,
            justify=tk.LEFT,
            relief=tk.SOLID,
            borderwidth=1,
        )
        flag.pack(fill=tk.X, pady=(0, 5))

    def _build_badge(self, state_name, category, param_config):
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()

        if category == 8:
            self._show_clinical_flag()

        color = self.STATE_CATEGORY_COLORS.get(category, "#E8F4FD")
        theme = self.theme_manager.get_theme()

        inner_frame = tk.Frame(self, bg=theme["bg"])
        inner_frame.pack(fill=tk.X, pady=5)

        # State badge label
        lbl = tk.Label(
            inner_frame,
            text=f"  {state_name}  ",
            fg="white",
            bg=color,
            font=get_font("sans", 10, bold=True),
            relief=tk.FLAT,
            padx=8,
            pady=2,
        )
        lbl.pack(side=tk.TOP)

        # Config label
        config_lbl = tk.Label(
            inner_frame,
            text=param_config,
            fg=theme["fg"],
            bg=theme["bg"],
            font=get_font("mono", 9),
        )
        config_lbl.pack(side=tk.TOP, pady=(5, 0))

    def update_badge(self, state_name, category, param_config):
        self._build_badge(state_name, category, param_config)


class APGIHeaderWidget(tk.Frame):
    def __init__(self, parent, app_name, theme_manager: Optional[ThemeManager] = None):
        super().__init__(parent)
        self.app_name = app_name
        self.theme_manager = theme_manager or ThemeManager()
        theme = self.theme_manager.get_theme()
        self.configure(bg=theme["dark"], height=50)
        self.pack_propagate(False)
        self._build_header()

    def _build_header(self):
        theme = self.theme_manager.get_theme()
        mono_font = get_font("mono", 9)
        sans_font = get_font("sans", 12)
        sans_bold = get_font("sans", 16, bold=True)
        mono_eq = get_font("mono", 11)

        # Use grid layout for better control
        self.columnconfigure(0, weight=0)  # Wordmark
        self.columnconfigure(1, weight=0)  # Separator
        self.columnconfigure(2, weight=1)  # Spacer
        self.columnconfigure(3, weight=0)  # Equation
        self.columnconfigure(4, weight=0)  # Badges
        self.columnconfigure(5, weight=0)  # Session dot

        # APGI Logo
        apgi_logo = tk.Label(self, text="APGI", fg=APGI_BLUE, bg=theme["dark"], font=sans_bold)
        apgi_logo.grid(row=0, column=0, padx=(12, 0), pady=6)

        # Subtitle
        sep = tk.Label(
            self,
            text=f"|  {self.app_name}",
            fg=theme["fg"],
            bg=theme["dark"],
            font=sans_font,
        )
        sep.grid(row=0, column=1, padx=(5, 0), pady=6)

        # Equation label
        self.equation_lbl = tk.Label(
            self,
            text="Π × |ε| = ?  > Bt",
            fg=APGI_GREEN,
            bg=theme["dark"],
            font=mono_eq,
        )
        self.equation_lbl.grid(row=0, column=3, padx=(20, 20), pady=6, sticky="e")

        # Badges frame
        badges_frame = tk.Frame(self, bg=theme["dark"])
        badges_frame.grid(row=0, column=4, padx=(0, 10), pady=6)

        self.b1 = tk.Label(
            badges_frame,
            text="Bt: 0.00",
            fg=APGI_BLUE,
            bg=theme["dark"],
            font=mono_font,
            padx=4,
            pady=2,
        )
        self.b1.pack(side=tk.LEFT, padx=2)

        self.b2 = tk.Label(
            badges_frame,
            text="PI: 0.00",
            fg=APGI_RED,
            bg=theme["dark"],
            font=mono_font,
            padx=4,
            pady=2,
        )
        self.b2.pack(side=tk.LEFT, padx=2)

        self.b3 = tk.Label(
            badges_frame,
            text="|ε|: 0.00",
            fg=APGI_YELLOW,
            bg=theme["dark"],
            font=mono_font,
            padx=4,
            pady=2,
        )
        self.b3.pack(side=tk.LEFT, padx=2)

        self.b4 = tk.Label(
            badges_frame,
            text="β: 0.00",
            fg=APGI_GREEN,
            bg=theme["dark"],
            font=mono_font,
            padx=4,
            pady=2,
        )
        self.b4.pack(side=tk.LEFT, padx=2)

        # Session dot
        self.session_dot = tk.Label(
            self, text="●", fg="#7F8C8D", bg=theme["dark"], font=get_font("sans", 14)
        )
        self.session_dot.grid(row=0, column=5, padx=(0, 12), pady=6)


class APGICanvas:
    def __init__(
        self,
        parent,
        width=9,
        height=7,
        dpi=110,
        theme_manager: Optional[ThemeManager] = None,
    ):
        if not MATPLOTLIB_AVAILABLE:
            raise RuntimeError("Matplotlib is required for canvas visualization")

        self.theme_manager = theme_manager or ThemeManager()
        theme = self.theme_manager.get_theme()

        # Update rcparams with theme
        rcparams = APGI_RCPARAMS.copy()
        rcparams["figure.facecolor"] = theme["bg"]
        rcparams["axes.facecolor"] = theme["bg"]
        rcparams["axes.edgecolor"] = theme["dark"]
        rcparams["grid.alpha"] = theme["grid_alpha"]
        plt.rcParams.update(rcparams)

        self.fig = Figure(
            figsize=(width, height),
            dpi=dpi,
            facecolor=theme["bg"],
            constrained_layout=True,
        )
        self.gs = GridSpec(2, 2, figure=self.fig, hspace=0.4, wspace=0.35)

        self.ax_radar = self.fig.add_subplot(self.gs[0, 0], projection="polar")
        self.ax_traj = self.fig.add_subplot(self.gs[0, 1])
        self.ax_heat = self.fig.add_subplot(self.gs[1, :])

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.configure(bg=theme["bg"])

        # Initial dummy data render
        self.update_plot(
            {
                "bt": 3.0,
                "pi": 0.5,
                "eps": 1.5,
                "beta": 0.0,
                "t": np.linspace(0, 10, 100),
            }
        )

    def export_to_png(self, filepath: Path):
        """Export current plot to PNG file."""
        try:
            self.fig.savefig(
                filepath,
                dpi=150,
                bbox_inches="tight",
                facecolor=self.fig.get_facecolor(),
            )
            logger.info(f"Plot exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export plot: {e}")
            return False

    def update_plot(self, data: dict, history: Optional[List[Dict]] = None):
        if history:
            self.history = history

        self.ax_radar.cla()
        self.ax_traj.cla()
        self.ax_heat.cla()

        # Radar Plot
        radar_vals = [
            max(0.0, min(1.0, 1.0 - data["bt"] / 10.0)),
            data["pi"],
            max(0.0, min(1.0, data["eps"] / 5.0)),
            max(0.0, min(1.0, (data["beta"] + 3.0) / 6.0)),
            max(0.0, min(1.0, (data["beta"] + 3.0) / 6.0)),
        ]
        plot_apgi_radar(self.ax_radar, radar_vals)

        # SDE Trajectory
        t = data["t"]
        B_t = np.full_like(t, data["bt"])
        S_t = np.zeros_like(t)
        S_t[0] = data["pi"] * abs(data["eps"]) * 0.1
        for i in range(1, len(t)):
            S_t[i] = integrate_euler_maruyama(S_t[i - 1], mu=0.05, sigma=0.2, dt=0.1)
        ign_idx = np.where(S_t > B_t)[0]
        ign_events = [t[i] for i in ign_idx] if len(ign_idx) > 0 else None
        plot_sde_trajectory(self.ax_traj, t, S_t, B_t, ignition_events=ign_events)

        # Correlation Heatmap
        corr_mat = self._calculate_correlation_matrix(data)
        plot_correlation_heatmap(self.ax_heat, corr_mat)

        # Draw canvas (constrained_layout handles spacing)
        self.canvas.draw()

    def _calculate_correlation_matrix(self, data: dict) -> np.ndarray:
        """Calculate real correlation matrix from parameter history if available."""
        if hasattr(self, "history") and len(self.history) > 5:
            # Use real history
            bt = np.array([h["threshold"] for h in self.history])
            pi = np.array([h["precision"] for h in self.history])
            eps = np.array([h["prediction_error"] for h in self.history])
            beta = np.array([h["neuromodulator"] for h in self.history])
            st = np.array(
                [h.get("signal_strength", pi[i] * abs(eps[i])) for i, h in enumerate(self.history)]
            )

            # Ensure enough samples
            if len(bt) < 100:
                # Pad with small noise to stabilize correlation
                n_pad = 100 - len(bt)
                bt = np.append(bt, [bt[-1] + np.random.normal(0, 0.01) for _ in range(n_pad)])
                pi = np.append(pi, [pi[-1] + np.random.normal(0, 0.01) for _ in range(n_pad)])
                eps = np.append(eps, [eps[-1] + np.random.normal(0, 0.01) for _ in range(n_pad)])
                beta = np.append(beta, [beta[-1] + np.random.normal(0, 0.01) for _ in range(n_pad)])
                st = np.append(st, [st[-1] + np.random.normal(0, 0.01) for _ in range(n_pad)])
        else:
            # Initial dummy simulation
            bt = np.array([data["bt"] + np.random.normal(0, 0.1) for _ in range(100)])
            pi = np.array([data["pi"] + np.random.normal(0, 0.05) for _ in range(100)])
            eps = np.array([data["eps"] + np.random.normal(0, 0.2) for _ in range(100)])
            beta = np.array([data["beta"] + np.random.normal(0, 0.1) for _ in range(100)])
            st = pi * np.abs(eps)

        params = np.column_stack([bt, pi, eps, beta, st])
        # Add epsilon to prevent constant values causing NaNs in correlation
        params += np.random.normal(0, 1e-6, params.shape)
        return np.corrcoef(params.T)

        self.fig.text(
            0.01,
            0.01,
            "APGI Framework — Friston 2010; Barrett 2017; Dehaene 2014",
            fontsize=6,
            color="#4A5568",
            alpha=0.7,
            transform=self.fig.transFigure,
        )
        self.canvas.draw()


class APGIControlPanel(tk.Frame):
    def __init__(
        self,
        parent,
        session_manager: Optional[SessionDataManager] = None,
        theme_manager: Optional[ThemeManager] = None,
        canvas_widget: Optional[APGICanvas] = None,
    ):
        super().__init__(parent)
        self.theme_manager = theme_manager or ThemeManager()
        theme = self.theme_manager.get_theme()
        self.configure(bg=theme["bg"], padx=10, pady=10)
        self.params = {
            "threshold": 3.0,
            "precision": 0.5,
            "prediction_error": 1.5,
            "neuromodulator": 0.0,
        }
        self.update_callback = None
        self.session_manager = session_manager
        self.canvas_widget = canvas_widget
        self.current_state = (
            3,
            "Balanced / Regulated",
            "Default resting state nominal",
        )
        self.animation_paused = False
        self._build_controls()

    def _build_controls(self):
        theme = self.theme_manager.get_theme()
        sans_font = get_font("sans", 9)
        sans_bold = get_font("sans", 15, bold=True)

        # Title
        sec_lbl = tk.Label(
            self,
            text="PARAMETER EXPLORER",
            fg=theme["fg"],
            bg=theme["bg"],
            font=sans_bold,
        )
        sec_lbl.pack(anchor="w", pady=(0, 10))

        # Preset dropdown
        preset_frame = tk.Frame(self, bg=theme["bg"])
        preset_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            preset_frame,
            text="Presets:",
            fg=theme["fg"],
            bg=theme["bg"],
            font=sans_font,
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.preset_var = tk.StringVar(value="Balanced")
        preset_menu = tk.OptionMenu(
            preset_frame,
            self.preset_var,
            *PRESET_CONFIGURATIONS.keys(),
            command=self._apply_preset,
        )
        preset_menu.configure(bg=theme["dark"], fg=theme["fg"], font=sans_font)
        preset_menu.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Sliders
        self.sliders = {
            "threshold": APGIParameterSlider(
                self,
                "threshold",
                "Threshold Sensitivity",
                "Bt",
                0.0,
                10.0,
                3.0,
                0.1,
                "Dehaene et al. 2014, Eq. 1",
                self.theme_manager,
            ),
            "precision": APGIParameterSlider(
                self,
                "precision",
                "Interoceptive Precision",
                "Π",
                0.0,
                1.0,
                0.5,
                0.01,
                "Friston 2010, Eq. 7",
                self.theme_manager,
            ),
            "prediction_error": APGIParameterSlider(
                self,
                "prediction_error",
                "Prediction Error Mag.",
                "|ε|",
                0.0,
                5.0,
                1.5,
                0.1,
                "Barrett & Simmons 2015, Eq. 2",
                self.theme_manager,
            ),
            "neuromodulator": APGIParameterSlider(
                self,
                "neuromodulator",
                "Neuromodulator Tone",
                "β",
                -3.0,
                3.0,
                0.0,
                0.1,
                "Friston et al. 2012, Eq. 4",
                self.theme_manager,
            ),
        }

        for k, slider in self.sliders.items():
            slider.set_value_callback(self._on_slider_change)
            slider.pack(fill=tk.X, pady=5)

        # State Output
        self.state_badge = APGIStateBadge(self, theme_manager=self.theme_manager)
        self.state_badge.pack(fill=tk.X, pady=10)

        # Button frame
        btn_frame = tk.Frame(self, bg=theme["bg"])
        btn_frame.pack(fill=tk.X, pady=5)

        # Button style configuration - high contrast for visibility on dark bg
        btn_style = {
            "bg": APGI_LIGHT_BG,  # White/light background for contrast
            "fg": APGI_LIGHT_FG,  # Dark text for readability
            "font": sans_font,
            "activebackground": APGI_BLUE,
            "activeforeground": "white",
            "relief": tk.RAISED,
            "borderwidth": 2,
            "padx": 8,
            "pady": 4,
            "cursor": "hand2",
        }

        # Import Session
        import_btn = tk.Button(btn_frame, text="Import", command=self._import_data, **btn_style)
        import_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # Export Session
        export_btn = tk.Button(btn_frame, text="Export", command=self._export_data, **btn_style)
        export_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # Statistics
        stats_btn = tk.Button(btn_frame, text="Stats", command=self._show_statistics, **btn_style)
        stats_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # Pause/Resume
        self.pause_btn = tk.Button(btn_frame, text="Pause", command=self._toggle_pause, **btn_style)
        self.pause_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # Reset
        reset_btn = tk.Button(btn_frame, text="Reset", command=self._reset_params, **btn_style)
        reset_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # Second button row
        btn_frame2 = tk.Frame(self, bg=theme["bg"])
        btn_frame2.pack(fill=tk.X, pady=5)

        # Export PNG
        png_btn = tk.Button(btn_frame2, text="PNG Export", command=self._export_png, **btn_style)
        png_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # Undo
        undo_btn = tk.Button(btn_frame2, text="Undo", command=self._undo_last, **btn_style)
        undo_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # Theme Toggle
        theme_btn = tk.Button(btn_frame2, text="Theme", command=self._toggle_theme, **btn_style)
        theme_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # Help
        help_btn = tk.Button(btn_frame2, text="Help", command=self._show_help, **btn_style)
        help_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

    def _on_slider_change(self, name, value):
        self.params[name] = value
        if self.update_callback:
            self.update_callback(self.params.copy())
        self._update_state()

    def _update_state(self):
        """Update state classification using the new classify_system_state function."""
        bt = self.params["threshold"]
        pi = self.params["precision"]
        eps = self.params["prediction_error"]
        beta = self.params["neuromodulator"]
        st = pi * abs(eps)

        # Use the new classification function
        self.current_state = classify_system_state(st, bt, pi, eps, beta)
        cat, name, cfg = self.current_state
        self.state_badge.update_badge(name, cat, cfg)

        # Log to session if available
        if self.session_manager and not self.animation_paused:
            self.session_manager.log_frame(self.params, self.current_state)

    def _apply_preset(self, preset_name):
        """Apply a preset configuration."""
        preset = PRESET_CONFIGURATIONS.get(preset_name)
        if preset:
            self.params["threshold"] = preset.threshold
            self.params["precision"] = preset.precision
            self.params["prediction_error"] = preset.prediction_error
            self.params["neuromodulator"] = preset.neuromodulator

            # Update sliders
            self.sliders["threshold"].set_value(preset.threshold)
            self.sliders["precision"].set_value(preset.precision)
            self.sliders["prediction_error"].set_value(preset.prediction_error)
            self.sliders["neuromodulator"].set_value(preset.neuromodulator)

            self._update_state()
            if self.update_callback:
                self.update_callback(self.params.copy())
            logger.info(f"Applied preset: {preset_name}")

    def _toggle_pause(self):
        """Toggle animation pause/resume."""
        self.animation_paused = not self.animation_paused
        self.pause_btn.config(text="Resume" if self.animation_paused else "Pause")
        logger.info(f"Animation {'paused' if self.animation_paused else 'resumed'}")

    def _export_png(self):
        """Export current plot to PNG."""
        if not self.canvas_widget:
            messagebox.showwarning("Export", "No canvas available.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
        )
        if filepath:
            if self.canvas_widget.export_to_png(Path(filepath)):
                messagebox.showinfo("Export", f"Plot exported to:\n{filepath}")
            else:
                messagebox.showerror("Export", "Failed to export plot.")

    def _undo_last(self):
        """Undo to last parameter state."""
        if not self.session_manager:
            return

        last_params = self.session_manager.undo_last_parameters()
        if last_params:
            self.params = last_params.copy()
            self.sliders["threshold"].set_value(last_params["threshold"])
            self.sliders["precision"].set_value(last_params["precision"])
            self.sliders["prediction_error"].set_value(last_params["prediction_error"])
            self.sliders["neuromodulator"].set_value(last_params["neuromodulator"])
            self._update_state()
            if self.update_callback:
                self.update_callback(self.params.copy())
            logger.info("Undid last parameter change")
        else:
            messagebox.showinfo("Undo", "No previous state to undo.")

    def _toggle_theme(self):
        """Toggle between dark and light theme."""
        new_theme = self.theme_manager.toggle_theme()
        logger.info(f"Theme switched to: {new_theme}")
        messagebox.showinfo(
            "Theme",
            f"Theme changed to {new_theme}.\nRestart application to apply changes fully.",
        )

    def _show_help(self):
        """Show help dialog."""
        help_text = """APGI Design Template Help
========================

Keyboard Shortcuts:
  Ctrl+E - Export session data
  Ctrl+S - Show statistics
  Ctrl+R - Reset parameters
  Ctrl+P - Toggle pause/resume
  Ctrl+T - Toggle theme
  Ctrl+Z - Undo last change
  F1 - Show this help

Presets:
  Use the preset dropdown to quickly load predefined
  parameter configurations for different states.

Parameters:
  Bt (Threshold): Broadcast threshold for ignition
  PI (Precision): Interoceptive precision weight
  |ε| (Error): Prediction error magnitude
  β (Neuromodulator): Somatic bias parameter

For more information, see the APGI documentation.
"""
        messagebox.showinfo("Help", help_text)

    def _import_data(self):
        """Import session data from file."""
        if not self.session_manager:
            return

        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filepath:
            if self.session_manager.import_session(Path(filepath)):
                messagebox.showinfo("Import", "Session data imported successfully.")
                # Update to the last state of the imported data
                if self.session_manager.parameter_history:
                    last_params = self.session_manager.parameter_history[-1]
                    self.params = last_params.copy()
                    for name, value in self.params.items():
                        if name in self.sliders:
                            self.sliders[name].set_value(value)
                    self._update_state()
                    if self.update_callback:
                        self.update_callback(self.params.copy())
            else:
                messagebox.showerror("Import", "Failed to import session data.")

    def _export_data(self):
        """Export session data to file."""
        if not self.session_manager:
            messagebox.showwarning("Export", "No session data available.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("All files", "*.*"),
            ],
        )
        if filepath:
            result = None
            if filepath.endswith(".json"):
                result = self.session_manager.export_json(Path(filepath))
            else:
                result = Path(filepath)
                # Copy CSV file
                import shutil

                shutil.copy(self.session_manager.session_file, result)

            if result:
                messagebox.showinfo("Export", f"Session data exported to:\n{result}")
            else:
                messagebox.showerror("Export", "Failed to export session data.")

    def _show_statistics(self):
        """Display session statistics."""
        if not self.session_manager:
            messagebox.showwarning("Statistics", "No session data available.")
            return

        stats = self.session_manager.get_statistics()
        if not stats:
            messagebox.showinfo("Statistics", "No data collected yet.")
            return

        msg = f"""Session Statistics:
        
Frames: {stats['frame_count']}
Duration: {stats['duration_s']:.1f}s

Threshold:
  Mean: {stats['threshold_mean']:.2f}
  Std: {stats['threshold_std']:.2f}

Precision:
  Mean: {stats['precision_mean']:.2f}
  Std: {stats['precision_std']:.2f}

Prediction Error:
  Mean: {stats['error_mean']:.2f}
  Std: {stats['error_std']:.2f}

Signal Strength:
  Mean: {stats['signal_mean']:.2f}
  Std: {stats['signal_std']:.2f}

Ignition Events: {stats['ignition_count']}
Ignition Rate: {stats['ignition_rate']:.1%}
"""
        messagebox.showinfo("Session Statistics", msg)

    def _reset_params(self):
        """Reset all parameters to defaults."""
        defaults = {
            "threshold": 3.0,
            "precision": 0.5,
            "prediction_error": 1.5,
            "neuromodulator": 0.0,
        }
        for name, value in defaults.items():
            self.sliders[name].set_value(value)
            self.params[name] = value
        self._update_state()

    def set_update_callback(self, callback):
        self.update_callback = callback


# ============================================================================
# 5. APPLICATION BOOTSTRAP & MAIN WINDOW (apgi/gui/layout.py)
# ============================================================================
class APGIMainWindow:
    """Main application window with integrated session management."""

    def __init__(self, root, app_name: str = "Neuroscape / Architect"):
        self.root = root
        self.root.title(f"APGI {app_name}")
        self.root.geometry("1100x750")
        self.root.minsize(1100, 750)

        # Initialize theme manager
        self.theme_manager = ThemeManager()
        theme = self.theme_manager.get_theme()
        self.root.configure(bg=theme["dark"])

        # Initialize session management
        self.session_manager = SessionDataManager()

        self.header = None
        self.canvas_widget = None
        self.control_panel = None
        self.session_time = 0.0
        self.active = True

        self._build_header(app_name)
        self._build_body()
        self._setup_keyboard_shortcuts()
        self._setup_timers()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _build_header(self, app_name):
        self.header = APGIHeaderWidget(self.root, app_name, self.theme_manager)
        self.header.pack(fill=tk.X)

    def _build_body(self):
        theme = self.theme_manager.get_theme()

        # Main content frame with two columns (splitter replacement)
        body_frame = tk.Frame(self.root, bg=theme["dark"])
        body_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Configure grid weights for proportional sizing (65/35 split)
        body_frame.columnconfigure(0, weight=65)
        body_frame.columnconfigure(1, weight=35)
        body_frame.rowconfigure(0, weight=1)

        # Canvas (left side)
        canvas_frame = tk.Frame(body_frame, bg=theme["bg"])
        canvas_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)

        self.canvas_widget = APGICanvas(
            canvas_frame, width=9, height=7, dpi=100, theme_manager=self.theme_manager
        )
        self.canvas_widget.canvas_widget.grid(row=0, column=0, sticky="nsew")

        # Control panel (right side) with session manager
        self.control_panel = APGIControlPanel(
            body_frame,
            session_manager=self.session_manager,
            theme_manager=self.theme_manager,
            canvas_widget=self.canvas_widget,
        )
        self.control_panel.grid(row=0, column=1, sticky="nsew")
        self.control_panel.set_update_callback(self._sync_live_ui)

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts."""
        self.root.bind("<Control-e>", lambda e: self.control_panel._export_data())
        self.root.bind("<Control-E>", lambda e: self.control_panel._export_data())
        self.root.bind("<Control-s>", lambda e: self.control_panel._show_statistics())
        self.root.bind("<Control-S>", lambda e: self.control_panel._show_statistics())
        self.root.bind("<Control-r>", lambda e: self.control_panel._reset_params())
        self.root.bind("<Control-R>", lambda e: self.control_panel._reset_params())
        self.root.bind("<Control-p>", lambda e: self.control_panel._toggle_pause())
        self.root.bind("<Control-P>", lambda e: self.control_panel._toggle_pause())
        self.root.bind("<Control-t>", lambda e: self.control_panel._toggle_theme())
        self.root.bind("<Control-T>", lambda e: self.control_panel._toggle_theme())
        self.root.bind("<Control-z>", lambda e: self.control_panel._undo_last())
        self.root.bind("<Control-Z>", lambda e: self.control_panel._undo_last())
        self.root.bind("<F1>", lambda e: self.control_panel._show_help())
        logger.info("Keyboard shortcuts configured")

    def _setup_timers(self):
        # Use tkinter's after method for 10Hz live update (100ms)
        self._animate_data()

    def _sync_live_ui(self, params):
        bt = params.get("threshold", 3.0)
        pi = params.get("precision", 0.5)
        eps = params.get("prediction_error", 1.5)
        beta = params.get("neuromodulator", 0.0)
        st = pi * abs(eps)
        ign = "✓ IGNITION" if st > bt else "○ WAITING"

        # Update equation label
        self.header.equation_lbl.config(text=f"Π × |ε| = {st:.2f}  {ign}  > Bt ({bt:.1f})")
        color = APGI_PURPLE if st > bt else APGI_GREEN
        self.header.equation_lbl.config(fg=color)

        # Update badges
        self.header.b1.config(text=f"Bt: {bt:.1f}", fg=APGI_BLUE)
        self.header.b2.config(text=f"PI: {pi:.2f}", fg=APGI_RED)
        self.header.b3.config(text=f"|ε|: {eps:.1f}", fg=APGI_YELLOW)
        self.header.b4.config(text=f"β: {beta:.1f}", fg=APGI_GREEN)

        # Update session dot
        self.header.session_dot.config(fg=APGI_GREEN)

    def _animate_data(self):
        if not self.active or self.control_panel.animation_paused:
            return
        self.session_time += 0.1

        # For visual smoothness, we just push current params + tiny noise to plot
        # Map internal param names to update_plot expected keys
        p = {
            "bt": self.control_panel.params["threshold"],
            "pi": self.control_panel.params["precision"],
            "eps": self.control_panel.params["prediction_error"],
            "beta": self.control_panel.params["neuromodulator"],
            "t": np.linspace(max(0, self.session_time - 10), self.session_time, 100),
        }

        # Use real data log for history if available
        history = self.session_manager.data_log if self.session_manager else None
        self.canvas_widget.update_plot(p, history=history)

        # Schedule next update (10Hz = 100ms)
        self.root.after(100, self._animate_data)

    def _on_closing(self):
        """Handle window closing with session cleanup."""
        self.active = False
        if self.session_manager and self.session_manager.data_log:
            response = messagebox.askyesno(
                "Save Session",
                f"Save session data? ({len(self.session_manager.data_log)} frames recorded)",
            )
            if response:
                try:
                    json_path = self.session_manager.export_json()
                    messagebox.showinfo("Session Saved", f"Session saved to:\n{json_path}")
                except Exception as e:
                    messagebox.showerror("Save Error", f"Failed to save session:\n{e}")
        self.root.destroy()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
def main():
    """Application entry point with error handling."""
    try:
        plt.rcParams.update(APGI_RCPARAMS)  # Apply once at startup

        root = tk.Tk()
        setup_apgi_fonts()  # Must be called after root window exists
        window = APGIMainWindow(root, "Neuroscape / Architect")
        root.protocol("WM_DELETE_WINDOW", window._on_closing)
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
