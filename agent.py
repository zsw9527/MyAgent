"""
简单对话 Agent：使用 LangChain 的 PromptTemplate、Memory 与 Tools。
"""
from __future__ import annotations

import ast
import operator
import os
import sys
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.messages import ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


@tool
def get_current_time() -> str:
    """获取当前本地时间，返回 yyyy-mm-dd HH:MM:SS。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")





def _model(model: str) -> ChatOpenAI:
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
    if not api_key:
        api_key = "ollama"
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
    )


class ChatAgent:
    def __init__(
        self,
        model: str | None = None,
        system_prompt: str = "你是一个有帮助的助手，用用户使用的语言简洁回答。",
    ) -> None:
        load_dotenv()
        selected_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._system_prompt = system_prompt
        self._llm = _model(selected_model)
        self._tools = [get_current_time]
        self._llm_with_tools = self._llm.bind_tools(self._tools)

        self._memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
        )
        self._prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_prompt}"),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )

    def _render_assistant_text(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "\n".join(str(item) for item in content)
        return str(content or "")

    def reply(self, user_text: str) -> str:
        variables = self._memory.load_memory_variables({})
        chat_history = variables.get("chat_history", [])
        messages = self._prompt.format_messages(
            system_prompt=self._system_prompt,
            chat_history=chat_history,
            input=user_text,
        )

        response = self._llm_with_tools.invoke(messages)
        tool_calls = getattr(response, "tool_calls", None) or []
        tool_map = {tool_obj.name: tool_obj for tool_obj in self._tools}

        for call in tool_calls:
            tool_name = call["name"]
            tool_args = call.get("args", {})
            tool_obj = tool_map.get(tool_name)
            if tool_obj is None:
                continue

            tool_result = tool_obj.invoke(tool_args)
            messages.append(response)
            messages.append(
                ToolMessage(content=str(tool_result), tool_call_id=call["id"])
            )
            response = self._llm_with_tools.invoke(messages)

        assistant_text = self._render_assistant_text(response.content)
        self._memory.save_context({"input": user_text}, {"output": assistant_text})
        return assistant_text

    def reset(self, system_prompt: str | None = None) -> None:
        self._memory.clear()
        if system_prompt:
            self._system_prompt = system_prompt



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
