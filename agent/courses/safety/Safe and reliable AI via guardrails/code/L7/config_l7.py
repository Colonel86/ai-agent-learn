"""L7 guardrails 服务器配置 —— pii_guard(真 guardrails 服务器 + 本地 Presidio)。

对应课程 config.py 的结构:输入侧 refrain(有 PII 就拒绝处理)、输出侧 fix(把 PII 打码)。
课程 config.py 用 hub 的 `DetectPII`,但装它需 Guardrails Hub key(实测 401);这里用课程自己
引入的 **Presidio** + 自定义 `PIIDetector`(真 guardrails Validator)实现同样的两侧防护——
hub DetectPII 本质也是 Presidio 封装,故非等价替代,是用课程本身的工具还原。

同步 Guard(非 AsyncGuard),原因见 L3 说明。

启动:PYTHONPATH=. guardrails start --config config_l7.py --env server.env --port 8000
"""

from guardrails import Guard, OnFailAction

from helpers.pii import PIIDetector

pii_guard = (
    Guard(name="pii_guard")
    .use(PIIDetector(entities=("PERSON", "PHONE_NUMBER"),
                     on_fail=OnFailAction.REFRAIN), on="messages")
    .use(PIIDetector(entities=("PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS"),
                     on_fail=OnFailAction.FIX), on="output")
)
