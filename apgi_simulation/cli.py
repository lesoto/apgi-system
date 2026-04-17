import argparse
import sys
from apgi_simulation.system import APGISystem


def main() -> None:
    parser = argparse.ArgumentParser(description="APGI Simulation CLI")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--mode", choices=["single", "batch"], default="single")
    args = parser.parse_args()

    system = APGISystem(config_path=args.config)
    if args.mode == "single":
        print("Running single trial simulation...")
        # Assuming run_single_trial exists in APGISystem
        try:
            system.run_single_trial()  # type: ignore[attr-defined]
        except AttributeError:
            print(
                "Error: run_single_trial method not found in APGISystem. Please check implementation."
            )
            sys.exit(1)
    else:
        print("Running batch simulation...")
        # Assuming run_batch exists in APGISystem
        try:
            system.run_batch()  # type: ignore[attr-defined]
        except AttributeError:
            print("Error: run_batch method not found in APGISystem. Please check implementation.")
            sys.exit(1)


if __name__ == "__main__":
    main()
