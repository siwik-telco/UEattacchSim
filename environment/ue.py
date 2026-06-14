import random

class UserEquipment:
    def __init__(self, ue_id: int, num_rb: int, arrival_time: float):
        self.ue_id = ue_id
        self.arrival_time = arrival_time
        # random.randint(1, 10) w przeciwieństwie do numpy zwraca wartości z przedziału domkniętego [1, 10]
        self.data_total = float(random.randint(1, 10) * 25)
        self.data_received = 0.0

        # Inicjalizacja stawek dla każdego bloku zasobów używając pythonowskiego random
        self.rb_rates = [random.uniform(20.0, 800.0) for _ in range(num_rb)]

        self.total_bits_received = 0.0
        self._arrival_time = arrival_time

    def get_avg_throughput(self, current_time: float) -> float:
        elapsed = current_time - self._arrival_time
        if elapsed <= 0 or self.total_bits_received == 0:
            return 1e-9  # Bardzo mała wartość, by nadać wysoki priorytet na start
        return (self.total_bits_received / elapsed) * 1000.0