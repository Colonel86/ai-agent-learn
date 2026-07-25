"""L3 guardrails 服务器配置 —— 严格对应课程 config.py 里 L3 实际用到的部分。

L3 这一课的示例代码只用到 colosseum guard(自定义 ColosseumDetector),所以这里只保留:
  - ColosseumDetector 自定义校验器(与课程逐字一致)
  - colosseum_guard      (on_fail=EXCEPTION) —— 命中即抛异常
  - colosseum_guard_2    (on_fail=FIX)       —— 命中则用 fix_value 优雅替换

课程原 config.py 里还有 hallucination/pii/topic/competitor/final 等 guard,那些属于
**L4–L8**、且依赖 guardrails hub 上的模型(需 hub API key + 下载 spacy/PII 模型),不在 L3 的
示例逻辑内,故此处不引入。等做到那几课时再按各自的示例补上。

启动(注意用 guardrails-api 的 CLI,`guardrails start` 封装层在 0.10.2 有 bug,见 README):
  guardrails-api start --config config_l3.py --env server.env --port 8000
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


# 说明:课程原 config.py 用的是 AsyncGuard。0.5.3 时代 guardrails-api 0.0.1 对 AsyncGuard
# 同步调用会直接 500,故当时改成了同步 Guard;0.10.2 + guardrails-api 0.4.3 的 handler 已是
# async(会把同步 Guard 转成 AsyncGuard 执行),同步 Guard 依旧可用,维持不变。
# ColosseumDetector 校验器、on/on_fail 语义、服务器全部保持课程原样。

# 注意:0.10.2 里 Guard.id 默认是随机 UUID,而 guardrails-api 0.4.x 的内存注册表和
# /guards/{id}/openai/v1/... 路由都按 **id** 查找(不按 name 回退),启动横幅却打印
# name 型 URL —— 不显式设 id=name 的话,按 name 访问一律 404。故这里 id 与 name 取同值。

# 一个空 guard(备用)
basic_guard = Guard(id="basic", name="basic")

# 版本 1:命中 colosseum 就抛异常(on_fail=EXCEPTION)
colosseum_guard = Guard(id="colosseum_guard", name="colosseum_guard").use(
    ColosseumDetector(on_fail=OnFailAction.EXCEPTION), on="messages"
)

# 版本 2:命中则用 fix_value 优雅替换,不报错(on_fail=FIX)
colosseum_guard_2 = Guard(id="colosseum_guard_2", name="colosseum_guard_2").use(
    ColosseumDetector(on_fail=OnFailAction.FIX), on="messages"
)
