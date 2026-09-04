#!/usr/bin/env python3
"""Fetch the latest source of a public Kaggle notebook without credentials."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen


DEFAULT_REF = "foysalemonshanto/lb-9-arc3-duck-v12-with-qwen-3-8-27b"
API_ROOT = "https://www.kaggle.com/api/v1/kernels/pull"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", default=DEFAULT_REF)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("baselines/foysal-qwen38-v6"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    request = Request(
        f"{API_ROOT}/{args.ref}",
        headers={"User-Agent": "arc3-public-baseline-fetcher/1.0"},
    )
    with urlopen(request, timeout=60) as response:
        payload = json.load(response)

    source = payload["blob"]["source"]
    notebook = json.loads(source)
    metadata = payload["metadata"]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    notebook_path = args.output_dir / "notebook.ipynb"
    metadata_path = args.output_dir / "source-metadata.json"
    notebook_path.write_text(
        json.dumps(notebook, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"Downloaded {metadata['ref']} version {metadata['currentVersionNumber']}")
    print(f"Notebook: {notebook_path}")
    print(f"Metadata: {metadata_path}")


if __name__ == "__main__":
    main()

