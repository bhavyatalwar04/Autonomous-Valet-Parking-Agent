# Results

**Section written by:** Bhavya Talwar, from each module's experiments.

This section gathers the measurements from all four modules. It answers four questions:

1. Which planner gives routes the car can drive?
2. Which steering controller tracks those routes best?
3. Does the whole agent park, and does it cope when the lot changes?
4. Do the offline results hold in Webots?

Section 4 explains why some of these results are new; here they are presented in full.

## Experimental setup

Two simulators were used.

- **Offline simulator** (`agent/sim_world.py`, `m4_control/sim.py`):
  - the same lot as the Webots world, with a ray-cast lidar of 721 rays;
  - the car modelled as a kinematic bicycle;
  - it runs the same agent code as Webots, so many runs are cheap: one run per bay, controller sweeps over many settings, and repeated noisy runs.
- **Webots R2025b**, with the world `worlds/parking_lot.wbt` and the integrated controller `controllers/valet_agent`. Here M1 detects bays from the simulated lidar and M4 drives the four wheel and two steering motors.

All runs start at the lot entrance, rear axle at (2.0, 8.5) m, facing +x. Unless stated otherwise, 22 bays are occupied, as in the default lot. A run counts as parked when M3's checks pass: stopped, within 0.15 m of the bay centre, within 3° of the bay's axis, and with the whole body inside the bay.

## Comparison 1: route planners

Three planners were run from the entrance to the pre-park pose of six bays, one or two in each row (`python -m planner.compare_planners`, `results/planner_comparison.md`).

| Method | Length (m) | Time (ms) | Max curvature, worst route (1/m) | Too-tight length (m) | Footprint hits | Goal heading error (°) |
|---|---|---|---|---|---|---|
| A* | 28.7 | 9.9 | 2.53 | 3.27 | 4.0 | 52.5 |
| A* + smoothing | 28.0 | 21.6 | 1.06 | 3.46 | 1.8 | 44.7 |
| Hybrid A* | 31.0 | 372.9 | 0.20 | 0.00 | 0.0 | 3.4 |

*Mean of six routes, except maximum curvature, which is the worst route. "Too-tight length" is route length with curvature above the car's limit of 0.195 m⁻¹. "Footprint hits" counts route poses where the car's rectangle overlaps an obstacle.*

Grid A* is the shortest and the fastest, but none of its routes can be driven as planned. On average 3.3 m of each route is tighter than the car can turn, the body would hit an obstacle at four poses, and the route ends 52° off the heading the parking manoeuvre needs. Smoothing reduces the curvature peak and the collisions, but because it does not model the turning radius, the too-tight length rises slightly. Hybrid A* has no stretch tighter than the car's limit and no collision, and ends within 3.4° of the required heading. It costs 8 % more length and about 0.4 s of planning, up to 1.3 s for the farthest bay (C9).

Figures: `results/planner_paths_C4.png` (the three routes to bay C4), `results/planner_summary.png`.

## Comparison 2: path tracking

All tracking experiments use M4's offline vehicle model, which includes steering lag and rate limits, on three synthetic routes that end with a reverse park (`python -m m4_control.run_experiments`, `results/m4/tables.md`):

- **straight:** along an aisle, then reverse in;
- **L-route:** two filleted corners, then reverse in;
- **tight:** like straight, but with a reverse arc close to the minimum radius.

The car starts 0.3 m and 0.05 rad off the route. Tracking error is the true cross-track error at the rear axle for every controller, so the comparison is fair. A run counts as parked when the final pose is within 20 cm sideways, 30 cm along the bay and 3°.

### E1: controller comparison

| Route | Controller | RMS error forward (m) | RMS error reverse (m) | Final sideways error (cm) | Final heading error (°) | Parked |
|---|---|---|---|---|---|---|
| straight | Pure Pursuit | 0.105 | 0.023 | 0.8 | 0.65 | Yes |
| straight | Stanley | 0.118 | 0.405 | 13.5 | 3.96 | No |
| straight | Stanley + FF | 0.118 | 0.012 | 1.3 | 0.52 | Yes |
| L-route | Pure Pursuit | 0.096 | 0.023 | 0.8 | 0.65 | Yes |
| L-route | Stanley | 0.365 | 0.420 | 14.7 | 3.61 | No |
| L-route | Stanley + FF | 0.365 | 0.018 | 1.4 | 0.65 | Yes |
| tight | Pure Pursuit | 0.105 | 0.027 | 0.9 | 0.74 | Yes |
| tight | Stanley | 0.118 | 0.578 | 24.0 | 7.67 | No |
| tight | Stanley + FF | 0.118 | 0.014 | 1.5 | 0.64 | Yes |

