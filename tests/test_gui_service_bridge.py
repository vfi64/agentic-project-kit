import sys
from threading import Event, get_ident
import time
from types import SimpleNamespace

import pytest

from agentic_project_kit.gui_service_bridge import TkServiceBridge


class Var:
    def __init__(self, **kwargs):
        self.value = kwargs.get("value")

    def set(self, value):
        self.value = value


class Root:
    def __init__(self):
        self.callbacks = {}
        self.next_id = 0
        self.close = "original-close-command"
        self.grab = None
        self.main_thread = get_ident()

    def protocol(self, name, command=None):
        assert get_ident() == self.main_thread
        if command is not None:
            self.close = command
        return self.close

    def grab_current(self):
        return self.grab

    def after(self, delay, callback):
        self.next_id += 1
        self.callbacks[self.next_id] = callback
        return self.next_id

    def after_cancel(self, ident):
        self.callbacks.pop(ident, None)

    def wait_variable(self, var):
        deadline = time.monotonic() + 3
        while not var.value:
            assert time.monotonic() < deadline
            ident = next(iter(self.callbacks))
            self.callbacks.pop(ident)()
            time.sleep(0.001)


class Widget:
    def __init__(self, parent, **kwargs):
        self.root = parent.root if isinstance(parent, Widget) else parent
        assert get_ident() == self.root.main_thread
        self.destroyed = False

    def title(self, text):
        pass

    def transient(self, root):
        pass

    def protocol(self, *args):
        pass

    def pack(self, **kwargs):
        pass

    def start(self, speed):
        pass

    def stop(self):
        pass

    def grab_set(self):
        self.root.grab = self

    def grab_release(self):
        self.root.grab = None

    def lift(self):
        pass

    def destroy(self):
        self.destroyed = True

    def winfo_exists(self):
        return not self.destroyed


@pytest.fixture
def bridge(monkeypatch):
    ttk = SimpleNamespace(Label=Widget, Progressbar=Widget)
    monkeypatch.setitem(sys.modules, "tkinter", SimpleNamespace(Toplevel=Widget, BooleanVar=Var, ttk=ttk))
    monkeypatch.setitem(sys.modules, "tkinter.ttk", ttk)
    return TkServiceBridge(Root())


def test_modal_bridge_keeps_ui_events_on_main_thread_and_blocks_reentry(bridge):
    release = Event()
    events = []

    def heartbeat():
        events.append(get_ident())
        assert bridge.busy
        with pytest.raises(RuntimeError, match="Another Kit"):
            bridge.call(lambda: None, label="second")
        bridge.root.close()  # The root close request lifts the progress dialog.
        release.set()

    bridge.root.after(1, heartbeat)
    worker_thread = bridge.call(lambda: (release.wait(2), get_ident())[1], label="test")
    assert events == [bridge.root.main_thread]
    assert worker_thread != bridge.root.main_thread
    assert not bridge.busy
    assert bridge.operation.pending is None
    assert bridge.root.close == "original-close-command"
    assert bridge.root.grab is None
    assert not bridge.root.callbacks


def test_worker_failure_restores_modal_state_and_previous_grab(bridge):
    previous = Widget(bridge.root)
    previous.grab_set()
    with pytest.raises(ValueError, match="failed"):
        bridge.call(lambda: (_ for _ in ()).throw(ValueError("failed")), label="failure")
    assert not bridge.busy
    assert bridge.root.grab is previous
    assert bridge.root.close == "original-close-command"
    assert bridge.call(lambda: "retry", label="retry") == "retry"
