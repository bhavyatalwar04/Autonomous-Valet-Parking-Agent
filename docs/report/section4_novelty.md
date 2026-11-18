# 4. Novelty

Each layer of our agent uses a known method: A* and Hybrid A* for planning, a state machine for the parking manoeuvre, and Stanley / pure pursuit for tracking. What is new is how the layers were joined and measured. Building the whole chain showed several dependencies between the global planner and the local manoeuvre that single-layer studies do not show. We solved them with small, explainable additions and measured each one. The full measurements are in Section 9; this section states each contribution and its key result.

## 4.1 A drivability-focused comparison of three planners

We compare grid A*, grid A* with gradient smoothing, and Hybrid A* on the same lot, start and goals. Path length and planning time are the usual measures, but they do not show whether a car can drive a route. We added measures that do:

- maximum curvature, computed separately for each forward and reverse stretch, so a direction change is not counted as a sharp turn;
- the length of route that is tighter than the car can turn;
- how often the car's real rectangular footprint hits an obstacle along the route;
- the heading error at the goal.

These measures change the conclusion. On length and time alone, grid A* wins: its routes are shortest and it is about 40 times faster. On the new measures, none of its routes can be driven as planned. On average 3.3 m of each route is tighter than the car can turn, and the body would hit an obstacle at four poses. Smoothing does not fix this; the too-tight length even rises slightly. Only Hybrid A* has no too-tight stretch and no collision, for 8 % more length (Section 9.2).

## 4.2 A pre-park pose derived from the manoeuvre's geometry

The planner does not drive into the bay. It stops at a "pre-park" pose on the aisle, and the reactive layer reverses in from there. Placing that pose on the aisle centre line seemed natural, but in the integrated run the reverse swing touched the parked car in the next bay. The geometry explains why. The manoeuvre reverses on a quarter circle of radius `R = L / tan(0.85 δ_max) = 6.19 m`, and the neighbouring car lies inside that turn. It must therefore stay within the innermost circle the body sweeps, radius `R − w/2 = 5.24 m`. From the centre line, 3.5 m out from the bay, the neighbour's far corner is exactly 5.24 m from the circle's centre, so the gap is zero. From 4.0 m out it is 0.2 m, and the simulation measured 0.19 m. The pre-park pose is now worked out from the manoeuvre rather than chosen by eye.

## 4.3 An exact final approach without Reeds–Shepp curves

Hybrid A* only promises to reach the goal within 0.5 m, but the geometry above leaves about 0.3 m of room across the aisle. Instead of the usual Reeds–Shepp step [9], [10], we search to a point 5 m before the goal and join it to the exact goal with a cubic curve, checked against the turning limit and for collisions. This works because every pre-park pose lies on a straight aisle, facing along it. It is a few lines of algebra, easy to explain, and every route now ends exactly on the goal (Section 6.8).

## 4.4 Two-stage slot choice

Choosing a slot needs a route cost for every free slot. Hybrid A* takes about a second per slot, so we rank all free slots with fast grid A* (a few ms each) and then run Hybrid A* only on the best one, moving to the next only if it fails. The slot choice takes about one Hybrid A* run instead of one per free slot.

## 4.5 Reflexive stops that trigger deliberative replanning

The three layers interact in a defined way:

- the reflexive layer (M3 safety) stops the car whenever a gap around the body is below its stopping distance;
- once the car is stopped, the deliberative layer (M2) rebuilds the map from the lidar and plans again from where the car is, to the same slot if it is still free, otherwise to the next best;
- if every new route is stopped again before the car can move, the agent reports that it is boxed in rather than looping.

In the offline scenarios the agent parked in every case: in A2 with no replanning, in B0 after another car took its first choice, and in A2 after a pedestrian blocked the route and two replans. It never came closer than 0.20 m to anything (Section 9.5).

## 4.6 Measured parking success in every bay

Rather than one demonstration, we tried to park in each of the 40 bays with both neighbours occupied, the tightest case. That test found the problems behind Sections 4.2 and 4.3, plus two more:

- bays drawn against the outer wall left no room behind a parked car;
- the last bay in a row has no room to set up the manoeuvre when approached towards the end wall.

With all four fixed, the agent parked in 34 of 40 bays (85 %), with no contact in any run; the closest the body came to an obstacle was 0.07 m. The six bays that still fail are at the ends of the aisles, and in each the safety layer stopped the car before contact (Section 9.6).

## 4.7 Offline results confirmed in Webots

The offline runs use our own simulated lidar and a bicycle model of the car, so the same agent was also run in Webots. Webots exposed one problem the offline model could not: with the lidar mounted 0.28 m above the rear axle, it saw the car's own wheels, the map showed obstacles all around the car, and no route could be planned. Raising it to 0.35 m, above the tyres and below the cabin, fixed this.

On the final code, the same run to bay A2 parked at 52.90 s offline and 52.93 s in Webots, with every phase beginning within 0.15 s of the offline time. The car ended about 1 cm further from the bay centre in Webots and 0.3° less straight. This agreement is what supports using the offline 40-bay test as the success rate (Section 9.7).
