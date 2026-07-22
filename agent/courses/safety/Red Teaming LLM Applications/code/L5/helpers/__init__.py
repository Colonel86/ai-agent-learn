"""L5 本地演示的 helpers 包:导出带工具的 ByteChaptersBot(客服 Agent)。"""

import logging

from .byte_chapters import ByteChaptersBot

logging.getLogger("httpx").setLevel(logging.WARNING)

__all__ = ["ByteChaptersBot"]
