"""L2 本地演示的 helpers 包。

导出两个靶子:
  - ask_bot / MOZART_BIO / PROMPT:Mozart 传记机器人(前四类越狱技术)
  - ZephyrApp:L1 那个未加固客服机器人(第五类:系统提示词探测)
"""

import logging

from .mozart_bot import ask_bot, MOZART_BIO, PROMPT
from .zb_app import ZephyrApp

logging.getLogger("httpx").setLevel(logging.WARNING)

__all__ = ["ask_bot", "MOZART_BIO", "PROMPT", "ZephyrApp"]
