# L07 Jupyter Notebook 重构 → Streamlit Dashboard

> 原始字幕：`subtitles/L7-eng.vtt`
> 实战：把一份混乱的 e-commerce notebook **重构** + **迁移成 web dashboard**

---

## 一、起点：典型的"乱 notebook"

常见痛点：
- 业务逻辑和展示代码全杂在 cell 里
- 多次 `pd.read_csv`、重复 merge
- 硬编码年份（"2023 vs 2022"）
- 警告满屏，可视化粗糙
- 想换个时间窗就要改十几处

> Claude Code 对 notebook 有**专门的 read/edit 工具**（不是按文本读 cell），能精准定位 cell。

---

## 二、重构 prompt 的写法

不要只说"refactor this notebook"。给清晰的 **目标产物清单**：

```markdown
Refactor @ecommerce_analysis.ipynb @ecommerce_data/

Structure requirements:
- Separate Python file for data loading & processing
- Separate Python file for business metrics calculation
- Improved visualizations (use plotly, hover info, ...)
- Configurable analysis (year, comparison year, month)
- requirements.txt
- README

Code quality:
- Type hints, docstrings
- ...
```

> Tip：**不确定怎么写好 prompt 时，问 Claude 帮你写 prompt**。把目标讲给 Claude AI / Claude Code，让它生成"最佳 prompt"。

---

## 三、重构后的产物

```
data_loader.py          ← CSV 读取 + 清洗（OO 风格）
business_metrics.py     ← 指标计算类（输入 df，输出 df + 可视化）
ecommerce_analysis_refactored.ipynb
requirements.txt
README.md
```

收益：
- Notebook 只剩"调用 + 展示"
- 业务逻辑可被**单测覆盖**
- 改 config 顶部常量就能切换分析窗口

---

## 四、调试重构产物

跑 cell 出 `KeyError` —— 直接把代码贴回 Claude：

```text
I'm getting KeyError when I run this cell: [paste code]
```

Claude 读 → 改 → 再跑 ✅。

> 给 context 越具体，Claude 修得越准。复制错误代码 + 错误堆栈 > 仅说"报错了"。

---

## 五、从 Notebook 到 Streamlit Dashboard

### 5.1 prompt 模板（写成 `convert-to-dashboard.md`）

具体到布局：

```markdown
Convert @ecommerce_analysis_refactored.ipynb into a Streamlit dashboard.

Layout:
- Header: title + year filter
- KPI row: revenue / growth / AOV / total orders
- Charts: revenue trend, category, by state (map), satisfaction (bar)
- Bottom row: 2 cards

Specifics:
- Use plotly for charts
- ...
```

### 5.2 启动 + 装依赖

```bash
pip install -r requirements.txt
streamlit run dashboard.py
```

### 5.3 迭代式修正

观察实际效果，发现：
- 默认显示 2024 → 数据不全 → 改 2023
- 多余的空 card
- 缺月份过滤器

把这些反馈一次性丢回 Claude：

```text
The default year should be 2023.
Add filters for months as well.
Remove the empty cards.
```

→ 一轮修复完成。

---

## 六、架构师视角

- **业务逻辑 / 展示分离**是 notebook 长期维护的核心模式。一旦分离，notebook 和 Streamlit 共用一套 `*_metrics.py`、`data_loader.py`，两端零迁移成本。
- **Claude 给的 prompt 越具体（含布局、库、产物清单），输出质量越接近一次成型**。"模糊 prompt → 反复改"是新手最常见的 Claude 反模式。
- **Streamlit / dashboard 是"分析 → 产品"的最低成本路径**——把你的分析洞察从 notebook 推给同事/上级，几小时即可上线 demo。

---

## 七、要点速记

- Claude Code 对 notebook 有**专用工具**，不是当文本搞。
- 重构 prompt 要写**产物清单 + 结构要求 + 质量要求**三段式。
- 出错时把错误代码片段贴回 Claude，定位最快。
- 业务逻辑抽 `.py`、展示留 notebook / dashboard——同一份逻辑双端复用。
- 写不好 prompt 时，问 Claude 帮你写。
