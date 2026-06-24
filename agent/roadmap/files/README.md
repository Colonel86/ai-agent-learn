# nfr-standard — 已迁出为独立仓

这套「AI-Agent NFR 标准」(建立在 spec-kit 之上、可强制执行的非功能性需求标准)已从本学习仓抽出，成为独立可复用仓，作为**唯一真源**：

- **GitHub**：https://github.com/Colonel86/nfr-standard （private）
- **本地**：`~/projects/nfr-standard`

## 为什么迁出

- 它属于「可执行工具叠加层」——会安装/校验/门控**别的** repo，需要独立的地址 + 版本 + 升级路径。
- 留在学习仓会与独立仓形成两处真源、必然漂移。
- 迁出顺带修了一个坑：原来 `.claude/` 被全局 `.gitignore` 忽略，导致 `nfr-architect` skill 没进版本控制；独立仓里它已纳入跟踪。

## 怎么用（装进某个项目）

```bash
# 在目标 repo 根目录执行，或显式传目标路径；非破坏，不覆盖已存在文件
bash ~/projects/nfr-standard/install.sh                 # 装进当前目录
bash ~/projects/nfr-standard/install.sh /path/to/repo   # 装进指定 repo
```

模型是「文件即真源」：真源在独立仓的 `template/` 下，`install.sh` 只负责把它们投影进目标 repo。详见独立仓的 `README.md` 与 `CHANGELOG.md`。
