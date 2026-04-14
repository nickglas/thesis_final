"""Artifact logging: saves raw iterations, summaries, environment metadata, and config copies."""

import os
import csv
import json
import shutil
import platform
import subprocess
import datetime
from typing import Any, Dict, List


class ArtifactLogger:

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "plots"), exist_ok=True)

    def save_config_copy(self, config_path: str):
        shutil.copy2(config_path, os.path.join(self.output_dir, "config.yaml"))

    def save_environment(self):
        import torch
        git_hash = "unknown"
        try:
            git_hash = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
            ).decode().strip()
        except Exception:
            pass

        env = {
            "timestamp": datetime.datetime.now().isoformat(),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "torch_version": torch.__version__,
            "cpu_count": os.cpu_count(),
            "git_commit": git_hash,
        }
        with open(os.path.join(self.output_dir, "environment.json"), "w") as f:
            json.dump(env, f, indent=2)

    def save_raw_iterations(self, rows: List[Dict[str, Any]]):
        if not rows:
            return
        path = os.path.join(self.output_dir, "raw_iterations.csv")
        fieldnames = list(rows[0].keys())
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def save_json(self, filename: str, data: Any):
        with open(os.path.join(self.output_dir, filename), "w") as f:
            json.dump(data, f, indent=2)

    def save_csv(self, filename: str, rows: List[Dict[str, Any]]):
        if not rows:
            return
        path = os.path.join(self.output_dir, filename)
        fieldnames = list(rows[0].keys())
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
