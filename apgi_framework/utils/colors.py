# apgi_framework/utils/colors.py

# APGI Visual Identity System - Color Palette
APGI_BLUE = "#00B4FF"  # Threshold (Bt)
APGI_RED = "#FF3366"  # Interoceptive Precision (PI)
APGI_YELLOW = "#FFCC00"  # Prediction Error (|epsilon|)
APGI_GREEN = "#00CC99"  # Neuromodulator Tone
APGI_PURPLE = "#9966FF"  # Global Workspace / Ignition
APGI_DARK = "#2C3E50"  # Background / Structure / Header
APGI_BG = "#1A2634"  # Main Application Background
APGI_TEXT = "#E8F4FD"  # Primary Text Color

# Parameter -> Color map
PARAM_COLORS = {
    "threshold": APGI_BLUE,
    "precision": APGI_RED,
    "prediction_error": APGI_YELLOW,
    "neuromodulator": APGI_GREEN,
    "ignition": APGI_PURPLE,
}

# Matplotlib rcParams for APGI Visual Identity
APGI_RCPARAMS = {
    "figure.facecolor": APGI_BG,
    "axes.facecolor": APGI_BG,
    "axes.edgecolor": APGI_DARK,
    "axes.labelcolor": APGI_TEXT,
    "xtick.color": APGI_TEXT,
    "ytick.color": APGI_TEXT,
    "text.color": APGI_TEXT,
    "grid.color": APGI_DARK,
    "grid.alpha": 0.4,
    "mathtext.fontset": "cm",
}
