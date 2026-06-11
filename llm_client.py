import json
import os
from openai import OpenAI
from dotenv import load_dotenv

from schemas import AnalyzeResult

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.DEEPSEEK.com/v1"),
)

MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")


def extract_json(raw_text: str) -> dict:
    """
    尽量从模型输出中解析 JSON。
    第一版简单处理：要求模型只输出 JSON。
    如果失败，直接抛错。
    """
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM did not return valid JSON: {raw_text}") from exc


def analyze_logs_with_llm(prompt: str) -> AnalyzeResult:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "你是一个严谨的 SRE 助手，必须按要求输出合法 JSON。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content
    data = extract_json(content)

    return AnalyzeResult.model_validate(data)