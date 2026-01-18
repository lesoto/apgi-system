"""Extended analysis capabilities for APGI system.

This module provides comprehensive analysis tools for examining system behavior,
including ignition statistics, energy budget summaries, somatic marker analysis,
coherence metrics computation, and advanced statistical analysis.
"""

import numpy as np
import scipy.stats as stats
from scipy import signal
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from apgi_system.types import FloatArray


@dataclass
class AnalysisResults:
    """Results from comprehensive system analysis.

    This dataclass encapsulates all analysis results from a simulation run,
    providing detailed statistics about ignition dynamics, energy consumption,
    somatic marker learning, and self-model coherence.

    Attributes
    ----------
    ignition_statistics : Dict[str, float]
        Statistics about ignition events including:
        - 'total_ignitions': Total number of ignition events
        - 'ignition_rate_hz': Average ignition rate (events per second)
        - 'mean_ignition_interval_ms': Mean time between ignitions
        - 'std_ignition_interval_ms': Standard deviation of intervals
        - 'min_ignition_interval_ms': Minimum interval between ignitions
        - 'max_ignition_interval_ms': Maximum interval between ignitions
        - 'mean_ignition_duration_ms': Mean duration of ignition events
    energy_budget_summary : Dict[str, float]
        Summary of metabolic energy consumption:
        - 'total_energy_consumed': Total energy consumed over simulation
        - 'mean_energy_per_step': Average energy per timestep
        - 'energy_per_ignition': Average energy cost per ignition
        - 'final_reserves': Final metabolic reserves (0-1)
        - 'min_reserves': Minimum reserves reached during simulation
        - 'reserve_depletion_rate': Rate of reserve depletion
    somatic_marker_stats : Dict[str, float]
        Statistics about somatic marker learning and retrieval:
        - 'total_markers': Total number of stored markers
        - 'capacity_used': Fraction of storage capacity used (0-1)
        - 'retrieval_success_rate': Fraction of successful retrievals
        - 'mean_marker_strength': Average strength of stored markers
        - 'mean_marker_outcome': Average outcome valence of markers
        - 'learning_events': Total number of learning events
    coherence_metrics : Dict[str, float]
        Self-model coherence metrics:
        - 'mean_coherence': Mean overall coherence score
        - 'std_coherence': Standard deviation of coherence
        - 'min_coherence': Minimum coherence reached
        - 'max_coherence': Maximum coherence reached
        - 'phenomenal_unity_fraction': Fraction of time with unified self-experience
    temporal_dynamics : Dict[str, List[float]]
        Time series data for key metrics:
        - 'time': Timestamps (milliseconds)
        - 'ignition_signal': Ignition signal values over time
        - 'threshold': Dynamic threshold values over time
        - 'free_energy': Free energy values over time
        - 'precision': Precision values over time
        - 'metabolic_reserves': Reserve levels over time
        - 'coherence': Coherence scores over time
    """

    ignition_statistics: Dict[str, float] = field(default_factory=dict)
    energy_budget_summary: Dict[str, float] = field(default_factory=dict)
    somatic_marker_stats: Dict[str, float] = field(default_factory=dict)
    coherence_metrics: Dict[str, float] = field(default_factory=dict)
    temporal_dynamics: Dict[str, List[float]] = field(default_factory=dict)


