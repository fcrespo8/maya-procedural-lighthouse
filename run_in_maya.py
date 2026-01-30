# -*- coding: utf-8 -*-
"""
Entrypoint del proyecto.

Este archivo está pensado para ser ejecutado desde Maya (Script Editor),
y llama a la API del backend. Por ahora solo hacemos un test mínimo.
"""

from __future__ import annotations

import time

import maya.cmds as cmds


def run() -> None:
    """Ejecuta una prueba mínima para validar que el proyecto corre en Maya."""
    start_time = time.time()

    # Creamos un cubo de prueba para verificar que el script está funcionando.
    cube, _ = cmds.polyCube(name="TEST_cube_GEO", w=1, h=1, d=1)
    cmds.select(cube)

    elapsed = time.time() - start_time
    print(f"[MAYA-LIGHTHOUSE] Test OK. Created: {cube}. Time: {elapsed:.3f}s")
