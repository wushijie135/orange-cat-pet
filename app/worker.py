from PySide6.QtCore import QThread, Signal


class ReplyWorker(QThread):
    """一次性回复任务，避免 AI 请求阻塞界面。"""

    done = Signal(str, str)
    failed = Signal(str)

    def __init__(self, engine, message):
        super().__init__()
        self.engine = engine
        self.message = message

    def run(self):
        try:
            text, source = self.engine.reply(self.message)
            self.done.emit(text, source)
        except Exception as exc:
            self.failed.emit(str(exc))
