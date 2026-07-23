"""L6 guardrails 服务器配置 —— topic_guard(真 guardrails 服务器 + 本地 zero-shot 分类器)。

这**对应课程自带的 local_config.py**:课程 Lesson_6 服务器段给了两种 config——
  - config.py / on_topic_config.py:用 hub 的 `RestrictToTopic`(需 Guardrails Hub key,实测 401)
  - local_config.py:用课程自己写的 `ConstrainTopic`(zero-shot 分类器,无需 key)
这里用**后者**(课程本就提供的本地版),因此是忠实还原、非等价替代;若你有 Hub key,可换用
config.py 里的 RestrictToTopic。

topic_guard 校验**用户输入**(on="messages"):把输入按 zero-shot 分类,命中 banned 话题
(politics / automobiles)即抛异常,off-topic 的问题在进 LLM 之前就被挡下。

用同步 Guard(非 AsyncGuard),原因见 L3 说明(guardrails-api 0.0.1 同步 handler)。

启动:
  PYTHONPATH=. guardrails start --config config_l6.py --env server.env --port 8000
"""

from guardrails import Guard, OnFailAction

from helpers.topic import ConstrainTopic

topic_guard = Guard(name="topic_guard").use(
    ConstrainTopic(
        banned_topics=["politics", "automobiles"],
        on_fail=OnFailAction.EXCEPTION,
    ),
    on="messages",
)
