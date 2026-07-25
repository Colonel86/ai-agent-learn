"""L5 guardrails 服务器配置 —— hallucination_guard(真 guardrails 服务器 + 真 validator)。

⚠️ 关于与课程的唯一偏离(已如实标注,非偷偷替换):
   课程 Part 2 用的是 guardrails **hub** 上的 `ProvenanceLLM` 校验器。但安装它需要
   Guardrails Hub 的注册/付费 API key(`guardrails hub install` 实测返回 401 Unauthorized),
   本环境拿不到。因此这里改用**课程自己在 L4 建的 `HallucinationValidation`**
   (真 guardrails Validator,基于 NLI 的 provenance 检测)跑在**同一个真 guardrails 服务器**上。
   —— 服务器、Guard、guarded client、on_fail 语义全部是真 guardrails;只是把"hub 的 LLM 版
   provenance"换成"课程 NLI 版 provenance"。若你有 Hub key,把本文件的 guard 换成
   `Guard().use(ProvenanceLLM(...))` 即可,其余不变。

这个 guard 校验 **LLM 输出**(默认 on=output):把回答逐句和知识库来源做 NLI 蕴含判定,
有任何一句无出处即判幻觉 → on_fail=EXCEPTION 抛错。

启动:
  guardrails start --config config_l5.py --env server.env --port 8000
"""

import os
import sys

# guardrails-api 0.4.x 加载 config 时不会把本目录加进 sys.path,自举以便 import helpers
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from guardrails import AsyncGuard, OnFailAction

# 复用 L4/本课的 HallucinationValidation(真 guardrails Validator,逐字照课程)
from helpers.hallucination import HallucinationValidation, ensure_punkt
from helpers.rag import chunk_markdown_files

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

ensure_punkt()

# 知识库全文作为 provenance 的来源(校验输出是否有出处)
_DATA_DIR = os.path.join(os.path.dirname(__file__), "shared_data")
SOURCES = chunk_markdown_files(_DATA_DIR)

# 用 AsyncGuard:guardrails-api 0.4.x 对同步 Guard 会 to_dict/from_dict 序列化重建,自定义 validator 的构造参数(如 sources)不进序列化契约会丢失且每请求重载模型;AsyncGuard 直接用活实例。
hallucination_guard = AsyncGuard(id="hallucination_guard", name="hallucination_guard").use(
    HallucinationValidation(
        embedding_model="all-MiniLM-L6-v2",
        entailment_model="GuardrailsAI/finetuned_nli_provenance",
        sources=SOURCES,
        on_fail=OnFailAction.EXCEPTION,
    )
)
