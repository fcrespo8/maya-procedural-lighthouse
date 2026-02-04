import time
import importlib

import maya.cmds as cmds

import backend.cliff
import backend.tower


def _reload_modules() -> None:
    """Recarga módulos del proyecto para iterar sin reiniciar Maya."""
    importlib.reload(backend.cliff)
    importlib.reload(backend.tower)


def run() -> None:
    _reload_modules()

    # Importar DESPUÉS del reload para asegurar clases actualizadas
    from backend.cliff import CliffBuilder, CliffParams
    from backend.tower import TowerBuilder, TowerParams

    t0 = time.time()

    CliffBuilder.cleanup()
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
    cliff = CliffBuilder(cliff_params).build()

    tower_params = TowerParams(
        quality="draft",
        height=28.0,
        radius_base=4.0,
        radius_top=3.0,
    )
    tower = TowerBuilder(tower_params).build()

    cmds.select([cliff, tower], r=True)
    t2 = time.time()

    print("[--- MAYA-LIGHTHOUSE] Done")
    print(f"  Cleanup: {(t1 - t0):.3f}s")
    print(f"  Build:   {(t2 - t1):.3f}s")
    print(f"  Total:   {(t2 - t0):.3f}s")
