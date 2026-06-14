import heapq
import itertools
import random
from environment.enodeb import eNodeB

class Simulator:
    def __init__(self):
        self.network = eNodeB()
        self.event_queue = []
        self.event_counter = itertools.count()

    def push_event(self, time: float, event_type: str, args: dict = None):
        # itertools.count gwarantuje stabilność kolejkowania dla takich samych czasów zdarzeń
        heapq.heappush(self.event_queue, (time, next(self.event_counter), event_type, args))

    def run(self, lam: float, max_time: float) -> dict:
        self.network.initialize()
        self.event_queue.clear()
        self.event_counter = itertools.count()

        # Pierwsze wejście UE do systemu
        first_arrival = random.expovariate(lam)
        self.push_event(first_arrival, 'arrival', {'lam': lam})
        self.push_event(self.network.S, 'scheduler')

        while self.event_queue:
            time, _, event_type, args = heapq.heappop(self.event_queue)

            if time > max_time:
                break

            # Early stopping - przerwanie, jeśli system nie nadąża z obsługą (ρ > 1)
            if len(self.network.active_ues) > 500:
                print(f" [!] Zatrzymano dla λ={lam:^6.4f}: brak stabilności (zbyt długa kolejka).")
                break

            if event_type == 'arrival':
                lam_val = args['lam']
                ue_id = self.network.add_ue(time)

                inter_arrival = random.expovariate(lam_val)
                self.push_event(time + inter_arrival, 'arrival', {'lam': lam_val})

                # tau ~ Exp(1/10) w Numpy oznacza skalę 10. W module random podajemy 1/skala
                tau = random.expovariate(1.0 / 10.0)
                self.push_event(time + tau, 'prop_change', {'ue_id': ue_id})

            elif event_type == 'scheduler':
                done_ues = self.network.run_scheduler(time)
                for ue_id in done_ues:
                    self.network.remove_ue(ue_id, time)

                self.push_event(time + self.network.S, 'scheduler')

            elif event_type == 'prop_change':
                ue_id = args['ue_id']
                if ue_id in self.network.active_ues:
                    self.network.update_propagation(ue_id)
                    tau = random.expovariate(1.0 / 10.0)
                    self.push_event(time + tau, 'prop_change', {'ue_id': ue_id})

        completed = self.network.completed_ues
        if completed:
            # Obliczenia bez użycia numpy.mean
            avg_wait = sum(c["wait_time"] for c in completed) / len(completed)
            avg_user_tp = sum(c["avg_tp_kbps"] for c in completed) / len(completed)
            all_user_tps = [c["avg_tp_kbps"] for c in completed]
        else:
            avg_wait = 0.0
            avg_user_tp = 0.0
            all_user_tps = []

        system_tp = (self.network.total_system_bits / max_time) * 1000.0

        return {
            "lambda": lam,
            "avg_wait_ms": avg_wait,
            "system_tp_kbps": system_tp,
            "avg_user_tp_kbps": avg_user_tp,
            "user_tps": all_user_tps,
            "num_completed": len(completed),
        }