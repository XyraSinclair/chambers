# bobs_service/queue.py — fixture: clean file (no findings; the sweep must
# not manufacture work where there is none).
import collections


class Queue:
    def __init__(self):
        self._items = collections.deque()

    def push(self, item):
        self._items.append(item)

    def pop(self):
        return self._items.popleft()
