"""Test-suite bootstrap: make ``src/`` and ``tools/`` importable
without a package install, so ``pytest tests`` works directly from the
repository root.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
_TOOLS = _ROOT / "tools"
for _path in (_SRC, _TOOLS):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))
