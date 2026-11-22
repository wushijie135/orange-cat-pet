import re
import time

from PySide6.QtCore import QThread, Signal

from platforms.qq import QQPlatform
from platforms.wechat import WeChatPlatform
from .reply_engine import ReplyEngine

TIME_PATTERN = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")
SYSTEM_HINTS = ("撤回了一条消息", "以下为新消息", "你已添加", "已成为好友", "消息已读", "拍了拍", "以上是打招呼")


def clean_message(raw: str) -> str:
    """控件 Name 可能是 '昵称\n内容'，取最后一行作为消息正文。"""
    lines = [line.strip() for line in raw.split("\n") if line.strip()]
    if not lines:
        return ""
    return lines[-1]


def is_system_message(text: str) -> bool:
    if TIME_PATTERN.match(text):
        return True
    return any(hint in text for hint in SYSTEM_HINTS)


class MonitorThread(QThread):
    message_received = Signal(str, str, str)   # 平台、昵称行、消息
    reply_sent = Signal(str, str, str)         # 平台、回复、来源
    status_changed = Signal(str, bool, str)    # 平台、是否正常、说明

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.engine = ReplyEngine(config)
        self.platforms = {
            "wechat": WeChatPlatform(),
            "qq": QQPlatform(),
        }
        self.states = {
            key: {"last_raw": "", "last_reply_at": 0.0, "available": None, "message": None}
            for key in self.platforms
        }
        self._running = True

    def run(self):
        while self._running:
            interval = float(self.config.get("poll_interval", default=2.5))
            for key, platform in self.platforms.items():
                if not self._running:
                    break
                enabled = self.config.get("platforms", key, "enabled", default=False)
                state = self.states[key]
                if not enabled:
                    self._report_status(key, state, None, "已关闭")
                    continue
                try:
                    self._poll_once(key, platform, state)
                except Exception as exc:  # 轮询异常不能让线程退出
                    self._report_status(key, state, False, f"监听异常：{exc}")
            self.msleep(int(interval * 1000))

    def _poll_once(self, key, platform, state):
        snap = platform.snapshot()
        if snap is None:
            self._report_status(key, state, False, f"未找到{platform.display_name}窗口，请打开并登录")
            return
        self._report_status(key, state, True, f"正在监听{platform.display_name}")
        if not snap:
            return

        last = snap[-1]
        raw = last["text"]
        if raw == state["last_raw"]:
            return
        state["last_raw"] = raw
        if last["is_self"]:
            return  # 自己发出的消息，仅更新基线

        message = clean_message(raw)
        if not message or is_system_message(message):
            return

        cooldown = float(self.config.get("reply_cooldown", default=3))
        if time.time() - state["last_reply_at"] < cooldown:
            return
        state["last_reply_at"] = time.time()

        sender_line = raw.split("\n")[0].strip() if "\n" in raw else "好友"
        self.message_received.emit(key, sender_line, message)

        reply, source = self.engine.reply(message)
        ok, err = platform.send(reply)
        if ok:
            self.reply_sent.emit(key, reply, source)
        else:
            self.status_changed.emit(key, False, err)

    def _report_status(self, key, state, available, message):
        if state["available"] != available or state["message"] != message:
            state["available"] = available
            state["message"] = message
            self.status_changed.emit(key, bool(available), message)

    def stop(self):
        self._running = False
        self.wait(3000)
