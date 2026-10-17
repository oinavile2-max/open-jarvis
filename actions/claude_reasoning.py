"""On-demand Claude specialist tool.

The main realtime conversation stays on Gemini Live. This action lets JARVIS
hand difficult reasoning/code/planning tasks to Claude without paying for Claude
on every spoken turn.
"""
from __future__ import annotations

from core import claude
from memory.memory_manager import load_memory, format_memory_for_prompt


_SYSTEM = """You are the deep-reasoning specialist inside JARVIS, a desktop AI assistant.
Answer the user's task directly. Be practical and precise. Do not claim that you
performed computer actions; execution is handled by JARVIS tools. Reply in the
language used by the user's request unless they explicitly ask for another one."""


def claude_reasoning(parameters=None, player=None, **kwargs) -> str:
    params = parameters or {}
    task = str(params.get("task") or "").strip()
    if not task:
        return "No task was provided for Claude."

    if not claude.is_configured():
        return (
            "Claude is not configured yet. Add 'anthropic_api_key' to "
            "config/api_keys.json or set the ANTHROPIC_API_KEY environment variable."
        )

    if player:
        try:
            player.write_log("[Claude] Deep reasoning request")
        except Exception:
            pass

    memory = format_memory_for_prompt(load_memory())
    try:
        answer = claude.ask(task, system=_SYSTEM, memory=memory)
        return answer or "Claude returned an empty response."
    except Exception as exc:
        return f"Claude request failed: {exc}"


TOOL = {
    "name": "claude_reasoning",
    "description": (
        "Use Claude as an optional deep-reasoning specialist for difficult planning, "
        "coding, architecture, analysis, debugging, or when the user explicitly asks "
        "to use Claude. Do NOT use it for simple chat or routine desktop actions, "
        "because it is a paid API call."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "task": {
                "type": "STRING",
                "description": "The complete task/question to send to Claude, with necessary context."
            }
        },
        "required": ["task"]
    },
    "handler": claude_reasoning,
}
