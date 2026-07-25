"""L7 guardrails 服务器配置 —— pii_guard(真 guardrails 服务器 + 本地 Presidio)。

对应课程 config.py 的结构:输入侧 refrain(有 PII 就拒绝处理)、输出侧 fix(把 PII 打码)。
课程 config.py 用 hub 的 `DetectPII`,但装它需 Guardrails Hub key(实测 401);这里用课程自己
引入的 **Presidio** + 自定义 `PIIDetector`(真 guardrails Validator)实现同样的两侧防护——
hub DetectPII 本质也是 Presidio 封装,故非等价替代,是用课程本身的工具还原。

用 AsyncGuard:guardrails-api 0.4.x 对同步 Guard 会 to_dict/from_dict 序列化重建,自定义 validator 的构造参数(如 sources)不进序列化契约会丢失且每请求重载模型;AsyncGuard 直接用活实例。

启动:PYTHONPATH=. guardrails start --config config_l7.py --env server.env --port 8000
"""

import os
import sys

# guardrails-api 0.4.x 加载 config 时不会把本目录加进 sys.path,自举以便 import helpers
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from guardrails import AsyncGuard, OnFailAction

from helpers.pii import PIIDetector

pii_guard = (
    AsyncGuard(id="pii_guard", name="pii_guard")
    .use(PIIDetector(entities=("PERSON", "PHONE_NUMBER"),
                     on_fail=OnFailAction.REFRAIN), on="messages")
    .use(PIIDetector(entities=("PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS"),
                     on_fail=OnFailAction.FIX), on="output")
)
