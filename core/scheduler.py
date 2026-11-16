"""Background loop that wakes the Brain periodically. Lives only as long as the host process does."""
import threading
import time
from typing import Dict, Optional

from core.brain import Brain


class Scheduler:
    TICK_S = 20

    def __init__(self, store, guard, brain: Brain):
        self.store, self.guard, self.brain = store, guard, brain
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self.last_run = 0.0
        self.last_result = ""

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="zyphere-scheduler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    @property
    def alive(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def _loop(self) -> None:
        while not self._stop.wait(self.TICK_S):
            try:
                self.tick()
            except Exception as e:  # the loop must never die
                print(f"scheduler error: {type(e).__name__}")

    def tick(self) -> None:
        if not self.guard.autonomy_enabled():
            return
        try:
            interval = max(1, int(self.store.get_setting("interval_min", 10))) * 60
        except (TypeError, ValueError):
            interval = 600
        if time.time() - self.last_run >= interval:
            self.run_once(force=False)

    def run_once(self, force: bool = False) -> Dict[str, object]:
        if not self._lock.acquire(blocking=False):
            return {"ran": False, "reason": "another cycle is running"}
        try:
            self.last_run = time.time()
            res = self.brain.cycle(force=force)
            self.last_result = str(res.get("reason", ""))
            return res
        finally:
            self._lock.release()
