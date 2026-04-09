# MyAgent

基于 Python 的简单对话 Agent：使用 **LangChain + OpenAI 兼容 API** 调用大模型，支持 **命令行交互** 与 **HTTP 服务**（FastAPI）。

## 环境要求

- Python 3.10+（推荐）
- 可用的对话 API：OpenAI、DeepSeek、通义等兼容接口，或本地 [Ollama](https://ollama.com/)

## 安装

```bash
cd MyAgent
pip install -r requirements.txt
```

建议使用虚拟环境：

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## 配置（`.env`）

在项目根目录创建 `.env`（不要提交到 Git，仓库已配置忽略）。常用变量如下：

| 变量 | 说明 |
|------|------|
| `OPENAI_API_KEY` | API 密钥（必填，除非仅用本地 Ollama 且已设置 `OPENAI_BASE_URL`） |
| `OPENAI_BASE_URL` | 可选。自定义接口地址，例如 Ollama：`http://localhost:11434/v1` |
| `OPENAI_MODEL` | 可选。模型名，默认 `gpt-4o-mini`（需与服务商提供的名称一致） |

**OpenAI 官方示例：**

```env
OPENAI_API_KEY=sk-xxxxxxxx
```

**本地 Ollama 示例：**

```env
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.2
OPENAI_API_KEY=ollama
```

（仅 `OPENAI_BASE_URL`、无密钥时，程序会使用占位密钥，便于连接本地服务。）

**其他兼容服务商：** 在其控制台创建 Key，并查阅文档填写正确的 `OPENAI_BASE_URL` 与 `OPENAI_MODEL`。

---

## 方式一：命令行对话

```bash
python agent.py
```

- 输入内容后回车发送，多轮连续对话。
- 输入 `quit`、`exit` 或 `q` 退出。
- 输入 `/reset` 清空当前对话历史（保留系统提示）。

---

## 方式二：HTTP 接口

### 启动服务

```bash
python server.py
```

默认监听 `0.0.0.0:8000`。可通过环境变量修改：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HOST` | `0.0.0.0` | 监听地址 |
| `PORT` | `8000` | 端口 |
| `CORS_ORIGINS` | `*` | 跨域来源，多个用英文逗号分隔，如 `https://a.com,https://b.com` |

示例：

```bash
set HOST=127.0.0.1
set PORT=8080
python server.py
```

### 接口说明

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查，返回 `{"status":"ok"}` |
| POST | `/v1/chat` | 发送一条用户消息，返回模型回复与会话 ID |
| POST | `/v1/chat/reset` | 按会话 ID 清空该路对话历史 |

**POST `/v1/chat`**

请求体（JSON）：

```json
{
  "message": "你好",
  "session_id": null
}
```

- `message`：必填，用户输入。
- `session_id`：可选。不传则**新建会话**；多轮对话时把**上一次响应里的 `session_id`** 原样带回。

响应示例：

```json
{
  "reply": "你好！有什么可以帮你？",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**POST `/v1/chat/reset`**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

若 `session_id` 不存在，返回 HTTP 404。

调用大模型失败时，接口返回 **502**，`detail` 中为错误信息（例如余额不足、模型名错误等）。

### 在线文档

服务启动后浏览器访问：

- Swagger UI：`http://127.0.0.1:8000/docs`
- ReDoc：`http://127.0.0.1:8000/redoc`

### curl 示例

```bash
curl http://127.0.0.1:8000/health

curl -X POST http://127.0.0.1:8000/v1/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"用一句话介绍 Python\"}"
```

（Linux / macOS 将 `^` 换为 `\` 并调整引号即可。）

---

## 在代码中调用

```python
from agent import ChatAgent

agent = ChatAgent(
    model="gpt-4o-mini",
    system_prompt="你是一个简洁的编程助手。",
)
print(agent.reply("什么是列表推导式？"))
agent.reset()
```

## LangChain 能力说明

- `PromptTemplate`：使用 `ChatPromptTemplate + MessagesPlaceholder` 统一系统提示与上下文拼装。
- `Memory`：使用 `ConversationBufferMemory` 保存多轮对话历史；`/v1/chat/reset` 或 `agent.reset()` 可清空。
- `Tools`：内置一个工具，模型可按需自动调用：
  - `get_current_time`：返回本地当前时间

---

## 项目结构

| 文件 | 说明 |
|------|------|
| `agent.py` | `ChatAgent` 与命令行入口 |
| `server.py` | FastAPI HTTP 服务 |
| `requirements.txt` | Python 依赖 |
| `.gitignore` | 忽略 `.env`、虚拟环境等 |

---

## 常见问题

1. **提示未配置 `OPENAI_API_KEY`**  
   检查项目目录下是否有 `.env`，且其中包含密钥或（仅本地）`OPENAI_BASE_URL`。

2. **HTTP 402 / Insufficient Balance**  
   账户余额或额度不足，需在对应平台充值或更换 Key。

3. **Windows 终端中文乱码**  
   可先执行 `chcp 65001` 再运行，或使用 Windows Terminal，并确认终端字体支持中文。

4. **会话仅存于内存**  
   HTTP 模式下的对话保存在进程内存中，重启服务后 `session_id` 会失效，需重新对话。

---

## 许可证

按仓库维护者约定为准；若未指定，以项目根目录许可证文件为准。
