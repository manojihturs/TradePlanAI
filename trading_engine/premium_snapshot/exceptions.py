"""Exceptions raised by the premium snapshot infrastructure.

Traceability notes
-------------------
Mirrors the per-package exception style already established by
``trading_engine.market_data.exceptions.MarketDataError`` and its
siblings - one base exception per package, plus specific subclasses.
"""

from __future__ import annotations


class PremiumSnapshotError(Exception):
    """Base class for every exception raised by
    :mod:`trading_engine.premium_snapshot`.

    Never raised directly - always one of the subclasses below.
    """


class SnapshotValidationError(PremiumSnapshotError):
    """Raised when a snapshot value object (:class:`~trading_engine.premium_snapshot.premium_snapshot_models.ContractSnapshot`,
    :class:`~trading_engine.premium_snapshot.premium_snapshot_models.PremiumSnapshot`,
    :class:`~trading_engine.premium_snapshot.market_recorder.TickRecord`) is
    constructed with structurally invalid data.
    """


class SnapshotCaptureError(PremiumSnapshotError):
    """Raised when the capture workflow itself is misused - e.g.
    completing a capture that was never started, or starting a second
    capture before the first one completed.
    """


class RepositoryError(PremiumSnapshotError):
    """Raised when a repository (:mod:`~trading_engine.premium_snapshot.premium_snapshot_repository`
    or the tick-record repository in
    :mod:`~trading_engine.premium_snapshot.market_recorder`) cannot
    save, load, or flush data.
    """


class RecorderError(PremiumSnapshotError):
    """Raised when :class:`~trading_engine.premium_snapshot.market_recorder.MarketRecorder`
    is used incorrectly - recording before ``start()``, starting an
    already-running recorder, or stopping one that is not running.
    """
