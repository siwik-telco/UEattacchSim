# 📡 Mobile Network Downlink Simulator — Proportional Fairness

A discrete-event simulation of a single-cell mobile network downlink, implementing the **Proportional Fairness (PF)** resource scheduling algorithm. Built with Python using the **event-scheduling (M2)** simulation method.

---

## Table of Contents

- [Overview](#overview)
- [System Model](#system-model)
- [Project Structure](#project-structure)
- [Algorithm Description](#algorithm-description)
  - [Main Event Loop](#main-event-loop)
  - [Proportional Fairness Scheduler](#proportional-fairness-scheduler)
- [Random Variables & Generators](#random-variables--generators)
- [Simulation Parameters](#simulation-parameters)
- [How to Run](#how-to-run)
- [Output & Results](#output--results)
- [Key Results Summary](#key-results-summary)
- [Technologies Used](#technologies-used)

---

## Overview

This simulator models a **4G/LTE-style downlink** in a single base station (eNodeB) cell. Users (UEs) arrive randomly, request data downloads, and are served by the scheduler which allocates Resource Blocks (RBs) according to the Proportional Fairness algorithm. The simulation finds the maximum user arrival intensity λ that keeps average waiting time under 50 ms.

---

## System Model

The network consists of three logical components:

| Component | Role |
|-----------|------|
| **eNodeB** | Base station — manages Resource Blocks (RBs), runs the PF scheduler, tracks active/completed UEs |
| **UE (UserEquipment)** | End user — holds propagation conditions (`rb_rates`), data volume, transmission history |
| **Simulator** | Event engine — generates arrivals, propagation changes, and triggers scheduling cycles |

### Channel Model

Each UE has `K = 100` independent per-RB channel rates drawn from `Uniform(20, 800) kbit/s`, which are re-randomized periodically according to a propagation change event with inter-change time `τ ~ Exp(1/10 ms⁻¹)`. Each transmission slot may fail independently with error probability `ε = 0.1`; failed bits are retransmitted until successfully received.

---

## Project Structure

```
.
├── simulator/
│   └── main_loop.py       # Simulator class — event queue, main run loop
├── environment/
│   ├── enodeb.py          # eNodeB class — PF scheduler, UE management
│   └── ue.py              # UserEquipment class — per-user state
├── main.py                # Entry point — sweeps λ values, computes stats, generates plots
└── results/               # Output directory for plots (auto-created)
    ├── wait_vs_lambda_ci.png
    ├── throughput_vs_lambda_ci.png
    ├── transient_phase.png
    └── histogram_user_throughput.png
```

---

## Algorithm Description

### Main Event Loop

The simulator uses a **priority queue (min-heap)** to process events in chronological order. Each event is a tuple `(time, counter, type, args)`, where `counter` breaks ties deterministically.

```
┌─────────────────────────────────────────────────────┐
│                       START                         │
│  Initialize: schedule first arrival + first         │
│              scheduler tick                         │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  Event queue   │◄──────────────────────┐
              │  non-empty?    │                       │
              └───────┬────────┘                       │
                 YES  │    NO                          │
                      │──────► Compute stats, EXIT     │
                      ▼                                │
          ┌───────────────────────┐                    │
          │  Pop event (time,     │                    │
          │  type, args)          │                    │
          └──────────┬────────────┘                    │
                     │                                 │
                     ▼                                 │
           ┌──────────────────┐                        │
           │  time > max_time?│──── YES ──► EXIT loop  │
           └────────┬─────────┘                        │
                 NO │                                  │
                    ▼                                  │
        ┌───────────────────────────────────┐          │
        │         Event type?               │          │
        └───┬───────────┬────────────┬──────┘          │
            │           │            │                 │
     'arrival'   'scheduler'   'prop_change'           │
            │           │            │                 │
            ▼           ▼            ▼                 │
   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │
   │ add_ue()     │ │run_scheduler │ │update_propag │  │
   │ schedule     │ │remove done   │ │ation()        │  │
   │ next arrival │ │ UEs          │ │schedule next │  │
   │ schedule     │ │ schedule     │ │ prop_change  │  │
   │ prop_change  │ │ next tick    │ │              │  │
   └──────┬───────┘ └──────┬───────┘ └──────┬───────┘  │
          └────────────────┴────────────────┘          │
                           │                           │
                           └───────────────────────────┘
```

Three event types drive the simulation:

| Event | Type | Description |
|-------|------|-------------|
| `arrival` | Time-based | A new UE enters the system; next arrival and propagation change are immediately scheduled |
| `scheduler` | Time-based (cyclic) | PF scheduler runs every `S = 1 ms`; completed UEs are removed |
| `prop_change` | Time-based | Channel conditions (`rb_rates`) for one UE are re-drawn; next change rescheduled |

**Departure** and **transmission error** are conditional events handled inside `run_scheduler`:
- A UE departs when `data_received >= data_total`
- Bits are credited only when `rng.random() >= EPSILON` (i.e., 90% of transmissions succeed)

---

### Proportional Fairness Scheduler

The PF scheduler runs once per millisecond and allocates each of the `K = 100` RBs independently. For each RB `k`, the UE with the highest **PF score** wins the block, subject to a per-UE cap of `L = 10` RBs per scheduling round.

The PF score for UE `i` on RB `k` is:

$$\text{score}_{i,k} = \frac{r_{i,k}}{\bar{R}_i}$$

where \(r_{i,k}\) is the instantaneous rate of UE `i` on RB `k` [kbit/s], and \(\bar{R}_i\) is UE `i`'s average throughput since arrival [kbit/s].

```
FOR each RB k in {0 ... K-1}:
    best_score = -∞
    best_ue = None

    FOR each active UE i (with alloc_count[i] < L):
        score = rb_rates[i][k] / avg_throughput(i)
        IF score > best_score:
            best_score = score
            best_ue = i

    Assign RB k to best_ue
    alloc_count[best_ue] += 1

FOR each UE i with allocated rate > 0:
    bits_sent = total_rate[i] * (S / 1000)
    UE.total_bits_received += bits_sent

    IF random() >= EPSILON:           # transmission success
        UE.data_received += bits_sent
        system_total_bits += bits_sent

    IF UE.data_received >= UE.data_total:
        mark UE as DONE
```

This mechanism naturally favors UEs with good channel conditions relative to their recent history, achieving multi-user diversity while maintaining long-term fairness.

---

## Random Variables & Generators

Each random process uses an **independent `random.Random` instance** seeded deterministically, ensuring full reproducibility and statistical independence between arrivals, propagation, errors, and per-UE parameters.

| Variable | Distribution | Parameters | Generator call |
|----------|-------------|-----------|----------------|
| Inter-arrival time `t` | Exponential | rate `λ` [1/ms] | `rng_arrival.expovariate(λ)` |
| Data volume `d` | Discrete Uniform | `{25, 50, ..., 250}` Mbit | `rng.randint(1,10) * 25` |
| Per-RB rate `r_k` | Continuous Uniform | `[20, 800]` kbit/s | `rng.uniform(20.0, 800.0)` |
| Propagation change time `τ` | Exponential | rate `1/10` ms⁻¹ | `rng_prop_tau.expovariate(0.1)` |
| Transmission error `ε` | Bernoulli | P(error) = 0.1 | `rng_error.random() < 0.1` |

### Seed Structure

```
base_seed
├── base_seed + 2   → rng_arrival       (inter-arrival times)
├── base_seed + 3   → rng_prop_tau      (propagation change intervals)
├── base_seed + 10  → eNodeB seed
│   ├── seed        → rng_error         (transmission errors)
│   ├── seed + 1    → rng_prop          (channel rate updates)
│   └── seed + 1000 + ue_id → per-UE rng (data volume, initial rates)
```

For each replication, the seed is computed as:
```python
seed = 74 + int(lam * 1000) + rep * 13
```

---

## Simulation Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `K` | 100 | Number of Resource Blocks |
| `L` | 10 | Max RBs per UE per scheduling round |
| `S` | 1.0 ms | Scheduler period |
| `EPSILON` | 0.1 | Transmission error probability |
| `SIM_TIME` | 100,000 ms | Duration of one replication |
| `REPLICATIONS` | 10 | Independent runs per λ value |
| `MAX_WAIT` | 50 ms | Maximum acceptable average waiting time |
| λ values tested | 0.001 … 0.25 [1/ms] | Arrival intensity sweep |

### Warm-up Phase

Analysis of the transient phase (queue length over time) shows the system stabilizes within approximately **15 seconds** from the start. The full 100,000 ms simulation horizon provides ample steady-state data after this warm-up period.

---

## How to Run

### Prerequisites

```bash
pip install -r requirements.txt
```

### Run the full experiment

```bash
python main.py
```

This will:
1. Sweep all λ values defined in `lambdas` list
2. Run 10 independent replications per λ
3. Print a results table with 95% confidence intervals to stdout
4. Save all plots to `results/`

### Example output (stdout)

```
  λ [1/ms] |   avg_wait [ms] ±CI |  sys_tp [k/ms] ±CI | ukończeni (śr)
--------------------------------------------------------------------------------
    0.0010 |        39.32 ±0.7  |       24.61 ±0.0   |            104
    0.0050 |        36.03 ±0.2  |      704.26 ±29.2  |            506
    ...
    0.2500 |        24.61 ±0.0  |    35138.59 ±152.4 |          24961 ✔

╔══════════════════════════════════════════════════════════╗
 Maksymalna λ z avg_wait ≤ 50.0 ms:
 λ* = 0.2500 1/ms
 Avg wait = 24.61 ± 0.00 ms
╚══════════════════════════════════════════════════════════╝
```

---

## Output & Results

Four plots are generated in the `results/` directory:

### 1. Waiting Time vs λ
Average user waiting time with 95% CIs across all tested arrival rates. The 50 ms threshold and optimal λ* are marked.

### 2. Throughput vs λ
System throughput (total bits sent by eNodeB per ms) and average per-user throughput, both with 95% CIs. System throughput grows linearly with λ, while per-user throughput saturates due to RB sharing.

### 3. Transient Phase (Warm-up)
Active UE count sampled every second at λ* = 0.25, used to determine the warm-up period (~15 s).

### 4. Per-User Throughput Histogram
Aggregated distribution of average per-user throughputs across all 10 replications at λ*. The distribution is approximately normal, centered around 6,300–6,500 kbit/s.

---

## Key Results Summary

Results at the optimal arrival intensity **λ\* = 0.25 [1/ms]** (maximum λ satisfying avg wait ≤ 50 ms):

| Metric | Value |
|--------|-------|
| Average waiting time | 24.61 ms |
| System throughput | ≈ 35.14 Mbit/s |
| Average per-user throughput | ≈ 6.5 Mbit/s |
| Users served (per 100 s run) | ~24,961 |

The waiting time decreases monotonically across the tested λ range, indicating the system remains stable and unsaturated up to λ = 0.25 [1/ms]. This counter-intuitive behavior (more arrivals → shorter wait) occurs because higher λ keeps more UEs active simultaneously, enabling the PF scheduler to exploit multi-user diversity more effectively across the 100 RBs.

---

## Technologies Used

| Technology | Purpose |
|------------|---------|
| **Python 3.x** | Core simulation language |
| `heapq` (stdlib) | Priority queue for event scheduling — O(log n) push/pop |
| `itertools.count` | Tie-breaking counter for simultaneous events |
| `random.Random` | Isolated per-process RNG instances for reproducibility |
| `math` | Confidence interval computation (stddev, sqrt) |
| `matplotlib` | Generating all result plots (errorbar, hist, plot) |

No external scientific libraries (NumPy, SciPy, SimPy) are used — the simulator is built entirely on the Python standard library, making it portable and dependency-light.

---

*Group A3-B · Authors: Adrian Świątek, Oskar Kachaniuk, Bartosz Siwik*
