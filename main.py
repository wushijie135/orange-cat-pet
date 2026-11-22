import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from app.config import Config
from app.monitor import MonitorThread
from app.pet_window import PetWindow

DISCLAIMER = (
    "欢迎使用橘橘桌宠，使用前请知晓：\n\n"
    "1. 本软件通过 Windows 辅助功能模拟人工操作，仅可用于个人便捷自动应答；\n"
    "2. 请勿用于骚扰、群发、营销引流等违规行为，否则后果自负；\n"
    "3. 微信、QQ 官方可能限制自动化操作，存在风控风险，建议先用小号测试；\n"
    "4. 自动回复期间请勿抢占鼠标键盘，保持软件处于登录状态。\n\n"
    "点击“我已知晓”开始使用。"
)


def show_disclaimer(config):
    if config.get("disclaimer_accepted", default=False):
        return True
    box = QMessageBox()
    box.setWindowTitle("使用须知")
    box.setText(DISCLAIMER)
    accept = box.addButton("我已知晓", QMessageBox.AcceptRole)
    box.addButton("退出", QMessageBox.RejectRole)
    box.exec()
    if box.clickedButton() is accept:
        config.set(True, "disclaimer_accepted")
        config.save()
        return True
    return False


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    config = Config()
    if not show_disclaimer(config):
        sys.exit(0)

    pet = PetWindow(config)
    pet.show()

    monitor = MonitorThread(config)
    pet.attach_monitor(monitor)
    monitor.message_received.connect(pet.on_message_received)
    monitor.reply_sent.connect(pet.on_reply_sent)
    monitor.status_changed.connect(pet.on_status)
    monitor.start()

    exit_code = app.exec()
    monitor.stop()
    config.save()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
