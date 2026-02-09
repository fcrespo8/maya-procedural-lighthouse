import time
import importlib

import maya.cmds as cmds

import backend.cliff
import backend.tower
import backend.lighthouse
import backend.config


def _reload_modules() -> None:
    importlib.reload(backend.cliff)
    importlib.reload(backend.tower)
    importlib.reload(backend.lighthouse)
    importlib.reload(backend.config)


def run() -> None:
    _reload_modules()

    from backend.cliff import CliffParams
    from backend.tower import TowerParams
    from backend.lighthouse import LighthouseBuilder, LighthouseParams, PlacementParams

    t0 = time.time()

    LighthouseBuilder.cleanup()
    t1 = time.time()

    from backend.config import get_preset
    params = get_preset("shutter", quality="draft")


    root = LighthouseBuilder(params).build()
    cmds.select(root, r=True)

    t2 = time.time()

    print("[--- MAYA-LIGHTHOUSE] Done")
    print(f"  Cleanup: {(t1 - t0):.3f}s")
    print(f"  Build:   {(t2 - t1):.3f}s")
    print(f"  Total:   {(t2 - t0):.3f}s")
