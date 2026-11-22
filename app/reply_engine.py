import random

import requests


class ReplyEngine:
    """规则 + AI 回复引擎，线程安全：只读取配置快照，不碰 Qt 对象。"""

    def __init__(self, config):
        self.config = config

    def _rule_reply(self, message: str):
        text = message.strip().lower()
        for rule in self.config.get("rules", default=[]):
            keywords = rule.get("keywords", [])
            replies = rule.get("replies", [])
            if any(kw.lower() in text for kw in keywords) and replies:
                return random.choice(replies), True
        return None, False

    def _default_reply(self):
        replies = self.config.get("default_replies", default=["收到~"])
        return random.choice(replies or ["收到~"])

    def _ai_reply(self, message: str):
        ai = self.config.get("ai", default={})
        api_key = ai.get("api_key", "")
        base_url = ai.get("base_url", "").rstrip("/")
        model = ai.get("model", "")
        if not api_key or not base_url:
            return None, "未配置 AI API Key"
        url = f"{base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": ai.get("system_prompt", "你是一个可爱的桌宠助手。")},
                {"role": "user", "content": message},
            ],
            "temperature": 0.8,
            "max_tokens": 120,
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            return content, None
        except requests.RequestException as exc:
            return None, f"AI 请求失败：{exc}"
        except (KeyError, IndexError, ValueError) as exc:
            return None, f"AI 返回解析失败：{exc}"

    def reply(self, message: str):
        """返回 (回复文本, 来源说明)。"""
        mode = self.config.get("reply_mode", default="rules")
        rule_text, hit = self._rule_reply(message)

        if mode == "rules":
            if hit:
                return rule_text, "规则"
            return self._default_reply(), "默认"

        if mode == "ai":
            ai_text, err = self._ai_reply(message)
            if ai_text:
                return ai_text, "AI"
            if hit:
                return rule_text, f"{err}，回退规则"
            return self._default_reply(), f"{err}，回退默认"

        # hybrid：规则优先，未命中走 AI，AI 失败兜底
        if hit:
            return rule_text, "规则"
        ai_text, err = self._ai_reply(message)
        if ai_text:
            return ai_text, "AI"
        return self._default_reply(), f"{err}，回退默认"
