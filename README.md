# 🗼 Procedural Lighthouse for Maya

A procedural lighthouse generator built in **Python for Autodesk Maya**, designed as a clean, production-style tool with a modular backend and multiple artistic presets.

This project focuses on **tool architecture, performance, and usability**, following patterns commonly used in animation and VFX pipelines.

---

## ✨ Features

- 🧱 **Procedural cliff generation**
  - Vertex-based noise deformation
  - Draft / High quality modes for fast iteration
  - Reproducible results using seeds

- 🗼 **Procedural lighthouse tower**
  - Adjustable height, base radius and taper
  - Architectural details:
    - Horizontal bands
    - Entrance door
    - Lantern top

- 🎨 **Style presets**
  - **Shutter** – rugged, dramatic cliff
  - **Calm** – softer terrain and proportions
  - **Storm** – tall, aggressive silhouette

- 🎛️ **Simple UI (maya.cmds)**
  - Preset selector
  - Draft / High quality toggle
  - Build / Cleanup buttons

- 🧠 **Clean architecture**
  - Backend logic separated from UI
  - Orchestrator pattern (`LighthouseBuilder`)
  - Easy to extend (new presets, UI, or behaviors)

---

## 📂 Project Structure

```text
maya-procedural-lighthouse/
│
├── backend/
│   ├── cliff.py          # CliffBuilder + CliffParams
│   ├── tower.py          # TowerBuilder + TowerParams
│   ├── lighthouse.py     # Orchestrator (cliff + tower + placement)
│   └── config.py         # Style presets (Shutter / Calm / Storm)
│
├── ui/
│   └── simple_ui.py      # Minimal maya.cmds UI
│
├── run_in_maya.py        # Maya entrypoint (reload + timing)
└── README.md
