# -*- coding: utf-8 -*-
"""
Generador de acantilado (cliff) procedural.

Idea:
- Crear un polyCube con muchas subdivisiones.
- Deformar vértices para un look rocoso (random controlado).
- Agrupar todo bajo un grupo raíz para poder limpiar fácil.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

import maya.cmds as cmds


@dataclass
class CliffParams:
    """Parámetros de generación del acantilado."""
    name: str = "cliff_GEO"
    width: float = 30.0
    height: float = 10.0
    depth: float = 30.0
    sub_x: int = 40
    sub_y: int = 20
    sub_z: int = 40
    noise_amplitude: float = 1.2  # intensidad máxima del desplazamiento
    seed: int = 42


class CliffBuilder:
    """Builder responsable de crear y deformar el acantilado."""

    ROOT_GRP = "LHT_root_GRP"   # Lighthouse Tool root group
    CLIFF_GRP = "LHT_cliff_GRP"

    def __init__(self, params: CliffParams) -> None:
        self.params = params

    # -------------------------
    # Public API
    # -------------------------
    def build(self) -> str:
        """
        Crea el acantilado y devuelve el nombre del transform principal.
        """
        self._ensure_groups()
        cliff_transform = self._create_base_cube()
        self._apply_vertex_noise(cliff_transform)
        return cliff_transform

    @classmethod
    def cleanup(cls) -> None:
        """Borra la iteración anterior del tool (si existe)."""
        if cmds.objExists(cls.ROOT_GRP):
            cmds.delete(cls.ROOT_GRP)

    # -------------------------
    # Internal helpers
    # -------------------------
    def _ensure_groups(self) -> None:
        """Crea grupos raíz si no existen."""
        if not cmds.objExists(self.ROOT_GRP):
            cmds.group(empty=True, name=self.ROOT_GRP)

        if not cmds.objExists(self.CLIFF_GRP):
            cliff_grp = cmds.group(empty=True, name=self.CLIFF_GRP, parent=self.ROOT_GRP)
            cmds.setAttr(f"{cliff_grp}.visibility", 1)

    def _create_base_cube(self) -> str:
        """Crea un polyCube con subdivisiones, lo mete en el grupo y retorna el transform."""
        p = self.params

        transform, _shape = cmds.polyCube(
            name=p.name,
            w=p.width,
            h=p.height,
            d=p.depth,
            sx=p.sub_x,
            sy=p.sub_y,
            sz=p.sub_z,
        )

        cmds.parent(transform, self.CLIFF_GRP)
        cmds.makeIdentity(transform, apply=True, t=1, r=1, s=1, n=0)
        return transform

    def _apply_vertex_noise(self, transform: str) -> None:
        """
        Deforma vértices del mesh para look rocoso.
        Estrategia simple:
        - Random con seed para reproducibilidad.
        - Más deformación hacia la parte superior (y) para formar relieve.
        """
        p = self.params
        random.seed(p.seed)

        # Seleccionamos todos los vértices del objeto
        vertices = cmds.ls(f"{transform}.vtx[*]", flatten=True) or []
        if not vertices:
            return

        # Obtenemos bounding box para normalizar la altura
        bbox = cmds.exactWorldBoundingBox(transform)
        min_y, max_y = bbox[1], bbox[4]
        height_range = max(max_y - min_y, 0.0001)

        for vtx in vertices:
            pos = cmds.pointPosition(vtx, world=True)
            y_norm = (pos[1] - min_y) / height_range  # 0 en base, 1 en top

            # factor: menos ruido en base, más arriba (suave)
            strength = p.noise_amplitude * (0.25 + 0.75 * y_norm)

            dx = random.uniform(-strength, strength)
            dy = random.uniform(-strength * 0.35, strength * 0.35)  # menos vertical
            dz = random.uniform(-strength, strength)

            cmds.move(dx, dy, dz, vtx, r=True, os=True, wd=True)
