# -*- coding: utf-8 -*-
"""
Generador de torre del faro (tower) procedural.

Versión v1:
- Un cilindro principal con taper (radio top menor).
- Grupo dedicado LHT_tower_GRP dentro de LHT_root_GRP.
"""

from __future__ import annotations

from dataclasses import dataclass

import maya.cmds as cmds


@dataclass
class TowerParams:
    name: str = "tower_GEO"
    height: float = 28.0
    radius_base: float = 4.0
    radius_top: float = 3.0  # taper
    subdivisions_axis: int = 24
    subdivisions_height: int = 10
    quality: str = "draft"  # "draft" | "high"


class TowerBuilder:
    ROOT_GRP = "LHT_root_GRP"
    TOWER_GRP = "LHT_tower_GRP"

    def __init__(self, params: TowerParams) -> None:
        self.params = params

    def build(self) -> str:
        self._ensure_groups()
        tower = self._create_tapered_cylinder()
        self._assign_material(tower)
        return tower

    def _ensure_groups(self) -> None:
        if not cmds.objExists(self.ROOT_GRP):
            cmds.group(empty=True, name=self.ROOT_GRP)

        if not cmds.objExists(self.TOWER_GRP):
            cmds.group(empty=True, name=self.TOWER_GRP, parent=self.ROOT_GRP)

    def _create_tapered_cylinder(self) -> str:
        p = self.params

        if p.quality == "draft":
            sub_ax = 16
            sub_h = 6
        else:
            sub_ax = p.subdivisions_axis
            sub_h = p.subdivisions_height

        # Crear cilindro base
        transform, _shape = cmds.polyCylinder(
            name=p.name,
            h=p.height,
            r=p.radius_base,
            sx=sub_ax,
            sy=sub_h,
        )

        cmds.parent(transform, self.TOWER_GRP)

        # Taper: escalar el loop de arriba
        top_faces = cmds.ls(f"{transform}.f[*]", flatten=True) or []
        if top_faces:
            # Seleccionar la "tapa" de arriba (cara final)
            top_cap = f"{transform}.f[{len(top_faces) - 1}]"
            cmds.select(top_cap, r=True)

            # Convertir a vertices de la tapa y escalar en XZ
            verts = cmds.polyListComponentConversion(top_cap, toVertex=True)
            verts = cmds.ls(verts, flatten=True) or []

            if verts and p.radius_base > 0.0001:
                scale = p.radius_top / p.radius_base
                cmds.scale(scale, 1.0, scale, verts, r=True, os=True)

        cmds.select(clear=True)
        cmds.makeIdentity(transform, apply=True, t=1, r=1, s=1, n=0)
        return transform

    def _assign_material(self, transform: str) -> None:
        material_name = "LHT_tower_MAT"
        shading_group = f"{material_name}SG"

        if not cmds.objExists(material_name):
            material = cmds.shadingNode("lambert", asShader=True, name=material_name)
            # blanco sucio / crema
            cmds.setAttr(f"{material}.color", 0.85, 0.83, 0.78, type="double3")
            cmds.setAttr(f"{material}.diffuse", 0.8)

            shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=shading_group)
            cmds.connectAttr(f"{material}.outColor", f"{shading_group}.surfaceShader", force=True)

        cmds.sets(transform, edit=True, forceElement=shading_group)
