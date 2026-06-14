import os
import random
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Importujemy z naszych nowych modułów
from simulator.main_loop import Simulator

if __name__ == "__main__":
    SIM_TIME = 100_000  # ms (100 s)
    MAX_WAIT = 150.0  # ms – kryterium

    # Zakres λ do badania
    lambdas = [0.001, 0.005, 0.010, 0.020, 0.030, 0.050]
               

    results = []
    sim = Simulator()

    print(
        f"{'λ [1/ms]':>10} | {'avg_wait [ms]':>14} | {'sys_tp [kbit/ms]':>17} | {'usr_tp [kbit/ms]':>17} | {'ukończeni':>10}")
    print("-" * 85)

    for lam in lambdas:
        # Zastąpienie np.random.seed standardowym
        random.seed(1)
        stats = sim.run(lam=lam, max_time=SIM_TIME)
        results.append(stats)

        # Wyświetlanie tabelaryczne z oznaczaniem wartości spełniających warunek
        marker = " ✔" if stats["avg_wait_ms"] <= MAX_WAIT and stats["avg_wait_ms"] > 0 else ""
        print(f"{lam:10.4f} | {stats['avg_wait_ms']:14.2f} | "
              f"{stats['system_tp_kbps']:17.4f} | "
              f"{stats['avg_user_tp_kbps']:17.4f} | "
              f"{stats['num_completed']:10d}{marker}")

    # Szukanie optymalnej λ (maksymalnej, ale spełniającej kryterium oczekiwania)
    valid = [r for r in results if 0 < r["avg_wait_ms"] <= MAX_WAIT]
    if valid:
        best = max(valid, key=lambda r: r["lambda"])
        print(f"\n╔══════════════════════════════════════════════════════════╗")
        print(f"  Maksymalna λ z avg_wait ≤ {MAX_WAIT} ms:")
        print(f"  λ* = {best['lambda']:.4f} 1/ms")
        print(f"  Przep. sys.  = {best['system_tp_kbps']:.4f} kbit/ms")
        print(f"  Przep. usr.  = {best['avg_user_tp_kbps']:.4f} kbit/ms")
        print(f"  Avg wait     = {best['avg_wait_ms']:.2f} ms")
        print(f"  Ukończonych  = {best['num_completed']} UE")
        print(f"╚══════════════════════════════════════════════════════════╝")
    else:
        print("\n✘  Żadna λ nie spełnia kryterium. Zmniejsz λ lub zwiększ k/l.")

    # Generowanie wykresów przy użyciu matplotlib
    os.makedirs("results", exist_ok=True)
    lam_vals = [r["lambda"] for r in results]
    wait_vals = [r["avg_wait_ms"] for r in results]
    sys_tp_vals = [r["system_tp_kbps"] for r in results]
    usr_tp_vals = [r["avg_user_tp_kbps"] for r in results]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Symulator LTE – Proportional Fairness (k=10 RB, l=3, ε=0.1)", fontsize=13, fontweight="bold")

    # Wykres 1: Czas oczekiwania w funkcji λ
    ax1 = axes[0]
    ax1.plot(lam_vals, wait_vals, "o-", color="#01696f", linewidth=2, markersize=7, label="avg czas oczekiwania")
    ax1.axhline(MAX_WAIT, color="#a12c7b", linestyle="--", linewidth=1.8, label=f"Kryterium: {MAX_WAIT} ms")
    if valid:
        ax1.axvline(best["lambda"], color="#da7101", linestyle=":", linewidth=1.5, label=f"λ* = {best['lambda']:.4f}")
    ax1.set_xlabel("λ [1/ms]", fontsize=11)
    ax1.set_ylabel("Średni czas oczekiwania [ms]", fontsize=11)
    ax1.set_title("Czas oczekiwania vs λ", fontsize=12)
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)

    # Wykres 2: Przepływność systemu w funkcji λ
    ax2 = axes[1]
    ln1, = ax2.plot(lam_vals, sys_tp_vals, "s-", color="#006494", linewidth=2, markersize=7,
                    label="Przep. systemu [kbit/ms]")
    ax2r = ax2.twinx()
    ln2, = ax2r.plot(lam_vals, usr_tp_vals, "^--", color="#da7101", linewidth=1.8, markersize=7,
                     label="Przep. użytkownika [kbit/ms]")
    ax2.set_xlabel("λ [1/ms]", fontsize=11)
    ax2.set_ylabel("Przepływność systemu [kbit/ms]", color="#006494", fontsize=11)
    ax2r.set_ylabel("Przep. użytkownika [kbit/ms]", color="#da7101", fontsize=11)
    ax2.set_title("Przepływność vs λ", fontsize=12)
    ax2.legend(handles=[ln1, ln2], fontsize=9, loc="upper left")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("results/throughput_wait_vs_lambda.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\nWykres 1 zapisany: results/throughput_wait_vs_lambda.png")

    # Histogram przepływności dla optymalnej lambdy
    if valid and best["user_tps"]:
        fig2, ax3 = plt.subplots(figsize=(8, 5))
        ax3.hist(best["user_tps"], bins=40, color="#01696f", edgecolor="white", alpha=0.85)
        ax3.set_xlabel("Średnia przepływność użytkownika [kbit/ms]", fontsize=11)
        ax3.set_ylabel("Liczba użytkowników", fontsize=11)
        ax3.set_title(
            f"Histogram przepływności użytkowników\nλ* = {best['lambda']:.4f} 1/ms | PF Scheduler | k=10, l=3",
            fontsize=11)
        ax3.grid(True, alpha=0.3, axis="y")
        plt.tight_layout()
        plt.savefig("results/histogram_user_throughput.png", dpi=150, bbox_inches="tight")
        plt.close()
        print("Wykres 2 zapisany: results/histogram_user_throughput.png")