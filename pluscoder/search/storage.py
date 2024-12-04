"""Storage implementation for search index persistence."""

# ruff: noqa: S301
import pickle  # nosec B403
from pathlib import Path
from typing import Any
from typing import Optional


class IndexStorage:
    """Handles persistence of search index and related data.

    Note: This storage is for internal use only and should not be used
    with untrusted data as pickle can be unsafe in such cases.
    """

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, name: str) -> Path:
        """Get full path for a storage item."""
        return self.storage_dir / f"{name}.pickle"

    def save(self, name: str, data: Any) -> None:
        """Save data to storage."""
        with open(self._get_path(name), "wb") as f:
            pickle.dump(data, f)

    def load(self, name: str) -> Optional[Any]:
        """Load data from storage.

        Note: Only use with trusted data as pickle can be unsafe
        with untrusted input.
        """
        path = self._get_path(name)
        if not path.exists():
            return None
        with open(path, "rb") as f:
            # Internal trusted data only
            return pickle.load(f)

    def delete(self, name: str) -> None:
        """Delete data from storage."""
        path = self._get_path(name)
        if path.exists():
            path.unlink()

    def exists(self, name: str) -> bool:
        """Check if data exists in storage."""
        return self._get_path(name).exists()
