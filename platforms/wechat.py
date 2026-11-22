from .base import BasePlatform


class WeChatPlatform(BasePlatform):
    platform_key = "wechat"
    display_name = "微信"
    # 兼容微信 3.x（WeChatMainWndForPC）与 4.x（WeixinMainWnd）
    window_candidates = [
        ("PaneControl", {"ClassName": "WeChatMainWndForPC", "Name": "微信"}),
        ("PaneControl", {"ClassName": "WeixinMainWnd"}),
        ("WindowControl", {"Name": "微信"}),
    ]
    edit_name_candidates = ["输入", "发消息"]
