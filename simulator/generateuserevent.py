from simulator.event import Event
from simulator.endofservice import EndOfService
from environment.departurehall import DepartureHall
from sortedcontainers import SortedList
import numpy as np

class GenerateUserEvent(Event):

    def __init__(self, time:int) -> None:
        Event.__init__(self, time=time)

    def execute(self, departurehall: DepartureHall, event_list: SortedList):

        # add statistics
        id = departurehall.generate_client()
        print(f'Generated client with id {id}')

        # generate new event
        time = departurehall.getTPG() + self.time
        event_list.add(GenerateUserEvent(time=time))

        any_free, service_desk_id = departurehall.findFreeServiceDesk()
        if any_free:
            departurehall.putClientToServiceDesk(service_desk_id)
            time = self.time+departurehall.getTPW()
            event_list.add(EndOfService(service_desk_id=service_desk_id, time=time))

class GenerateUserEventM3(Event):

    def __init__(self, time:int) -> None:
        Event.__init__(self, time=time)

    def execute(self, departurehall: DepartureHall, event_list: SortedList):

        # add statistics
        id = departurehall.generate_client()
        print(f'Generated client with id {id}')

        # generate new event
        time = departurehall.getTPG() + self.time
        event_list.add(GenerateUserEventM3(time=time))
        

        # generate user report event
       