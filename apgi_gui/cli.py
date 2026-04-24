import argparse
import logging
import tkinter as tk
from pathlib import Path

from apgi_gui.main import APGIGui

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="APGI Simulation GUI Launcher")
    parser.add_argument("--config", help="Initial configuration file path (YAML or JSON)")
    args = parser.parse_args()

    root = tk.Tk()
    gui = APGIGui(root)

    if args.config:
        config_path = Path(args.config)
        if config_path.exists():
            logger.info(f"Loading configuration from {config_path}")
            gui._load_config_from_path(config_path)
        else:
            logger.error(f"Configuration file not found: {config_path}")

    root.mainloop()


if __name__ == "__main__":
    main()
