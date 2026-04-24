"""
Tests for ML classification module coverage.
"""

import numpy as np
import pandas as pd
import pytest

from apgi_framework.analysis.ml_classification import (
    ConsciousnessClassifier,
    ClassificationResult,
    BiomarkerClassifierEnsemble,
    create_biomarker_features,
    feature_selection,
    SKLEARN_AVAILABLE,
    PYTORCH_AVAILABLE,
)


@pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not available")
class TestMLClassification:
    """Test suite for ML classification tools."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        X = np.random.randn(100, 10)
        y = (X[:, 0] + X[:, 1] > 0).astype(int)
        feature_names = [f"feat_{i}" for i in range(10)]
        return X, y, feature_names

    def test_classifier_initialization(self):
        """Test classifier initialization with different algorithms."""
        algorithms = [
            "random_forest",
            "svm",
            "gradient_boosting",
            "logistic_regression",
            "mlp",
        ]
        for alg in algorithms:
            clf = ConsciousnessClassifier(algorithm=alg)
            assert clf.algorithm == alg
            assert clf.model is not None

    def test_classifier_invalid_algorithm(self):
        """Test classifier with invalid algorithm."""
        with pytest.raises(ValueError, match="Unknown algorithm"):
            ConsciousnessClassifier(algorithm="invalid_alg")

    def test_classifier_fit_predict(self, sample_data):
        """Test fitting and predicting with a classifier."""
        X, y, feature_names = sample_data
        clf = ConsciousnessClassifier(algorithm="random_forest")
        clf.fit(X, y, feature_names)

        predictions = clf.predict(X)
        assert len(predictions) == len(y)
        assert np.all(np.isin(predictions, [0, 1]))

        probabilities = clf.predict_proba(X)
        assert probabilities.shape == (len(y), 2)

    def test_classifier_evaluate(self, sample_data):
        """Test classifier evaluation."""
        X, y, feature_names = sample_data
        clf = ConsciousnessClassifier(algorithm="random_forest")
        clf.fit(X, y, feature_names)

        result = clf.evaluate(X, y, cv_folds=2)
        assert isinstance(result, ClassificationResult)
        assert 0 <= result.accuracy <= 1
        assert result.confusion_matrix.shape == (2, 2)
        assert result.feature_importance is not None
        assert len(result.cross_val_scores) == 2

    def test_ensemble_classifier(self, sample_data):
        """Test ensemble classifier."""
        X, y, feature_names = sample_data
        ensemble = BiomarkerClassifierEnsemble(algorithms=["random_forest", "logistic_regression"])
        ensemble.fit(X, y, feature_names)

        predictions = ensemble.predict(X)
        assert len(predictions) == len(y)

        probabilities = ensemble.predict_proba(X)
        assert probabilities.shape == (len(y), 2)

        results = ensemble.evaluate_ensemble(X, y)
        assert "ensemble" in results
        assert "random_forest" in results
        assert "logistic_regression" in results

    def test_feature_selection(self, sample_data):
        """Test feature selection."""
        X, y, feature_names = sample_data
        X_df = pd.DataFrame(X, columns=feature_names)

        X_selected, selected_names = feature_selection(X_df, y, k=5)
        assert X_selected.shape[1] == 5
        assert len(selected_names) == 5
        assert all(name in feature_names for name in selected_names)

    def test_create_biomarker_features(self):
        """Test biomarker feature extraction."""
        sfreq = 1000.0
        n_channels = 2
        n_samples = 2000
        eeg_data = np.random.randn(n_channels, n_samples)

        features_df = create_biomarker_features(eeg_data, sfreq)
        assert isinstance(features_df, pd.DataFrame)
        assert not features_df.empty
        # Check for some expected features
        assert "Ch1_mean" in features_df.columns
        assert "Ch2_alpha_power" in features_df.columns
        assert "mean_correlation" in features_df.columns


@pytest.mark.skipif(not PYTORCH_AVAILABLE, reason="PyTorch not available")
class TestDeepLearning:
    """Test suite for deep learning features."""

    def test_deep_nn_classifier(self):
        """Test deep neural network classifier."""
        np.random.seed(42)
        X = np.random.randn(50, 5)
        y = (X[:, 0] > 0).astype(int)

        clf = ConsciousnessClassifier(algorithm="deep_nn")
        clf.fit(X, y)

        predictions = clf.predict(X)
        assert len(predictions) == len(y)

        probabilities = clf.predict_proba(X)
        assert probabilities.shape == (len(y), 2)
