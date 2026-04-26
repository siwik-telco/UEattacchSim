from abc import ABC, abstractmethod
from environment.departurehall import DepartureHall
from sortedcontainers import SortedList

class Event(ABC):

    time: int = 0 # time of execution

    def __init__(self, time:int) -> None:
        super().__init__()
        self.time = time


    @abstractmethod
    def execute(self, wireless_network:DepartureHall, event_list: SortedList):
        pass