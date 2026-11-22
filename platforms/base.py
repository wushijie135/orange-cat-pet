import uiautomation as auto

# 全局搜索超时，避免找不到控件时长时间卡住
auto.SetGlobalSearchTimeout(1.0)


def _walk(control, depth=4):
    """受控深度遍历控件树。"""
    if depth <= 0:
        return
    try:
        children = control.GetChildren()
    except Exception:
        return
    for child in children:
        yield child, depth
        yield from _walk(child, depth - 1)


class BasePlatform:
    """聊天平台适配基类：负责窗口查找、消息快照、模拟发送。"""

    platform_key = ""
    display_name = ""
    window_candidates = []
    edit_name_candidates = []

    def find_window(self):
        for type_name, kwargs in self.window_candidates:
            factory = getattr(auto, type_name, None)
            if factory is None:
                continue
            ctrl = factory(**kwargs)
            if ctrl.Exists(1, 0.3):
                return ctrl
        return None

    def is_available(self):
        return self.find_window() is not None

    def _find_message_list(self, win):
        for list_name in ("消息", "聊天消息", "消息列表"):
            lst = win.ListControl(Name=list_name)
            if lst.Exists(1, 0.2):
                return lst
        # 兜底：找子树中子项最多的 ListControl
        best, best_count = None, 0
        for ctrl, _ in _walk(win, 4):
            if ctrl.ControlTypeName == "ListControl":
                try:
                    count = len(ctrl.GetChildren())
                except Exception:
                    count = 0
                if count > best_count:
                    best, best_count = ctrl, count
        return best

    def _find_edit(self, win):
        for edit_name in self.edit_name_candidates:
            edit = win.EditControl(Name=edit_name)
            if edit.Exists(1, 0.2):
                return edit
        # 兜底：挑选最靠下、面积最大的可见 EditControl
        best, best_score = None, -1
        for ctrl, _ in _walk(win, 5):
            if ctrl.ControlTypeName != "EditControl":
                continue
            rect = ctrl.BoundingRectangle
            if rect.width() <= 0 or rect.height() <= 0:
                continue
            score = rect.top * 10 + rect.width() * rect.height() / 10000
            if score > best_score:
                best, best_score = ctrl, score
        return best

    def snapshot(self):
        """返回最近若干条消息 [{text, is_self}]，窗口不可用时返回 None。"""
        win = self.find_window()
        if win is None:
            return None
        win_rect = win.BoundingRectangle
        msg_list = self._find_message_list(win)
        if msg_list is None:
            return []
        try:
            items = msg_list.GetChildren()
        except Exception:
            return []
        center_x = (win_rect.left + win_rect.right) / 2
        result = []
        for item in items[-10:]:
            name = (item.Name or "").strip()
            if not name:
                continue
            rect = item.BoundingRectangle
            is_self = (rect.left + rect.right) / 2 > center_x
            result.append({"text": name, "is_self": is_self})
        return result

    def send(self, text):
        win = self.find_window()
        if win is None:
            return False, f"未找到{self.display_name}窗口，请先打开并登录"
        edit = self._find_edit(win)
        if edit is None:
            return False, "未找到聊天输入框，请打开一个聊天会话"
        try:
            edit.Click()
            auto.SendText(text)
            auto.SendKeys("{Enter}", waitTime=0.3)
            return True, None
        except Exception as exc:
            return False, f"发送失败：{exc}"
