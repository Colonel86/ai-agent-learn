# flake8: noqa

# Import the module so its @register_function decorators run and register all five tools
from . import climate_analyzer

# ---------------------------------------------------------------------------
# Shim(2026-07):让 DeepSeek 能当 ragas 裁判。
# NAT 的 NatLangChainRagasLLMAdapter 调 with_structured_output() 走默认 method
# (ChatOpenAI 默认 json_schema),DeepSeek 不支持该 response_format → 判分全部
# 400 → 分数静默落 0。DeepSeek 支持 function_calling(需非思考模式,配合
# extra_body: {"thinking": {"type": "disabled"}})。这里把 ChatOpenAI 系的判分
# 调用改走 function_calling;其他 LLM(如 ChatNVIDIA)不受影响。
# NAT 若日后支持配置 method,删除本段即可。
# ---------------------------------------------------------------------------
try:
    from nat.plugins.ragas.rag_evaluator import llm_adapter as _ragas_llm_adapter

    _orig_structured_llm = _ragas_llm_adapter.NatLangChainRagasLLMAdapter._structured_llm

    def _structured_llm_function_calling(self, response_model):
        llm = self._langchain_llm
        if llm.__class__.__name__ == "ChatOpenAI":
            return llm.with_structured_output(response_model, method="function_calling")
        return _orig_structured_llm(self, response_model)

    _ragas_llm_adapter.NatLangChainRagasLLMAdapter._structured_llm = _structured_llm_function_calling
except ImportError:
    pass  # ragas 插件未安装的环境(如仅跑 nat run)不需要该补丁
