from environment.departurehall import DepartureHall
from simulator.generateuserevent import GenerateUserEvent, GenerateUserEventM3
from simulator.endofservice import EndOfService
from simulator.endofservice import EndOfServiceM3
from sortedcontainers import SortedList


class MainLoop:

    departure_hall:DepartureHall



    
    event_list:SortedList

    def __init__(self) -> None:
        self.departure_hall = DepartureHall()
        self.event_list = SortedList(key=lambda x: x.time)

    def runM1(self, max_time):
        time=0
        time2TPG=self.departure_hall.getTPG()
        time2TPW=[-1,-1,-1]
        while time < max_time:
            no_event=False
            while no_event == False:
                no_event=True
                if time==time2TPG:
                    id = self.departure_hall.generate_client()
                    print(f'Generated client with id {id}')
                    time2TPG=self.departure_hall.getTPG()+time
                    no_event=False
                for xx in range(self.departure_hall.no_service_Desks):
                    if time==time2TPW[xx]:
                        self.departure_hall.removeClientFromServiceDesk(xx)
                        time2TPW[xx]=-1
                        no_event=False

                any_free, service_desk_id = self.departure_hall.findFreeServiceDesk()
                if any_free and self.departure_hall.isAnyClient():
                    self.departure_hall.putClientToServiceDesk(service_desk_id)
                    time2TPW[service_desk_id] = time+self.departure_hall.getTPW()
                    no_event=False

            # increase time - TBD more effectively
            time=time+1



    def runM2(self, max_time):

        self.departure_hall.initialize()
        self.event_list.add(GenerateUserEvent(time=0))

        # MAIN LOOP
        time=0
        while time < max_time:
            time = self.event_list[0].time
            print(f'Simulation time:{time} ms')
            event = self.event_list.pop(index=0)
            event.execute(self.departure_hall, self.event_list)

    def runM3(self, max_time):

        self.departure_hall.initialize()
        self.event_list.add(GenerateUserEventM3(time=0))

        # MAIN LOOP
        time=0
        while time < max_time:
            time = self.event_list[0].time
            print(f'Simulation time:{time} ms')
            event = self.event_list.pop(index=0)
            event.execute(self.departure_hall, self.event_list)

        
            any_free, service_desk_id = self.departure_hall.findFreeServiceDesk()
            if any_free and self.departure_hall.isAnyClient():
                self.departure_hall.putClientToServiceDesk(service_desk_id)
                time_tmp = time+self.departure_hall.getTPW()
                self.event_list.add(EndOfServiceM3(service_desk_id=service_desk_id, time=time_tmp))





