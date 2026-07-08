"""微调闭环:标准 fine-tuning vs memory tuning —— 对应课程 L4/L5,也是本项目的核心。

课程 L4 讲清了区别,L5 把微调派发到 Lamini 服务器(本地无法复现)。这里用 LoRA 在一个
小模型上「真跑」两种训练,让你亲眼看到行为差异:

  finetune(标准):低 rank、少 epoch、带 dropout、只调注意力投影、带正则。
                  学到的是「SQL 风格/泛化」,单条事实 loss 压不到 0 → 硬事实仍会糊。

  memory  (记忆):高 rank、多 epoch、无 dropout、调所有线性层、激进 LR。
                  故意把训练 loss 打到 ~0,把 gold 事实「背」进权重 → 训练过的事实近乎零幻觉。
                  这就是 Lamini「memory tuning(MoME)」在行为层的本质:per-fact loss → 0。

为什么手写训练循环而不用 TRL:
  1) 不吃 TRL/transformers 版本 API 变动;
  2) 直接记录每步 loss → 能画出「memory tuning 把 loss 打到 0」的曲线(这就是要展示的东西);
  3) 完全控制 completion-only 掩码(只在 SQL 答案上算 loss,不在 prompt 上)。
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

from . import config
from .prompt import sql_agent_system, plain_prompt
from .schema import get_updated_schema


@dataclass
class Preset:
    name: str
    r: int
    alpha: int
    dropout: float
    epochs: int
    lr: float
    target_modules: list[str]
    note: str


FINETUNE = Preset(
    name="finetune", r=8, alpha=16, dropout=0.05, epochs=5, lr=2e-4,
    target_modules=["q_proj", "v_proj"],
    note="标准 fine-tuning:低 rank/少 epoch/只调注意力/带 dropout,loss 停在平台、不背具体事实",
)
MEMORY = Preset(
    name="memory", r=32, alpha=64, dropout=0.0, epochs=15, lr=1e-4,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    note="memory tuning:高 rank/多 epoch/无 dropout/调所有线性层,把 loss 逼到 0、背进事实",
)
PRESETS = {"finetune": FINETUNE, "memory": MEMORY}


def _build_examples(tokenizer, rows: list[dict]) -> list[dict]:
    """把 {question, sql} 变成 (input_ids, labels),labels 对 prompt 部分掩 -100
    (completion-only:只在 SQL 答案上算 loss)。"""
    is_base = tokenizer.chat_template is None
    system = sql_agent_system(get_updated_schema())
    examples = []
    for r in rows:
        if is_base:
            # base 模型:零样本 prompt(与「微调后推理」一致)。答案前留一个空格对齐 "SQL: "。
            prompt_text = plain_prompt(r["question"], fewshot=False)
            prompt_ids = tokenizer(prompt_text, return_tensors="pt")["input_ids"][0]
            answer = " " + r["sql"].strip()
        else:
            msgs = [{"role": "system", "content": system},
                    {"role": "user", "content": r["question"]}]
            prompt_ids = tokenizer.apply_chat_template(
                msgs, add_generation_prompt=True, return_tensors="pt",
                return_dict=True)["input_ids"][0]
            answer = r["sql"].strip()
        answer_ids = tokenizer(answer + tokenizer.eos_token,
                               add_special_tokens=False, return_tensors="pt")["input_ids"][0]
        input_ids = torch.cat([prompt_ids, answer_ids])
        labels = input_ids.clone()
        labels[:len(prompt_ids)] = -100  # 掩掉 prompt,只学答案
        examples.append({"input_ids": input_ids, "labels": labels})
    return examples


def train(preset_name: str, data_path: str | None = None,
          base_model: str | None = None, verbose: bool = True) -> dict:
    preset = PRESETS[preset_name]
    base_model = base_model or config.DEFAULT_BASE_MODEL
    data_path = data_path or str(config.TRAINING_DATA / "generated_queries.jsonl")
    device = config.train_device()  # 默认 CPU:MPS 长训练会拖崩整机(见 config 注释)

    with open(data_path) as f:
        rows = [json.loads(line) for line in f]

    tok = AutoTokenizer.from_pretrained(base_model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    # base 模型(chat_template is None)走 _build_examples 里的 few-shot 纯文本分支,
    # 不需要 chat 模板;instruct 模型自带模板。
    model = AutoModelForCausalLM.from_pretrained(base_model, dtype=torch.float32)

    lora = LoraConfig(
        r=preset.r, lora_alpha=preset.alpha, lora_dropout=preset.dropout,
        target_modules=preset.target_modules, task_type="CAUSAL_LM", bias="none",
    )
    model = get_peft_model(model, lora)
    model.to(device)
    model.train()

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    if verbose:
        print(f"[{preset.name}] {preset.note}")
        print(f"[{preset.name}] base={base_model} device={device} "
              f"可训练参数={trainable:,} 样本={len(rows)} epochs={preset.epochs}")

    examples = _build_examples(tok, rows)
    opt = torch.optim.AdamW(
        (p for p in model.parameters() if p.requires_grad), lr=preset.lr)

    loss_history = []  # 每 epoch 平均 loss —— 这就是要展示的曲线
    t0 = time.time()
    for epoch in range(preset.epochs):
        torch.manual_seed(epoch)
        order = torch.randperm(len(examples))
        epoch_loss = 0.0
        for idx in order:
            ex = examples[idx]
            input_ids = ex["input_ids"].unsqueeze(0).to(device)
            labels = ex["labels"].unsqueeze(0).to(device)
            out = model(input_ids=input_ids, labels=labels)
            loss = out.loss
            loss.backward()
            # 梯度裁剪:memory 预设 LR 高、rank 大、调所有层,不裁剪会在长训练里发散
            # (实测 MPS float32 下会 loss 冲到两位数再塌成 NaN/退化)
            torch.nn.utils.clip_grad_norm_(
                (p for p in model.parameters() if p.requires_grad), max_norm=1.0)
            opt.step()
            opt.zero_grad()
            epoch_loss += loss.item()
        avg = epoch_loss / len(examples)
        loss_history.append(round(avg, 4))
        if verbose and (epoch % max(1, preset.epochs // 10) == 0 or epoch == preset.epochs - 1):
            print(f"  epoch {epoch+1:2d}/{preset.epochs}  loss={avg:.4f}")

    # 保存 adapter
    outdir = config.ADAPTERS / preset.name
    outdir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(outdir)
    tok.save_pretrained(outdir)

    summary = {
        "preset": asdict(preset),
        "base_model": base_model,
        "n_examples": len(rows),
        "trainable_params": trainable,
        "loss_history": loss_history,
        "final_loss": loss_history[-1],
        "seconds": round(time.time() - t0, 1),
        "adapter_dir": str(outdir),
    }
    with open(outdir / "train_summary.json", "w") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    if verbose:
        print(f"[{preset.name}] 完成:final loss={loss_history[-1]}  "
              f"用时 {summary['seconds']}s  -> {outdir}\n")
    return summary
