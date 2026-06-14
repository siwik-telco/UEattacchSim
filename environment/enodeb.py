import numpy as np
from environment.ue import UserEquipment

class eNodeB:
    """
    Stacja bazowa LTE.

    Parametry:
      k       – liczba bloków zasobów RB
      l       – max RB przydzielanych jednemu UE na raz
      s       – interwał schedulera [ms]
      epsilon – prawdopodobieństwo błędu transmisji
    """

    K       = 10      # liczba bloków zasobów
    L       = 3       # max RB / UE / slot
    S       = 1.0     # interwał schedulera [ms]
    EPSILON = 0.1     # prawdopodobieństwo błędu transmisji

    def __init__(self):
        self.active_ues: dict[int, UserEquipment] = {}   # ue_id -> UE
        self.no_users = 0

        # statystyki globalne
        self.total_system_bits   = 0.0   # kbit – poprawnie przesłane przez BS
        self.simulation_end_time = 0.0

        # lista statystyk zakończonych UE
        self.completed_ues: list[dict] = []

    def initialize(self):
        self.active_ues          = {}
        self.no_users            = 0
        self.total_system_bits   = 0.0
        self.simulation_end_time = 0.0
        self.completed_ues       = []

    # ── zarządzanie UE ──────────────────────────────────────────────────────

    def add_ue(self, arrival_time: float) -> int:
        self.no_users += 1
        ue = UserEquipment(self.no_users, self.K, arrival_time)
        self.active_ues[self.no_users] = ue
        return self.no_users

    def remove_ue(self, ue_id: int, current_time: float):
        if ue_id in self.active_ues:
            ue = self.active_ues.pop(ue_id)
            wait_time = current_time - ue.arrival_time
            avg_tp    = (ue.total_bits_received / wait_time)*1000.0 if wait_time > 0 else 0.0
            self.completed_ues.append({
                "ue_id"     : ue_id,
                "wait_time" : wait_time,          # ms
                "avg_tp_kbps": avg_tp,            # kbit/s (kbit/ms = Mbit/s * 1e-3 → zostawiamy w kbit/ms)
                "data_total": ue.data_total,
            })

    # ── algorytm Proportional Fairness ──────────────────────────────────────

    def run_scheduler(self, current_time: float):
        """
        Dla każdego z K bloków zasobów przydziela go UE o najwyższym stosunku
        r_k(i) / avg_throughput(i).
        Każde UE może dostać co najwyżej L bloków.
        Transmisja na przydzielonym RB trwa S ms; z prawdopodobieństwem epsilon
        dane NIE docierają (błąd), ale UE i tak rejestruje czas w sieci.
        """
        if not self.active_ues:
            return

        ues = list(self.active_ues.values())
        rb_allocations: dict[int, list[int]] = {ue.ue_id: [] for ue in ues}

        for k in range(self.K):
            best_ue   = None
            best_score = -1.0
            for ue in ues:
                # sprawdź czy nie przekroczono limitu L
                if len(rb_allocations[ue.ue_id]) >= self.L:
                    continue
                avg_tp = ue.avg_throughput(current_time)
                score  = ue.rb_rates[k] / avg_tp
                if score > best_score:
                    best_score = score
                    best_ue    = ue
            if best_ue is not None:
                rb_allocations[best_ue.ue_id].append(k)

        # realizacja transmisji
        for ue in ues:
            assigned_rbs = rb_allocations[ue.ue_id]
            if not assigned_rbs:
                continue
            total_rate = sum(ue.rb_rates[k] for k in assigned_rbs)  # kbit/s
            # dane wysłane w ciągu S ms = rate * S [kbit]
            bits_sent = total_rate * (self.S/1000.0)
            # aktualizacja średniej przepływności (zawsze, niezależnie od błędu)
            ue.total_bits_received += bits_sent
            # z prawdopodobieństwem (1-epsilon) dane są poprawnie odebrane
            if np.random.random() >= self.EPSILON:
                ue.data_received += bits_sent
                self.total_system_bits += bits_sent

    # ── zmiana warunków propagacyjnych ──────────────────────────────────────

    def update_propagation(self, ue_id: int):
        if ue_id in self.active_ues:
            ue = self.active_ues[ue_id]
            ue.rb_rates = np.random.uniform(20.0, 800.0, size=self.K)

    def get_done_ues(self) -> list:
        return [ue for ue in self.active_ues.values() if ue.is_done()]
