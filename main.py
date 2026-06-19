import os
import math
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from simulator.main_loop import Simulator

def compute_stats(data_list: list) -> tuple:
    """Zwraca średnią oraz 95% przedział ufności dla listy wartości."""
    if not data_list:
        return 0.0, 0.0
    n = len(data_list)
    mean = sum(data_list) / n
    if n <= 1:
        return mean, 0.0
    
    variance = sum((x - mean) ** 2 for x in data_list) / (n - 1)
    std_dev = math.sqrt(variance)
    ci95 = 1.96 * (std_dev / math.sqrt(n))
    return mean, ci95

if __name__ == "__main__":
    SIM_TIME = 100_000  # ms - zmiejszone na rzecz replikacji 
    MAX_WAIT = 50.0   # ms
    REPLICATIONS = 10    # Liczba powtórzeń dla każdego punktu (do error barów)

    lambdas = [0.001, 0.005, 0.010, 0.020, 0.030, 0.045,0.05,0.1,0.25]

    results = []
    
    print(f"{'λ [1/ms]':>10} | {'avg_wait [ms]':>14} ±CI | {'sys_tp [k/ms]':>14} ±CI | {'ukończeni (śr)':>14}")
    print("-" * 80)

    for lam in lambdas:
        wait_reps = []
        sys_tp_reps = []
        usr_tp_reps = []
        completed_reps = []
        all_user_tps_agg = [] # Do histogramu (z najlepszej lambdy)

        for rep in range(REPLICATIONS):
            # Dynamiczne, unikalne ziarno dla każdej replikacji
            seed = 74 + int(lam * 1000) + rep * 13 
            sim = Simulator(seed)
            stats = sim.run(lam=lam, max_time=SIM_TIME)
            
            wait_reps.append(stats["avg_wait_ms"])
            sys_tp_reps.append(stats["system_tp_kbps"])
            usr_tp_reps.append(stats["avg_user_tp_kbps"])
            completed_reps.append(stats["num_completed"])
            all_user_tps_agg.extend(stats["user_tps"])

        # Agregacja wyników i wyliczanie CI
        mean_wait, ci_wait = compute_stats(wait_reps)
        mean_sys_tp, ci_sys_tp = compute_stats(sys_tp_reps)
        mean_usr_tp, ci_usr_tp = compute_stats(usr_tp_reps)
        mean_comp = sum(completed_reps) / len(completed_reps)

        results.append({
            "lambda": lam,
            "wait_mean": mean_wait, "wait_ci": ci_wait,
            "sys_tp_mean": mean_sys_tp, "sys_tp_ci": ci_sys_tp,
            "usr_tp_mean": mean_usr_tp, "usr_tp_ci": ci_usr_tp,
            "num_completed": int(mean_comp),
            "all_tps": all_user_tps_agg
        })

        marker = " ✔" if 0 < mean_wait <= MAX_WAIT else ""
        print(f"{lam:10.4f} | {mean_wait:10.2f} ±{ci_wait:4.1f} | "
              f"{mean_sys_tp:10.2f} ±{ci_sys_tp:4.1f} | "
              f"{int(mean_comp):14d}{marker}")

    # Szukanie optymalnej λ
    valid = [r for r in results if 0 < r["wait_mean"] <= MAX_WAIT]
    best = None
    if valid:
        best = max(valid, key=lambda r: r["lambda"])
        print(f"\n╔══════════════════════════════════════════════════════════╗")
        print(f"  Maksymalna λ z avg_wait ≤ {MAX_WAIT} ms:")
        print(f"  λ* = {best['lambda']:.4f} 1/ms")
        print(f"  Avg wait     = {best['wait_mean']:.2f} ± {best['wait_ci']:.2f} ms")
        print(f"╚══════════════════════════════════════════════════════════╝")

    os.makedirs("results", exist_ok=True)
    lam_vals = [r["lambda"] for r in results]

    # --- Wykres 1: Czas oczekiwania + Error bars ---
    fig1, ax1 = plt.subplots(figsize=(8, 5))
    ax1.errorbar(lam_vals, [r["wait_mean"] for r in results], yerr=[r["wait_ci"] for r in results], 
                 fmt="o-", color="#01696f", linewidth=2, capsize=4, label="Czas oczekiwania (95% CI)")
    ax1.axhline(MAX_WAIT, color="#a12c7b", linestyle="--", linewidth=1.8, label=f"Kryterium: {MAX_WAIT} ms")
    if best:
        ax1.axvline(best["lambda"], color="#da7101", linestyle=":", linewidth=1.5, label=f"λ* = {best['lambda']:.4f}")
    
    ax1.set_xlabel("λ [1/ms]", fontsize=11)
    ax1.set_ylabel("Średni czas oczekiwania [ms]", fontsize=11)
    ax1.set_title("Czas oczekiwania vs λ (z przedziałami ufności)", fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("results/wait_vs_lambda_ci.png", dpi=150)
    plt.close()

    # --- Wykres 2: Przepływność + Error bars ---
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    ax2.errorbar(lam_vals, [r["sys_tp_mean"] for r in results], yerr=[r["sys_tp_ci"] for r in results],
                 fmt="s-", color="#006494", capsize=4, label="System [kbit/ms]")
    ax2.errorbar(lam_vals, [r["usr_tp_mean"] for r in results], yerr=[r["usr_tp_ci"] for r in results],
                 fmt="^-", color="#da7101", capsize=4, label="Użytkownicy [kbit/ms]")
    
    ax2.set_xlabel("λ [1/ms]")
    ax2.set_ylabel("Przepływność")
    ax2.set_title("Przepływność vs λ (z przedziałami ufności)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("results/throughput_vs_lambda_ci.png", dpi=150)
    plt.close()

    # --- Wykres 3: Faza Początkowa (Transient Phase) ---
    if best:
        print("\nGenerowanie wykresu fazy początkowej dla λ*...")
        # Robimy pojedynczy dłuższy run, aby zapisać zmienność stanu w czasie
        sim_transient = Simulator(seed=9999)
        stats_transient = sim_transient.run(lam=best["lambda"], max_time=SIM_TIME, track_transient=True)
        t_data = stats_transient["transient_data"]

        fig3, ax3 = plt.subplots(figsize=(9, 4))
        ax3.plot([t / 1000.0 for t in t_data["time"]], t_data["queue_length"], color="#a12c7b", alpha=0.85)
        ax3.set_xlabel("Czas symulacji [s]")
        ax3.set_ylabel("Liczba aktywnych UE (długość kolejki)")
        ax3.set_title(f"Wykres fazy przejściowej (Warm-up) dla λ = {best['lambda']:.4f}")
        ax3.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig("results/transient_phase.png", dpi=150)
        plt.close()
        
        # Histogram dla optymalnej
        if best["all_tps"]:
            fig4, ax4 = plt.subplots(figsize=(8, 5))
            ax4.hist(best["all_tps"], bins=50, color="#01696f", edgecolor="white", alpha=0.85)
            ax4.set_title(f"Histogram przepływności (Zestawienie z {REPLICATIONS} replikacji)")
            plt.savefig("results/histogram_user_throughput.png", dpi=150)
            plt.close()

    print("\nWszystkie wykresy zostały wygenerowane w folderze 'results/'.")