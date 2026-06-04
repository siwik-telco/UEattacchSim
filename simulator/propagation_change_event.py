import numpy as np
from sortedcontainers import SortedList
from simulator.event import Event

class PropagationChangeEvent(Event):
    """
    Zdarzenie: zmiana warunków propagacyjnych dla konkretnego UE.
    τ ~ Exp(1/10 ms).
    """

    def __init__(self, time: float, ue_id: int) -> None:
        super().__init__(time)
        self.ue_id = ue_id

    def execute(self, network, event_list: SortedList):
        if self.ue_id not in network.active_ues:
            return   # UE już opuścił sieć
        network.update_propagation(self.ue_id)
        tau = np.random.exponential(10.0)
        event_list.add(PropagationChangeEvent(time=self.time + tau, ue_id=self.ue_id))
