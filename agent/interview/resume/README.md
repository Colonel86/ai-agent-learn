# 简历维护

## 单一事实源

**`resume.md` 是简历的源文件**，所有改动先改这里，git 记录每次变更。

三个载体的关系：

| 载体 | 角色 | 更新方式 |
|---|---|---|
| `resume.md`（本目录） | 源文件，git 版本化 | 直接编辑 |
| https://cv.ha7ch.com/colonel | 线上可分享版 | 改完 md 后让 Claude 经 cv MCP 同步 |
| PDF | 投递用导出产物，**不作为编辑对象** | 从招聘平台或线上版导出，投递归档存 `archive/` |

## 归档约定

投递用过的 PDF 按日期存 `archive/`（如 `archive/2026-08-耿明-AI Agent.pdf`），
保留"当时投出去的是哪一版"的记录；平时不要直接改 PDF。

## 定向变体

针对具体 JD 的定制版不复制 md 文件，用线上 variant 机制（`?company=` / `?role=` 参数），
JD 放 `../jd/` 目录，让 Claude 基于 resume.md + JD 生成 variant。
