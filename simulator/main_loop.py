import heapq
import itertools
import random
from environment.enodeb import eNodeB

class Simulator:
    def __init__(self, seed: int):
        self.base_seed = seed
        self.rng_arrival = random.Random(seed + 2)
        self.rng_prop_tau = random.Random(seed + 3)
        self.network = eNodeB(seed + 10)
        self.event_queue = []
        self.event_counter = itertools.count()

    def push_event(self, time: float, event_type: str, args: dict = None):
        heapq.heappush(self.event_queue, (time, next(self.event_counter), event_type, args))

    def run(self, lam: float, max_time: float, track_transient: bool = False) -> dict:
        self.network.initialize()
        self.event_queue.clear()
        self.event_counter = itertools.count()

        first_arrival = self.rng_arrival.expovariate(lam)
        self.push_event(first_arrival, 'arrival', {'lam': lam})
        self.push_event(self.network.S, 'scheduler')

        # Struktura do wykresu fazy początkowej
        transient_data = {"time": [], "queue_length": []}
        sample_interval = 1000.0  # Próbkowanie stanu systemu co 1000 ms (1 s)
        next_sample_time = sample_interval

        while self.event_queue:
            time, _, event_type, args = heapq.heappop(self.event_queue)

            if time > max_time:
                break
            
            # Próbkowanie długości kolejki w czasie
            if track_transient and time >= next_sample_time:
                transient_data["time"].append(time)
                transient_data["queue_length"].append(len(self.network.active_ues))
                next_sample_time += sample_interval

            if len(self.network.active_ues) > 1000:
                # Poluzowane kryterium zatrzymania, by nie przerywać za wcześnie przy badaniu CI
                pass

            if event_type == 'arrival':
                lam_val = args['lam']
                ue_id = self.network.add_ue(time)

                inter_arrival = self.rng_arrival.expovariate(lam_val)
                self.push_event(time + inter_arrival, 'arrival', {'lam': lam_val})

                tau = self.rng_prop_tau.expovariate(1.0 / 10.0)
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
                    tau = self.rng_prop_tau.expovariate(1.0 / 10.0)
                    self.push_event(time + tau, 'prop_change', {'ue_id': ue_id})

        completed = self.network.completed_ues
        if completed:
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
            "transient_data": transient_data
        }