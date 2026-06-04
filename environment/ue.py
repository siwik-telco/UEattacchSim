import numpy as np

class UserEquipment:
    """
    Reprezentuje pojedynczego użytkownika (UE) w komórce LTE.

    d   ~ Uniform{1..10} × 25 kbit   (przyjmujemy kbit, bo przy kbit/s i 50ms kryterium
                                        wartości w Mbit byłyby fizycznie nieosiągalne)
    r_k ~ Uniform[20, 800] kbit/s per RB
    """

    def __init__(self, ue_id: int, num_rb: int, arrival_time: float):
        self.ue_id        = ue_id
        self.arrival_time = arrival_time  # ms

        # d ∈ {1,...,10} × 25 kbit
        self.data_total    = float(np.random.randint(1, 11) * 25)   # kbit
        self.data_received = 0.0                                      # kbit

        # warunki propagacyjne: r_k ~ Uniform[20, 800] kbit/s per RB
        self.rb_rates = np.random.uniform(20.0, 800.0, size=num_rb)  # kbit/s

        # do PF: suma poprawnie odebranych bitów i czas w sieci
        self.total_bits_received = 0.0   # kbit
        # Inicjalizacja z bardzo małą wartością aby uniknąć dzielenia przez 0
        # i aby nowi UE mieli wysoki priorytet PF
        self._arrival_time = arrival_time

    def avg_throughput(self, current_time: float) -> float:
        """
        Średnia przepływność od pojawienia się [kbit/ms].
        Inicjalizacja z epsilon aby nowi UE mieli wysoki priorytet PF.
        """
        elapsed = current_time - self._arrival_time
        if elapsed <= 0 or self.total_bits_received == 0:
            return 1e-9   # bardzo mała wartość -> wysoki priorytet PF
        return self.total_bits_received / elapsed   # kbit/ms

    def is_done(self) -> bool:
        return self.data_received >= self.data_total
