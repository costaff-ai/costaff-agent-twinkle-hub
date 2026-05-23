"""pytest fixtures for the Twinkle Hub agent.

The local_io tools write to a hardcoded `/app/data/shared/costaff-agent-twinkle-hub/`
inside the container. Tests run on host, so we redirect that path to a
per-test `tmp_path` by monkeypatching the module-level constant.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def tmp_shared_root(monkeypatch, tmp_path):
    """Redirect tools.local_io.COSTAFF_SHARED_DIR_TWINKLE_HUB to tmp dir."""
    import tools.local_io as local_io  # noqa: WPS433

    new_root = tmp_path / "shared" / "costaff-agent-twinkle-hub"
    new_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(local_io, "COSTAFF_SHARED_DIR_TWINKLE_HUB", str(new_root))
    return new_root
