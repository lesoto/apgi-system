"""Metabolic energy budget tracking."""

import numpy as np
from typing import Dict, Any


class MetabolicBudget:
    """Tracks ATP consumption and metabolic constraints."""

    def __init__(self, config: Dict[str, Any]):
        thermo_config = config.get('thermodynamic', {})
        self.total_budget = thermo_config.get('total_energy_budget', 100.0)
        self.baseline_rate = thermo_config.get('baseline_consumption', 20.0)
        self.ignition_cost = thermo_config.get('ignition_cost', 7.5)
        self.task_overhead = thermo_config.get('task_overhead', 27.5)
        self.recovery_rate = thermo_config.get('recovery_rate', 5.0)
        self.depletion_threshold = thermo_config.get('depletion_threshold', 10.0)

        self.current_reserves = self.total_budget
        self.total_consumed = 0.0

    def update(self, ignition_occurred: bool, task_active: bool, dt: float = 1.0) -> Dict[str, Any]:
        # Consumption
        consumption = self.baseline_rate * dt / 1000.0

        if ignition_occurred:
            consumption += self.ignition_cost

        if task_active:
            consumption += self.task_overhead * dt / 1000.0

        self.current_reserves -= consumption
        self.total_consumed += consumption

        # Recovery
        self.current_reserves += self.recovery_rate * dt / 1000.0
        self.current_reserves = min(self.current_reserves, self.total_budget)

        depleted = self.current_reserves < self.depletion_threshold

        return {
            'reserves': float(self.current_reserves),
            'consumed': float(self.total_consumed),
            'depleted': depleted,
            'reserve_fraction': float(self.current_reserves / self.total_budget)
        }

    def reset(self):
        self.current_reserves = self.total_budget
        self.total_consumed = 0.0
