"""Test-suite bootstrap: make ``src/`` importable without a package
install, so ``pytest tests`` works directly from the repository root.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
