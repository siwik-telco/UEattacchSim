from sortedcontainers import SortedList
from simulator.event import Event

class SchedulerEvent(Event):
    """
    Zdarzenie cykliczne: scheduler PF przydziela RB co S ms.
    Po każdym przydziale sprawdza, które UE zakończyły odbiór danych.
    """

    def __init__(self, time: float) -> None:
        super().__init__(time)

    def execute(self, network, event_list: SortedList):
        # uruchom algorytm PF
        network.run_scheduler(self.time)

        # usuń UE, które odebrały wszystkie dane
        done = network.get_done_ues()
        for ue in done:
            network.remove_ue(ue.ue_id, self.time)

        # zaplanuj następny slot schedulera
        event_list.add(SchedulerEvent(time=self.time + network.S))
