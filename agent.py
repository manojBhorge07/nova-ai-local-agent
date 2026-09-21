from __future__ import annotations

import ast
import json
import operator
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Generator, Optional

import requests


class EventKind(str, Enum):
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    FINAL = "final"
    ERROR = "error"
    DONE = "done"


@dataclass
class AgentEvent:
    kind: EventKind
    content: str = ""
    meta: dict = field(default_factory=dict)


# ---------- Safe calculator ----------
_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left, right = _safe_eval(node.left), _safe_eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("Exponent is too large")
        return _BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Unsupported expression")


def tool_calculator(expression: str) -> str:
    try:
        expression = expression.strip().replace("^", "**").replace(",", "")
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return str(result)
    except ZeroDivisionError:
        return "Error: division by zero"
    except Exception as exc:
        return f"Calculator error: {exc}"


def tool_datetime(fmt: str = "%A, %d %B %Y at %H:%M:%S") -> str:
    try:
        return datetime.now().strftime(fmt or "%A, %d %B %Y at %H:%M:%S")
    except Exception as exc:
        return f"Date/time error: {exc}"


def tool_search_wikipedia(query: str) -> str:
    try:
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + requests.utils.quote(query)
        response = requests.get(url, timeout=8, headers={"User-Agent": "NovaChat/2.0"})
        if response.status_code == 200:
            data = response.json()
            title = data.get("title", query)
            extract = data.get("extract", "No summary found.")
            return f"{title}: {extract[:1200]}"
        return f"Wikipedia returned status {response.status_code}."
    except Exception as exc:
        return f"Wikipedia error: {exc}"


def tool_web_fetch(url: str) -> str:
    try:
        if not re.match(r"^https?://", url.strip(), re.I):
            return "URL must start with http:// or https://"
        response = requests.get(
            url.strip(),
            timeout=10,
            headers={"User-Agent": "NovaChat/2.0"},
        )
        text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", response.text, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:1600] or "No readable page text found."
    except Exception as exc:
        return f"Web fetch error: {exc}"


TOOLS: dict[str, dict[str, Any]] = {
    "calculator": {
        "fn": tool_calculator,
        "description": "Evaluate arithmetic. Input example: (3+5)*2",
        "param": "expression",
        "icon": "⌁",
    },
    "datetime": {
        "fn": tool_datetime,
        "description": "Get the current date and time.",
        "param": "fmt",
        "icon": "◷",
    },
    "wikipedia": {
        "fn": tool_search_wikipedia,
        "description": "Get a short Wikipedia summary for a topic.",
        "param": "query",
        "icon": "W",
    },
    "web_fetch": {
        "fn": tool_web_fetch,
        "description": "Fetch readable text from a public URL.",
        "param": "url",
        "icon": "↗",
    },
}


def build_tool_docs() -> str:
    return "\n".join(
        f"- {name}({info['param']}): {info['description']}"
        for name, info in TOOLS.items()
    )


SYSTEM_PROMPT = f"""
You are Nova, a helpful local AI assistant powered by Ollama.

You have optional tools:
{build_tool_docs()}

TOOL PROTOCOL:
- If a tool is needed, output ONLY: <tool>TOOL_NAME|ARGUMENT</tool>
- After an observation, either call another tool or output ONLY: <final>ANSWER</final>
- Never expose XML tags to the user.
- Do not invent tool results.
- Prefer direct answers when no tool is needed.
- Use Markdown in final answers when it improves readability.
- Be concise but useful.
"""


OLLAMA_URL = "http://localhost:11434/api/chat"


def stream_ollama(
    messages: list[dict],
    model: str,
    temperature: float = 0.3,
    stop: Optional[list[str]] = None,
) -> Generator[str, None, None]:
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": min(max(temperature, 0.0), 1.0),
            "num_ctx": 8192,
            "stop": stop or [],
        },
    }
    with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=180) as response:
        if not response.ok:
            body = response.text[:500]
            raise RuntimeError(
                f"Ollama returned {response.status_code}. "
                f"Make sure the model is installed with: ollama pull {model}\n{body}"
            )
        for line in response.iter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            token = chunk.get("message", {}).get("content", "")
            if token:
                yield token
            if chunk.get("done"):
                break


