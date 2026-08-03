"""课程共享 helpers。

原课程每课目录下各放一份完全相同的 helpers/,这里合并成一份共享包(五份之间仅
模型名有差异,已改为从 .env 读)。各课 main.py 把 code/ 加进 sys.path 后即可
`from helpers import ZephyrApp`,写法和课程 notebook 一致。

注意 import 顺序:local_stack 必须最先导入,它要在 fastembed / transformers 被加载
之前打好环境补丁。
"""

from . import local_stack  # noqa: F401  必须最先导入(打环境补丁)
from .byte_chapters import ByteChaptersBot
from .zb_app import ZephyrApp

local_stack.quiet_logs()

__all__ = ["ZephyrApp", "ByteChaptersBot", "local_stack"]
