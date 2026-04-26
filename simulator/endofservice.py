from environment.departurehall import DepartureHall
from simulator.event import Event
from sortedcontainers import SortedList

class EndOfServiceM3(Event):

    device_id: int = None
    def __init__(self, service_desk_id:int, time:int) -> None:
        Event.__init__(self,time=time)
        self.service_desk_id = service_desk_id

    def execute(self, departurehall: DepartureHall, event_list: SortedList):
   
        departurehall.removeClientFromServiceDesk(self.service_desk_id)

class EndOfService(Event):

    device_id: int = None
    def __init__(self, service_desk_id:int, time:int) -> None:
        Event.__init__(self,time=time)
        self.service_desk_id = service_desk_id

    def execute(self, departurehall: DepartureHall, event_list: SortedList):
   
        departurehall.removeClientFromServiceDesk(self.service_desk_id)

        any_free, service_desk_id = departurehall.findFreeServiceDesk()
        if any_free and departurehall.isAnyClient():
            departurehall.putClientToServiceDesk(service_desk_id)
            time = self.time+departurehall.getTPW()
            event_list.add(EndOfService(service_desk_id=service_desk_id, time=time))

        
