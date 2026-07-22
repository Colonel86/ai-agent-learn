"""L3 guardrails 服务器配置 —— 严格对应课程 config.py 里 L3 实际用到的部分。

L3 这一课的示例代码只用到 colosseum guard(自定义 ColosseumDetector),所以这里只保留:
  - ColosseumDetector 自定义校验器(与课程逐字一致)
  - colosseum_guard      (on_fail=EXCEPTION) —— 命中即抛异常
  - colosseum_guard_2    (on_fail=FIX)       —— 命中则用 fix_value 优雅替换

课程原 config.py 里还有 hallucination/pii/topic/competitor/final 等 guard,那些属于
**L4–L8**、且依赖 guardrails hub 上的模型(需 hub API key + 下载 spacy/PII 模型),不在 L3 的
示例逻辑内,故此处不引入。等做到那几课时再按各自的示例补上。

启动:
  guardrails start --config config_l3.py
"""

from typing import Any, Dict

from guardrails import Guard, OnFailAction
from guardrails.validator_base import (
    FailResult,
    PassResult,
    ValidationResult,
    Validator,
    register_validator,
)


@register_validator(name="detect_colosseum", data_type="string")
class ColosseumDetector(Validator):
    def _validate(self, value: Any, metadata: Dict[str, Any] = {}) -> ValidationResult:
        if "colosseum" in value.lower():
            return FailResult(
                error_message="Colosseum detected",
                fix_value="I'm sorry, I can't answer questions about Project Colosseum (via server).",
            )
        return PassResult()


# 说明:课程原 config.py 用的是 AsyncGuard。但 guardrails-api 0.0.1 的非流式
# /openai/v1/chat/completions handler 是**同步**调用 `guard(**payload)` 后立刻读
# `guard.history.last`——对 AsyncGuard 同步调用只会拿到协程、不执行、history 为 None,
# 直接 500(这是该 pinned 版本的一个已知 bug)。改用同步 Guard 即可正常跑通;
# ColosseumDetector 校验器、on/on_fail 语义、服务器全部保持课程原样,仅换 Guard 类型。

# 一个空 guard(备用)
basic_guard = Guard(name="basic")

# 版本 1:命中 colosseum 就抛异常(on_fail=EXCEPTION)
colosseum_guard = Guard(name="colosseum_guard").use(
    ColosseumDetector(on_fail=OnFailAction.EXCEPTION), on="messages"
)

# 版本 2:命中则用 fix_value 优雅替换,不报错(on_fail=FIX)
colosseum_guard_2 = Guard(name="colosseum_guard_2").use(
    ColosseumDetector(on_fail=OnFailAction.FIX), on="messages"
)
