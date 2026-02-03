import time
import importlib

import maya.cmds as cmds

import backend.cliff
importlib.reload(backend.cliff)

from backend.cliff import CliffBuilder, CliffParams


def run() -> None:
    t0 = time.time()

    CliffBuilder.cleanup()
    t_cleanup = time.time()

    params = CliffParams(
        quality="draft",
        # quality="high",
        width=35.0,
        height=12.0,
        depth=35.0,
        sub_x=50,
        sub_y=25,
        sub_z=50,
        noise_amplitude=1.4,
        seed=7,
    )

    cliff = CliffBuilder(params).build()
    t_build = time.time()

    cmds.select(cliff)
    t_end = time.time()

    print("[--- MAYA-LIGHTHOUSE] Done")
    print(f"  Cleanup: {(t_cleanup - t0):.3f}s")
    print(f"  Build:   {(t_build - t_cleanup):.3f}s")
    print(f"  Select:  {(t_end - t_build):.3f}s")
    print(f"  Total:   {(t_end - t0):.3f}s")
