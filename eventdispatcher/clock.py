__author__ = 'calvin'

from builtins import range
from collections import deque, Counter
from typing import Callable


class Clock:
    clock: "Clock"

    def __init__(self, *args, **kwargs) -> None:
        self.scheduled_funcs: Counter[Callable[[], None]] = Counter()
        self.queue: deque[Callable[[], None]] = deque([])
        self._running: int = 0
        Clock.clock = self
        super().__init__(*args, **kwargs)

    @staticmethod
    def get_running_clock() -> "Clock":
        return Clock.clock

    def _run_scheduled_events(self) -> None:
        events = self.queue
        funcs = self.scheduled_funcs
        popleft = events.popleft
        for i in range(len(events)):
            f = popleft()
            funcs[f] -= 1
            f()

    def run(self) -> None:
        # Use all local variables to speed up the loop
        _run_scheduled_events = self._run_scheduled_events
        self._running = 1
        while self._running:
            _run_scheduled_events()
