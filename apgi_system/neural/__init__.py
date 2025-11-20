"""Neural network substrate at multiple scales."""

from apgi_system.neural.oscillations import OscillationEngine
from apgi_system.neural.microscale.spiking_network import SpikingNeuralNetwork
from apgi_system.neural.mesoscale.neural_columns import NeuralColumn
from apgi_system.neural.macroscale.large_scale_networks import (
    FrontoparietalNetwork,
    SalienceNetwork,
    DefaultModeNetwork
)

__all__ = [
    "OscillationEngine",
    "SpikingNeuralNetwork",
    "NeuralColumn",
    "FrontoparietalNetwork",
    "SalienceNetwork",
    "DefaultModeNetwork",
]
