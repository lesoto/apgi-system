"""
Free Energy Calculation Module

Implements variational free energy (F) and expected free energy (G)
calculations for active inference.
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any, Union
from scipy import linalg
from scipy.special import xlogy

from apgi_system.validation import InputValidator
from apgi_system.types import FloatArray, ConfigDict
from apgi_system.stability import NumericalStabilityMonitor


class FreeEnergyCalculator:
    """
    Calculates variational free energy and expected free energy.

    Implements the core free energy calculations for active inference:

    1. Variational Free Energy (F): Measures how well the current model
       explains observations. Minimizing F corresponds to perceptual inference.

       F = E_q[log q(s) - log p(o,s)]
         = Complexity - Accuracy
         ≈ Prediction Error + Divergence from Prior

    2. Expected Free Energy (G): Measures expected future surprise under
       a policy. Minimizing G corresponds to action selection.

       G = Epistemic Value + Pragmatic Value
         = Expected Information Gain + Expected Cost

    The calculator provides methods for computing both forms of free energy,
    along with their constituent components (accuracy, complexity, epistemic
    value, pragmatic value).

    Attributes
    ----------
    config : Dict[str, Any]
        Configuration dictionary
    eps : float
        Small constant for numerical stability (default: 1e-10)

    Notes
    -----
    Free energy provides a unified objective function for perception and action:
    - Perception: Minimize F by updating beliefs
    - Action: Minimize G by selecting policies

    This implements the free energy principle, which states that biological
    systems act to minimize their free energy (or equivalently, surprise).

    References
    ----------
    .. [1] Friston, K. (2010). The free-energy principle: a unified brain theory?
           Nature Reviews Neuroscience, 11(2), 127-138.
    .. [2] Friston, K., FitzGerald, T., Rigoli, F., Schwartenbeck, P., & Pezzulo, G. (2017).
           Active inference: a process theory. Neural computation, 29(1), 1-49.

    Examples
    --------
    >>> calc = FreeEnergyCalculator()
    >>> obs = np.array([1.0, 2.0, 3.0])
    >>> pred = np.array([1.1, 1.9, 3.2])
    >>> precision = np.eye(3)
    >>> post_mean = np.array([1.0, 2.0, 3.0])
    >>> post_cov = np.eye(3) * 0.1
    >>> prior_mean = np.zeros(3)
    >>> prior_cov = np.eye(3)
    >>> fe, components = calc.compute_variational_free_energy(
    ...     obs, pred, precision, post_mean, post_cov, prior_mean, prior_cov
    ... )
    >>> print(f"Free energy: {fe:.3f}")
    """

    def __init__(self, config: Optional[ConfigDict] = None) -> None:
        """
        Initialize free energy calculator.

        Parameters
        ----------
        config : Dict[str, Any], optional
            Configuration dictionary (currently unused, reserved for future extensions)

        Examples
        --------
        >>> calc = FreeEnergyCalculator()
        >>> calc = FreeEnergyCalculator(config={'numerical_tolerance': 1e-8})
        """
        self.config = config or {}
        self.eps = 1e-10  # Numerical stability
        self.stability_monitor = NumericalStabilityMonitor(config)

        # Precision bounds to prevent numerical instability
        self.precision_min = 1e-6  # Minimum precision to prevent overflow
        self.precision_max = 1e6  # Maximum precision to prevent underflow

    def compute_variational_free_energy(
        self,
        observation: FloatArray,
        prediction: FloatArray,
        precision: Union[float, FloatArray],
        posterior_mean: FloatArray,
        posterior_cov: FloatArray,
        prior_mean: FloatArray,
        prior_cov: FloatArray,
    ) -> Tuple[float, Dict[str, float]]:
        """
        Compute variational free energy F.

        Free energy decomposes into accuracy and complexity:

        F = Accuracy + Complexity

        Accuracy = 0.5 * (o - μ̂)ᵀ Π (o - μ̂)  [Prediction error term]
        Complexity = KL[q(s)||p(s)]  [Divergence from prior]

        Lower free energy indicates better model fit. The system performs
        gradient descent on F to improve its internal model.

        Parameters
        ----------
        observation : np.ndarray
            Observed sensory data vector
        prediction : np.ndarray
            Predicted observation vector
        precision : np.ndarray
            Precision matrix (inverse covariance). Can be scalar, 1D, or 2D.
        posterior_mean : np.ndarray
            Posterior belief mean (recognition density)
        posterior_cov : np.ndarray
            Posterior belief covariance matrix
        prior_mean : np.ndarray
            Prior belief mean (generative model)
        prior_cov : np.ndarray
            Prior belief covariance matrix

        Returns
        -------
        total_fe : float
            Total variational free energy
        components : Dict[str, float]
            Dictionary containing:
            - 'accuracy': Precision-weighted prediction error
            - 'complexity': KL divergence from prior
            - 'prediction_error': Raw prediction error magnitude

        Raises
        ------
        TypeError
            If inputs are not numpy arrays or numeric types
        ValueError
            If array shapes are incompatible, arrays contain NaN/Inf,
            or precision is not positive

        Notes
        -----
        The accuracy term measures how well predictions match observations,
        weighted by precision (confidence). The complexity term penalizes
        deviations from prior beliefs, implementing Occam's razor.

        Minimizing F balances fitting the data (accuracy) with staying close
        to prior beliefs (complexity), preventing overfitting.

        Examples
        --------
        >>> calc = FreeEnergyCalculator()
        >>> obs = np.array([1.0, 2.0, 3.0])
        >>> pred = np.array([1.1, 1.9, 3.2])
        >>> precision = 2.0 * np.eye(3)
        >>> post_mean = obs
        >>> post_cov = 0.1 * np.eye(3)
        >>> prior_mean = np.zeros(3)
        >>> prior_cov = np.eye(3)
        >>> fe, comp = calc.compute_variational_free_energy(
        ...     obs, pred, precision, post_mean, post_cov, prior_mean, prior_cov
        ... )
        >>> print(f"FE: {fe:.3f}, Accuracy: {comp['accuracy']:.3f}")
        """
        # Validate inputs
        InputValidator.validate_array(observation, "observation")
        InputValidator.validate_array(prediction, "prediction")

        # Validate observation and prediction have same shape
        if observation.shape != prediction.shape:
            raise ValueError(
                f"observation and prediction shapes must match: "
                f"got {observation.shape} and {prediction.shape}"
            )

        # Validate precision
        if np.isscalar(precision):
            InputValidator.validate_scalar(precision, "precision", positive=True)
        else:
            InputValidator.validate_array(precision, "precision")
            # Check precision is positive
            if np.any(precision <= 0):
                raise ValueError("precision must be positive")

        # Validate posterior and prior parameters
        InputValidator.validate_array(posterior_mean, "posterior_mean")
        InputValidator.validate_array(posterior_cov, "posterior_cov")
        InputValidator.validate_array(prior_mean, "prior_mean")
        InputValidator.validate_array(prior_cov, "prior_cov")

        # Validate posterior and prior have compatible shapes
        if posterior_mean.shape != prior_mean.shape:
            raise ValueError(
                f"posterior_mean and prior_mean shapes must match: "
                f"got {posterior_mean.shape} and {prior_mean.shape}"
            )

        # Prediction error (accuracy term)
        error = observation - prediction

        # If precision is scalar, convert to diagonal matrix
        if np.isscalar(precision):
            # Clamp precision to prevent numerical instability
            precision = np.clip(precision, self.precision_min, self.precision_max)
            precision_matrix = precision * np.eye(len(error))
        elif precision.ndim == 1:
            # Clamp vector precision
            precision = np.clip(precision, self.precision_min, self.precision_max)
            precision_matrix = np.diag(precision)
        else:
            # Clamp matrix precision (clamp diagonal elements)
            precision = precision.copy()
            np.fill_diagonal(
                precision, np.clip(np.diag(precision), self.precision_min, self.precision_max)
            )
            precision_matrix = precision

        accuracy = 0.5 * error.T @ precision_matrix @ error

        # Check stability of accuracy term
        self.stability_monitor.check_stability(accuracy, context="free_energy_accuracy_term")

        # KL divergence (complexity term)
        complexity = self._kl_divergence_gaussian(
            posterior_mean, posterior_cov, prior_mean, prior_cov
        )

        # Check stability of complexity term
        self.stability_monitor.check_stability(complexity, context="free_energy_complexity_term")

        total_fe = accuracy + complexity

        # Check stability of total free energy
        self.stability_monitor.check_stability(total_fe, context="total_free_energy")

        components = {
            "accuracy": float(accuracy),
            "complexity": float(complexity),
            "prediction_error": float(np.sqrt(error.T @ error)),
        }

        return float(total_fe), components

    def compute_expected_free_energy(
        self,
        policy: FloatArray,
        predicted_states: FloatArray,
        predicted_observations: FloatArray,
        preferences: FloatArray,
        state_uncertainty: FloatArray,
        horizon: int = 3,
    ) -> Tuple[float, Dict[str, float]]:
        """
        Compute expected free energy G for a policy.

        Expected free energy decomposes into epistemic and pragmatic values:

        G = Epistemic Value + Pragmatic Value

        Epistemic Value: Expected information gain (exploration)
        Pragmatic Value: Expected divergence from preferences (exploitation)

        Policies with lower G are preferred. This naturally balances exploration
        (seeking information) and exploitation (achieving goals).

        Parameters
        ----------
        policy : np.ndarray
            Action sequence or policy identifier
        predicted_states : np.ndarray
            Predicted future states under the policy
        predicted_observations : np.ndarray
            Predicted future observations under the policy
        preferences : np.ndarray
            Preferred observation distribution (goal states)
        state_uncertainty : np.ndarray
            Uncertainty in state predictions at each time step
        horizon : int, default=3
            Planning horizon (number of steps to look ahead)

        Returns
        -------
        total_efe : float
            Total expected free energy
        components : Dict[str, float]
            Dictionary containing:
            - 'epistemic_value': Expected information gain
            - 'pragmatic_value': Expected cost/divergence from preferences
            - 'exploration_drive': Magnitude of exploration motivation
            - 'exploitation_drive': Magnitude of exploitation motivation

        Notes
        -----
        Epistemic value is negative (more negative = more information gain):
        Epistemic = -E[H[p(s|o)] - H[p(s)]]

        Pragmatic value measures divergence from preferences:
        Pragmatic = E[KL(p(o|π) || p*(o))]

        The balance between epistemic and pragmatic values implements the
        exploration-exploitation tradeoff in active inference.

        Examples
        --------
        >>> calc = FreeEnergyCalculator()
        >>> policy = np.array([1.0])
        >>> pred_states = [np.random.randn(10) for _ in range(3)]
        >>> pred_obs = np.random.rand(3, 10)
        >>> preferences = np.ones(10) / 10
        >>> uncertainty = np.array([0.5, 0.4, 0.3])
        >>> efe, comp = calc.compute_expected_free_energy(
        ...     policy, pred_states, pred_obs, preferences, uncertainty, horizon=3
        ... )
        >>> print(f"EFE: {efe:.3f}, Epistemic: {comp['epistemic_value']:.3f}")
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
            "epistemic_value": float(epistemic_value),
            "pragmatic_value": float(pragmatic_value),
            "exploration_drive": float(-epistemic_value),
            "exploitation_drive": float(-pragmatic_value),
        }

        return float(total_efe), components

    def _kl_divergence_gaussian(
        self, mu_q: FloatArray, sigma_q: FloatArray, mu_p: FloatArray, sigma_p: FloatArray
    ) -> float:
        """
        Compute KL divergence between two Gaussian distributions.

        Calculates the Kullback-Leibler divergence from distribution p to
        distribution q, measuring how much information is lost when using q
        to approximate p.

        Parameters
        ----------
        mu_q : np.ndarray
            Mean of distribution q (recognition density)
        sigma_q : np.ndarray
            Covariance of distribution q
        mu_p : np.ndarray
            Mean of distribution p (generative model)
        sigma_p : np.ndarray
            Covariance of distribution p

        Returns
        -------
        kl_divergence : float
            KL divergence KL[q||p] ≥ 0

        Notes
        -----
        For Gaussian distributions:

        KL[q||p] = 0.5 * [log|Σ_p|/|Σ_q| - d + tr(Σ_p⁻¹Σ_q) +
                          (μ_p - μ_q)ᵀ Σ_p⁻¹ (μ_p - μ_q)]

        where d is the dimensionality.

        KL divergence is always non-negative and equals zero only when
        the distributions are identical.

        Raises
        ------
        linalg.LinAlgError
            If covariance matrices are singular (returns large value)

        Examples
        --------
        >>> calc = FreeEnergyCalculator()
        >>> mu_q = np.array([1.0, 2.0])
        >>> sigma_q = np.eye(2) * 0.5
        >>> mu_p = np.zeros(2)
        >>> sigma_p = np.eye(2)
        >>> kl = calc._kl_divergence_gaussian(mu_q, sigma_q, mu_p, sigma_p)
        >>> print(f"KL divergence: {kl:.3f}")
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
            # Use pseudoinverse for better numerical stability
            sigma_p_inv = linalg.pinv(sigma_p, rcond=1e-10)

            # Check condition number to detect near-singular matrices
            cond_num = np.linalg.cond(sigma_p)
            if cond_num > 1e12:
                # Matrix is ill-conditioned, use regularization
                sigma_p_reg = sigma_p + 1e-6 * np.eye(d)
                sigma_p_inv = linalg.pinv(sigma_p_reg, rcond=1e-10)

            log_det_ratio = np.log(linalg.det(sigma_p) + self.eps) - np.log(
                linalg.det(sigma_q) + self.eps
            )

            trace_term = np.trace(sigma_p_inv @ sigma_q)

            mean_diff = mu_p - mu_q
            mahalanobis = mean_diff.T @ sigma_p_inv @ mean_diff

            kl_div = 0.5 * (log_det_ratio - d + trace_term + mahalanobis)

            return max(0.0, float(kl_div))  # KL divergence is non-negative

        except linalg.LinAlgError as e:
            # Log the error and raise a proper exception
            raise ValueError(
                f"Matrix inversion failed in KL divergence calculation: {str(e)}. "
                f"This may indicate singular covariance matrices. "
                f"Consider adding regularization to your covariance matrices."
            )

    def compute_prediction_error(
        self,
        observation: FloatArray,
        prediction: FloatArray,
        precision: Optional[Union[float, FloatArray]] = None,
    ) -> Dict[str, float]:
        """
        Compute precision-weighted prediction error.

        Calculates multiple error metrics including raw error, precision-weighted
        error, and element-wise statistics. Useful for diagnostics and monitoring.

        Parameters
        ----------
        observation : np.ndarray
            Observed data vector
        prediction : np.ndarray
            Predicted data vector
        precision : np.ndarray, optional
            Precision weights. If None, uses uniform precision of 1.0.
            Can be scalar or vector.

        Returns
        -------
        error_metrics : Dict[str, float]
            Dictionary containing:
            - 'raw_error': L2 norm of error vector
            - 'weighted_error': Precision-weighted L2 norm
            - 'mean_absolute_error': Mean of absolute element-wise errors
            - 'max_error': Maximum absolute element-wise error
            - 'precision_weighted_elements': List of weighted element errors

        Notes
        -----
        Prediction error: ε = o - μ̂

        Precision-weighted error: ||ε||_Π = √(εᵀ Π ε)

        This provides a scalar measure of prediction failure, weighted by
        confidence (precision).

        Examples
        --------
        >>> calc = FreeEnergyCalculator()
        >>> obs = np.array([1.0, 2.0, 3.0])
        >>> pred = np.array([1.1, 1.9, 3.2])
        >>> precision = np.array([1.0, 2.0, 1.5])
        >>> errors = calc.compute_prediction_error(obs, pred, precision)
        >>> print(f"Weighted error: {errors['weighted_error']:.3f}")
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
            "raw_error": float(raw_error),
            "weighted_error": float(weighted_error),
            "mean_absolute_error": float(np.mean(element_errors)),
            "max_error": float(np.max(element_errors)),
            "precision_weighted_elements": (precision * element_errors).tolist(),
        }

    def compute_surprise(self, observation: FloatArray, generative_density: FloatArray) -> float:
        """
        Compute surprise (negative log probability).

        Surprise measures how unexpected an observation is under the current
        generative model. High surprise indicates observations that are poorly
        predicted by the model.

        Parameters
        ----------
        observation : np.ndarray
            Observed data (not directly used in current implementation)
        generative_density : np.ndarray
            Probability density p(o|m) under the generative model

        Returns
        -------
        surprise : float
            Surprise value: -log p(o|m)

        Notes
        -----
        Surprise is the negative log probability:
        S = -log p(o|m)

        Free energy provides an upper bound on surprise:
        F ≥ S

        Minimizing free energy thus minimizes an upper bound on surprise,
        implementing the free energy principle.

        Examples
        --------
        >>> calc = FreeEnergyCalculator()
        >>> obs = np.array([1.0, 2.0])
        >>> prob_density = np.array([0.8, 0.7])
        >>> surprise = calc.compute_surprise(obs, prob_density)
        >>> print(f"Surprise: {surprise:.3f}")
        """
        # Ensure probability is valid
        prob = np.clip(generative_density, self.eps, 1.0)
        surprise = -np.log(prob)
        return float(np.mean(surprise))
