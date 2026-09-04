#!/usr/bin/env python3
"""Static checks for the mirrored public Kaggle baseline."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "baselines" / "foysal-qwen38-v6"


def load_json(name: str) -> dict:
    return json.loads((BASELINE / name).read_text(encoding="utf-8"))


def main() -> None:
    notebook = load_json("notebook.ipynb")
    source_metadata = load_json("source-metadata.json")
    kernel_template = load_json("kernel-metadata.template.json")

    assert notebook["nbformat"] == 4
    assert source_metadata["ref"] == (
        "foysalemonshanto/lb-9-arc3-duck-v12-with-qwen-3-8-27b"
    )
    assert source_metadata["currentVersionNumber"] == 6
    assert source_metadata["machineShape"] == "NvidiaRtxPro6000"
    assert source_metadata["enableGpu"] is True
    assert source_metadata["enableInternet"] is False
    assert kernel_template["enable_gpu"] is True
    assert kernel_template["enable_internet"] is False
    assert kernel_template["competition_sources"] == [
        "arc-prize-2026-arc-agi-3"
    ]
    assert "REPLACE_WITH_YOUR_USERNAME" in kernel_template["id"]

    language_info = notebook["metadata"]["language_info"]
    source_header = notebook["metadata"].get("kaggle", {})
    print("Static preflight: PASS")
    print(f"Source version: {source_metadata['currentVersionNumber']}")
    print(f"Python recorded by source: {language_info.get('version')}")
    print(f"Kernel machine shape: {source_metadata['machineShape']}")
    print(f"Kernel GPU enabled: {source_metadata['enableGpu']}")
    print(f"Kernel internet enabled: {source_metadata['enableInternet']}")
    print(
        "Embedded notebook isGpuEnabled: "
        f"{source_header.get('isGpuEnabled')} (stale; push metadata must request GPU)"
    )
    print("Kaggle username/template replacement: REQUIRED")
    print("Authenticated Save & Run: REQUIRED before competition submission")


if __name__ == "__main__":
    main()

