import random
from environment.ue import UserEquipment

class eNodeB:
    K = 10
    L = 3
    S = 1.0
    EPSILON = 0.1

    def __init__(self):
        self.initialize()

    def initialize(self):
        self.active_ues = {}
        self.no_users = 0
        self.total_system_bits = 0.0
        self.completed_ues = []

    def add_ue(self, arrival_time: float) -> int:
        self.no_users += 1
        ue = UserEquipment(self.no_users, self.K, arrival_time)
        self.active_ues[self.no_users] = ue
        return self.no_users

    def remove_ue(self, ue_id: int, current_time: float):
        if ue_id in self.active_ues:
            ue = self.active_ues.pop(ue_id)
            wait_time = current_time - ue.arrival_time
            avg_tp = (ue.total_bits_received / wait_time) * 1000.0 if wait_time > 0 else 0.0
            self.completed_ues.append({
                "ue_id": ue_id,
                "wait_time": wait_time,
                "avg_tp_kbps": avg_tp,
                "data_total": ue.data_total,
            })

    def run_scheduler(self, current_time: float) -> list:
        if not self.active_ues:
            return []

        ues = list(self.active_ues.values())
        avg_tps = {ue.ue_id: ue.get_avg_throughput(current_time) for ue in ues}
        alloc_counts = {ue.ue_id: 0 for ue in ues}
        allocated_rates = {ue.ue_id: 0.0 for ue in ues}

        # Przydział zasobów (Algorytm Proportional Fairness)
        for k in range(self.K):
            best_ue_id = None
            best_score = -1.0
            for ue in ues:
                if alloc_counts[ue.ue_id] >= self.L:
                    continue
                score = ue.rb_rates[k] / avg_tps[ue.ue_id]
                if score > best_score:
                    best_score = score
                    best_ue_id = ue.ue_id

            if best_ue_id is not None:
                alloc_counts[best_ue_id] += 1
                allocated_rates[best_ue_id] += self.active_ues[best_ue_id].rb_rates[k]

        done_ues = []
        for ue in ues:
            rate = allocated_rates[ue.ue_id]
            if rate == 0:
                continue

            bits_sent = rate * (self.S / 1000.0)
            ue.total_bits_received += bits_sent

            # Symulacja błędów transmisji
            if random.random() >= self.EPSILON:
                ue.data_received += bits_sent
                self.total_system_bits += bits_sent
                if ue.data_received >= ue.data_total:
                    done_ues.append(ue.ue_id)

        return done_ues

    def update_propagation(self, ue_id: int):
        if ue_id in self.active_ues:
            self.active_ues[ue_id].rb_rates = [random.uniform(20.0, 800.0) for _ in range(self.K)]