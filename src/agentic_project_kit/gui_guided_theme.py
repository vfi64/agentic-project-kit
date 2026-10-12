"""Consistent light colors for fixed-color Kit panels, including dark macOS."""

from __future__ import annotations

from typing import Any


def apply_guided_theme(root: Any) -> None:
    from tkinter import ttk

    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    style.configure("TFrame", background="#ffffff")
    style.configure("TLabel", foreground="#202b33", background="#ffffff")
    style.configure("TButton", padding=(10, 6), foreground="#202b33", background="#edf2f6", borderwidth=1)
    style.map("TButton", background=[("active", "#dce8f3")], foreground=[("disabled", "#7c8994")])
    style.configure("TNotebook", background="#f1f4f6", borderwidth=0)
    style.configure("TNotebook.Tab", padding=(16, 8), background="#e7edf2", foreground="#202b33")
    style.map("TNotebook.Tab", background=[("selected", "#ffffff")])
    style.configure("TCombobox", foreground="#202b33", fieldbackground="#ffffff")
    for widget in ("Label", "Text", "Listbox", "Entry"):
        root.option_add(f"*{widget}.foreground", "#202b33")
        root.option_add(f"*{widget}.background", "#ffffff")
    root.option_add("*Text.insertBackground", "#202b33")
