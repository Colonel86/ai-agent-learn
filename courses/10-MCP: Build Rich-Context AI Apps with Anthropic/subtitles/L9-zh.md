本节将 MCP 服务端从本地部署改为远程部署，让任何人都可以访问。

---

**服务端改动：切换传输层**

代码本体（工具、资源、提示词模板）完全不变，只需修改启动时的传输层参数：

```python
# 本地
mcp.run(transport="stdio")

# 远程（录制时 Python SDK 尚不支持 Streamable HTTP，使用 SSE）
mcp.run(transport="sse", port=8001)
```

未来 SDK 支持后，切换到 Streamable HTTP 只需改一行参数。

---

**用 Inspector 测试远程服务端**

启动远程服务端后，在 Inspector 中：
- 将传输类型从 Stdio 切换为 **SSE**
- 输入服务端的 SSE URL（如 `http://localhost:8001/sse`）
- 连接后与本地测试体验完全一致，可以列出并调用工具、资源、提示词模板

---

**部署到 Render（云平台）**

**准备文件**

```bash
# 1. 生成 pip 兼容的依赖文件（Render 不支持 uv）
uv pip compile pyproject.toml > requirements.txt

# 2. 指定 Python 版本
echo "python-3.11.11" > runtime.txt

# 3. Git 初始化（排除虚拟环境）
echo ".venv" > .gitignore
git init
git add .
git commit -m "ready for deployment"
```

**推送到 GitHub**

```bash
git remote add origin https://github.com/用户名/remote-research.git
git push origin main
```

**在 Render 配置部署**

1. 登录 render.com → New → Web Service
2. 关联 GitHub 仓库（remote-research）
3. 修改启动命令为：`python research_server.py`
4. 选择免费计划 → Deploy

Render 会自动使用 `runtime.txt` 指定的 Python 版本，并通过 `requirements.txt` 安装依赖。

**验证部署成功**

- 访问根路径 → 预期返回 404（正常）
- 访问 `/sse` 端点 → 返回包含 session ID 的响应 → **部署成功**

部署完成后，这个服务端的 URL 可以在任何 MCP 兼容应用中使用，包括 Claude Desktop、Cursor 等，只需将传输类型设为 SSE 并填入远程 URL 即可。

---

至此，整个 MCP 课程从协议原理、本地开发到远程部署全部串通。我们下节课见。