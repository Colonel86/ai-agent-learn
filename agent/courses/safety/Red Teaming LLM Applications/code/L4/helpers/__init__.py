"""本地演示的 helpers 包:导出未加固的 ZephyrApp(RAG 客服机器人)。"""

import logging

from .zb_app import ZephyrApp

logging.getLogger("httpx").setLevel(logging.WARNING)

__all__ = ["ZephyrApp"]
