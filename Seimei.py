# -*- coding: utf-8 -*-
import os
import wx

# 置換ルールをここに追加することで、禁止文字の追加や調整がしやすい
REPLACEMENTS = [
    ("_vti_", "_"),
    ('"', "_"),
    (" ", "_"),
    ("/", "_"),
    ("#", "_"),
    ("%", "_"),
    ("&", "_"),
    ("*", "_"),
    (":", "_"),
    ("<", "_"),
    (">", "_"),
    ("?", "_"),
    ("|", "_"),
    ("　", "_"),
    ("\u00A0","_"),  # 改行不可のスペース
    ("~$", "_"),     # 本来は、"~$"で始まるファイル名が不可だが一律に置き換える
]

RESERVED_NAMES = {
    "desktop.ini",
    ".lock",
    "con",
    "prn",
    "aux",
    "nul",
    "com0",
    "com1",
    "com2",
    "com3",
    "com4",
    "com5",
    "com6",
    "com7",
    "com8",
    "com9",
    "lpt0",
    "lpt1",
    "lpt2",
    "lpt3",
    "lpt4",
    "lpt5",
    "lpt6",
    "lpt7",
    "lpt8",
    "lpt9",
}


def sanitize_name(name: str) -> str:
    """置換ルールに従ってファイル名を変換する"""
    sanitized = name
    for target, replacement in REPLACEMENTS:
        sanitized = sanitized.replace(target, replacement)
    return sanitized


def make_safe_name(name: str) -> str:
    """禁止文字置換後に、予約語の場合は末尾に'_'を追加する"""
    sanitized = sanitize_name(name)
    lower_name = sanitized.lower()
    stem_lower, _ = os.path.splitext(lower_name)
    if lower_name in RESERVED_NAMES or stem_lower in RESERVED_NAMES:
        return sanitized + "_"
    return sanitized


class RenameDropTarget(wx.FileDropTarget):
    """ファイルのDnDを受け取り、指定されたハンドラへ渡す"""

    def __init__(self, handler):
        super().__init__()
        self.handler = handler

    def OnDropFiles(self, x, y, filenames):
        self.handler(filenames)
        return True


class RenameFrame(wx.Frame):
    """メインウィンドウ"""

    def __init__(self):
        super().__init__(None, title="整名", size=(900, 520))
        self._build_ui()
        self.Centre()
        self.Show()

    def _build_ui(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        # 左右にラベルと読み取り専用のマルチラインテキストを配置
        left_box = wx.BoxSizer(wx.VERTICAL)
        right_box = wx.BoxSizer(wx.VERTICAL)

        left_label = wx.StaticText(panel, label="変更前")
        right_label = wx.StaticText(panel, label="変更後")
        left_label.SetFont(font)
        right_label.SetFont(font)

        self.left_text = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.TE_DONTWRAP,
        )
        self.right_text = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.TE_DONTWRAP,
        )
        self.left_text.SetFont(font)
        self.right_text.SetFont(font)

        self.left_text.SetDropTarget(RenameDropTarget(self.handle_drop))
        self.right_text.SetDropTarget(RenameDropTarget(self.handle_drop))

        left_box.Add(left_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        left_box.Add(self.left_text, 1, wx.EXPAND | wx.ALL, 8)
        right_box.Add(right_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        right_box.Add(self.right_text, 1, wx.EXPAND | wx.ALL, 8)

        sizer.Add(left_box, 1, wx.EXPAND)
        sizer.Add(right_box, 1, wx.EXPAND)
        panel.SetSizer(sizer)

    def handle_drop(self, paths):
        """DnDされたファイル/フォルダをリネームし、結果を表示"""
        for path in paths:
            self._process_path(path)

    def _process_path(self, path: str):
        """ファイルとフォルダの両方に対応して処理する"""
        if os.path.isfile(path):
            self._rename_path(path)
        elif os.path.isdir(path):
            self._process_directory(path)
        else:
            self._append_result(os.path.basename(path), "ファイル/フォルダ以外はスキップ")

    def _process_directory(self, path: str):
        """フォルダ配下を再帰的に処理した後でフォルダ名も変換する"""
        try:
            entries = [os.path.join(path, name) for name in os.listdir(path)]
        except OSError as err:
            self._append_result(os.path.basename(path), f"エラー: {err}")
            return

        for entry in entries:
            self._process_path(entry)

        self._rename_path(path)

    def _rename_path(self, path: str):
        """単一のファイルまたはフォルダをリネームする"""
        original_name = os.path.basename(path)
        new_name = make_safe_name(original_name)
        parent_dir = os.path.dirname(path)
        new_path = os.path.join(parent_dir, new_name)

        if os.path.abspath(path) == os.path.abspath(new_path):
            self._append_result(original_name, new_name)
            return

        if os.path.exists(new_path):
            self._append_result(original_name, f"{new_name}（同名が存在するため未変更）")
            return

        try:
            os.rename(path, new_path)
            self._append_result(original_name, new_name)
        except OSError as err:
            self._append_result(original_name, f"エラー: {err}")

    def _append_result(self, before: str, after: str):
        """左右のテキストボックスに結果を追記"""
        self.left_text.AppendText(f"{before}\n")
        self.right_text.AppendText(f"{after}\n")


def main():
    app = wx.App(False)
    RenameFrame()
    app.MainLoop()


if __name__ == "__main__":
    main()
