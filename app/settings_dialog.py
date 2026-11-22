from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from platforms.qq import QQPlatform
from platforms.wechat import WeChatPlatform
from .reply_engine import ReplyEngine
from .worker import ReplyWorker


class SettingsDialog(QWidget):
    saved = Signal()

    def __init__(self, config, parent=None):
        super().__init__(None)
        self.config = config
        self.setWindowTitle("桌宠设置")
        self.resize(520, 560)

        self.tabs = QTabWidget(self)
        self.tabs.addTab(self._build_general_tab(), "通用")
        self.tabs.addTab(self._build_platform_tab(), "聊天平台")
        self.tabs.addTab(self._build_reply_tab(), "回复与AI")
        self.tabs.addTab(self._build_rules_tab(), "关键词规则")

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.close)
        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(cancel_btn)
        bottom.addWidget(save_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)
        layout.addLayout(bottom)

    # ---------- 通用 ----------
    def _build_general_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        self.name_edit = QLineEdit(self.config.get("pet_name", default="橘橘"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(80, 220)
        self.size_spin.setValue(int(self.config.get("pet_size", default=130)))
        self.poll_spin = QDoubleSpinBox()
        self.poll_spin.setRange(1.0, 10.0)
        self.poll_spin.setSingleStep(0.5)
        self.poll_spin.setValue(float(self.config.get("poll_interval", default=2.5)))
        self.cooldown_spin = QDoubleSpinBox()
        self.cooldown_spin.setRange(0.0, 60.0)
        self.cooldown_spin.setSingleStep(1.0)
        self.cooldown_spin.setValue(float(self.config.get("reply_cooldown", default=3)))
        self.sleep_spin = QSpinBox()
        self.sleep_spin.setRange(1, 30)
        self.sleep_spin.setValue(int(self.config.get("auto_sleep_minutes", default=3)))
        form.addRow("宠物名字", self.name_edit)
        form.addRow("显示大小（像素）", self.size_spin)
        form.addRow("消息检查间隔（秒）", self.poll_spin)
        form.addRow("两次回复冷却（秒）", self.cooldown_spin)
        form.addRow("多久无操作睡觉（分钟）", self.sleep_spin)
        return tab

    # ---------- 平台 ----------
    def _build_platform_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.wechat_check = QCheckBox("启用微信自动回复")
        self.wechat_check.setChecked(bool(self.config.get("platforms", "wechat", "enabled", default=False)))
        self.wechat_status = QLabel("状态：未检测")
        wechat_btn = QPushButton("检测微信窗口")
        wechat_btn.clicked.connect(lambda: self._detect(WeChatPlatform(), self.wechat_status))
        layout.addWidget(self._platform_group(self.wechat_check, self.wechat_status, wechat_btn))

        self.qq_check = QCheckBox("启用QQ自动回复")
        self.qq_check.setChecked(bool(self.config.get("platforms", "qq", "enabled", default=False)))
        self.qq_status = QLabel("状态：未检测")
        qq_btn = QPushButton("检测QQ窗口")
        qq_btn.clicked.connect(lambda: self._detect(QQPlatform(), self.qq_status))
        layout.addWidget(self._platform_group(self.qq_check, self.qq_status, qq_btn))

        tip = QLabel("提示：需要先在电脑上打开并登录对应软件，且进入一个聊天会话。")
        tip.setWordWrap(True)
        tip.setStyleSheet("color:#888;font-size:12px;")
        layout.addWidget(tip)
        layout.addStretch()
        return tab

    def _platform_group(self, check, status, button):
        group = QGroupBox()
        layout = QVBoxLayout(group)
        row = QHBoxLayout()
        row.addWidget(check)
        row.addWidget(button)
        layout.addLayout(row)
        layout.addWidget(status)
        return group

    def _detect(self, platform, label):
        label.setText("状态：检测中...")
        label.repaint()
        if platform.is_available():
            label.setText("状态：✅ 已找到窗口")
        else:
            label.setText("状态：❌ 未找到，请先打开软件并登录")

    # ---------- 回复与 AI ----------
    def _build_reply_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("仅本地规则（离线免费）", "rules")
        self.mode_combo.addItem("仅AI大模型", "ai")
        self.mode_combo.addItem("规则优先，没命中再问AI", "hybrid")
        index = {"rules": 0, "ai": 1, "hybrid": 2}.get(self.config.get("reply_mode", default="rules"), 0)
        self.mode_combo.setCurrentIndex(index)
        layout.addWidget(QLabel("回复模式"))
        layout.addWidget(self.mode_combo)

        ai = self.config.get("ai", default={})
        self.base_url_edit = QLineEdit(ai.get("base_url", ""))
        self.api_key_edit = QLineEdit(ai.get("api_key", ""))
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.model_edit = QLineEdit(ai.get("model", ""))
        self.prompt_edit = QPlainTextEdit(ai.get("system_prompt", ""))
        form = QFormLayout()
        form.addRow("接口地址", self.base_url_edit)
        form.addRow("API Key", self.api_key_edit)
        form.addRow("模型名称", self.model_edit)
        layout.addLayout(form)
        layout.addWidget(QLabel("AI 人设提示词"))
        layout.addWidget(self.prompt_edit)

        test_row = QHBoxLayout()
        self.test_edit = QLineEdit()
        self.test_edit.setPlaceholderText("输入一条测试消息")
        test_btn = QPushButton("测试回复")
        test_btn.clicked.connect(self._test_reply)
        test_row.addWidget(self.test_edit)
        test_row.addWidget(test_btn)
        layout.addLayout(test_row)
        self.test_result = QLabel("")
        self.test_result.setWordWrap(True)
        self.test_result.setStyleSheet("color:#e8820c;")
        layout.addWidget(self.test_result)
        return tab

    def _test_reply(self):
        self._flush_ai_to_config()
        message = self.test_edit.text().strip()
        if not message:
            return
        self.test_result.setText("测试中...")
        worker = ReplyWorker(ReplyEngine(self.config), message)
        worker.done.connect(lambda text, source: self.test_result.setText(f"[{source}] {text}"))
        worker.failed.connect(lambda err: self.test_result.setText(f"失败：{err}"))
        worker.start()
        self._test_worker = worker

    # ---------- 规则 ----------
    def _build_rules_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.rules_table = QTableWidget(0, 2)
        self.rules_table.setHorizontalHeaderLabels(["关键词（逗号分隔）", "回复（多条用 | 分隔）"])
        for rule in self.config.get("rules", default=[]):
            self._append_rule_row(",".join(rule.get("keywords", [])), "|".join(rule.get("replies", [])))
        self.rules_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.rules_table)
        row = QHBoxLayout()
        add_btn = QPushButton("添加一行")
        add_btn.clicked.connect(lambda: self._append_rule_row("", ""))
        del_btn = QPushButton("删除选中行")
        del_btn.clicked.connect(lambda: self.rules_table.removeRow(self.rules_table.currentRow()))
        row.addWidget(add_btn)
        row.addWidget(del_btn)
        row.addStretch()
        layout.addLayout(row)

        layout.addWidget(QLabel("未命中规则时的默认回复（每行一条）"))
        self.default_edit = QPlainTextEdit("\n".join(self.config.get("default_replies", default=[])))
        layout.addWidget(self.default_edit)
        layout.addWidget(QLabel("点击宠物时的闲聊语（每行一条）"))
        self.talk_edit = QPlainTextEdit("\n".join(self.config.get("pet_talk", default=[])))
        layout.addWidget(self.talk_edit)
        return tab

    def _append_rule_row(self, keywords, replies):
        row = self.rules_table.rowCount()
        self.rules_table.insertRow(row)
        self.rules_table.setItem(row, 0, QTableWidgetItem(keywords))
        self.rules_table.setItem(row, 1, QTableWidgetItem(replies))

    # ---------- 保存 ----------
    def _flush_ai_to_config(self):
        self.config.set(self.base_url_edit.text().strip(), "ai", "base_url")
        self.config.set(self.api_key_edit.text().strip(), "ai", "api_key")
        self.config.set(self.model_edit.text().strip(), "ai", "model")
        self.config.set(self.prompt_edit.toPlainText().strip(), "ai", "system_prompt")

    def _save(self):
        self.config.set(self.name_edit.text().strip() or "橘橘", "pet_name")
        self.config.set(self.size_spin.value(), "pet_size")
        self.config.set(self.poll_spin.value(), "poll_interval")
        self.config.set(self.cooldown_spin.value(), "reply_cooldown")
        self.config.set(self.sleep_spin.value(), "auto_sleep_minutes")
        self.config.set(self.mode_combo.currentData(), "reply_mode")
        self._flush_ai_to_config()

        self.config.set(self.wechat_check.isChecked(), "platforms", "wechat", "enabled")
        self.config.set(self.qq_check.isChecked(), "platforms", "qq", "enabled")

        rules = []
        for row in range(self.rules_table.rowCount()):
            kw_item = self.rules_table.item(row, 0)
            reply_item = self.rules_table.item(row, 1)
            keywords = [k.strip() for k in (kw_item.text() if kw_item else "").split(",") if k.strip()]
            replies = [r.strip() for r in (reply_item.text() if reply_item else "").split("|") if r.strip()]
            if keywords and replies:
                rules.append({"keywords": keywords, "replies": replies})
        self.config.set(rules, "rules")

        defaults = [line.strip() for line in self.default_edit.toPlainText().split("\n") if line.strip()]
        self.config.set(defaults or ["收到~"], "default_replies")
        talks = [line.strip() for line in self.talk_edit.toPlainText().split("\n") if line.strip()]
        self.config.set(talks or ["喵~"], "pet_talk")

        self.config.save()
        self.saved.emit()
        self.close()
