from abc import ABC, abstractmethod
from sortedcontainers import SortedList

class Event(ABC):
    time: float = 0.0

    def __init__(self, time: float) -> None:
        super().__init__()
        self.time = time

    @abstractmethod
    def execute(self, network, event_list: SortedList):
        pass
