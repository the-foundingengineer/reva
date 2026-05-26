#!/usr/bin/env python3
"""
One-shot inventory setup: migration (if DB URL set) + seed.

Usage:
  python scripts/setup_inventory.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    print("=== Reva inventory setup ===\n")

    mig = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "apply_migration.py")],
        cwd=str(ROOT),
    )
    if mig.returncode != 0:
        print(
            "\nMigration was not applied automatically.\n"
            "Run migrations/001_inventory.sql in Supabase SQL editor, then continue.\n"
        )
        answer = input("Continue to seed anyway? [y/N]: ").strip().lower()
        if answer != "y":
            raise SystemExit(1)

    seed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "seed_inventory.py")],
        cwd=str(ROOT),
    )
    raise SystemExit(seed.returncode)


if __name__ == "__main__":
    main()
