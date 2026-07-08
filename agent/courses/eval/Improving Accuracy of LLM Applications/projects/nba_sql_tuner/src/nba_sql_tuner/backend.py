"""LLM 后端适配层 —— 把课程的 lamini.Lamini 换成本地 HF transformers。

课程:llm = lamini.Lamini(model_name=...); llm.generate(prompt, output_type=...)
本地:LLM(base_model, adapter=None).sql(system, user) / .chat(system, user)

设计要点:
  - 用 tokenizer.apply_chat_template,换任何基座(Qwen/Llama)都自动套对模板。
  - adapter 参数指向一个 LoRA 目录 —— 这就是「加载 fine-tune / memory-tune 后的模型」,
    对应课程里 lamini.Lamini(model_name="<tuned-model-id>") 那一步。
  - 已加载模型按 (base, adapter) 缓存,避免评估时反复加载。
  - 评估要可复现,所以默认贪心解码 (do_sample=False)。
"""
from __future__ import annotations

import re
from functools import lru_cache

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from . import config


@lru_cache(maxsize=8)
def _load(base_model: str, adapter: str | None):
    tok = AutoTokenizer.from_pretrained(base_model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        base_model, dtype=torch.float32
    )
    if adapter:
        model = PeftModel.from_pretrained(model, adapter)
        model = model.merge_and_unload()  # 合并权重,推理更快
    model.to(config.device())
    model.eval()
    return tok, model


class LLM:
    """一个已加载的模型(可选带 LoRA adapter)。"""

    def __init__(self, base_model: str | None = None, adapter: str | None = None):
        self.base_model = base_model or config.DEFAULT_BASE_MODEL
        self.adapter = str(adapter) if adapter else None
        self.name = self.adapter or self.base_model

    def is_base(self) -> bool:
        """base 模型(无 chat 模板)走 few-shot 纯文本补全;instruct 走 chat。"""
        tok, _ = _load(self.base_model, self.adapter)
        return tok.chat_template is None

    def _gen(self, ids, max_new_tokens: int):
        tok, model = _load(self.base_model, self.adapter)
        with torch.no_grad():
            out = model.generate(
                ids, max_new_tokens=max_new_tokens, do_sample=False,
                temperature=None, top_p=None, pad_token_id=tok.pad_token_id,
            )
        return tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)

    def chat(self, system: str, user: str, max_new_tokens: int = 300) -> str:
        """instruct 模型:走 chat 模板(课程的方式)。"""
        tok, model = _load(self.base_model, self.adapter)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        ids = tok.apply_chat_template(
            messages, add_generation_prompt=True, return_tensors="pt",
            return_dict=True,
        )["input_ids"].to(model.device)
        return self._gen(ids, max_new_tokens).strip()

    def complete(self, prompt_text: str, max_new_tokens: int = 80) -> str:
        """base 模型:纯文本补全。"""
        tok, model = _load(self.base_model, self.adapter)
        ids = tok(prompt_text, return_tensors="pt").input_ids.to(model.device)
        return self._gen(ids, max_new_tokens)

    def sql(self, system: str, user: str, max_new_tokens: int = 300) -> str:
        """生成并抽取一条 SQL —— 对应课程的 output_type={'sqlite_query': 'str'}。
        system 参数为兼容课程接口保留;base 模型实际用 few-shot 纯文本 prompt。"""
        from .prompt import plain_prompt
        if self.is_base():
            # 每个模型都在它「该有的工作点」上评估:
            #   baseline(无 adapter)必须靠 few-shot 示例才出 SQL —— prompt 拐杖;
            #   微调后的模型(有 adapter)已把 Q→SQL 映射内化,走零样本(也更省 token,
            #   且不被 few-shot 的简单示例带偏)。这才是部署时的真实用法。
            fewshot = self.adapter is None
            raw = self.complete(plain_prompt(user, fewshot=fewshot), max_new_tokens=80)
        else:
            raw = self.chat(system, user, max_new_tokens=max_new_tokens)
        return extract_sql(raw)


def extract_sql(text: str) -> str:
    """从模型输出里抽出 SQL。课程用 Lamini 的结构化输出直接拿到 SQL 字段;
    本地模型返回自由文本,这里做鲁棒抽取:优先 ```sql``` 代码块,否则找第一个 SELECT。"""
    # 1) ```sql ... ``` 或 ``` ... ``` 代码块
    m = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        text = m.group(1)
    # 2) 从第一个 SELECT/WITH 截到分号(含)
    m = re.search(r"(SELECT|WITH)\b.*?;", text, re.DOTALL | re.IGNORECASE)
    if m:
        return " ".join(m.group(0).split())
    # 3) 兜底:从第一个 SELECT/WITH 到结尾
    m = re.search(r"(SELECT|WITH)\b.*", text, re.DOTALL | re.IGNORECASE)
    if m:
        return " ".join(m.group(0).split()).rstrip(";") + ";"
    return text.strip()
