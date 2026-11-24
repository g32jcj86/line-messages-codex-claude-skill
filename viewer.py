"""Local Tk viewer, with no HTTP listener or HTML rendering."""
import os
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

from archive import INBOX, archive_status, import_exports, search


def main():
    window = tk.Tk()
    window.title("LINE 文字封存")
    window.geometry("900x620")
    controls = ttk.Frame(window, padding=12)
    controls.pack(fill="x")
    chat = ttk.Combobox(controls, state="readonly", width=28)
    chat.grid(row=0, column=0, padx=4)
    keyword = ttk.Entry(controls, width=25)
    keyword.grid(row=0, column=1, padx=4)
    status = ttk.Label(window, padding=8)
    status.pack(fill="x")
    output = tk.Text(window, wrap="word", padx=12, pady=8, state="disabled")
    scrollbar = ttk.Scrollbar(window, command=output.yview)
    output.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    output.pack(fill="both", expand=True)
    next_page = None
    filters = ("", "")

    def display(append=False):
        nonlocal next_page, filters
        if not append:
            filters = (chat.get(), keyword.get())
        try:
            page = search(*filters, before_id=next_page if append else None)
        except sqlite3.Error:
            status.configure(text="暫時無法讀取封存，請稍後再試。")
            return
        next_page = page["next_before_id"]
        more.configure(state="normal" if next_page is not None else "disabled")
        output.configure(state="normal")
        if not append:
            output.delete("1.0", "end")
        for item in page["messages"]:
            suffix = "（已截短）" if item["text_truncated"] else ""
            output.insert("end", f'{item["local_time"]}  {item["sender"]}  #{item["id"]}\n{item["text"]}{suffix}\n\n')
        output.configure(state="disabled")
        status.configure(text="顯示已匯入的紀錄，最新匯入的項目優先。" if page["messages"]
                         else "沒有符合的已匯入資料。請查看 README 的資料不足排除步驟。")

    def reload_chats():
        try:
            aliases = list(archive_status())
        except sqlite3.Error:
            status.configure(text="暫時無法讀取封存，請稍後再試。")
            return
        chat.configure(values=aliases)
        if aliases and chat.get() not in aliases:
            chat.current(0)
        display()

    def sync():
        try:
            count, skipped = import_exports()
        except (OSError, sqlite3.Error):
            messagebox.showerror("匯入失敗", "請確認匯入資料夾與封存可讀寫，再重試。")
            return
        reload_chats()
        messagebox.showinfo("匯入結果", f"更新 {count} 份匯出檔，略過 {skipped} 份。")

    def open_inbox():
        INBOX.mkdir(parents=True, exist_ok=True)
        os.startfile(INBOX)

    ttk.Button(controls, text="搜尋", command=display).grid(row=0, column=2, padx=4)
    more = ttk.Button(controls, text="載入更多", command=lambda: display(append=True))
    more.grid(row=0, column=3, padx=4)
    ttk.Button(controls, text="立即匯入", command=sync).grid(row=0, column=4, padx=4)
    ttk.Button(controls, text="開啟匯入資料夾", command=open_inbox).grid(row=0, column=5, padx=4)
    chat.bind("<<ComboboxSelected>>", lambda _: display())
    keyword.bind("<Return>", lambda _: display())
    reload_chats()
    window.mainloop()


if __name__ == "__main__":
    main()
