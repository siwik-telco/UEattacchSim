import random

class UserEquipment:
    def __init__(self, ue_id: int, num_rb: int, arrival_time: float, seed: int):
        self.ue_id = ue_id
        self.arrival_time = arrival_time
        
        # Własna instancja generatora dla tego konkretnego użytkownika
        self.rng = random.Random(seed)
        
        self.data_total = float(self.rng.randint(1, 10) * 25)
        self.data_received = 0.0

        # Inicjalizacja stawek
        self.rb_rates = [self.rng.uniform(20.0, 800.0) for _ in range(num_rb)]

        self.total_bits_received = 0.0
        self._arrival_time = arrival_time

    def get_avg_throughput(self, current_time: float) -> float:
        elapsed = current_time - self._arrival_time
        if elapsed <= 0 or self.total_bits_received == 0:
            return 1e-9  
        return (self.total_bits_received / elapsed) * 1000.0