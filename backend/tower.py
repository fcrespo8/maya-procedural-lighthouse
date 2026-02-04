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
    add_bands: bool = True
    band_count: int = 3
    band_height_ratio: float = 0.08  # % de altura total por banda
    band_outset: float = 0.15        # cuánto sobresale
    add_door: bool = True
    door_width: float = 1.6
    door_height: float = 3.2
    door_depth: float = 0.2



class TowerBuilder:
    ROOT_GRP = "LHT_root_GRP"
    TOWER_GRP = "LHT_tower_GRP"

    def __init__(self, params: TowerParams) -> None:
        self.params = params

    def build(self) -> str:
        self._ensure_groups()
        tower = self._create_tapered_cylinder()
        self._add_details(tower)
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

    def _add_details(self, transform: str) -> None:
        p = self.params

        if p.add_bands:
            self._add_bands(transform)

        if p.add_door:
            self._add_door(transform)

    def _add_bands(self, transform: str) -> None:
        """
        Crea bandas horizontales extruyendo loops de caras cercanas a ciertas alturas.
        """
        p = self.params

        # En draft, pocas bandas / menor costo
        band_count = p.band_count if p.quality != "draft" else max(1, p.band_count - 1)

        bbox = cmds.exactWorldBoundingBox(transform)
        min_y, max_y = bbox[1], bbox[4]
        height = max(max_y - min_y, 0.0001)

        # alturas relativas: abajo, medio, arriba
        rel_positions = [0.20, 0.50, 0.80][:band_count]

        for rel in rel_positions:
            y = min_y + height * rel

            # Seleccionar caras cercanas a ese Y (simple: buscar caras cuyo centro esté cerca)
            faces = cmds.ls(f"{transform}.f[*]", flatten=True) or []
            target_faces = []

            for f in faces[::10] if p.quality == "draft" else faces:
                center = cmds.xform(f, q=True, ws=True, t=True)
                if abs(center[1] - y) < (height * p.band_height_ratio):
                    target_faces.append(f)

            if not target_faces:
                continue

            cmds.select(target_faces, r=True)
            cmds.polyExtrudeFacet(
                ltz=p.band_outset,  # empuja hacia afuera
                ls=(1.0, 1.0, 1.0),
                ch=False,
            )

        cmds.select(clear=True)

    def _add_door(self, tower_tr: str) -> None:
        """
        Agrega una puerta simple como cubo pegado al frente del faro.
        Se posiciona relativo al bounding box de la torre en WORLD, así no queda bajo el cliff.
        """
        p = self.params

        bbox = cmds.exactWorldBoundingBox(tower_tr)
        min_x, min_y, min_z, max_x, max_y, max_z = bbox

        cx = (min_x + max_x) * 0.5
        cz = max_z  # frente (asumido)
        base_y = min_y

        door_tr, _ = cmds.polyCube(
            name="towerDoor_GEO",
            w=p.door_width,
            h=p.door_height,
            d=p.door_depth,
        )

        # Colocar la puerta apoyada sobre la base de la torre
        y = base_y + (p.door_height * 0.5)
        z = cz + (p.door_depth * 0.5)

        cmds.xform(door_tr, ws=True, t=(cx, y, z))

        # Parent al transform de la torre (no al grupo), así acompaña siempre
        cmds.parent(door_tr, tower_tr)
        cmds.makeIdentity(door_tr, apply=True, t=1, r=1, s=1, n=0)


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
