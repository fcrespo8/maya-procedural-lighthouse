# -*- coding: utf-8 -*-
"""
Entrypoint del proyecto.

Este archivo está pensado para ser ejecutado desde Maya (Script Editor),
y llama a la API del backend. Por ahora solo hacemos un test mínimo.
"""

from __future__ import annotations

import time

import maya.cmds as cmds

from backend.cliff import CliffBuilder, CliffParams

def run() -> None:
    start_time = time.time()

    # Limpieza de iteración anterior
    CliffBuilder.cleanup()

    # Construcción del acantilado
    params = CliffParams(
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
    cmds.select(cliff)

    elapsed = time.time() - start_time
    print(f"[MAYA-LIGHTHOUSE] Cliff created: {cliff}. Time: {elapsed:.3f}s")
