"""应用入口。"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import flet as ft

from src.ui.app import run_app


def main() -> None:
    ft.app(target=run_app)


if __name__ == "__main__":
    main()
