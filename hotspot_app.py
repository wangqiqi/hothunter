"""Flet App 可直接打开的单文件入口（手机端 Open File）。"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.main import main

if __name__ == "__main__":
    main()
