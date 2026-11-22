from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .reply_engine import ReplyEngine
from .worker import ReplyWorker


class ChatWindow(QWidget):
    def __init__(self, config, pet):
        super().__init__(None, Qt.Window)
        self.config = config
        self.pet = pet
        self.engine = ReplyEngine(config)
        self.worker = None
        self.setWindowTitle(f"和{config.get('pet_name', default='橘橘')}聊天")
        self.resize(360, 420)

        self.history = QTextEdit(self)
        self.history.setReadOnly(True)
        self.history.setStyleSheet("QTextEdit{background:#fffaf2;border:1px solid #ffd9a8;border-radius:10px;padding:6px;font-size:13px;}")

        self.input = QLineEdit(self)
        self.input.setPlaceholderText("说点什么吧，回车发送~")
        self.input.returnPressed.connect(self._send)

        self.send_btn = QPushButton("发送", self)
        self.send_btn.clicked.connect(self._send)
        self.send_btn.setStyleSheet(
            "QPushButton{background:#ffb347;color:white;border:none;border-radius:8px;padding:6px 16px;font-size:13px;}"
            "QPushButton:hover{background:#ffa726;}"
        )

        bottom = QHBoxLayout()
        bottom.addWidget(self.input)
        bottom.addWidget(self.send_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.history)
        layout.addLayout(bottom)

        self._append_pet("嗨，我是橘橘，随时可以陪你聊天喵~")

    def _send(self):
        text = self.input.text().strip()
        if not text or (self.worker is not None and self.worker.isRunning()):
            return
        self.input.clear()
        self._append_me(text)
        self.pet._temp_state("talk", 2.0)
        self.worker = ReplyWorker(self.engine, text)
        self.worker.done.connect(self._on_reply)
        self.worker.failed.connect(lambda err: self._append_pet(f"出错了喵：{err}"))
        self.worker.start()

    def _on_reply(self, text, source):
        self.pet._temp_state("happy", 1.6)
        self.pet.say(text)
        self._append_pet(text)

    def _append_me(self, text):
        self.history.append(f'<p style="text-align:right;"><span style="background:#ffb347;color:white;padding:5px 10px;border-radius:10px;">{text}</span></p>')

    def _append_pet(self, text):
        name = self.config.get("pet_name", default="橘橘")
        self.history.append(f'<p><b style="color:#e8820c;">{name}：</b>{text}</p>')

    def closeEvent(self, event):
        event.ignore()
        self.hide()
