#!/usr/bin/env python3
"""
Test script for Iowa Gambling Task implementation.

This script creates an APGI system instance and runs a short version of the
Iowa Gambling Task to verify the implementation works correctly.
"""

from apgi_system.system import APGISystem
from apgi_system.experiments.tasks import IowaGamblingTask


def main():
    """Run Iowa Gambling Task test."""
    print("=" * 80)
    print("Iowa Gambling Task - Test Run")
    print("=" * 80)
    print("\nInitializing APGI system...")

    # Create APGI system
    system = APGISystem()

    print("\nCreating Iowa Gambling Task...")
    print("Running a short version with 40 trials (10 per deck)...")

    # Create task with reduced trials for testing
    task = IowaGamblingTask(
        num_trials=40,
        initial_balance=2000,
        deck_stimulus_strength=1.5,
        outcome_stimulus_strength=2.0,
        interoceptive_gain=1.0,
        deck_selection_strategy="balanced",
    )

    print("\nRunning task...")
    # Run all trials
    results = task.run_all_trials(system)

    # Print results
    task.print_results(results)

    # Save results
    task.save_results("test_iowa_gambling_results.json")

    print("\n" + "=" * 80)
    print("Test completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
