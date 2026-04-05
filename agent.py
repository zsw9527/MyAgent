"""
简单对话 Agent：调用 OpenAI 兼容 API，在终端多轮聊天。
"""
from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI




def _client() -> OpenAI:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL") or None
    if not api_key and not base_url:
        here = os.path.dirname(os.path.abspath(__file__))
        print(
            "未找到 API 配置。请任选其一：\n"
            f"  1) 在本目录新建或编辑 .env 文件：{here}\\.env\n"
            "     写入一行：OPENAI_API_KEY=你的密钥\n"
            "  2) 或在系统/终端里设置环境变量 OPENAI_API_KEY\n"
            "  3) 若用本地 Ollama：在 .env 里设置 OPENAI_BASE_URL=http://localhost:11434/v1",
            file=sys.stderr,
        )
        sys.exit(1)
    # 部分本地服务允许空 key，传占位符避免 SDK 报错
    if not api_key:
        api_key = "ollama"
    return OpenAI(api_key=api_key, base_url=base_url)


class ChatAgent:
    def __init__(
        self,
        model: str | None = None,
        system_prompt: str = "你是一个有帮助的助手，用用户使用的语言简洁回答。",
    ) -> None:
        load_dotenv()
        self._model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._client = _client()
        self._messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]

    def reply(self, user_text: str) -> str:
        self._messages.append({"role": "user", "content": user_text})
        completion = self._client.chat.completions.create(
            model=self._model,
            messages=self._messages,
        )
        assistant = completion.choices[0].message.content or ""
        self._messages.append({"role": "assistant", "content": assistant})
        return assistant

    def reset(self, system_prompt: str | None = None) -> None:
        sp = system_prompt or self._messages[0]["content"]
        self._messages = [{"role": "system", "content": sp}]


def main() -> None:
    agent = ChatAgent()
    print("Agent 已就绪。输入内容后回车发送，输入 quit 或 exit 退出，/reset 清空对话。\n")
    while True:
        try:
            line = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        lower = line.lower()
        if lower in ("quit", "exit", "q"):
            break
        if lower == "/reset":
            agent.reset()
            print("（对话已清空）\n")
            continue
        try:
            answer = agent.reply(line)
        except Exception as e:
            print(f"请求失败: {e}\n", file=sys.stderr)
            continue
        print(f"Agent: {answer}\n")


if __name__ == "__main__":
    main()
