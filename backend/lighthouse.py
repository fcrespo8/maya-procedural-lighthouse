# -*- coding: utf-8 -*-
"""
Orquestador del proyecto: construye el faro completo (cliff + tower)
usando los builders del backend.

- Un solo entrypoint: LighthouseBuilder.build()
- Cleanup centralizado
- Placement robusto (por bounding box, no por pivot)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import maya.cmds as cmds

from backend.cliff import CliffBuilder, CliffParams
from backend.tower import TowerBuilder, TowerParams


@dataclass
class PlacementParams:
    """Parámetros para colocar la torre sobre el cliff."""
    top_ratio: float = 0.10   # promedio del top X% de vértices (evita picos)
    y_offset: float = -0.20   # hundir un poco la base de la torre en la roca


@dataclass
class LighthouseParams:
    """Params del faro completo."""
    cliff: CliffParams
    tower: TowerParams
    placement: PlacementParams = field(default_factory=PlacementParams)


class LighthouseBuilder:
    """Construye el faro completo (cliff + tower) y devuelve el ROOT_GRP."""

    ROOT_GRP = "LHT_root_GRP"

    def __init__(self, params: LighthouseParams) -> None:
        self.params = params

    @classmethod
    def cleanup(cls) -> None:
        """Borra toda la iteración anterior."""
        CliffBuilder.cleanup()

    def build(self) -> str:
        """Construye cliff + tower, posiciona la torre, y devuelve ROOT_GRP."""
        cliff_tr = CliffBuilder(self.params.cliff).build()
        tower_tr = TowerBuilder(self.params.tower).build()

        self._place_tower_on_cliff(
            cliff_tr=cliff_tr,
            tower_tr=tower_tr,
            placement=self.params.placement,
        )

        return self.ROOT_GRP

    # -------------------------
    # Placement helpers
    # -------------------------
    @staticmethod
    def _get_cliff_top_y(transform: str, top_ratio: float) -> float:
        """
        Devuelve una altura 'top' estable del cliff:
        promedio del top X% de vértices en Y, para ignorar picos extremos.
        """
        verts = cmds.ls(f"{transform}.vtx[*]", flatten=True) or []
        if not verts:
            bbox = cmds.exactWorldBoundingBox(transform)
            return bbox[4]  # max_y

        ys = [cmds.pointPosition(v, world=True)[1] for v in verts]
        ys.sort()

        top_count = max(1, int(len(ys) * top_ratio))
        top_slice = ys[-top_count:]
        return sum(top_slice) / float(len(top_slice))

    @classmethod
    def _place_tower_on_cliff(cls, cliff_tr: str, tower_tr: str, placement: PlacementParams) -> None:
        """
        Coloca la torre centrada en XZ y apoyada sobre el cliff de forma robusta.
        IMPORTANTÍSIMO: no usa el pivot, usa bbox.

        Objetivo:
        - bbox_minY(torre) == topY(cliff) + y_offset
        - bbox_centerXZ(torre) == bbox_centerXZ(cliff)
        """
        # 1) Centro XZ del cliff
        base_bbox = cmds.exactWorldBoundingBox(cliff_tr)
        base_min_x, _, base_min_z, base_max_x, _, base_max_z = base_bbox
        base_cx = (base_min_x + base_max_x) * 0.5
        base_cz = (base_min_z + base_max_z) * 0.5

        # 2) Top estable del cliff
        base_top_y = cls._get_cliff_top_y(cliff_tr, top_ratio=placement.top_ratio)
        target_base_y = base_top_y + placement.y_offset

        # 3) BBox actual de la torre (incluye puerta/linterna si son hijos)
        tower_bbox = cmds.exactWorldBoundingBox(tower_tr)
        tow_min_x, tow_min_y, tow_min_z, tow_max_x, tow_max_y, tow_max_z = tower_bbox
        tow_cx = (tow_min_x + tow_max_x) * 0.5
        tow_cz = (tow_min_z + tow_max_z) * 0.5

        # 4) Calculamos deltas para mover de manera RELATIVA (super robusto)
        dx = base_cx - tow_cx
        dz = base_cz - tow_cz
        dy = target_base_y - tow_min_y  # <-- clave: apoya por bbox minY

        cmds.move(dx, dy, dz, tower_tr, r=True, ws=True)
