"""Generate build/idel-faker.ico for PyInstaller packaging."""

import os
import sys

# Make the repo root importable when run as `python scripts/make_ico.py`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from idel_faker.icons import save_ico

OUT_DIR = "build"
OUT_PATH = os.path.join(OUT_DIR, "idel-faker.ico")


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    save_ico(OUT_PATH)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
