from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from threading import Lock


@dataclass
class FaultSnapshot:
    mode: str | None = None
    latency_ms: int = 0
    activated_at: str | None = None


class FaultController:
    """Thread-safe, process-local state used only for controlled incident drills."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._state = FaultSnapshot()

    def activate(self, mode: str, latency_ms: int = 0) -> dict[str, str | int | None]:
        with self._lock:
            self._state = FaultSnapshot(
                mode=mode,
                latency_ms=latency_ms,
                activated_at=datetime.now(UTC).isoformat(),
            )
            return asdict(self._state)

    def recover(self) -> dict[str, str | int | None]:
        with self._lock:
            previous = asdict(self._state)
            self._state = FaultSnapshot()
            return previous

    def snapshot(self) -> FaultSnapshot:
        with self._lock:
            return FaultSnapshot(**asdict(self._state))


fault_controller = FaultController()
