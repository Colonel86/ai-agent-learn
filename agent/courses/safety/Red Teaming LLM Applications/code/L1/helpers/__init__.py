"""L1 本地演示的 helpers 包。

原版这里还导出 ByteChaptersBot(L4/L5 用),L1 只需要 ZephyrApp,故本地化版本
只保留 ZephyrApp,不引入 llama-index / giskard 等重依赖。
"""

import logging

from .zb_app import ZephyrApp

# 压掉 httpx 每次请求打的 INFO 日志,让演示输出干净
logging.getLogger("httpx").setLevel(logging.WARNING)

__all__ = ["ZephyrApp"]
