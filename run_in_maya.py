import time
import importlib

import maya.cmds as cmds

import backend.cliff
import backend.tower
import backend.lighthouse


def _reload_modules() -> None:
    importlib.reload(backend.cliff)
    importlib.reload(backend.tower)
    importlib.reload(backend.lighthouse)


def run() -> None:
    _reload_modules()

    from backend.cliff import CliffParams
    from backend.tower import TowerParams
    from backend.lighthouse import LighthouseBuilder, LighthouseParams, PlacementParams

    t0 = time.time()

    LighthouseBuilder.cleanup()
    t1 = time.time()

    cliff_params = CliffParams(
        quality="draft",
        width=35.0,
        height=12.0,
        depth=35.0,
        sub_x=50,
        sub_y=25,
        sub_z=50,
        noise_amplitude=1.4,
        seed=7,
    )

    tower_params = TowerParams(
        quality="draft",
        height=28.0,
        radius_base=4.0,
        radius_top=3.0,
        # tus detalles v1 quedan en TowerParams si los agregaste
    )

    params = LighthouseParams(
        cliff=cliff_params,
        tower=tower_params,
        placement=PlacementParams(top_ratio=0.08, y_offset=-0.4),
    )

    root = LighthouseBuilder(params).build()
    cmds.select(root, r=True)

    t2 = time.time()

    print("[--- MAYA-LIGHTHOUSE] Done")
    print(f"  Cleanup: {(t1 - t0):.3f}s")
    print(f"  Build:   {(t2 - t1):.3f}s")
    print(f"  Total:   {(t2 - t0):.3f}s")
