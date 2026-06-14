import numpy as np
from sortedcontainers import SortedList
from environment.enodeb import eNodeB
from simulator.ue_arrival_event import UEArrivalEvent
from simulator.scheduler_event import SchedulerEvent

class MainLoop:

    def __init__(self):
        self.network    = eNodeB()
        self.event_list = SortedList(key=lambda x: x.time)

    def run(self, lam: float, max_time: float) -> dict:
        """
        Uruchamia symulację dla danej intensywności λ [1/ms].
        Zwraca słownik ze statystykami.
        """
        self.network.initialize()
        self.event_list.clear()

        # pierwsze zdarzenia startowe
        first_arrival = np.random.exponential(1.0 / lam)
        self.event_list.add(UEArrivalEvent(time=first_arrival, lam=lam))
        self.event_list.add(SchedulerEvent(time=eNodeB.S))

        # główna pętla
        while self.event_list:
            event = self.event_list.pop(index=0)

            if event.time > max_time:
                break
            event.execute(self.network, self.event_list)

        self.network.simulation_end_time = max_time
        return self._collect_stats(lam, max_time)

    def _collect_stats(self, lam: float, max_time: float) -> dict:
        completed = self.network.completed_ues

        if completed:
            avg_wait     = np.mean([c["wait_time"] for c in completed])         # ms
            avg_user_tp  = np.mean([c["avg_tp_kbps"] for c in completed])       # kbit/ms
            all_user_tps = [c["avg_tp_kbps"] for c in completed]
        else:
            avg_wait     = 0.0
            avg_user_tp  = 0.0
            all_user_tps = []

        system_tp = (self.network.total_system_bits / max_time)*1000.0   # kbit/ms = Gbit/s * 1e-6

        return {
            "lambda"        : lam,
            "avg_wait_ms"   : avg_wait,
            "system_tp_kbps": system_tp,         # kbit/ms
            "avg_user_tp_kbps": avg_user_tp,
            "user_tps"      : all_user_tps,
            "num_completed" : len(completed),
        }
