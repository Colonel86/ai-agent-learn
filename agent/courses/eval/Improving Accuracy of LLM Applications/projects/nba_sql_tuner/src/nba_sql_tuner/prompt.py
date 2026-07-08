"""Llama-3 prompt 模板 —— 对应课程 L1 / util/make_llama_3_prompt.py。

课程 L1 的核心:Llama-3-Instruct 靠特殊 token(<|begin_of_text|>、<|start_header_id|>…)
划分 system/user/assistant。手写这个模板是理解「模型为什么需要固定格式」的第一课,
所以这里忠实保留。

注意:实际调用本地模型时(backend.py),我们改用 tokenizer.apply_chat_template,
这样换任何基座模型(Qwen / Llama)都能自动套对该模型的模板 —— 更鲁棒。
make_llama_3_prompt 保留作为 L1 的教学演示与 Llama 系模型的等价实现。
"""


def make_llama_3_prompt(user: str, system: str = "") -> str:
    """忠实复现课程的 Llama-3 手写模板。"""
    system_prompt = ""
    if system != "":
        system_prompt = (
            f"<|start_header_id|>system<|end_header_id|>\n\n{system}<|eot_id|>"
        )
    return (
        f"<|begin_of_text|>{system_prompt}"
        f"<|start_header_id|>user<|end_header_id|>\n\n{user}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n"
    )


def sql_agent_system(schema: str) -> str:
    """SQL Agent 的 system prompt —— 对应课程 L2/L3 反复用的那段(instruct 模型走 chat 格式用)。"""
    return (
        "You are an NBA analyst with 15 years of experience writing complex SQL "
        "queries. Consider the nba_roster table with the following schema:\n"
        f"{schema}\n"
        "Write a sqlite SQL query that would help you answer the following "
        "question. Make sure the query ends with a semicolon:\n"
    )


# ---- base 模型(无 chat 模板)走的纯文本 few-shot 补全格式 -----------------
# 课程用的是 Llama-3-8B-Instruct(zero-shot 就能出 SQL)。本地退回 base 小模型后,
# zero-shot 完全不出 SQL,必须给 few-shot 示范。
#
# 关键设计:few-shot 示例故意只用「简单查询」(计数 / 按 AGE 排序 / 分组),
# 不示范薪资 REPLACE、体重 SUBSTR 这些技巧 —— 这样 baseline 在硬事实上仍会幻觉
# (对 SALARY 字符串直接排序、用错列),忠实复现课程 L2 的幻觉现场。
FEWSHOT_EXAMPLES = [
    ("How many players are on the Boston Celtics?",
     "SELECT COUNT(*) FROM nba_roster WHERE Team = 'Boston Celtics';"),
    ("Who is the oldest player in the NBA?",
     "SELECT NAME, AGE FROM nba_roster ORDER BY AGE DESC LIMIT 1;"),
    ("How many centers are there in the NBA?",
     "SELECT COUNT(*) FROM nba_roster WHERE POS = 'C';"),
]

_PREAMBLE = (
    "Translate each question into a sqlite query over table "
    "nba_roster(Team, NAME, Jersey, POS, AGE, HT, WT, COLLEGE, SALARY).\n"
    'SALARY is text like "$9,945,830" (null "--"); WT is text like "232 lbs"; '
    "HT is text like `6' 7\"`.\n\n"
)


def plain_prompt(question: str, fewshot: bool = True) -> str:
    """base 模型的纯文本补全 prompt。

    fewshot=True(baseline 用):带 3 个简单示例,让**未微调**的 base 模型也能出 SQL
                               —— 示例只示范简单查询,所以 baseline 在硬事实上仍会幻觉。
    fewshot=False(微调后用):零样本,只有 schema + 问题。微调过的模型已把 Q→SQL 映射
                             背进权重,不需要示例;去掉示例还能避免示例把它往简单/错误答案带,
                             并缩短 prompt、让记忆化更干净(否则长 SQL 会因 exposure bias 崩)。
    训练(finetune._build_examples)用 fewshot=False,和微调后推理完全一致。
    """
    body = _PREAMBLE
    if fewshot:
        for q, sql in FEWSHOT_EXAMPLES:
            body += f"Q: {q}\nSQL: {sql}\n"
    body += f"Q: {question}\nSQL:"
    return body


def plain_fewshot_prompt(question: str) -> str:  # 兼容旧调用
    return plain_prompt(question, fewshot=True)
