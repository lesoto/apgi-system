"""Neural network substrate at multiple scales."""

from apgi_simulation.neural.macroscale.large_scale_networks import (
    DefaultModeNetwork,
    FrontoparietalNetwork,
    SalienceNetwork,
)
from apgi_simulation.neural.mesoscale.neural_columns import NeuralColumn
from apgi_simulation.neural.microscale.spiking_network import SpikingNeuralNetwork
from apgi_simulation.neural.oscillations import OscillationEngine

__all__ = [
    "OscillationEngine",
    "SpikingNeuralNetwork",
    "NeuralColumn",
    "FrontoparietalNetwork",
    "SalienceNetwork",
    "DefaultModeNetwork",
]
