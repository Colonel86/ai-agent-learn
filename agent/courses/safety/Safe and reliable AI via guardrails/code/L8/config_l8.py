"""L8 guardrails 服务器配置 —— competitor_check(真 guardrails 服务器 + 本地 NER validator)。

对应课程 config.py 的 competitor_check,但课程用 hub 的 CompetitorCheck(需 Guardrails Hub key,
实测 401)。这里用课程自己写的 CheckCompetitorMentions(真 guardrails Validator,NER+向量相似,
全本地无需 key)——非等价替代,是用课程本身的自定义校验器还原。有 key 者可换 hub 的 CompetitorCheck。

校验 LLM **输出**(默认 on=output):回答里若提到竞品(精确/NER/相似三层任一命中)即抛异常。
用 AsyncGuard:guardrails-api 0.4.x 对同步 Guard 会 to_dict/from_dict 序列化重建,自定义 validator 的构造参数(如 sources)不进序列化契约会丢失且每请求重载模型;AsyncGuard 直接用活实例。

启动:PYTHONPATH=. guardrails start --config config_l8.py --env server.env --port 8000
"""

import os
os.environ.setdefault("OTEL_SDK_DISABLED", "true")  # transformers.utils.metrics 会无条件注册 localhost:4318 OTLP exporter,没起 collector 就刷警告
import sys

# guardrails-api 0.4.x 加载 config 时不会把本目录加进 sys.path,自举以便 import helpers
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from guardrails import AsyncGuard, OnFailAction

from helpers.competitor import CheckCompetitorMentions

competitor_check = AsyncGuard(id="competitor_check", name="competitor_check").use(
    CheckCompetitorMentions(competitors=["Pizza by Alfredo"],
                            on_fail=OnFailAction.EXCEPTION)
)
