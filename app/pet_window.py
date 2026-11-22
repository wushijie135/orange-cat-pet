import random
import time

from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QIcon, QPixmap, QAction
from PySide6.QtWidgets import (
    QLabel,
    QMenu,
    QSystemTrayIcon,
    QWidget,
)

from .config import app_root


class SpeechBubble(QWidget):
    """宠物头顶的对话气泡，独立置顶小窗。"""

    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.label = QLabel(self)
        self.label.setWordWrap(True)
        self.label.setMaximumWidth(230)
        self.label.setStyleSheet(
            "QLabel{background:white;color:#333;border:2px solid #ffb347;"
            "border-radius:14px;padding:8px 12px;font-size:13px;}"
        )
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

    def show_text(self, text, anchor_top_center: QPoint):
        self.label.setText(text)
        self.label.adjustSize()
        self.adjustSize()
        x = anchor_top_center.x() - self.width() // 2
        y = anchor_top_center.y() - self.height() - 8
        self.move(x, y)
        self.show()
        self.raise_()
        self._hide_timer.start(3000)


class PetWindow(QWidget):
    def __init__(self, config):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.config = config
        self._pixmaps = {}
        self._state = "idle"
        self._last_interaction = time.time()
        self._next_blink = time.time() + 2.5
        self._temp_until = 0
        self._drag_offset = None
        self._moved = False
        self._chat_window = None
        self._settings_dialog = None
        self._monitor = None

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.bubble = SpeechBubble()
        self._reload_pixmaps()
        self.resize(self._pet_size(), self._pet_size())
        self._move_to_corner()
        self._set_state("idle")

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._tick)
        self.anim_timer.start(200)

        self.tray = self._build_tray()
        self.tray.show()

    # ---------- 资源与外观 ----------
    def _pet_size(self):
        return int(self.config.get("pet_size", default=130))

    def _reload_pixmaps(self):
        size = self._pet_size()
        self._pixmaps.clear()
        for name in ("idle", "blink", "talk", "happy", "sleep"):
            path = app_root() / "assets" / f"{name}.png"
            pm = QPixmap(str(path))
            self._pixmaps[name] = pm.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def apply_appearance(self):
        self._reload_pixmaps()
        size = self._pet_size()
        self.resize(size, size)
        self._set_state(self._state if self._state == "sleep" else "idle")

    def _move_to_corner(self):
        screen = self.screen().availableGeometry()
        self.move(screen.right() - self._pet_size() - 30, screen.bottom() - self._pet_size() - 30)

    def _set_state(self, state):
        self._state = state
        self.label.setPixmap(self._pixmaps.get(state, self._pixmaps["idle"]))

    def _temp_state(self, state, duration=2.0):
        self._set_state(state)
        self._temp_until = time.time() + duration

    # ---------- 动画循环 ----------
    def _tick(self):
        now = time.time()
        sleep_after = float(self.config.get("auto_sleep_minutes", default=3)) * 60
        if self._state != "sleep" and now - self._last_interaction > sleep_after:
            self._set_state("sleep")
            return
        if self._state == "sleep":
            return
        if self._state in ("talk", "happy") and now >= self._temp_until:
            self._set_state("idle")
        if self._state == "idle" and now >= self._next_blink:
            self._set_state("blink")
            QTimer.singleShot(220, lambda: self._set_state("idle") if self._state == "blink" else None)
            self._next_blink = now + random.uniform(2.2, 4.5)

    def _wake(self):
        self._last_interaction = time.time()
        if self._state == "sleep":
            self._set_state("idle")
            self._next_blink = time.time() + 2.5

    # ---------- 鼠标交互 ----------
    def enterEvent(self, event):
        self._wake()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._wake()
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._press_point = event.globalPosition().toPoint()
            self._moved = False

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self._drag_offset is not None:
            new_pos = event.globalPosition().toPoint() - self._drag_offset
            self.move(new_pos)
            if (event.globalPosition().toPoint() - self._press_point).manhattanLength() > 6:
                self._moved = True
            self._follow_bubble()

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        if event.button() == Qt.LeftButton and not self._moved:
            self._on_click()

    def mouseDoubleClickEvent(self, event):
        self._wake()
        self.open_chat()

    def contextMenuEvent(self, event):
        self._build_menu().exec(event.globalPos())

    def _on_click(self):
        self._wake()
        self._temp_state("happy", 1.6)
        self.say(random.choice(self.config.get("pet_talk", default=["喵~"])))

    def say(self, text):
        center = QPoint(self.x() + self.width() // 2, self.y())
        self.bubble.show_text(text, center)

    def _follow_bubble(self):
        if self.bubble.isVisible():
            center = QPoint(self.x() + self.width() // 2, self.y())
            self.bubble.move(center.x() - self.bubble.width() // 2, center.y() - self.bubble.height() - 8)

    # ---------- 菜单与托盘 ----------
    def _build_menu(self):
        menu = QMenu(self)
        wechat_action = QAction("微信自动回复", self, checkable=True)
        wechat_action.setChecked(bool(self.config.get("platforms", "wechat", "enabled", default=False)))
        wechat_action.triggered.connect(lambda checked: self._toggle_platform("wechat", checked))
        qq_action = QAction("QQ自动回复", self, checkable=True)
        qq_action.setChecked(bool(self.config.get("platforms", "qq", "enabled", default=False)))
        qq_action.triggered.connect(lambda checked: self._toggle_platform("qq", checked))
        menu.addAction(wechat_action)
        menu.addAction(qq_action)
        menu.addSeparator()
        interact = QAction("逗逗它", self)
        interact.triggered.connect(self._on_click)
        chat = QAction("和它聊天", self)
        chat.triggered.connect(self.open_chat)
        settings = QAction("设置", self)
        settings.triggered.connect(self.open_settings)
        menu.addAction(interact)
        menu.addAction(chat)
        menu.addAction(settings)
        menu.addSeparator()
        hide = QAction("隐藏到托盘", self)
        hide.triggered.connect(self.hide)
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(hide)
        menu.addAction(quit_action)
        return menu

    def _build_tray(self):
        icon = QIcon(str(app_root() / "assets" / "idle.png"))
        tray = QSystemTrayIcon(icon, self)
        tray.setToolTip(self.config.get("pet_name", default="橘橘"))
        tray.activated.connect(self._tray_activated)
        tray.setContextMenu(self._build_menu())
        return tray

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()

    def _toggle_platform(self, key, checked):
        self.config.set(checked, "platforms", key, "enabled")
        self.config.save()
        names = {"wechat": "微信", "qq": "QQ"}
        self.say(f"{names[key]}自动回复已{'开启' if checked else '关闭'}喵~")

    # ---------- 子窗口 ----------
    def attach_monitor(self, monitor):
        self._monitor = monitor

    def open_chat(self):
        from .chat_window import ChatWindow
        if self._chat_window is None:
            self._chat_window = ChatWindow(self.config, self)
        self._chat_window.show()
        self._chat_window.raise_()
        self._chat_window.activateWindow()

    def open_settings(self):
        from .settings_dialog import SettingsDialog
        self._settings_dialog = SettingsDialog(self.config, self)
        self._settings_dialog.saved.connect(self.apply_appearance)
        self._settings_dialog.show()
        self._settings_dialog.raise_()
        self._settings_dialog.activateWindow()

    # ---------- 监听事件 ----------
    def on_message_received(self, platform, sender, message):
        names = {"wechat": "微信", "qq": "QQ"}
        self._temp_state("talk", 2.2)
        self.say(f"{names.get(platform, platform)}新消息：{message}")

    def on_reply_sent(self, platform, reply, source):
        self._temp_state("talk", 2.2)
        self.say(f"我回复：{reply}")

    def on_status(self, platform, ok, message):
        if not ok:
            self.bubble.show_text(message, QPoint(self.x() + self.width() // 2, self.y()))

    def quit_app(self):
        if self._monitor is not None:
            self._monitor.stop()
        self.config.save()
        self.tray.hide()
        self.close()
        from PySide6.QtWidgets import QApplication
        QApplication.instance().quit()