Pure Pursuit tracks well in both directions on every route. Plain Stanley tracks forward but fails every reverse park, by 13 to 24 cm sideways and 3.6 to 7.7°. With curvature feed-forward, Stanley's reverse error falls to 1.2–1.8 cm and every run parks. Forward, Stanley's larger error on the L-route comes from the front-axle reference: the rear axle cuts inside the filleted corners. Figure: `results/m4/figures/F1_trajectories.png`.

### E2: tuning sweeps

Six noisy runs per setting, on the L-route, with 5 cm of GPS noise:

- **Pure Pursuit look-ahead:** raising the minimum look-ahead from 0.5 m to 3 m lowers the steering rate from 0.50 to 0.15 rad/s, so the steering is smoother. But the route is cut more, and the final sideways error rises from 0.3 cm to 18 cm. All settings parked.
- **Stanley + FF gain `k`:** between 0.3 and 3 all runs parked, with the final error lowest at `k` = 3 (0.7 cm). At `k` = 5 only 83 % parked, and at `k` = 8 none did, because the steering oscillates.

The defaults (look-ahead 1.2 m, `k` = 1.5) sit inside the safe range on both sweeps. Figure: `F3_param_sweeps.png`.

### E3: speed control

A 0 → 2 m/s step response:

| Variant | Rise time (s) | Overshoot (%) | Steady-state error (m/s) |
|---|---|---|---|
| P only | 1.74 | 0 | 0.18 |
| PI | 1.38 | 5.8 | −0.01 |
| PID | 1.44 | 8.4 | −0.03 |
| PI aggressive | 1.20 | 5.3 | 0.00 |

P alone leaves a steady error because of drag; the integral term removes it. The derivative term added overshoot without a benefit, so `k_d` = 0. In a full parking run (ten noisy runs), the acceleration **feed-forward** mattered most:

| Speed controller | Final error along the bay (cm) | Parked |
|---|---|---|
| PI + feed-forward (default) | 0.6 | 100 % |
| PI, no feed-forward | 38.9 | 0 % |
| P + feed-forward | 2.7 | 100 % |

Without feed-forward, the car lagged its speed profile and stopped 39 cm short of its target every time. Figure: `F4_pid_step.png`.

### E4: noise

Twenty runs per cell on the L-route, with increasing GPS noise:

| GPS noise σ (m) | Pure Pursuit | Pure Pursuit + filter | Stanley + FF | Stanley + FF + filter | Stanley |
|---|---|---|---|---|---|
| 0 | 100 % | 100 % | 100 % | 100 % | 0 % |
| 0.1 | 100 % | 100 % | 100 % | 100 % | 15 % |
| 0.2 | 90 % | 100 % | 95 % | 100 % | 0 % |

*Share of runs that parked.*

Up to 10 cm of noise neither good controller is affected. At 20 cm, the final error along the bay grows to about 19 cm without the pose filter, and 5–10 % of runs miss the bay. The filter brings the error back to about 3 cm and every run parks. Figure: `F5_noise_robustness.png`.

### E5: reverse speed

On the L-route without noise, Pure Pursuit and Stanley + FF parked at every reverse speed from 0.5 to 2.5 m/s, though the final error grew with speed (Stanley + FF: 0.1 cm at 0.5 m/s, 10 cm at 2.5 m/s). Plain Stanley parked only at 0.75 m/s or slower. The agent reverses at 0.5 m/s. Figure: `F6_reverse_speed.png`.

## Parking manoeuvre in Webots

M3's parking speed and look-ahead were tuned in Webots, starting from the entrance each time, on bays A2, B0 and A5 (`docs/m3_webots_tuning.md`, `results/m3_webots_tuning/`). Parking time is measured from the start of ALIGN to DONE.

