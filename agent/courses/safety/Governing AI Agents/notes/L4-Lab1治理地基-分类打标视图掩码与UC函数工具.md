# L4 · Lab 1 治理地基：分类打标 → 匿名视图 → Group 权限 → 列掩码 → UC 函数工具

> 课程：Governing AI Agents（DeepLearning.AI × Databricks）
> 本课任务：在 HR 数据集上把治理地基完整搭一遍——建表打分类标签、建 classification-aware 视图、给 devs group 授最小权限、给 SSN 上列掩码，最后把查询封装成 Unity Catalog 函数作为 agent 的工具。

## 0. 本课目标与衔接

L3 定了路线：Manual Authentication——预建 service principal，agent 最终以它的凭证部署。本课就是 Lab 1 实操，产出五件套：

```
① HR 表 + 分类标签 → ② data_analyst_view（匿名化视图） → ③ devs group 最小权限
→ ④ SSN 列掩码 → ⑤ 两个 UC 函数 = agent 的工具
```

## 1. 环境准备：Free Edition + GitHub 联动

- 注册 Databricks Free Edition（链接在课程 reading note），fork 课程 GitHub repo（内含 `data/`、Lab1、Lab3、`agent.py`、README）；
- Settings → Developer 标签 → Link accounts 添加 Git credential，授权 Databricks 访问 GitHub；
- Workspace 里 **Create Git folder**，粘贴 repo 链接，自动识别 provider，代码直接拉进工作区（也可以手动下载 notebook 自建文件夹）；
- 计算资源连 **serverless compute**。

## 2. 创建 Service Principal 与 Devs Group（UI 操作）

在 workspace admin 的 **Identity and access** 页：

**Service Principal**：Add service principal → 命名 `hr_data_analyst`。注意两点：
- 它自带 entitlements（Databricks SQL access、Workspace access），可再加权限；
- UI 会警告：**Service Principal Manager 角色并不自动授予"使用"该 SP 的能力**——需要用它的 users/groups 必须显式授权。所以 Grant access 里给 `hr_data_analyst` 相关主体配 **manage 和 use**（讲师给自己也加了 use）。

**Group**：创建 group `devs`（全体 agent 开发者）。注意：
- 新建的 group 如果不授权、没有父 group，就只是"存在"，**没有任何默认权限**；
- 把 service principal 加入 group——**只给 member access 就够了**，member 即可继承 group 的权限；不想让它改 group 内控制，就把 manage 相关能力编辑删掉。

> **架构师视角**：group 是权限管理的"间接层"。权限授给 group 而不是逐个主体，身份的增删（新开发者入职、新 agent 上线）就不触发权限变更——变更面收敛到"加/移成员"一个操作。这和代码里"依赖接口不依赖实现"是同一个招式：加一层稳定的中间抽象，把 N×M 的授权关系降成 N+M。

## 3. 建 HR 数据：Catalog → Schema → 表

场景设定：公司 `clientcare`，HR 团队的数据库即 schema `hr_data`。先建容器，再灌数据：

```sql
-- 先建 catalog，再建 schema（Unity Catalog 三级命名空间：catalog.schema.table）
CREATE CATALOG IF NOT EXISTS clientcare;
CREATE SCHEMA IF NOT EXISTS clientcare.hr_data;
```

数据是 6 个 CSV：compensation_data（薪酬）、employee_records（员工档案）、hr_cases（HR 案例）、internal_procedures（内部流程）、performance_reviews（绩效）、public_policies（公开政策）。逐个读入并写成 UC 表：

```python
for table_name, file_name in csv_files:
    pdf = pd.read_csv(file_path)              # pandas 读本地 CSV（Spark 要绝对路径，故先用 pandas）
    df = spark.createDataFrame(pdf)           # 转 Spark DataFrame
    df.write.saveAsTable(f"clientcare.hr_data.{table_name}")  # 写入 catalog
```

验证：notebook 里查表 + Catalog UI 里直接能看到 `clientcare → hr_data → 各表`。

展示数据后发现敏感面很大：员工姓名、**完整 SSN**、电话、email、入职日期、薪资……联表 employee_records + compensation_data 一眼看全。HR 数据分析师需要 base salary / bonus / stock options 这些关键数字，但**不应能借此直接定位到具体员工**，更不该看到 email、电话、SSN。

## 4. 数据分类打标（Classification Tags）

给每张表定义分类标签 + 是否含 PII。关键认知：**table properties 是元数据标签**——

- 附着在表上的 metadata key-value 对，**不改变表结构和数据本身**；
- 供治理工具理解数据敏感度；
- **可编程查询**，用于合规检查。

四级分类方案：

| 级别 | 谁能访问 | 示例 |
|---|---|---|
| Public | 任何人 | public_policies |
| Internal | 仅本公司员工 | internal_procedures |
| Confidential | 受限访问 | employee_records（含 PII） |
| Restricted | 高度敏感 | — |

```sql
-- Spark SQL 设置表属性：分类级别 + PII 标记
ALTER TABLE clientcare.hr_data.employee_records
SET TBLPROPERTIES ('classification' = 'confidential', 'contains_pii' = 'true');
```

