import argparse
import tkinter as tk
from apgi_gui.main import APGIGui


def main():
    parser = argparse.ArgumentParser(description="APGI Simulation GUI Launcher")
    parser.add_argument("--config", help="Initial configuration file path")
    args = parser.parse_args()

    root = tk.Tk()
    _ = APGIGui(root)

    if args.config:
        # Assuming there is a way to load config into the GUI
        # Based on APGIGui implementation, it has a load_config method or logic
        pass

    root.mainloop()


if __name__ == "__main__":
    main()
