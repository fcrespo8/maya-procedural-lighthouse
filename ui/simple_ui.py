# -*- coding: utf-8 -*-
"""
UI mínima para el Lighthouse Tool (cmds).
"""

from __future__ import annotations

import importlib
import maya.cmds as cmds

import backend.lighthouse
import backend.config


WINDOW_NAME = "LHT_simpleUI"


def _reload_modules() -> None:
    import backend.cliff
    import backend.tower
    import backend.lighthouse
    import backend.config

    importlib.reload(backend.cliff)
    importlib.reload(backend.tower)
    importlib.reload(backend.lighthouse)
    importlib.reload(backend.config)



def build_lighthouse(*args) -> None:
    _reload_modules()

    from backend.lighthouse import LighthouseBuilder
    from backend.config import get_preset

    preset = cmds.optionMenu("LHT_presetMenu", q=True, value=True)
    quality = "high" if cmds.checkBox("LHT_highCheck", q=True, v=True) else "draft"

    LighthouseBuilder.cleanup()
    params = get_preset(preset.lower(), quality=quality)
    root = LighthouseBuilder(params).build()

    cmds.select(root, r=True)


def cleanup_lighthouse(*args) -> None:
    from backend.lighthouse import LighthouseBuilder
    LighthouseBuilder.cleanup()


def show() -> None:
    if cmds.window(WINDOW_NAME, exists=True):
        cmds.deleteUI(WINDOW_NAME)

    cmds.window(WINDOW_NAME, title="Procedural Lighthouse", widthHeight=(260, 160))
    cmds.columnLayout(adj=True, rs=8)

    cmds.text(label="Style Preset")
    cmds.optionMenu("LHT_presetMenu")
    cmds.menuItem(label="Shutter")
    cmds.menuItem(label="Calm")
    cmds.menuItem(label="Storm")

    cmds.separator(h=10, style="in")

    cmds.checkBox("LHT_highCheck", label="High Quality", value=False)

    cmds.separator(h=10, style="in")

    cmds.button(label="Build Lighthouse", h=35, c=build_lighthouse)
    cmds.button(label="Cleanup", h=25, c=cleanup_lighthouse)

    cmds.showWindow(WINDOW_NAME)
