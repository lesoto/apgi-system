"""Neural network substrate at multiple scales."""

from apgi_system.neural.macroscale.large_scale_networks import (
    DefaultModeNetwork,
    FrontoparietalNetwork,
    SalienceNetwork,
)
from apgi_system.neural.mesoscale.neural_columns import NeuralColumn
from apgi_system.neural.microscale.spiking_network import SpikingNeuralNetwork
from apgi_system.neural.oscillations import OscillationEngine

__all__ = [
    "OscillationEngine",
    "SpikingNeuralNetwork",
    "NeuralColumn",
    "FrontoparietalNetwork",
    "SalienceNetwork",
    "DefaultModeNetwork",
]