打完后在 Catalog UI 里点开表即可看到 `Confidential`、`contains PII` 标签。

> **对比 memory 课 12a 的数据层治理**：12a 里治理的是 agent 的**记忆写入侧**——什么该进长期记忆、怎么压实；本课治理的是**数据读取侧**——agent 能读到的数据先分级打标。两边共同的架构判断是：治理动作要落在**数据层的元数据**上（标签/schema），而不是散落在 agent 代码里，这样任何 agent / 任何访问路径都受同一套规则约束。

## 5. Agent 权限设计与 Classification-Aware View

打完标签后，为 HR analytics agent 设计"刚好够用"的访问面——先想清楚不同角色（HR admin / manager / data analyst）各该看到什么。目标行为：

| Agent 应该能回答 | Agent 不应该回答 |
|---|---|
| 薪资分布是什么？ | John Smith 的薪资是多少？ |
| 是否存在 pay equity（薪酬公平）问题？ | 谁是薪资最高的员工？ |
| 绩效与薪酬的相关性？ | 给我看 SSN |

**为什么用 View 做访问控制**（而不是给每类用户堆一套复杂掩码规则）：

- **Purpose-built**：每个视图有清晰的业务目的和目标用户类型；
- **易维护**：视图是优化过的 SQL，无运行时额外开销；
- **额外安全层**：Databricks 里视图充当安全层，权限直接授给 service principal。

`data_analyst_view` 的关键设计（按口播摘录）：

```sql
CREATE OR REPLACE VIEW clientcare.hr_data.data_analyst_view AS
SELECT
  sha2(e.employee_id, 256)  AS anon_id,      -- ① 员工 ID 匿名化
  e.department,
  year(e.hire_date)          AS hire_year,    -- ② 入职日期只留年份（精确日期可反推出人）
  c.base_salary, c.bonus, c.stock_options,    -- ③ 薪酬数字完整保留（分析需要）
  c.comp_year,
  p.rating, p.review_quarter, p.review_year   -- ④ 联表 compensation + performance
FROM employee_records e
JOIN compensation_data c ON ...
JOIN performance_reviews p ON ...
WHERE e.department != 'Legal';                -- ⑤ 排除 Legal 部门（合规要求，分析也不需要）
```

建完后验证三件事：视图确实落在 `clientcare.hr_data` schema 里；行数正常、部门齐全；ID 已匿名、**查不到 Legal**。

## 6. 配置 Group 权限：容器权限 vs 对象权限

devs group 已建好、SP 已入组，现在给 group 授"看数据 + 用 MLflow 注册模型"的最小权限。两类权限要分清（L2 详讲过）：

- **容器权限**（container permissions）：`USE CATALOG` / `USE SCHEMA`——**前置条件，必须显式授予**；
- **对象权限**（object permissions）：授在 schema 上后，schema 内的 table / model / function **自动继承**。

偷懒可以一句 `GRANT ALL` 到 `clientcare.hr_data`，但按最小权限原则逐项授：

```sql
GRANT USE CATALOG ON CATALOG clientcare TO `devs`;        -- 容器：进 catalog
GRANT USE SCHEMA  ON SCHEMA clientcare.hr_data TO `devs`; -- 容器：进 schema
GRANT CREATE TABLE ON SCHEMA clientcare.hr_data TO `devs`; -- 如需把推理日志落 UC 表
GRANT EXECUTE      ON SCHEMA clientcare.hr_data TO `devs`; -- 运行函数（agent 调工具）
GRANT CREATE MODEL ON SCHEMA clientcare.hr_data TO `devs`; -- 注册 agent 到 UC
-- + CREATE MODEL VERSION（注册新版本）
GRANT SELECT ON VIEW clientcare.hr_data.data_analyst_view TO `devs`; -- 只授视图，不授底表
```

验证：`SHOW GRANTS` 查 schema 级和视图级权限——devs 可 use schema、create model/table/version、execute；视图上 devs 有 SELECT。

## 7. 列掩码（Column Masking）：视图之外的强制层

**已经有视图了为什么还要掩码？** 视图可以被绕过——如果用户拿到了**底表的直接访问权**，视图形同虚设。而**表级列掩码由 Unity Catalog 在每一次查询上强制执行，无论数据从哪条路径被访问**，不可绕过。列掩码/行掩码上了之后，什么都穿不过去。

SSN 掩码策略：除 payroll 外没人需要完整 SSN——

```sql
-- 掩码本质是函数（和后面给 agent 的工具函数是同一种东西）
CREATE OR REPLACE FUNCTION ssn_mask(ssn STRING)
RETURN CASE
  WHEN is_account_group_member('devs')
    THEN 'ANALYTICS_MASKED'                        -- devs：什么都看不到
  ELSE CONCAT('*****', RIGHT(ssn, 4))              -- 高权限用户(manager/admin)：前五位星号+后四位真值
END;

-- 把掩码函数绑定到列上（行掩码同理）
ALTER TABLE clientcare.hr_data.employee_records
  ALTER COLUMN social_security_number SET MASK ssn_mask;
```

