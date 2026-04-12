from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class SubsystemProtocol(Protocol):
    def step(self, dt: float, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Perform one simulation step."""
        ...

    def reset(self) -> None:
        """Reset the subsystem to initial state."""
        ...

    def get_state(self) -> Dict[str, Any]:
        """Retrieve the current state dictionary."""
        ...