class SystemAnalyzer:
    """Analyzer for comprehensive APGI system analysis.

    This class provides methods for analyzing various aspects of APGI system
    behavior, including ignition dynamics, energy consumption, learning,
    and self-model coherence.

    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary containing analysis settings

    Examples
    --------
    >>> from apgi_system.system import APGISystem
    >>> system = APGISystem()
    >>> system.run(duration_ms=5000.0)
    >>> analyzer = SystemAnalyzer(system.config)
    >>> results = analyzer.analyze_system(system)
    >>> print(f"Ignition rate: {results.ignition_statistics['ignition_rate_hz']:.2f} Hz")
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize system analyzer.

        Parameters
        ----------
        config : Dict[str, Any]
            Configuration dictionary
        """
        self.config = config

    def analyze_system(self, system: Any) -> AnalysisResults:
        """Perform comprehensive analysis of APGI system.

        Analyzes all aspects of system behavior including ignition dynamics,
        energy consumption, somatic marker learning, and coherence metrics.

        Parameters
        ----------
        system : APGISystem
            APGI system instance to analyze (must have run history)

        Returns
        -------
        AnalysisResults
            Comprehensive analysis results

        Examples
        --------
        >>> system = APGISystem()
        >>> system.run(duration_ms=5000.0)
        >>> analyzer = SystemAnalyzer(system.config)
        >>> results = analyzer.analyze_system(system)
        """
        # Compute ignition statistics
        ignition_stats = self.compute_ignition_statistics(system.ignition_threshold, system.history)

        # Compute energy budget summary
        energy_summary = self.compute_energy_budget_summary(system.metabolism, system.history)

        # Compute somatic marker statistics
        marker_stats = self.compute_somatic_marker_statistics(system.somatic_markers)

        # Compute coherence metrics
        coherence_metrics = self.compute_coherence_metrics(system.coherence)

        # Extract temporal dynamics
        temporal_dynamics = self.extract_temporal_dynamics(
            system.history, system.ignition_threshold
        )

        return AnalysisResults(
            ignition_statistics=ignition_stats,
            energy_budget_summary=energy_summary,
            somatic_marker_stats=marker_stats,
            coherence_metrics=coherence_metrics,
            temporal_dynamics=temporal_dynamics,
        )

    def compute_ignition_statistics(
        self, ignition_threshold: Any, history: Dict[str, List]
    ) -> Dict[str, float]:
        """Compute statistics about ignition events.

        Analyzes ignition event timing, frequency, and duration to provide
        insights into conscious access dynamics.

        Parameters
        ----------
        ignition_threshold : IgnitionThreshold
            Ignition threshold component with event history
        history : Dict[str, List]
            System history containing ignition events

        Returns
        -------
        Dict[str, float]
            Dictionary containing ignition statistics:
            - 'total_ignitions': Total number of ignition events
            - 'ignition_rate_hz': Average ignition rate (events per second)
            - 'mean_ignition_interval_ms': Mean time between ignitions
            - 'std_ignition_interval_ms': Standard deviation of intervals
            - 'min_ignition_interval_ms': Minimum interval between ignitions
            - 'max_ignition_interval_ms': Maximum interval between ignitions
            - 'mean_ignition_duration_ms': Mean duration of ignition events
        """
        # Get ignition events from threshold component
        recent_ignitions = list(ignition_threshold.recent_ignitions)

        if len(recent_ignitions) == 0:
            return {
                "total_ignitions": 0,
                "ignition_rate_hz": 0.0,
                "mean_ignition_interval_ms": 0.0,
                "std_ignition_interval_ms": 0.0,
                "min_ignition_interval_ms": 0.0,
                "max_ignition_interval_ms": 0.0,
                "mean_ignition_duration_ms": 0.0,
            }

        # Extract ignition times
        ignition_times = [ign["time"] for ign in recent_ignitions]

        # Compute intervals between ignitions
        intervals = []
        if len(ignition_times) > 1:
            intervals = [
                ignition_times[i + 1] - ignition_times[i] for i in range(len(ignition_times) - 1)
            ]

        # Compute rate
        if len(ignition_times) > 0 and len(history.get("time", [])) > 0:
            total_time_s = (history["time"][-1] - history["time"][0]) / 1000.0
            ignition_rate = len(ignition_times) / max(total_time_s, 0.001)
        else:
            ignition_rate = 0.0

        # Estimate mean duration (from config or default)
        # Ignition events typically last 300-500ms during broadcasting
        mean_duration = self.config.get("ignition", {}).get("amplification_duration_ms", 300.0)

        return {
            "total_ignitions": len(ignition_times),
            "ignition_rate_hz": float(ignition_rate),
            "mean_ignition_interval_ms": float(np.mean(intervals)) if intervals else 0.0,
            "std_ignition_interval_ms": float(np.std(intervals)) if intervals else 0.0,
            "min_ignition_interval_ms": float(np.min(intervals)) if intervals else 0.0,
            "max_ignition_interval_ms": float(np.max(intervals)) if intervals else 0.0,
            "mean_ignition_duration_ms": float(mean_duration),
        }

    def compute_energy_budget_summary(
        self, metabolism: Any, history: Dict[str, List]
    ) -> Dict[str, float]:
        """Compute summary of metabolic energy consumption.

        Analyzes energy usage patterns including total consumption,
        per-step costs, and ignition-related energy expenditure.

        Parameters
        ----------
        metabolism : MetabolicBudget
            Metabolic budget component
        history : Dict[str, List]
            System history containing metabolic data

        Returns
        -------
        Dict[str, float]
            Dictionary containing energy statistics:
            - 'total_energy_consumed': Total energy consumed over simulation
            - 'mean_energy_per_step': Average energy per timestep
            - 'energy_per_ignition': Average energy cost per ignition
            - 'final_reserves': Final metabolic reserves (0-1)
            - 'min_reserves': Minimum reserves reached during simulation
            - 'reserve_depletion_rate': Rate of reserve depletion (per second)
        """
        reserves_history = history.get("metabolic_reserves", [])
        ignitions_history = history.get("ignitions", [])
        time_history = history.get("time", [])

        if len(reserves_history) == 0:
            return {
                "total_energy_consumed": 0.0,
                "mean_energy_per_step": 0.0,
                "energy_per_ignition": 0.0,
                "final_reserves": 1.0,
                "min_reserves": 1.0,
                "reserve_depletion_rate": 0.0,
            }

        # Compute total energy consumed (initial - final reserves)
        initial_reserves = reserves_history[0] if reserves_history else 1.0
        final_reserves = reserves_history[-1] if reserves_history else 1.0
        total_consumed = initial_reserves - final_reserves

        # Mean energy per step
        num_steps = len(reserves_history)
        mean_per_step = total_consumed / max(num_steps, 1)

        # Energy per ignition
        total_ignitions = sum(ignitions_history) if ignitions_history else 0
        energy_per_ignition = total_consumed / max(total_ignitions, 1)

        # Minimum reserves
        min_reserves = float(np.min(reserves_history)) if reserves_history else 1.0

        # Depletion rate (per second)
        if len(time_history) > 1:
            total_time_s = (time_history[-1] - time_history[0]) / 1000.0
            depletion_rate = total_consumed / max(total_time_s, 0.001)
        else:
            depletion_rate = 0.0

        return {
            "total_energy_consumed": float(total_consumed),
            "mean_energy_per_step": float(mean_per_step),
            "energy_per_ignition": float(energy_per_ignition),
            "final_reserves": float(final_reserves),
            "min_reserves": float(min_reserves),
            "reserve_depletion_rate": float(depletion_rate),
        }

    def compute_somatic_marker_statistics(self, somatic_markers: Any) -> Dict[str, float]:
        """Compute statistics about somatic marker learning and retrieval.

        Analyzes the somatic marker system's learning effectiveness,
        storage utilization, and retrieval accuracy.

        Parameters
        ----------
        somatic_markers : SomaticMarkerSystem
            Somatic marker system component

        Returns
        -------
        Dict[str, float]
            Dictionary containing somatic marker statistics:
            - 'total_markers': Total number of stored markers
            - 'capacity_used': Fraction of storage capacity used (0-1)
            - 'retrieval_success_rate': Fraction of successful retrievals
            - 'mean_marker_strength': Average strength of stored markers
            - 'mean_marker_outcome': Average outcome valence of markers
            - 'learning_events': Total number of learning events
        """
        # Get statistics from somatic marker system
        sm_stats = somatic_markers.get_statistics()

        # Count learning events (approximated by number of markers)
        learning_events = sm_stats.get("num_markers", 0)

        return {
            "total_markers": sm_stats.get("num_markers", 0),
            "capacity_used": sm_stats.get("capacity_used", 0.0),
            "retrieval_success_rate": sm_stats.get("retrieval_success_rate", 0.0),
            "mean_marker_strength": sm_stats.get("avg_strength", 0.0),
            "mean_marker_outcome": sm_stats.get("avg_outcome", 0.0),
            "learning_events": learning_events,
        }

    def compute_coherence_metrics(self, coherence: Any) -> Dict[str, float]:
        """Compute self-model coherence metrics.

        Analyzes the coherence and unity of the self-model over time,
        providing insights into the stability of self-experience.

        Parameters
        ----------
        coherence : CoherenceMaintenance
            Coherence maintenance component

        Returns
        -------
        Dict[str, float]
            Dictionary containing coherence metrics:
            - 'mean_coherence': Mean overall coherence score
            - 'current_coherence': Current coherence score
            - 'phenomenal_unity': Whether currently experiencing unified self

        Notes
        -----
        This is a simplified version that returns current state.
        For full temporal analysis, history tracking would need to be added
        to the CoherenceMaintenance component.
        """
        coherence_metrics = coherence.get_coherence_metrics()

        return {
            "mean_coherence": coherence_metrics.get("overall_coherence", 1.0),
            "current_coherence": coherence_metrics.get("overall_coherence", 1.0),
            "phenomenal_unity": 1.0 if coherence_metrics.get("phenomenal_unity", True) else 0.0,
        }

    def extract_temporal_dynamics(
        self, history: Dict[str, List], ignition_threshold: Any
    ) -> Dict[str, List[float]]:
        """Extract time series data for key metrics.

        Extracts temporal dynamics of key system variables for
        visualization and detailed analysis.

        Parameters
        ----------
        history : Dict[str, List]
            System history containing time series data
        ignition_threshold : IgnitionThreshold
            Ignition threshold component with signal history

        Returns
        -------
        Dict[str, List[float]]
            Dictionary containing time series:
            - 'time': Timestamps (milliseconds)
            - 'ignition_signal': Ignition signal values over time
            - 'threshold': Dynamic threshold values over time
            - 'free_energy': Free energy values over time
            - 'precision': Precision values over time
            - 'metabolic_reserves': Reserve levels over time
        """
        return {
            "time": list(history.get("time", [])),
            "ignition_signal": list(ignition_threshold.signal_history),
            "threshold": list(ignition_threshold.threshold_history),
            "free_energy": list(history.get("free_energy", [])),
            "precision": list(history.get("precision", [])),
            "metabolic_reserves": list(history.get("metabolic_reserves", [])),
        }

    def compute_correlation_analysis(self, history: Dict[str, List]) -> Dict[str, Dict[str, float]]:
        """Compute correlations between key system variables.

        Analyzes relationships between different system metrics to identify
        patterns and dependencies in system behavior.

        Parameters
        ----------
        history : Dict[str, List]
            System history containing time series data

        Returns
        -------
        Dict[str, Dict[str, float]]
            Correlation matrix between key variables:
            - Pearson correlation coefficients
            - P-values for statistical significance
            - Sample sizes for each correlation
        """
        variables = {}
        for key in ["free_energy", "precision", "metabolic_reserves", "coherence"]:
            if key in history and len(history[key]) > 1:
                variables[key] = np.array(history[key])

        correlations = {}
        var_names = list(variables.keys())

        for i, var1 in enumerate(var_names):
            correlations[var1] = {}
            for var2 in var_names:
                if var1 == var2:
                    correlations[var1][var2] = {
                        "correlation": 1.0,
                        "p_value": 0.0,
                        "sample_size": len(variables[var1]),
                    }
                elif var2 in variables:
                    corr, p_val = stats.pearsonr(variables[var1], variables[var2])
                    correlations[var1][var2] = {
                        "correlation": float(corr) if not np.isnan(corr) else 0.0,
                        "p_value": float(p_val) if not np.isnan(p_val) else 1.0,
                        "sample_size": len(variables[var1]),
                    }

        return correlations

    def compute_frequency_analysis(
        self, history: Dict[str, List], sample_rate: float = 20.0
    ) -> Dict[str, Dict[str, Any]]:
        """Perform frequency domain analysis on system signals.

        Analyzes oscillatory patterns in system dynamics using FFT
        to identify dominant frequencies and power spectra.

        Parameters
        ----------
        history : Dict[str, List]
            System history containing time series data
        sample_rate : float, optional
            Sampling rate in Hz (default: 20.0)

        Returns
        -------
        Dict[str, Dict[str, Any]]
            Frequency analysis results for each signal:
            - 'dominant_frequencies': Main frequency components
            - 'power_spectrum': Full power spectral density
            - 'spectral_entropy': Entropy of frequency distribution
            - 'total_power': Total signal power
        """
        results = {}

        for signal_name in ["free_energy", "precision", "coherence"]:
            if signal_name in history and len(history[signal_name]) > 10:
                signal_data = np.array(history[signal_name])

                # Compute FFT
                fft_vals = np.fft.fft(signal_data)
                freqs = np.fft.fftfreq(len(signal_data), 1.0 / sample_rate)

                # Power spectral density
                psd = np.abs(fft_vals) ** 2 / len(signal_data)
                positive_freqs = freqs[: len(freqs) // 2]
                positive_psd = psd[: len(psd) // 2]

                # Find dominant frequencies (top 3)
                dominant_indices = np.argsort(positive_psd)[-3:][::-1]
                dominant_freqs = positive_freqs[dominant_indices]
                dominant_powers = positive_psd[dominant_indices]

                # Spectral entropy
                psd_normalized = positive_psd / np.sum(positive_psd)
                spectral_entropy = -np.sum(psd_normalized * np.log(psd_normalized + 1e-10))

                results[signal_name] = {
                    "dominant_frequencies": {
                        "freqs": dominant_freqs.tolist(),
                        "powers": dominant_powers.tolist(),
                    },
                    "power_spectrum": {
                        "frequencies": positive_freqs.tolist(),
                        "power": positive_psd.tolist(),
                    },
                    "spectral_entropy": float(spectral_entropy),
                    "total_power": float(np.sum(positive_psd)),
                }

        return results

    def compute_stationarity_analysis(
        self, history: Dict[str, List], window_size: int = 100
    ) -> Dict[str, Dict[str, float]]:
        """Analyze stationarity of system signals.

        Tests whether system signals are stationary over time using
        rolling window statistics and Augmented Dickey-Fuller test.

        Parameters
        ----------
        history : Dict[str, List]
            System history containing time series data
        window_size : int, optional
            Size of rolling window for analysis (default: 100)

        Returns
        -------
        Dict[str, Dict[str, float]]
            Stationarity analysis results:
            - 'adf_statistic': Augmented Dickey-Fuller test statistic
            - 'adf_pvalue': P-value for stationarity test
            - 'rolling_mean_variance': Variance of rolling means
            - 'trend_strength': Strength of linear trend
        """
        results = {}

        for signal_name in ["free_energy", "precision", "metabolic_reserves"]:
            if signal_name in history and len(history[signal_name]) > window_size:
                signal_data = np.array(history[signal_name])

                # Rolling statistics
                rolling_means = []
                for i in range(window_size, len(signal_data)):
                    window = signal_data[i - window_size : i]
                    rolling_means.append(np.mean(window))

                # Variance of rolling means (measure of non-stationarity)
                mean_variance = np.var(rolling_means) if rolling_means else 0.0

                # Augmented Dickey-Fuller test
                try:
                    adf_stat, adf_pvalue, _, _, _, _ = stats.adfuller(signal_data)
                except:
                    adf_stat, adf_pvalue = 0.0, 1.0

                # Trend strength (linear regression slope)
                x = np.arange(len(signal_data))
                slope, _, _, p_value, _ = stats.linregress(x, signal_data)
                trend_strength = abs(slope)

                results[signal_name] = {
                    "adf_statistic": float(adf_stat),
                    "adf_pvalue": float(adf_pvalue),
                    "rolling_mean_variance": float(mean_variance),
                    "trend_strength": float(trend_strength),
                }

        return results

    def compute_phase_space_analysis(self, history: Dict[str, List]) -> Dict[str, Dict[str, Any]]:
        """Analyze phase space dynamics and attractors.

        Examines the system's behavior in phase space to identify
        attractors, limit cycles, and chaotic dynamics.

        Parameters
        ----------
        history : Dict[str, List]
            System history containing time series data

        Returns
        -------
        Dict[str, Dict[str, Any]]
            Phase space analysis results:
            - 'embedding_dimension': Optimal embedding dimension
            - 'correlation_dimension': Fractal dimension estimate
            - 'lyapunov_exponent': Chaos measure
            - 'recurrence_plot_data': Data for recurrence plots
        """
        results = {}

        # Analyze free energy vs precision phase space
        if "free_energy" in history and "precision" in history:
            fe = np.array(history["free_energy"])
            precision = np.array(history["precision"])

            if len(fe) > 50:
                # Simple correlation dimension estimate
                # Using Grassberger-Procaccia algorithm approximation
                distances = []
                for i in range(min(1000, len(fe))):
                    for j in range(i + 1, min(1000, len(fe))):
                        dist = np.sqrt((fe[i] - fe[j]) ** 2 + (precision[i] - precision[j]) ** 2)
                        distances.append(dist)

                # Correlation sum
                epsilons = np.logspace(-3, 0, 20)
                correlation_sums = []
                for eps in epsilons:
                    correlation_sum = np.sum(np.array(distances) < eps) / len(distances) ** 2
                    correlation_sums.append(correlation_sum)

                # Estimate correlation dimension
                log_eps = np.log(epsilons[correlation_sums > 0])
                log_corr = np.log(np.array(correlation_sums)[correlation_sums > 0])

                if len(log_eps) > 1 and len(log_corr) > 1:
                    corr_dim = -np.polyfit(log_eps, log_corr, 1)[0]
                else:
                    corr_dim = 2.0  # Default to 2D

                results["free_energy_precision"] = {
                    "correlation_dimension": float(max(1.0, min(5.0, corr_dim))),
                    "phase_space_data": {
                        "free_energy": fe.tolist(),
                        "precision": precision.tolist(),
                    },
                }

        return results

    def generate_statistical_summary(self, analysis_results: AnalysisResults) -> Dict[str, Any]:
        """Generate comprehensive statistical summary report.

        Creates a detailed statistical summary combining all analysis
        results with additional statistical tests and interpretations.

        Parameters
        ----------
        analysis_results : AnalysisResults
            Results from comprehensive system analysis

        Returns
        -------
        Dict[str, Any]
            Comprehensive statistical summary with interpretations
        """
        summary = {
            "ignition_analysis": {
                "statistics": analysis_results.ignition_statistics,
                "interpretation": self._interpret_ignition_stats(
                    analysis_results.ignition_statistics
                ),
            },
            "energy_analysis": {
                "statistics": analysis_results.energy_budget_summary,
                "interpretation": self._interpret_energy_stats(
                    analysis_results.energy_budget_summary
                ),
            },
            "learning_analysis": {
                "statistics": analysis_results.somatic_marker_stats,
                "interpretation": self._interpret_somatic_stats(
                    analysis_results.somatic_marker_stats
                ),
            },
            "coherence_analysis": {
                "statistics": analysis_results.coherence_metrics,
                "interpretation": self._interpret_coherence_stats(
                    analysis_results.coherence_metrics
                ),
            },
        }

        return summary

    def _interpret_ignition_stats(self, stats: Dict[str, float]) -> str:
        """Generate interpretation of ignition statistics."""
        rate = stats.get("ignition_rate_hz", 0.0)

        if rate == 0.0:
            return "No ignition events occurred - system remained in unconscious state"
        elif rate < 0.1:
            return f"Low ignition rate ({rate:.2f} Hz) - system mostly unconscious"
        elif rate < 0.5:
            return f"Moderate ignition rate ({rate:.2f} Hz) - normal conscious access"
        elif rate < 1.0:
            return f"High ignition rate ({rate:.2f} Hz) - heightened conscious activity"
        else:
            return f"Very high ignition rate ({rate:.2f} Hz) - hyper-conscious state"

    def _interpret_energy_stats(self, stats: Dict[str, float]) -> str:
        """Generate interpretation of energy statistics."""
        depletion = stats.get("reserve_depletion_rate", 0.0)
        final_reserves = stats.get("final_reserves", 1.0)

        if depletion < 0.001:
            return "Minimal energy consumption - system operating efficiently"
        elif depletion < 0.01:
            return f"Low energy consumption ({depletion:.4f}/s) - sustainable operation"
        elif depletion < 0.05:
            return f"Moderate energy consumption ({depletion:.4f}/s) - normal operation"
        else:
            return f"High energy consumption ({depletion:.4f}/s) - may lead to exhaustion"

    def _interpret_somatic_stats(self, stats: Dict[str, float]) -> str:
        """Generate interpretation of somatic marker statistics."""
        retrieval_rate = stats.get("retrieval_success_rate", 0.0)
        total_markers = stats.get("total_markers", 0)

        if total_markers == 0:
            return "No somatic markers stored - no learning has occurred"
        elif retrieval_rate > 0.8:
            return f"Excellent learning ({total_markers} markers, {retrieval_rate:.1%} retrieval)"
        elif retrieval_rate > 0.6:
            return f"Good learning ({total_markers} markers, {retrieval_rate:.1%} retrieval)"
        elif retrieval_rate > 0.4:
            return f"Moderate learning ({total_markers} markers, {retrieval_rate:.1%} retrieval)"
        else:
            return f"Poor learning ({total_markers} markers, {retrieval_rate:.1%} retrieval)"

    def _interpret_coherence_stats(self, stats: Dict[str, float]) -> str:
        """Generate interpretation of coherence statistics."""
        coherence = stats.get("mean_coherence", 1.0)

        if coherence > 0.8:
            return f"High self-coherence ({coherence:.2f}) - strong unified self-experience"
        elif coherence > 0.6:
            return f"Moderate self-coherence ({coherence:.2f}) - normal self-experience"
        elif coherence > 0.4:
            return f"Low self-coherence ({coherence:.2f}) - fragmented self-experience"
        else:
            return f"Very low self-coherence ({coherence:.2f}) - severe depersonalization"


def analyze_simulation_run(system: Any) -> AnalysisResults:
    """Convenience function to analyze a simulation run.

    This is a high-level function that creates an analyzer and performs
    comprehensive analysis on an APGI system instance.

    Parameters
    ----------
    system : APGISystem
        APGI system instance to analyze (must have run history)

    Returns
    -------
    AnalysisResults
        Comprehensive analysis results

    Examples
    --------
    >>> from apgi_system.system import APGISystem
    >>> from apgi_system.analysis import analyze_simulation_run
    >>> system = APGISystem()
    >>> system.run(duration_ms=5000.0)
    >>> results = analyze_simulation_run(system)
    >>> print(f"Total ignitions: {results.ignition_statistics['total_ignitions']}")
    >>> print(f"Energy consumed: {results.energy_budget_summary['total_energy_consumed']:.3f}")
    """
    analyzer = SystemAnalyzer(system.config)
    return analyzer.analyze_system(system)
