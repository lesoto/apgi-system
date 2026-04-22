#!/usr/bin/env python3
"""
Basic APGI System Simulation Example.

Runs a configurable simulation with sinusoidal sensory input and generates
visualizations of ignition events, free energy, precision, and metabolic reserves.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apgi_simulation.platform_utils import get_resource_path  # noqa: E402
from apgi_simulation.system import APGISystem  # noqa: E402
from utils.datetime_utils import format_duration_ms, get_elapsed_ms, utc_now  # noqa: E402


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run basic APGI system simulation",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=1000,
        help="Simulation duration in milliseconds",
    )
    parser.add_argument(
        "--input-size",
        type=int,
        default=256,
        help="Size of sensory input vector",
    )
    parser.add_argument(
        "--noise-level",
        type=float,
        default=0.2,
        help="Noise level for sensory input",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="apgi_simulation_results.png",
        help="Output plot filename",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Skip plotting (headless mode)",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show interactive plot window",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: 100ms simulation, no plots",
    )

    return parser.parse_args()


def sensory_input_factory(
    input_size: int = 256, noise_level: float = 0.2
) -> Callable[[float], np.ndarray[Any, np.dtype[Any]]]:
    """
    Create sensory input function with sinusoidal pattern and noise.

    Args:
        input_size: Size of the input vector
        noise_level: Standard deviation of Gaussian noise

    Returns:
        Function that generates sensory input for given time
    """

    def sensory_input(t: float) -> np.ndarray[Any, np.dtype[Any]]:
        """
        Generate sensory input at time t.

        Args:
            t: Time in milliseconds

        Returns:
            Sensory input vector
        """
        # Sinusoidal input with noise
        base = np.sin(2 * np.pi * t / 1000.0) * np.ones(input_size)
        noise = np.random.randn(input_size) * noise_level
        return base + noise

    return sensory_input


def run_simulation(
    duration_ms: int = 10000,
    input_size: int = 256,
    noise_level: float = 0.2,
    config_path: Optional[str] = None,
) -> Tuple[Dict[str, Any], APGISystem, float]:
    """
    Run APGI system simulation.

    Args:
        duration_ms: Simulation duration in milliseconds
        input_size: Size of sensory input vector
        noise_level: Noise level for input
        config_path: Path to configuration file

    Returns:
        Tuple of (results, system, elapsed_time_ms)
    """
    print("Initializing APGI System...")

    if config_path is None:
        config_path = str(get_resource_path("apgi_simulation/resources/config/default.yaml"))

    system = APGISystem(config_path=config_path)

    print(f"Running {format_duration_ms(duration_ms)} simulation...")

    # Create sensory input function
    sensory_input = sensory_input_factory(input_size, noise_level)

    # Record start time
    start_time = utc_now()

    # Run simulation
    results = system.run(duration_ms=duration_ms, extero_input_fn=sensory_input)

    # Calculate elapsed time
    elapsed_ms = get_elapsed_ms(start_time)

    print(f"\nSimulation Complete! ({format_duration_ms(elapsed_ms)})")
    print(f"Total steps: {results['total_steps']}")
    print(f"Ignition events: {results['ignition_count']}")
    print(f"Ignition rate: {results['ignition_count'] / results['total_steps']:.3f}")

    # Get final state summary
    summary = system.get_state_summary()
    print("\nFinal State:")
    print(f"  Allostatic load: {float(np.mean(summary['allostatic_load'])):.3f}")
    print(f"  Metabolic reserves: {float(np.mean(summary['metabolic_reserves'])):.1f}")
    print(f"  Somatic markers: {summary['somatic_markers']['num_markers']}")

    return results, system, elapsed_ms


def plot_results(
    history: Dict[str, Any], output_file: str = "apgi_simulation_results.png", show: bool = False
) -> None:
    """
    Plot simulation results.

    Args:
        history: Simulation history dictionary
        output_file: Output filename for saved plot
        show: Whether to show interactive plot window
    """
    try:
        plt.figure(figsize=(12, 8))

        # Ignition events
        plt.subplot(4, 1, 1)
        plt.plot(history["time"], history["ignitions"], "r.", alpha=0.5)
        plt.ylabel("Ignition Events")
        plt.title("APGI System Simulation Results")

        # Free energy
        plt.subplot(4, 1, 2)
        plt.plot(history["time"], history["free_energy"])
        plt.ylabel("Free Energy")

        # Precision
        plt.subplot(4, 1, 3)
        plt.plot(history["time"], history["precision"])
        plt.ylabel("Extero Precision")

        # Metabolic reserves
        plt.subplot(4, 1, 4)
        plt.plot(history["time"], history["metabolic_reserves"])
        plt.ylabel("Metabolic Reserves")
        plt.xlabel("Time (ms)")

        plt.tight_layout()
        plt.savefig(output_file, dpi=150)
        print(f"\nPlot saved as '{output_file}'")

        if show:
            plt.show()
        else:
            plt.close()

    except Exception as e:
        print(f"\nWarning: Failed to generate plot: {e}")
        print("Continuing without plot generation...")


def main() -> None:
    """Run basic simulation with command-line arguments."""
    args = parse_arguments()

    # Handle quick mode
    if args.quick:
        args.duration = 100
        args.no_plot = True

    try:
        # Run simulation
        results, system, elapsed_ms = run_simulation(
            duration_ms=args.duration,
            input_size=args.input_size,
            noise_level=args.noise_level,
            config_path=args.config,
        )

        # Plot results if not disabled
        if not args.no_plot:
            plot_results(history=system.history, output_file=args.output, show=args.show)

        print("\n[OK] Simulation completed successfully!")

    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user")
        sys.exit(130)

    except ImportError as e:
        print(f"\n[FAIL] Import error: {e}")
        print("Please ensure all required dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Check for headless environment
    if "DISPLAY" not in os.environ and sys.platform != "darwin":
        matplotlib.use("Agg")

    main()
