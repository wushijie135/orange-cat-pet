import json
import sys
from pathlib import Path

DEFAULT_CONFIG = {
    "pet_name": "橘橘",
    "pet_size": 130,
    "auto_sleep_minutes": 3,
    "reply_mode": "rules",
    "poll_interval": 2.5,
    "reply_cooldown": 3,
    "disclaimer_accepted": False,
    "platforms": {
        "wechat": {"enabled": False},
        "qq": {"enabled": False},
    },
    "ai": {
        "base_url": "https://api.deepseek.com/v1",
        "api_key": "",
        "model": "deepseek-chat",
        "system_prompt": "你是一只可爱的橘猫桌宠，名字叫橘橘。用简短、温暖、带点俏皮的语气回复朋友的消息，每次回复不超过40个字，不要使用表情符号代码，可以适当用语气词喵、呀、哦。",
    },
    "rules": [
        {"keywords": ["你好", "在吗", "在么", "hi", "hello"], "replies": ["在的喵~", "我在呀，怎么啦？", "哈喽哈喽~"]},
        {"keywords": ["再见", "拜拜", "bye", "晚安"], "replies": ["好的拜拜喵~", "嗯嗯，下次再聊呀", "晚安，做个好梦~"]},
        {"keywords": ["谢谢", "感谢"], "replies": ["不客气喵~", "应该的呀，小事一桩！"]},
        {"keywords": ["吃饭", "吃了吗", "吃饭了吗"], "replies": ["还没呢，你吃了吗喵？", "干饭不积极，思想有问题！"]},
        {"keywords": ["忙吗", "有空吗"], "replies": ["随时有空喵，你说~", "不忙不忙，怎么啦？"]},
    ],
    "default_replies": ["嗯嗯，我知道啦~", "收到喵！", "好的好的~", "哈哈，这样啊~", "让我想想呀喵~"],
    "pet_talk": [
        "摸摸头，好舒服喵~",
        "今天也要加油哦！",
        "无聊了就双击我聊天呀~",
        "我会一直陪着你的喵~",
        "记得多喝水，别久坐呀~",
        "你笑起来一定很好看喵~",
    ],
}


def app_root() -> Path:
    """打包后资源目录（只读），源码运行时为项目根目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def writable_root() -> Path:
    """配置文件放在可写位置：exe 旁边，源码运行时为项目根目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def config_path() -> Path:
    return writable_root() / "config.json"


def deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class Config:
    def __init__(self):
        self.data = json.loads(json.dumps(DEFAULT_CONFIG))
        self.path = config_path()
        self.load()

    def load(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    user_data = json.load(f)
                self.data = deep_merge(DEFAULT_CONFIG, user_data)
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get(self, *keys, default=None):
        cur = self.data
        for key in keys:
            if not isinstance(cur, dict) or key not in cur:
                return default
            cur = cur[key]
        return cur

    def set(self, value, *keys):
        cur = self.data
        for key in keys[:-1]:
            cur = cur.setdefault(key, {})
        cur[keys[-1]] = value
