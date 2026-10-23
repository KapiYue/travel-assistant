# TaskFlow AI · 个人旅行助手

TaskFlow AI 是一个面向个人使用的 AI 旅行助手。它会把自然语言旅行需求转换为可校验的数据，逐步协助用户补齐信息、生成可编辑的行程草案，并在接入可靠数据源后提供天气、路线和目的地资料等参考。

项目采用“固定工作流负责主流程、局部 Agent 负责理解和工具选择”的方式。没有可靠外部数据支持的内容，只会标记为草案、推荐或估算，不会伪装成已确认的事实或预订结果。

## 当前进度

当前正在实现旅行助手的第一个正式闭环：**旅行需求提取**。

```text
自然语言旅行需求
  → Structured Output
  → Pydantic 校验
  → 缺失字段清单
```

此阶段只提取用户已明确表达的信息，不会猜测日期、人数、预算或偏好；暂不生成行程，也不调用天气、路线或价格等实时工具。完整任务范围和验收样例见 [current-task.md](current-task.md)。

## 本地开发

项目支持 **Python 3.11**。请使用该版本创建并激活虚拟环境：`python3.11 -m venv .venv && source .venv/bin/activate`。

1. 创建并激活虚拟环境。
2. 安装依赖：`python -m pip install -r requirements.txt`。
3. 复制 `.env.example` 为 `.env`，按所使用的模型服务填写 `DATA_API_KEY`、`DATA_MODEL`；若服务兼容 OpenAI API，可按需填写 `DATA_BASE_URL`。

`.env` 只保留在本机，绝不能提交真实密钥。请始终从 `.env.example` 获取所需变量名称。

## 依赖与自动检查

- `requirements.txt` 是日常开发时维护的依赖范围。
- `requirements.lock` 锁定了当前 Python 3.11 环境的精确依赖版本。部署或多人协作时使用：`python -m pip install -r requirements.lock`。
- 有意升级依赖时，先在 Python 3.11 环境中更新 `requirements.txt` 所列依赖，再重新生成并提交 `requirements.lock`，同时运行检查。

每次推送及拉取请求都会自动执行 Python 编译检查和离线测试；工作流配置位于 `.github/workflows/ci.yml`。

## 仓库范围

这个仓库只保存旅行助手的正式代码、可复用的前端原型、配置模板、测试和与产品直接相关的说明。Python、LangChain/LangGraph、天气 Agent 和 RAG 等单项练习资料保留在本地工作区，但通过 `.gitignore` 排除，不会进入 GitHub。

```text
backend/
  travel_assistant/      # 正式旅行助手后端（逐步建立）
frontend/prototype/      # 旅行助手交互原型
docs/                    # 产品与技术说明
tests/                   # 正式模块的离线测试
.env.example             # 不含密钥的配置模板
current-task.md          # 当前阶段任务与验收标准
```

## 约定

- 所有外部实时事实都应记录来源与状态；查询失败时明确说明，不能生成貌似真实的结果。
- 模型负责理解和提取；字段校验、缺失判断与流程控制由程序完成。
- 新能力应同时补充离线测试和说明，并在完成后更新 `current-task.md`。
- 提交前检查：不包含 `.env`、密钥、虚拟环境、缓存、生成的索引或仅供学习的练习资料。

更多项目原则见 [AGENT.md](AGENT.md)。

本项目采用 [MIT License](LICENSE)。
