# -*- coding: utf-8 -*-
"""
Presets de estilo para el faro procedural.
Cada preset devuelve LighthouseParams listos para construir.
"""

from backend.cliff import CliffParams
from backend.tower import TowerParams
from backend.lighthouse import LighthouseParams, PlacementParams


def get_preset(name: str, quality: str = "draft") -> LighthouseParams:
    name = name.lower()

    if name == "shutter":
        return LighthouseParams(
            cliff=CliffParams(
                quality=quality,
                width=40.0,
                height=14.0,
                depth=40.0,
                noise_amplitude=1.8,
                seed=11,
            ),
            tower=TowerParams(
                quality=quality,
                height=30.0,
                radius_base=4.2,
                radius_top=2.8,
            ),
            placement=PlacementParams(top_ratio=0.08, y_offset=-0.35),
        )

    if name == "calm":
        return LighthouseParams(
            cliff=CliffParams(
                quality=quality,
                width=32.0,
                height=10.0,
                depth=32.0,
                noise_amplitude=1.0,
                seed=3,
            ),
            tower=TowerParams(
                quality=quality,
                height=26.0,
                radius_base=4.0,
                radius_top=3.5,
            ),
            placement=PlacementParams(top_ratio=0.10, y_offset=-0.25),
        )

    if name == "storm":
        return LighthouseParams(
            cliff=CliffParams(
                quality=quality,
                width=45.0,
                height=18.0,
                depth=45.0,
                noise_amplitude=2.2,
                seed=27,
            ),
            tower=TowerParams(
                quality=quality,
                height=34.0,
                radius_base=4.0,
                radius_top=2.5,
            ),
            placement=PlacementParams(top_ratio=0.06, y_offset=-0.45),
        )

    raise ValueError(f"Unknown preset: {name}")
