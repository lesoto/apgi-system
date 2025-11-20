"""
Free Energy Calculation Module

Implements variational free energy (F) and expected free energy (G)
calculations for active inference.
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any
from scipy import linalg
from scipy.special import xlogy


class FreeEnergyCalculator:
    """
    Calculates variational free energy and expected free energy.

    Variational Free Energy (F):
        F = E_q[log q(s) - log p(o,s)]
          = Complexity - Accuracy
          ≈ Prediction Error + Divergence from Prior

    Expected Free Energy (G):
        G = Epistemic Value + Pragmatic Value
          = Expected Information Gain + Expected Cost
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize free energy calculator.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.eps = 1e-10  # Numerical stability

    def compute_variational_free_energy(
        self,
        observation: np.ndarray,
        prediction: np.ndarray,
        precision: np.ndarray,
        posterior_mean: np.ndarray,
        posterior_cov: np.ndarray,
        prior_mean: np.ndarray,
        prior_cov: np.ndarray
    ) -> Tuple[float, Dict[str, float]]:
        """
        Compute variational free energy F.

        F = Accuracy + Complexity

        Accuracy = 0.5 * (o - μ)^T Π (o - μ)  [Prediction error term]
        Complexity = KL[q(s)||p(s)]  [Divergence from prior]

        Args:
            observation: Observed sensory data
            prediction: Predicted observation
            precision: Precision matrix (inverse variance)
            posterior_mean: Posterior belief mean
            posterior_cov: Posterior belief covariance
            prior_mean: Prior belief mean
            prior_cov: Prior belief covariance

        Returns:
            total_fe: Total free energy
            components: Dictionary with accuracy and complexity terms
        """
        # Prediction error (accuracy term)
        error = observation - prediction

        # If precision is scalar, convert to diagonal matrix
        if np.isscalar(precision):
            precision_matrix = precision * np.eye(len(error))
        elif precision.ndim == 1:
            precision_matrix = np.diag(precision)
        else:
            precision_matrix = precision

        accuracy = 0.5 * error.T @ precision_matrix @ error

        # KL divergence (complexity term)
        complexity = self._kl_divergence_gaussian(
            posterior_mean, posterior_cov,
            prior_mean, prior_cov
        )

        total_fe = accuracy + complexity

        components = {
            'accuracy': float(accuracy),
            'complexity': float(complexity),
            'prediction_error': float(np.sqrt(error.T @ error))
        }

        return float(total_fe), components

    def compute_expected_free_energy(
        self,
        policy: np.ndarray,
        predicted_states: np.ndarray,
        predicted_observations: np.ndarray,
        preferences: np.ndarray,
        state_uncertainty: np.ndarray,
        horizon: int = 3
    ) -> Tuple[float, Dict[str, float]]:
        """
        Compute expected free energy G for a policy.

        G = Epistemic Value + Pragmatic Value

        Epistemic Value: Expected information gain (exploration)
        Pragmatic Value: Expected divergence from preferred states (exploitation)

        Args:
            policy: Action sequence
            predicted_states: Predicted future states under policy
            predicted_observations: Predicted future observations
            preferences: Preferred observation distribution
            state_uncertainty: Uncertainty in state predictions
            horizon: Planning horizon

        Returns:
            total_efe: Total expected free energy
            components: Dictionary with epistemic and pragmatic values
        """
        epistemic_value = 0.0
        pragmatic_value = 0.0

        for t in range(min(horizon, len(predicted_states))):
            # Epistemic value: Expected information gain
            # Higher uncertainty -> more information gain -> more negative EFE
            epistemic_value -= np.mean(state_uncertainty[t])

            # Pragmatic value: KL divergence from preferences
            # Lower divergence from preferences -> more negative EFE
            pred_obs = predicted_observations[t]
            pred_obs = pred_obs / (np.sum(pred_obs) + self.eps)  # Normalize
            pref = preferences / (np.sum(preferences) + self.eps)

            kl_div = np.sum(xlogy(pred_obs, pred_obs / (pref + self.eps)))
            pragmatic_value += kl_div

        total_efe = epistemic_value + pragmatic_value

        components = {
            'epistemic_value': float(epistemic_value),
            'pragmatic_value': float(pragmatic_value),
            'exploration_drive': float(-epistemic_value),
            'exploitation_drive': float(-pragmatic_value)
        }

        return float(total_efe), components

    def _kl_divergence_gaussian(
        self,
        mu_q: np.ndarray,
        sigma_q: np.ndarray,
        mu_p: np.ndarray,
        sigma_p: np.ndarray
    ) -> float:
        """
        Compute KL divergence between two Gaussian distributions.

        KL[q||p] = 0.5 * [log|Σ_p|/|Σ_q| - d + tr(Σ_p^{-1}Σ_q) +
                          (μ_p - μ_q)^T Σ_p^{-1} (μ_p - μ_q)]

        Args:
            mu_q: Mean of q
            sigma_q: Covariance of q
            mu_p: Mean of p
            sigma_p: Covariance of p

        Returns:
            KL divergence
        """
        d = len(mu_q)

        # Ensure covariance matrices are 2D
        if sigma_q.ndim == 1:
            sigma_q = np.diag(sigma_q)
        if sigma_p.ndim == 1:
            sigma_p = np.diag(sigma_p)

        # Add small diagonal for numerical stability
        sigma_q = sigma_q + self.eps * np.eye(d)
        sigma_p = sigma_p + self.eps * np.eye(d)

        # Compute terms
        try:
            sigma_p_inv = linalg.inv(sigma_p)

            log_det_ratio = np.log(linalg.det(sigma_p) + self.eps) - \
                           np.log(linalg.det(sigma_q) + self.eps)

            trace_term = np.trace(sigma_p_inv @ sigma_q)

            mean_diff = mu_p - mu_q
            mahalanobis = mean_diff.T @ sigma_p_inv @ mean_diff

            kl_div = 0.5 * (log_det_ratio - d + trace_term + mahalanobis)

            return max(0.0, float(kl_div))  # KL divergence is non-negative

        except linalg.LinAlgError:
            # If matrix inversion fails, return large value
            return 1e6

    def compute_prediction_error(
        self,
        observation: np.ndarray,
        prediction: np.ndarray,
        precision: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        Compute precision-weighted prediction error.

        Args:
            observation: Observed data
            prediction: Predicted data
            precision: Precision weights (optional)

        Returns:
            Dictionary with error metrics
        """
        error = observation - prediction

        if precision is None:
            precision = np.ones_like(error)
        elif np.isscalar(precision):
            precision = precision * np.ones_like(error)

        # Raw error
        raw_error = np.linalg.norm(error)

        # Precision-weighted error
        weighted_error = np.sqrt(error.T @ np.diag(precision) @ error)

        # Element-wise errors
        element_errors = np.abs(error)

        return {
            'raw_error': float(raw_error),
            'weighted_error': float(weighted_error),
            'mean_absolute_error': float(np.mean(element_errors)),
            'max_error': float(np.max(element_errors)),
            'precision_weighted_elements': (precision * element_errors).tolist()
        }

    def compute_surprise(
        self,
        observation: np.ndarray,
        generative_density: np.ndarray
    ) -> float:
        """
        Compute surprise (negative log probability).

        Surprise = -log p(o|m)

        Args:
            observation: Observed data
            generative_density: Probability density under generative model

        Returns:
            Surprise value
        """
        # Ensure probability is valid
        prob = np.clip(generative_density, self.eps, 1.0)
        surprise = -np.log(prob)
        return float(np.mean(surprise))
