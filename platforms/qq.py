from .base import BasePlatform


class QQPlatform(BasePlatform):
    platform_key = "qq"
    display_name = "QQ"
    # QQ NT 架构窗口类名为 Chrome_Widget_Win
    window_candidates = [
        ("WindowControl", {"ClassName": "Chrome_Widget_Win", "Name": "QQ"}),
        ("PaneControl", {"ClassName": "Chrome_Widget_Win", "Name": "QQ"}),
        ("WindowControl", {"Name": "QQ"}),
    ]
    edit_name_candidates = ["输入", "发消息"]