验证掩码：直接查底表（不走视图），employee_id 还是原始的，但 SSN 前几位已被掩掉——**讲师自己是 admin 也一样被 mask**，除非主动移除掩码。

> **对比 7-safety-guardrails.md（输出护栏 vs 数据层强制）**：选型矩阵 ② 输出护栏在 LLM 输出后**检测** PII 泄漏——它是概率性的、在应用层、可能漏。本课的视图 + 列掩码把同一目标前移到**数据引擎层强制执行**：敏感字段根本进不了 agent 的上下文，泄漏概率降为零。架构排序应当是——能在数据层用确定性机制解决的，不留给 prompt 和输出过滤器兜底；护栏层只兜数据层管不到的部分（如生成内容的语义安全）。

## 8. UC 函数 = Agent 的工具（Secure Tools）

叫 tools、functions 或 skills 都行——本质是**给 agent 建一个查数据的函数，这是 agent 接触数据的唯一通道**。函数是 agent 与受治理数据之间的接口（interface）。

**为什么用 UC 函数做 agent 工具**：

| 特性 | 说明 |
|---|---|
| Governed access | 函数和表/模型一样继承 UC 权限体系 |
| 查询模板化 | 函数即受控的查询模板 |
| 审计轨迹 | 函数调用全部留痕，供合规审查 |
| 性能优化 | 索引/缓存；工具甚至可以背一个向量库 |

工具策略：两个通用函数，**只查匿名化的 `data_analyst_view`**——agent 以 SP 身份部署后，经这两个函数看到的永远是匿名 ID、无 SSN、无 Legal 部门，怎么查都掏不出敏感信息。

```sql
-- 工具① 绩效与留存分析
CREATE OR REPLACE FUNCTION analyze_performance()
COMMENT 'HR analytics: 按部门的基础绩效指标(平均/最高/最低评分、人数、平均在职年限)，只使用匿名数据'
RETURN SELECT department, AVG(rating), MIN(rating), MAX(rating),
              COUNT(*) AS employee_count, AVG(tenure)
       FROM clientcare.hr_data.data_analyst_view   -- 锁死数据源=匿名视图
       GROUP BY department;

-- 工具② 部门与薪酬分析
CREATE OR REPLACE FUNCTION analyze_operations()
COMMENT '部门薪酬与运营指标'
RETURN SELECT department, COUNT(*) AS employee_count,
              AVG(base_salary), AVG(bonus), AVG(total_comp), AVG(stock_options)
       FROM clientcare.hr_data.data_analyst_view
       GROUP BY department;
```

注意 `COMMENT` 直接进入函数元数据，**agent 靠它理解工具用途**（相当于工具描述）。`CREATE OR REPLACE` 保证 notebook 可反复重跑。

测试两个函数：绩效分析按部门出平均评分（没有 Legal、没有可识别信息）；薪酬分析按部门出人数、salary、bonus——**返回薪酬指标和 headcount，但零敏感数据暴露**。

## 9. 本课总结

| 要点 | 一句话 |
|---|---|
| 分类打标 | TBLPROPERTIES 元数据标签，四级分类 + PII 标记，不改数据结构、可编程查询 |
| Classification-aware view | 匿名 ID、日期降精度、保留分析必需数字、排除 Legal——purpose-built 视图即安全层 |
| Group 权限 | 容器权限（USE）须显式授予，对象权限沿 schema 继承；只授 SELECT ON VIEW 不授底表 |
| 列掩码 | 视图可被直接访问底表绕过，列掩码由 UC 在每次查询强制执行，admin 也不例外 |
| UC 函数工具 | agent 接触数据的唯一通道；锁死匿名视图；COMMENT 即工具描述；调用全留痕 |

> **记忆点（引出 L5）**：治理地基五件套齐了——标签、视图、权限、掩码、工具函数，agent 的数据通道已经"焊死"。但 agent 本体还没影子。L5 讲怎么把 agent 建出来并做 production-ready：评估方法（code-based / LLM-as-judge / human-in-the-loop）、MLflow tracing 与 logging、ResponsesAgent 统一接口，以及为什么最终要以 service principal 身份部署、部署完还要套 AI Gateway。

## 与我的资产映射

- 安全层：`agent/skills/agent-selection/7-safety-guardrails.md`（数据层确定性强制 vs 应用层概率性护栏的分工——本课是"最小权限 + 数据不出库"的最佳实例）
- 工具层：`agent/skills/agent-selection/4-tools.md`（"工具即受治理的查询模板"是工具网关之外的另一种收口方式：把治理下沉到目录服务）
- 记忆/数据层：memory 课 12a `L2-Memory-Manager与记忆存储.md`（数据层治理视角互补：写入侧 vs 读取侧）
- 面试包：`07-safety-guardrails`（列掩码不可绕过 vs 视图可绕过，是"纵深防御"的好例子）、`02-tool-gateway-auth-and-contract.md`（UC 函数 = 带权限与审计的工具契约）
- [[project_selection_matrix]]
