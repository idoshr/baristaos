"""Where saved shots and machine settings live.

The folder used to be ``~/.smart_espresso``. The first start that finds
only that folder moves it to ``~/.baristaos``. If the move fails, the
old folder stays in use so the shot history is not lost. When both
folders already exist, the new one is used and the old one is left alone.
"""

import logging
import os
import shutil
from typing import Dict, Optional

LEGACY_DIR = ".smart_espresso"
STATE_DIR = ".baristaos"

log = logging.getLogger(__name__)
_chosen: Dict[str, str] = {}


def state_dir(home: Optional[str] = None) -> str:
    """Return the state folder, moving the legacy folder once when needed."""
    root = os.path.abspath(home) if home is not None else os.path.expanduser("~")
    cached = _chosen.get(root)
    if cached is not None:
        return cached
    new = os.path.join(root, STATE_DIR)
    old = os.path.join(root, LEGACY_DIR)
    if os.path.isdir(new):
        chosen = new
    elif os.path.isdir(old):
        try:
            shutil.move(old, new)
        except OSError:
            chosen = old
        else:
            log.info("Moved saved state from %s to %s", old, new)
            chosen = new
    else:
        chosen = new
    _chosen[root] = chosen
    return chosen


def expand_state_path(path: str) -> str:
    """Expand ``~`` and follow a fallback to the legacy state folder."""
    if not path:
        return path
    expanded = os.path.expanduser(path)
    home = os.path.expanduser("~")
    new_root = os.path.join(home, STATE_DIR)
    if expanded == new_root or expanded.startswith(new_root + os.sep):
        actual = state_dir()
        return actual + expanded[len(new_root) :]
    return expanded
