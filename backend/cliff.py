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
    enable_face_colors: bool = True
    face_color_base: float = 0.35      # gris base
    face_color_variation: float = 0.08 # variación leve (+/-)


class CliffBuilder:
    """Builder responsable de crear y deformar el acantilado."""

    ROOT_GRP = "LHT_root_GRP"   # Lighthouse Tool root group
    CLIFF_GRP = "LHT_cliff_GRP"
    LIGHT_TR = "LHT_keyLight"


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
        self._apply_face_color_variation(cliff_transform)
        self._assign_material(cliff_transform)

        self._ensure_preview_light(cliff_transform)

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

    def _assign_material(self, transform: str) -> None:
        """
        Asigna un material simple tipo roca al acantilado.
        Si ya existe, lo reutiliza.
        """
        material_name = "LHT_cliff_MAT"
        shading_group = f"{material_name}SG"

        if not cmds.objExists(material_name):
            material = cmds.shadingNode(
                "lambert",
                asShader=True,
                name=material_name,
            )
            cmds.setAttr(f"{material}.color", 0.35, 0.35, 0.35, type="double3")
            cmds.setAttr(f"{material}.diffuse", 0.8)

            shading_group = cmds.sets(
                renderable=True,
                noSurfaceShader=True,
                empty=True,
                name=shading_group,
            )
            cmds.connectAttr(
                f"{material}.outColor",
                f"{shading_group}.surfaceShader",
                force=True,
            )

        cmds.sets(transform, edit=True, forceElement=shading_group)
    def _apply_face_color_variation(self, transform: str) -> None:
        """
        Aplica una variación leve de color por cara usando display colors.
        Esto mejora la lectura tipo "roca" sin texturas.
        """
        p = self.params
        if not p.enable_face_colors:
            return

        # Asegura reproducibilidad
        random.seed(p.seed + 1000)

        faces = cmds.ls(f"{transform}.f[*]", flatten=True) or []
        if not faces:
            return

        base = p.face_color_base
        var = p.face_color_variation

        # Aplicamos un gris random por cara (muy leve)
        for f in faces:
            v = random.uniform(-var, var)
            c = max(0.0, min(1.0, base + v))
            cmds.polyColorPerVertex(f, rgb=(c, c, c), colorDisplayOption=True)

        # Aseguramos que el mesh muestre display colors
        shapes = cmds.listRelatives(transform, shapes=True, fullPath=True) or []
        for shape in shapes:
            try:
                cmds.setAttr(f"{shape}.displayColors", 1)
            except Exception:
                pass

    def _ensure_preview_light(self, target_transform: str) -> None:
        """
        Crea o reutiliza una directional light para previsualización
        y la coloca 'arriba' del acantilado (solo por orden visual).
        La dirección real de la luz depende de la rotación.
        """
        light_tr = self.LIGHT_TR
        light_shape = f"{self.LIGHT_TR}Shape"

        # Crear si no existe
        if not cmds.objExists(light_tr):
            light_shape = cmds.createNode("directionalLight", name=light_shape)
            parents = cmds.listRelatives(light_shape, parent=True, fullPath=False) or []
            light_tr = parents[0] if parents else cmds.rename(light_shape, self.LIGHT_TR)

            # Parentear al root del tool
            cmds.parent(light_tr, self.ROOT_GRP)

        # Posicionar arriba del cliff (visual)
        bbox = cmds.exactWorldBoundingBox(target_transform)
        min_x, min_y, min_z, max_x, max_y, max_z = bbox
        cx = (min_x + max_x) * 0.5
        cz = (min_z + max_z) * 0.5

        height_offset = (max_y - min_y) * 1.5  # ajustable
        cmds.setAttr(f"{light_tr}.translateX", cx)
        cmds.setAttr(f"{light_tr}.translateY", max_y + height_offset)
        cmds.setAttr(f"{light_tr}.translateZ", cz)

        # Dirección de luz (esto es lo que realmente importa)
        cmds.setAttr(f"{light_tr}.rotateX", -55)
        cmds.setAttr(f"{light_tr}.rotateY", 35)
        cmds.setAttr(f"{light_tr}.rotateZ", 0)

        # Potencia
        shapes = cmds.listRelatives(light_tr, shapes=True, fullPath=False) or []
        if shapes:
            cmds.setAttr(f"{shapes[0]}.intensity", 2.5)

