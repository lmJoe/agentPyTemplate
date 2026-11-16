import sys
from pathlib import Path

# 把项目根目录加入 sys.path，保证直接执行 pytest 时也能 import app.*
PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
