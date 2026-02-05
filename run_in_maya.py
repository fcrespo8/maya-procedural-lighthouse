import time
import importlib

import maya.cmds as cmds

import backend.cliff
import backend.tower


def _reload_modules() -> None:
    """Recarga módulos del proyecto para iterar sin reiniciar Maya."""
    importlib.reload(backend.cliff)
    importlib.reload(backend.tower)

def get_cliff_top_y(transform: str, top_ratio: float = 0.08) -> float:
    """Promedio del top X% de vértices por Y para evitar picos."""
    verts = cmds.ls(f"{transform}.vtx[*]", flatten=True) or []
    if not verts:
        bbox = cmds.exactWorldBoundingBox(transform)
        return bbox[4]

    ys = [cmds.pointPosition(v, world=True)[1] for v in verts]
    ys.sort()

    top_count = max(1, int(len(ys) * top_ratio))
    top_slice = ys[-top_count:]
    return sum(top_slice) / float(len(top_slice))


def place_on_top(base_transform: str, obj_transform: str, base_top_y: float, y_offset: float = 0.0) -> None:
    """Centra en XZ y apoya obj_transform usando una altura top ya calculada."""
    base_bbox = cmds.exactWorldBoundingBox(base_transform)
    obj_bbox = cmds.exactWorldBoundingBox(obj_transform)

    base_min_x, _, base_min_z, base_max_x, _, base_max_z = base_bbox
    obj_min_y, obj_max_y = obj_bbox[1], obj_bbox[4]

    base_cx = (base_min_x + base_max_x) * 0.5
    base_cz = (base_min_z + base_max_z) * 0.5

    obj_height = obj_max_y - obj_min_y
    target_y = base_top_y + (obj_height * 0.5) + y_offset

    cmds.xform(obj_transform, ws=True, t=(base_cx, target_y, base_cz))


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
    cliff_top_y = get_cliff_top_y(cliff, top_ratio=0.08)
    place_on_top(cliff, tower, base_top_y=cliff_top_y, y_offset=-3.5)

    cmds.select([cliff, tower], r=True)
    t2 = time.time()

    print("[--- MAYA-LIGHTHOUSE] Done")
    print(f"  Cleanup: {(t1 - t0):.3f}s")
    print(f"  Build:   {(t2 - t1):.3f}s")
    print(f"  Total:   {(t2 - t0):.3f}s")
