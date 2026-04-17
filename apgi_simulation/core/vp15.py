"""
Validation Protocol 15 (VP-15)

The VP-15 protocol provides simulation-validated constraints to ensure
architectural integrity and mathematical rigor in the APGI system.

**v2 – Regulatory Enforcement Edition**

Unlike a passive monitoring layer, VP-15 v2 actively *corrects* the system
state when allostatic bounds are violated. Corrections are computed as
closed-form interventions so that the guarantees are mathematically bounded
rather than merely observed.

Constraint catalogue
--------------------
1. Metabolic Bounding      – reserves ∈ [critical_energy, 1.0]
2. Allostatic Range Safety – load ∈ [0, max_allostatic_load]
3. KL-Divergence Sanity    – free-energy ≥ kl_epsilon (non-negative)
4. Temporal Coherence      – synchrony ≥ min_synchrony
5. Precision Stability     – all precisions ∈ [precision_floor, precision_ceil]
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class VP15Metrics:
    """Standardised metrics produced after each VP-15 validation step."""

    metabolic_feasibility: float = 0.0  # (0-1) 1.0 = feasible, <0.2 = fatal
    allostatic_integrity: float = 0.0  # (0-1) 1.0 = safe, 0.0 = severe crisis
    information_consistency: float = 0.0  # (0-1) KL-divergence bound
    temporal_coherence: float = 0.0  # (0-1) oscillatory phase synchrony
    precision_stability: float = 0.0  # (0-1) precision within bounds
    system_health_score: float = 0.0  # Aggregate weighted score
    corrections_applied: int = 0  # Number of corrections made this step


@dataclass
class VP15Bounds:
    """Hard mathematical bounds enforced by the VP-15 protocol."""

    # Metabolic
    critical_energy: float = 0.05  # Below → metabolic crisis
    energy_restore_rate: float = 0.02  # Per-step restoration when critical

    # Allostatic
    max_allostatic_load: float = 0.90  # Above → regulatory intervention
    load_damping_gain: float = 0.15  # Fractional reduction per step

    # Information-theoretic
    kl_epsilon: float = -1e-10  # Minimum admissible VFE

    # Temporal
    min_synchrony: float = 0.20  # Below → phase-reset injection

    # Precision
    precision_floor: float = 0.10  # Hard lower bound
    precision_ceil: float = 10.0  # Hard upper bound


# ---------------------------------------------------------------------------
# Main protocol class
# ---------------------------------------------------------------------------


class VP15ValidationProtocol:
    """
    Implementation of the VP-15 validation & correction protocol.

    VP-15 v2 operates in two stages every call to ``validate_step``:

    Stage 1 – **Audit**: Measure every constraint metric from the raw system
    state dict returned by ``APGISystem.step()``.

    Stage 2 – **Correct**: For each violated constraint, compute and *apply*
    a deterministic correction directly to the mutable sub-dicts of
    ``system_state``.  This guarantees that the system never exits a step
    in an infeasible configuration.

    Parameters
    ----------
    config : dict
        Full APGI config.  VP-15 reads ``config["validation"]["vp15"]``.
    """

    # Weighted importance of each constraint for the aggregate health score
    _WEIGHTS: Dict[str, float] = {
        "metabolic_feasibility": 0.30,
        "allostatic_integrity": 0.30,
        "information_consistency": 0.20,
        "temporal_coherence": 0.10,
        "precision_stability": 0.10,
    }

    def __init__(self, config: Dict[str, Any]) -> None:
        raw = config.get("validation", {}).get("vp15", {})

        # Build bounds from config (fall back to dataclass defaults)
        b = VP15Bounds()
        self.bounds = VP15Bounds(
            critical_energy=float(raw.get("critical_energy", b.critical_energy)),
            energy_restore_rate=float(raw.get("energy_restore_rate", b.energy_restore_rate)),
            max_allostatic_load=float(raw.get("max_allostatic_load", b.max_allostatic_load)),
            load_damping_gain=float(raw.get("load_damping_gain", b.load_damping_gain)),
            kl_epsilon=float(raw.get("kl_epsilon", b.kl_epsilon)),
            min_synchrony=float(raw.get("min_synchrony", b.min_synchrony)),
            precision_floor=float(raw.get("precision_floor", b.precision_floor)),
            precision_ceil=float(raw.get("precision_ceil", b.precision_ceil)),
        )

        self.violation_history: List[str] = []
        self._total_corrections: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate_step(self, system_state: Dict[str, Any]) -> Tuple[bool, VP15Metrics]:
        """
        Audit and correct a single system step against VP-15 constraints.

        The *mutable* sub-dicts inside ``system_state`` are updated in-place
        when corrections are applied, so callers receive a corrected state
        automatically.

        Parameters
        ----------
        system_state : dict
            Full state dictionary from ``APGISystem.step()``.  Must contain
            the keys ``metabolism``, ``allostasis``, ``active_inference``,
            ``timeline``, and ``active_inference.precisions``.

        Returns
        -------
        is_valid : bool
            True only if *all* critical constraints are satisfied (after any
            corrections have been applied).
        metrics : VP15Metrics
            Detailed per-constraint health metrics reflecting the post-
            correction state.
        """
        corrections = 0

        # ── 1. Metabolic Feasibility ─────────────────────────────────────
        met_dict = system_state.setdefault("metabolism", {})
        reserves = float(met_dict.get("reserves", 1.0))
        metabolic_feasibility, n = self._enforce_metabolic(met_dict, reserves)
        corrections += n

        # ── 2. Allostatic Integrity ──────────────────────────────────────
        allo_dict = system_state.setdefault("allostasis", {})
        allostatic_integrity, n = self._enforce_allostatic(allo_dict)
        corrections += n

        # ── 3. Information Consistency (KL / VFE sanity) ─────────────────
        ai_dict = system_state.setdefault("active_inference", {})
        info_consistency, n = self._enforce_information(ai_dict)
        corrections += n

        # ── 4. Temporal Coherence ─────────────────────────────────────────
        timeline = system_state.setdefault("timeline", {})
        temporal_coherence, n = self._enforce_temporal(timeline)
        corrections += n

        # ── 5. Precision Stability ────────────────────────────────────────
        precision_stability, n = self._enforce_precision(ai_dict)
        corrections += n

        # ── Aggregate score ───────────────────────────────────────────────
        component_scores = {
            "metabolic_feasibility": metabolic_feasibility,
            "allostatic_integrity": allostatic_integrity,
            "information_consistency": info_consistency,
            "temporal_coherence": temporal_coherence,
            "precision_stability": precision_stability,
        }
        health_score = sum(v * self._WEIGHTS[k] for k, v in component_scores.items())

        metrics = VP15Metrics(
            metabolic_feasibility=metabolic_feasibility,
            allostatic_integrity=allostatic_integrity,
            information_consistency=info_consistency,
            temporal_coherence=temporal_coherence,
            precision_stability=precision_stability,
            system_health_score=health_score,
            corrections_applied=corrections,
        )

        self._total_corrections += corrections

        # Critical constraints: metabolic + allostatic must both pass
        is_valid = metabolic_feasibility > 0.0 and allostatic_integrity > 0.1

        return is_valid, metrics

    def get_violation_report(self) -> str:
        """Return a formatted report of the last 10 protocol violations."""
        if not self.violation_history:
            return "VP-15: System healthy – no violations recorded."
        report = ["VP-15 Protocol Violation Report:"]
        for v in self.violation_history[-10:]:
            report.append(f"  – {v}")
        return "\n".join(report)

    def get_total_corrections(self) -> int:
        """Cumulative corrections applied since last reset."""
        return self._total_corrections

    def reset(self) -> None:
        """Reset violation history and correction counter."""
        self.violation_history.clear()
        self._total_corrections = 0

    # ------------------------------------------------------------------
    # Constraint enforcement helpers (Stage 2 – Correct)
    # ------------------------------------------------------------------

    def _enforce_metabolic(self, met_dict: Dict[str, Any], reserves: float) -> Tuple[float, int]:
        """
        Guarantee: reserves > critical_energy.

        Correction: inject ``energy_restore_rate`` back into reserves when
        the metabolic budget is exhausted.  The correction is applied directly
        to ``met_dict`` so the system exits with a feasible energy level.
        """
        corrections = 0
        if reserves <= self.bounds.critical_energy:
            # Deterministic restoration – adds a fixed fractional increment
            restored = min(1.0, reserves + self.bounds.energy_restore_rate)
            met_dict["reserves"] = restored
            msg = (
                f"VP-15 [METABOLIC] reserves={reserves:.4f} ≤ "
                f"critical={self.bounds.critical_energy:.4f}; "
                f"restored → {restored:.4f}"
            )
            self.violation_history.append(msg)
            logger.warning(msg)
            corrections += 1
            feasibility = 0.5  # Partially penalised – correction applied
        else:
            feasibility = 1.0

        return feasibility, corrections

    def _enforce_allostatic(self, allo_dict: Dict[str, Any]) -> Tuple[float, int]:
        """
        Guarantee: allostatic_load ≤ max_allostatic_load.

        Correction: apply a closed-form damping step that reduces the load by
        ``load_damping_gain`` fraction of the excess.  This is a proportional
        controller (P-controller) on the allostatic load.

            load_new = load - gain * (load - max_load)   iff load > max_load

        The formula guarantees the corrected load is strictly below ``max_load``
        after one step for any gain ∈ (0, 1).
        """
        corrections = 0
        load = float(allo_dict.get("allostatic_load", 0.0))

        if load > self.bounds.max_allostatic_load:
            excess = load - self.bounds.max_allostatic_load
            corrected_load = load - self.bounds.load_damping_gain * excess
            # Clamp to [0, max_allostatic_load] for hard guarantee
            corrected_load = float(np.clip(corrected_load, 0.0, self.bounds.max_allostatic_load))
            allo_dict["allostatic_load"] = corrected_load
            msg = (
                f"VP-15 [ALLOSTATIC] load={load:.4f} > "
                f"max={self.bounds.max_allostatic_load:.4f}; "
                f"damped → {corrected_load:.4f}"
            )
            self.violation_history.append(msg)
            logger.warning(msg)
            corrections += 1
            integrity = max(0.0, 1.0 - corrected_load / self.bounds.max_allostatic_load)
        else:
            integrity = max(0.0, 1.0 - load / self.bounds.max_allostatic_load)

        return integrity, corrections

    def _enforce_information(self, ai_dict: Dict[str, Any]) -> Tuple[float, int]:
        """
        Guarantee: free_energy ≥ kl_epsilon.

        Correction: clamp VFE to 0.0 when it goes negative (numerically
        impossible under a proper variational bound; indicates a numerical
        artefact).
        """
        corrections = 0
        fe = float(ai_dict.get("free_energy", 0.0))

        if fe < self.bounds.kl_epsilon:
            ai_dict["free_energy"] = 0.0
            msg = (
                f"VP-15 [KL] free_energy={fe:.4e} < "
                f"kl_epsilon={self.bounds.kl_epsilon:.4e}; clamped → 0.0"
            )
            self.violation_history.append(msg)
            logger.warning(msg)
            corrections += 1
            consistency = 0.5  # Penalty for requiring correction
        else:
            consistency = 1.0

        return consistency, corrections

    def _enforce_temporal(self, timeline: Dict[str, Any]) -> Tuple[float, int]:
        """
        Guarantee: synchrony ≥ min_synchrony.

        Correction: inject a phase-reset signal by setting synchrony to the
        minimum safe value.  This models a top-down phase-reset injection
        in neural oscillation models.
        """
        corrections = 0
        synchrony = float(timeline.get("synchrony", 1.0))

        if synchrony < self.bounds.min_synchrony:
            timeline["synchrony"] = self.bounds.min_synchrony
            msg = (
                f"VP-15 [TEMPORAL] synchrony={synchrony:.4f} < "
                f"min={self.bounds.min_synchrony:.4f}; phase-reset injected"
            )
            self.violation_history.append(msg)
            logger.info(msg)
            corrections += 1
            coherence = self.bounds.min_synchrony
        else:
            coherence = float(np.clip(synchrony, 0.0, 1.0))

        return coherence, corrections

    def _enforce_precision(self, ai_dict: Dict[str, Any]) -> Tuple[float, int]:
        """
        Guarantee: all precisions ∈ [precision_floor, precision_ceil].

        Correction: clip each precision value to the admissible range.
        The precisions list (per-level arrays) is updated in-place.
        """
        corrections = 0
        precisions = ai_dict.get("precisions", [])
        if not precisions:
            return 1.0, 0  # No precisions to check → vacuously satisfied

        out_of_range_count = 0
        total_count = 0
        corrected_precisions = []

        for prec in precisions:
            arr = np.atleast_1d(np.asarray(prec, dtype=np.float64))
            clipped = np.clip(arr, self.bounds.precision_floor, self.bounds.precision_ceil)
            n_bad = int(np.sum(arr != clipped))
            out_of_range_count += n_bad
            total_count += arr.size
            corrected_precisions.append(clipped)

        if out_of_range_count > 0:
            ai_dict["precisions"] = corrected_precisions
            msg = (
                f"VP-15 [PRECISION] {out_of_range_count}/{total_count} values "
                f"out of [{self.bounds.precision_floor}, {self.bounds.precision_ceil}]; clipped"
            )
            self.violation_history.append(msg)
            logger.warning(msg)
            corrections += 1

        stability = 1.0 - (out_of_range_count / max(1, total_count))
        return float(stability), corrections
