import numpy as np
from sortedcontainers import SortedList
from simulator.event import Event
from simulator.propagation_change_event import PropagationChangeEvent

class UEArrivalEvent(Event):
    """
    Zdarzenie: pojawienie się nowego UE w komórce.
    Czas między zdarzeniami ~ Exp(lambda) [ms].
    """

    def __init__(self, time: float, lam: float) -> None:
        super().__init__(time)
        self.lam = lam   # intensywność zgłoszeń [1/ms]

    def execute(self, network, event_list: SortedList):
        # rejestracja UE
        ue_id = network.add_ue(arrival_time=self.time)

        # planowanie następnego przyjścia
        inter_arrival = np.random.exponential(1.0 / self.lam)   # ms
        event_list.add(UEArrivalEvent(time=self.time + inter_arrival, lam=self.lam))

        # planowanie pierwszej zmiany warunków propagacyjnych dla nowego UE
        tau = np.random.exponential(10.0)   # τ ~ Exp(1/10) ms
        event_list.add(PropagationChangeEvent(time=self.time + tau, ue_id=ue_id))
