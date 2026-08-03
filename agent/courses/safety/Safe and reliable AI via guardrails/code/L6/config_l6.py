"""L6 guardrails 服务器配置 —— topic_guard(真 guardrails 服务器 + 本地 zero-shot 分类器)。

这**对应课程自带的 local_config.py**:课程 Lesson_6 服务器段给了两种 config——
  - config.py / on_topic_config.py:用 hub 的 `RestrictToTopic`(需 Guardrails Hub key,实测 401)
  - local_config.py:用课程自己写的 `ConstrainTopic`(zero-shot 分类器,无需 key)
这里用**后者**(课程本就提供的本地版),因此是忠实还原、非等价替代;若你有 Hub key,可换用
config.py 里的 RestrictToTopic。

topic_guard 校验**用户输入**(on="messages"):把输入按 zero-shot 分类,命中 banned 话题
(politics / automobiles)即抛异常,off-topic 的问题在进 LLM 之前就被挡下。

用 AsyncGuard:guardrails-api 0.4.x 对同步 Guard 会 to_dict/from_dict 序列化重建,自定义 validator 的构造参数(如 sources)不进序列化契约会丢失且每请求重载模型;AsyncGuard 直接用活实例。

启动:
  PYTHONPATH=. guardrails start --config config_l6.py --env server.env --port 8000
"""

import os
os.environ.setdefault("OTEL_SDK_DISABLED", "true")  # transformers.utils.metrics 会无条件注册 localhost:4318 OTLP exporter,没起 collector 就刷警告
import sys

# guardrails-api 0.4.x 加载 config 时不会把本目录加进 sys.path,自举以便 import helpers
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from guardrails import AsyncGuard, OnFailAction

from helpers.topic import ConstrainTopic

topic_guard = AsyncGuard(id="topic_guard", name="topic_guard").use(
    ConstrainTopic(
        banned_topics=["politics", "automobiles"],
        on_fail=OnFailAction.EXCEPTION,
    ),
    on="messages",
)
