"""L8 guardrails 服务器配置 —— competitor_check(真 guardrails 服务器 + 本地 NER validator)。

对应课程 config.py 的 competitor_check,但课程用 hub 的 CompetitorCheck(需 Guardrails Hub key,
实测 401)。这里用课程自己写的 CheckCompetitorMentions(真 guardrails Validator,NER+向量相似,
全本地无需 key)——非等价替代,是用课程本身的自定义校验器还原。有 key 者可换 hub 的 CompetitorCheck。

校验 LLM **输出**(默认 on=output):回答里若提到竞品(精确/NER/相似三层任一命中)即抛异常。
同步 Guard(非 AsyncGuard),原因见 L3。

启动:PYTHONPATH=. guardrails start --config config_l8.py --env server.env --port 8000
"""

from guardrails import Guard, OnFailAction

from helpers.competitor import CheckCompetitorMentions

competitor_check = Guard(name="competitor_check").use(
    CheckCompetitorMentions(competitors=["Pizza by Alfredo"],
                            on_fail=OnFailAction.EXCEPTION)
)
