"""System-tray entry point: worker thread + pystray icon."""

import logging
import threading

import pystray

from . import activity
from .icons import make_icon
from .idle_monitor import seconds_since_last_input
from .session_state import is_locked
from .worker import run_once

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("idel_faker")

IDLE_THRESHOLD = 60  # seconds idle before injecting
POLL_INTERVAL = 5    # seconds between checks


def _inject() -> None:
    activity.send_f15()
    activity.nudge_mouse()


class TrayApp:
    def __init__(self):
        self._paused = threading.Event()      # set => paused
        self._stop = threading.Event()        # set => shutting down
        self._state = "green"
        self.icon = pystray.Icon(
            "idel-faker",
            make_icon("green"),
            "idel-faker",
            menu=pystray.Menu(
                pystray.MenuItem(self._pause_label, self._toggle_pause),
                pystray.MenuItem("Quit", self._quit),
            ),
        )

    def _pause_label(self, _item) -> str:
        return "Resume" if self._paused.is_set() else "Pause"

    def _toggle_pause(self, _icon, _item) -> None:
        if self._paused.is_set():
            self._paused.clear()
        else:
            self._paused.set()
        self.icon.update_menu()

    def _quit(self, _icon, _item) -> None:
        self._stop.set()
        self.icon.stop()

    def _set_state(self, state: str) -> None:
        if state != self._state:
            self._state = state
            self.icon.icon = make_icon(state)

    def _worker(self) -> None:
        try:
            while not self._stop.wait(POLL_INTERVAL):
                paused = self._paused.is_set()
                activity.keep_awake(not paused)
                result = run_once(
                    paused=paused,
                    idle_fn=seconds_since_last_input,
                    locked_fn=is_locked,
                    inject_fn=_inject,
                    threshold=IDLE_THRESHOLD,
                )
                if result == "paused":
                    self._set_state("grey")
                elif result == "locked":
                    self._set_state("orange")
                else:
                    self._set_state("green")
                log.info("tick: %s", result)
        finally:
            activity.keep_awake(False)

    def run(self) -> None:
        thread = threading.Thread(target=self._worker, daemon=True)
        thread.start()
        try:
            self.icon.run()
        finally:
            self._stop.set()
            thread.join(timeout=POLL_INTERVAL + 2)


def main() -> None:
    TrayApp().run()


if __name__ == "__main__":
    main()
