"""Tk-only modal adapter: keep redraws alive without concurrent user actions."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from agentic_project_kit.gui_services import BackgroundOperation


T = TypeVar("T")


class TkServiceBridge:
    def __init__(self, root: Any) -> None:
        self.root = root
        self.operation = BackgroundOperation()
        self.busy = False

    def call(self, operation: Callable[[], T], *, label: str) -> T:
        import tkinter as tk
        from tkinter import ttk

        if self.busy:
            raise RuntimeError("Another Kit action is running.")
        self.busy = True
        dialog = tk.Toplevel(self.root)
        dialog.title("Kit action in progress")
        dialog.transient(self.root)
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)
        ttk.Label(dialog, text=label, padding=16).pack(fill="x")
        ttk.Label(
            dialog,
            text="Please wait. The action cannot be cancelled or rolled back here.",
            padding=16,
        ).pack(fill="x")
        progress = ttk.Progressbar(dialog, mode="indeterminate", length=320)
        progress.pack(fill="x", padx=16, pady=16)
        done = tk.BooleanVar(master=self.root, value=False)
        previous_close = self.root.protocol("WM_DELETE_WINDOW")
        previous_grab = self.root.grab_current()
        poll_id = None

        def poll() -> None:
            nonlocal poll_id
            if self.operation.pending is not None and self.operation.pending.done():
                done.set(True)
            else:
                poll_id = self.root.after(50, poll)

        try:
            self.root.protocol("WM_DELETE_WINDOW", lambda: dialog.lift())
            dialog.grab_set()
            progress.start(8)
            self.operation.start(operation)
            poll_id = self.root.after(50, poll)
            # Tk's modal event loop keeps all widget access on the UI thread.
            self.root.wait_variable(done)
            return self.operation.consume()
        finally:
            if poll_id is not None:
                self.root.after_cancel(poll_id)
            progress.stop()
            dialog.grab_release()
            dialog.destroy()
            if previous_grab is not None and previous_grab.winfo_exists():
                previous_grab.grab_set()
            self.root.protocol("WM_DELETE_WINDOW", previous_close)
            self.busy = False
