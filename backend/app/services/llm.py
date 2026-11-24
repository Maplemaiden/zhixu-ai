"""DeepSeek 兼容 OpenAI SDK。无 Key / 欠费 / 网络异常时返回可读降级文案，避免前端 500。"""
from __future__ import annotations

from openai import APIStatusError, OpenAI

from app.config import get_settings


def available() -> bool:
    return bool(get_settings().deepseek_api_key)


def chat(messages: list[dict[str, str]], temperature: float = 0.3) -> str:
    s = get_settings()
    if not s.deepseek_api_key:
        return (
            "【本地降级】未配置 DEEPSEEK_API_KEY。"
            "请在项目根目录复制 .env.example 为 .env 并填写密钥后，即可启用课程约束下的智能讲解。"
            "当前仍可使用「计算校验 / 步骤卡 / 练习题」接口。"
        )
    client = OpenAI(api_key=s.deepseek_api_key, base_url=s.deepseek_base_url)
    try:
        resp = client.chat.completions.create(
            model=s.deepseek_model,
            messages=messages,
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""
    except APIStatusError as e:
        code = getattr(e, "status_code", None)
        msg = str(e)
        if code == 402 or "Insufficient Balance" in msg or "余额" in msg:
            return (
                "【模型暂时不可用】DeepSeek 账户余额不足（402）。"
                "请到 https://platform.deepseek.com/ 充值后重试。"
                "讲解步骤卡、程序验算和练习判分仍可正常使用。"
            )
        if code in {401, 403}:
            return "【模型暂时不可用】API Key 无效或无权限，请检查项目根目录 .env 中的 DEEPSEEK_API_KEY。"
        return f"【模型暂时不可用】DeepSeek 返回错误（{code}）。计算与练习仍可使用。"
    except Exception as e:
        return f"【模型暂时不可用】调用失败：{e}。计算与练习仍可使用。"
