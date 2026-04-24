from abc import ABC, abstractmethod
from typing import Any, Dict

import pandas as pd

from apgi_framework.logging.standardized_logging import get_logger

logger = get_logger("experiment")


class BaseExperiment(ABC):
    """Base class for all experimental paradigms."""

    def __init__(self, n_participants: int = 20) -> None:
        self.n_participants = n_participants
        self.data = pd.DataFrame()
        self.participant_data: Dict[int, Any] = {}

    @abstractmethod
    def setup(self, **kwargs: Any) -> None:
        """Set up the experimental parameters."""

    @abstractmethod
    def run_trial(self, participant_id: int, trial_params: Dict[str, Any]) -> None:
        """Run a single trial of the experiment."""

    @abstractmethod
    def run_block(self, participant_id: int, block_params: Dict[str, Any]) -> None:
        """Run a block of trials."""

    def run_experiment(self, **kwargs: Any) -> pd.DataFrame:
        """Run the full experiment for all participants."""
        self.setup(**kwargs)

        for participant in range(1, self.n_participants + 1):
            self.participant_data[participant] = self.run_participant(participant)

        return self._compile_data()

    @abstractmethod
    def run_participant(self, participant_id: int) -> Dict[str, Any]:
        """Run the experiment for a single participant."""

    def _compile_data(self) -> pd.DataFrame:
        """Compile all participant data into a single DataFrame."""
        all_data = []
        for participant, data in self.participant_data.items():
            if isinstance(data, dict) and "trials" in data:
                # Handle nested structure with 'trials' key
                all_data.extend(data["trials"])
            elif isinstance(data, list):
                all_data.extend(data)
            else:
                all_data.append(data)

        if all_data:
            self.data = pd.DataFrame(all_data)
        return self.data

    def save_data(self, filename: str) -> None:
        """Save the experiment data to a file."""
        if not self.data.empty:
            self.data.to_csv(filename, index=False)
            logger.info(f"Data saved to {filename}")
        else:
            logger.warning("No data to save.")
