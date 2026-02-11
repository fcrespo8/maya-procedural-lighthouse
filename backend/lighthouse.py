# -*- coding: utf-8 -*-
"""
Orquestador del proyecto: construye el faro completo (cliff + tower)
usando los builders del backend.

- Un solo entrypoint: LighthouseBuilder.build()
- Cleanup centralizado
- Placement robusto (por bounding box, no por pivot)
- Environment simple: sea + backdrop (con ondas leves)
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
    ENV_GRP = "LHT_env_GRP"
    SEA_GEO = "LHT_sea_GEO"
    BACKDROP_GEO = "LHT_backdrop_GEO"

    def __init__(self, params: LighthouseParams) -> None:
        self.params = params

    @classmethod
    def cleanup(cls) -> None:
        """Borra toda la iteración anterior."""
        CliffBuilder.cleanup()

    def build(self) -> str:
        """Construye cliff + tower, posiciona la torre, construye env y devuelve ROOT_GRP."""
        cliff_tr = CliffBuilder(self.params.cliff).build()
        tower_tr = TowerBuilder(self.params.tower).build()

        self._place_tower_on_cliff(
            cliff_tr=cliff_tr,
            tower_tr=tower_tr,
            placement=self.params.placement,
        )

        # Environment (B3)
        self._build_environment(cliff_tr)

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

    # -------------------------
    # Environment (B3)
    # -------------------------
    def _build_environment(self, cliff_tr: str) -> None:
        """
        Crea un entorno simple para preview:
        - Mar (plane) con ondas leves
        - Backdrop (plane vertical) tipo cielo
        """
        if not cmds.objExists(self.ENV_GRP):
            cmds.group(empty=True, name=self.ENV_GRP, parent=self.ROOT_GRP)

        bbox = cmds.exactWorldBoundingBox(cliff_tr)
        min_x, min_y, min_z, max_x, max_y, max_z = bbox

        cx = (min_x + max_x) * 0.5
        cz = (min_z + max_z) * 0.5
        size_x = (max_x - min_x) * 6.0
        size_z = (max_z - min_z) * 6.0

        # --- SEA ---
        if not cmds.objExists(self.SEA_GEO):
            # Subdivs para ondas (barato)
            sea_tr, _ = cmds.polyPlane(
                name=self.SEA_GEO,
                w=size_x,
                h=size_z,
                sx=80,
                sy=80,
            )
            cmds.parent(sea_tr, self.ENV_GRP)

            sea_y = min_y - 3.0
            cmds.xform(sea_tr, ws=True, t=(cx, sea_y, cz))

            self._apply_sea_waves(sea_tr, amplitude=0.25, seed=12)
            self._assign_sea_material(sea_tr)

        # --- BACKDROP ---
        if not cmds.objExists(self.BACKDROP_GEO):
            back_tr, _ = cmds.polyPlane(
                name=self.BACKDROP_GEO,
                w=size_x * 0.9,
                h=(max_y - min_y) * 4.0,
                sx=1,
                sy=1,
            )
            cmds.parent(back_tr, self.ENV_GRP)

            back_y = min_y + (max_y - min_y) * 1.2
            back_z = min_z - size_z * 0.25
            cmds.xform(back_tr, ws=True, t=(cx, back_y, back_z))
            cmds.setAttr(f"{back_tr}.rotateX", 90)

            self._assign_backdrop_material(back_tr)

    def _apply_sea_waves(self, sea_tr: str, amplitude: float = 0.25, seed: int = 12) -> None:
        """
        Ondas leves en el mar usando noise3D (deformer).
        """
        # Crear textura procedural
        noise = cmds.shadingNode("noise", asTexture=True, name="LHT_seaNoise")
        cmds.setAttr(f"{noise}.frequency", 4.0)

        # Convertir textura a desplazamiento con displacementShader
        disp = cmds.shadingNode("displacementShader", asShader=True, name="LHT_seaDisp")
        cmds.connectAttr(f"{noise}.outAlpha", f"{disp}.displacement", force=True)

        # Crear un SG para conectar el displacement al shape (no afecta shading del material)
        sg = "LHT_seaDispSG"
        if not cmds.objExists(sg):
            sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
        cmds.connectAttr(f"{disp}.displacement", f"{sg}.displacementShader", force=True)

        # Asignar el SG de displacement al plane (solo para que el deformer tenga input)
        # OJO: no reemplaza shading final porque después asignamos material al transform.
        cmds.sets(sea_tr, e=True, forceElement=sg)

        # Aplicar deformer de displacement
        # Maya crea un nodo tipo "displacement" que usa el displacement shader.
        # Alternativa más estable: usar aplanado y mover vértices, pero esto queda lindo y rápido.
        try:
            cmds.setAttr(f"{disp}.scale", amplitude)
        except Exception:
            pass

    def _get_or_create_material(self, name: str, shader_type: str = "lambert") -> tuple[str, str]:
        """
        Crea material + SG si no existe.
        Devuelve (material, shading_group).
        """
        sg = f"{name}SG"
        if not cmds.objExists(name):
            mat = cmds.shadingNode(shader_type, asShader=True, name=name)
            sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
            cmds.connectAttr(f"{mat}.outColor", f"{sg}.surfaceShader", force=True)
            return mat, sg

        return name, sg

    def _assign_sea_material(self, transform: str) -> None:
        mat, sg = self._get_or_create_material("LHT_sea_MAT", shader_type="blinn")
        cmds.setAttr(f"{mat}.color", 0.05, 0.12, 0.22, type="double3")  # azul oscuro
        cmds.setAttr(f"{mat}.specularColor", 0.25, 0.25, 0.25, type="double3")
        cmds.setAttr(f"{mat}.eccentricity", 0.2)
        cmds.sets(transform, e=True, forceElement=sg)

    def _assign_backdrop_material(self, transform: str) -> None:
        mat, sg = self._get_or_create_material("LHT_backdrop_MAT", shader_type="lambert")
        cmds.setAttr(f"{mat}.color", 0.65, 0.70, 0.75, type="double3")
        cmds.sets(transform, e=True, forceElement=sg)