def clean_answer(text: str) -> str:
    text = re.sub(r"<(?:tool|final|observation)>.*?</(?:tool|final|observation)>", "", text, flags=re.S)
    text = re.sub(r"</?(?:tool|final|observation)>", "", text)
    return text.strip()


class Agent:
    def __init__(self, model: str = "llama3.2", temperature: float = 0.4, max_steps: int = 8):
        self.model = model
        self.temperature = temperature
        self.max_steps = max_steps

    def run(
        self,
        user_message: str,
        history: list[dict] | None = None,
    ) -> Generator[AgentEvent, None, None]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            messages.extend(history[-20:])
        messages.append({"role": "user", "content": user_message})

        collected: list[str] = []
        seen_calls: set[str] = set()

        for step in range(self.max_steps):
            buffer = ""
            try:
                for token in stream_ollama(messages, self.model, self.temperature):
                    buffer += token
                    if "</tool>" in buffer or "</final>" in buffer:
                        break
            except requests.exceptions.ConnectionError:
                yield AgentEvent(EventKind.ERROR, "Cannot connect to Ollama. Start it with `ollama serve`.")
                yield AgentEvent(EventKind.DONE)
                return
            except Exception as exc:
                yield AgentEvent(EventKind.ERROR, str(exc))
                yield AgentEvent(EventKind.DONE)
                return

            final_match = re.search(r"<final>(.*?)</final>", buffer, re.S)
            if final_match:
                answer = clean_answer(final_match.group(1))
                yield AgentEvent(EventKind.FINAL, answer)
                yield AgentEvent(EventKind.DONE, meta={"steps": step + 1})
                return

            tool_match = re.search(r"<tool>(.*?)</tool>", buffer, re.S)
            if not tool_match:
                # Graceful fallback for models that answer without protocol tags.
                if buffer.strip():
                    yield AgentEvent(EventKind.FINAL, clean_answer(buffer))
                    yield AgentEvent(EventKind.DONE, meta={"steps": step + 1})
                    return
                continue

            raw = tool_match.group(1).strip()
            tool_name, arg = (raw.split("|", 1) + [""])[:2]
            tool_name, arg = tool_name.strip(), arg.strip()
            call_key = f"{tool_name}|{arg}"

            if call_key in seen_calls:
                answer = self._synthesize(user_message, collected)
                yield AgentEvent(EventKind.FINAL, answer)
                yield AgentEvent(EventKind.DONE, meta={"steps": step + 1})
                return

            seen_calls.add(call_key)
            yield AgentEvent(
                EventKind.TOOL_CALL,
                f"{tool_name}({arg})",
                {"tool": tool_name, "arg": arg},
            )

            started = time.time()
            if tool_name in TOOLS:
                try:
                    result = TOOLS[tool_name]["fn"](arg)
                except Exception as exc:
                    result = f"Tool error: {exc}"
            else:
                result = f"Unknown tool: {tool_name}"
            elapsed = round(time.time() - started, 3)

            yield AgentEvent(
                EventKind.TOOL_RESULT,
                result,
                {"tool": tool_name, "elapsed": elapsed},
            )
            collected.append(f"{tool_name}({arg}) => {result}")

            messages.append({"role": "assistant", "content": buffer})
            messages.append({
                "role": "user",
                "content": (
                    f"<observation>{result}</observation>\n"
                    "Continue with another tool if needed, otherwise output "
                    "ONLY <final>your answer</final>."
                ),
            })

        answer = self._synthesize(user_message, collected) if collected else (
            "I couldn't complete that request within the configured step limit."
        )
        yield AgentEvent(EventKind.FINAL, answer)
        yield AgentEvent(EventKind.DONE, meta={"steps": self.max_steps})

    def _synthesize(self, question: str, collected: list[str]) -> str:
        facts = "\n".join(f"- {item}" for item in collected)
        prompt = (
            f"Question: {question}\n\nFacts gathered:\n{facts}\n\n"
            "Answer clearly using only these facts. Do not mention internal tools."
        )
        try:
            messages = [
                {"role": "system", "content": "You are a concise assistant."},
                {"role": "user", "content": prompt},
            ]
            answer = "".join(stream_ollama(messages, self.model, 0.1))
            return clean_answer(answer) or "I gathered the requested information, but could not summarize it."
        except Exception:
            return "\n".join(item.split("=>", 1)[-1].strip() for item in collected)
