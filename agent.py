import json
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from schemas import AnalyzeResult
from tools import AVAILABLE_TOOLS

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
)

MODEL = os.getenv("OPENAI_MODEL", "deepseek-v4-flash")


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_pod_logs",
            "description": "Get recent logs from a Kubernetes Pod.",
            "parameters": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace"
                    },
                    "pod_name": {
                        "type": "string",
                        "description": "Kubernetes pod name"
                    },
                    "tail_lines": {
                        "type": "integer",
                        "description": "Number of log lines to retrieve"
                    }
                },
                "required": ["namespace", "pod_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "describe_pod",
            "description": "Describe a Kubernetes Pod and return status and events.",
            "parameters": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace"
                    },
                    "pod_name": {
                        "type": "string",
                        "description": "Kubernetes pod name"
                    }
                },
                "required": ["namespace", "pod_name"]
            }
        }
    }
]


def extract_json(raw_text: str) -> dict:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM did not return valid JSON: {raw_text}") from exc


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name not in AVAILABLE_TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")

    tool_func = AVAILABLE_TOOLS[tool_name]
    return tool_func(**arguments)


def diagnose_pod_with_tools(namespace: str, pod_name: str, context: str = "") -> AnalyzeResult:
    messages: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "你是资深 Kubernetes SRE Agent。"
                "你可以调用只读工具收集事实，然后基于工具结果输出合法 JSON。"
                "不要编造工具结果中没有的信息。"
            )
        },
        {
            "role": "user",
            "content": (
                f"请排查 Kubernetes Pod 故障。\n"
                f"namespace: {namespace}\n"
                f"pod_name: {pod_name}\n"
                f"额外上下文: {context}\n\n"
                f"请优先调用工具获取日志和 Pod 事件。"
            )
        }
    ]

    first_response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOL_SCHEMAS,
        tool_choice="auto",
        temperature=0.2,
    )

    first_message = first_response.choices[0].message
    messages.append(first_message)

    if first_message.tool_calls:
        for tool_call in first_message.tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            tool_result = execute_tool(tool_name, arguments)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result, ensure_ascii=False)
            })

    final_instruction = """
请基于以上工具返回结果，输出结构化 JSON。

规则：
1. 只基于工具结果和用户提供的上下文分析。
2. 不要编造工具结果中没有的信息。
3. facts 只能包含工具结果或用户上下文中明确出现的信息。
4. inferences 必须使用“可能”语气。
5. 如果无法确认根因，root_cause 填 null。
6. validation_commands 只给只读命令。
7. 只输出合法 JSON，不要输出 Markdown，不要输出解释文字。

输出 JSON schema：
{
  "summary": "string",
  "severity": "critical | high | medium | low | unknown",
  "facts": ["string"],
  "inferences": ["string"],
  "root_cause": "string or null",
  "confidence": "high | medium | low",
  "validation_commands": ["string"],
  "fix_suggestions": ["string"],
  "risk_notes": ["string"],
  "need_more_info": ["string"]
}
""".strip()

    messages.append({
        "role": "user",
        "content": final_instruction
    })

    final_response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.2,
    )

    content = final_response.choices[0].message.content
    data = extract_json(content)
    return AnalyzeResult.model_validate(data)