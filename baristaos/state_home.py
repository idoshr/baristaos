"""Where saved shots and machine settings live.

The folder used to be ``~/.smart_espresso``. The first start that finds
only that folder moves it to ``~/.baristaos``. An empty ``~/.baristaos``
does not count as a choice: the old folder is moved, or kept if the move
fails. A destination this attempt created is removed on failure, and the
old folder is never deleted. When the new folder already holds files,
it is used and the old one is left alone.
"""

import logging
import os
import shutil
from typing import Dict, Optional

LEGACY_DIR = ".smart_espresso"
STATE_DIR = ".baristaos"

log = logging.getLogger(__name__)
_chosen: Dict[str, str] = {}


def _occupied(path: str) -> bool:
    """True when ``path`` is a directory that already holds something."""
    try:
        with os.scandir(path) as scan:
            return next(scan, None) is not None
    except FileNotFoundError:
        return False


def _discard_created(path: str, existed: bool) -> None:
    """Drop a destination this attempt created. Never touch the old folder."""
    if not os.path.lexists(path):
        if existed:
            os.mkdir(path)
        return
    if not existed:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        return
    if os.path.isdir(path):
        with os.scandir(path) as scan:
            for entry in scan:
                if entry.is_dir(follow_symlinks=False):
                    shutil.rmtree(entry.path)
                else:
                    os.remove(entry.path)
        return
    os.remove(path)
    os.mkdir(path)


def state_dir(home: Optional[str] = None) -> str:
    """Return the state folder, moving the legacy folder once when needed."""
    root = os.path.abspath(home) if home is not None else os.path.expanduser("~")
    cached = _chosen.get(root)
    if cached is not None:
        return cached
    new = os.path.join(root, STATE_DIR)
    old = os.path.join(root, LEGACY_DIR)
    existed = os.path.isdir(new)
    if _occupied(new):
        chosen = new
    elif os.path.isdir(old):
        if existed:
            os.rmdir(new)
        try:
            shutil.move(old, new)
        except OSError:
            _discard_created(new, existed)
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