| Bay | Parking time, old → tuned (s) | Centre error, old → tuned (cm) | Heading error, old → tuned (°) | Closest lidar gap, tuned (m) |
|---|---|---|---|---|
| A2 | 45.2 → 36.7 | 6.3 → 5.9 | 0.76 → 0.40 | 0.18 |
| B0 | 46.0 → 37.2 | 6.3 → 6.0 | 0.74 → 0.36 | 0.21 |
| A5 | 45.2 → 36.7 | 6.3 → 5.9 | 0.78 → 0.40 | 0.20 |

*Old settings: 0.35 m/s, look-ahead 0.65 m. Tuned settings: 0.45 m/s, look-ahead 0.55 m.*

All five validation runs with the tuned settings parked. The time fell by about 19 % and the heading error by about half.

## Whole agent: scenarios

Three offline scenarios with the full agent (`python -m agent.run_offline`, `results/agent/agent_scenarios.md`):

| Scenario | Result | Time (s) | Replans | Closest gap (m) | Centre error (cm) | Heading error (°) |
|---|---|---|---|---|---|---|
| Normal | Parked in A2 | 52.9 | 0 | 0.20 | 5.0 | 0.08 |
| Another car takes the chosen bay after 3 s | Parked in B0 | 55.0 | 1 | 0.21 | 5.2 | 0.07 |
| A pedestrian steps onto the route 6 m ahead and leaves 10 s later | Parked in A2 | 78.3 | 2 | 0.23 | 5.0 | 0.05 |

In the second case the agent saw the bay become occupied on its next check, stopped and replanned to the next best bay. In the third, the safety layer stopped the car; the agent then replanned twice and waited until the way was clear. Figures: `results/agent/agent_*.png`.

## Whole agent: every bay

To measure reliability rather than one demonstration, the agent tried to park in each of the 40 bays in turn, with both neighbouring bays occupied (`python -m agent.run_offline --sweep`, `results/agent/agent_sweep.md`).

| Row | A | B | C | D | All |
|---|---|---|---|---|---|
| Parked | 9 / 10 | 9 / 10 | 7 / 10 | 9 / 10 | 34 / 40 (85 %) |

- **No contact** in any of the 40 runs; the closest the body came to an obstacle was 0.07 m.
- **Six failures:** A8, B8, C0, C8, C9 and D1, all at or next to an aisle end. Reaching them needs a multi-point turn in a narrow space, or the reverse swing passes the end wall inside the 0.15 m safety limit. In each case the safety layer stopped the car and the agent reported that it was boxed in.
- **Precision:** every parked car ended within 5.3 cm of the bay centre and 0.11° of its axis. The mean time to park was 68.6 s.

## Offline against Webots

On the final code, the full agent was run in Webots with the default lot. It chose A2, as it does offline. The two simulators agree closely:

| Normal run to A2 | Offline | Webots |
|---|---|---|
| ALIGN begins (s) | 16.32 | 16.26 |
| PARK begins (s) | 25.66 | 25.54 |
| Parked (s) | 52.90 | 52.93 |
| Centre error (cm) | 5.0 | 5.9 |
| Heading error (°) | 0.08 | 0.40 |

*Webots errors are from the three tuned runs to A2, which gave the same times.*

Every phase began within 0.15 s of the offline time over a 53 s run. The car ended about 1 cm further from the bay centre in Webots and 0.3° less straight, which we attribute to the wheel and steering dynamics the bicycle model leaves out. This agreement is why the 40-bay success rate, measured offline, is taken as representative.

## Summary

| Question | Answer |
|---|---|
| Which planner? | Hybrid A*: the only one with drivable, collision-free routes, for 8 % more length and under 1.3 s of planning |
| Which steering controller? | Pure Pursuit or Stanley with feed-forward; plain Stanley fails in reverse |
| Which speed controller? | PI with acceleration feed-forward; without feed-forward the car stops 39 cm short |
| Does the agent park? | In 34 of 40 bays, with no contact, and it recovers when the bay is taken or a pedestrian blocks the way |
| Do the results hold in Webots? | Yes: phase timings within 0.15 s, errors within about 1 cm and 0.3° |

The main limits are the six end-of-aisle bays, Webots coverage of only three bays without the pedestrian, and that M4's controllers were compared offline only.
