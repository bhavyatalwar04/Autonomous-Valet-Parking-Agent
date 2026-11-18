# Control (M4)

**Module owner:** Mohammad Shahvez (code in `m4_control/`)
**Section written by:** Bhavya Talwar

This section describes the control layer: how the car follows the planned route, holds its speed, and carries out the parking manoeuvre's requests. The experiments that compare the controllers are in the Results section.

## Role in the agent

M4 is the only module that commands the car's motion. Every control step it receives a command from M3 and the car's pose and speed, and it returns a steering angle and a speed or acceleration (`M4Controller.step` in `m4_control/m4_controller.py`). It has three modes, chosen by M3:

| Mode | What M4 does |
|---|---|
| `FOLLOW_ROUTE` | Tracks M2's route with a steering controller and a speed profile |
| `PARKING` | Applies M3's requested speed and steering angle, with the speed held by the PID loop |
| `STOP` | Brakes to a standstill and holds; a hard brake for an emergency stop or a failure |

All poses are taken at the centre of the rear axle, heading is measured anticlockwise, and a positive steering angle turns left. These are the same conventions as M1, M2 and M3, which matters because a sign mismatch between modules is the most common integration bug.

## Representing the route

The route from M2 is a list of poses, each marked forward or reverse. M4 splits it into segments at every change of direction, because each segment is driven in one gear (`m4_control/path.py`). Each segment is resampled to points 5 cm apart. Its heading and curvature at every point are computed from the points, and the curvature is smoothed over 0.5 m. A short straight extension is added to the end of each segment so that a look-ahead point never runs off the end of the path.

For a route from grid A*, which has sharp corners, `fillet_polyline` replaces each corner with a circular arc of a chosen radius. That made it possible to track A* routes in the experiments as well as Hybrid A* routes.

## Steering: Pure Pursuit

Pure Pursuit [14] picks a target point on the path a look-ahead distance `l_d` ahead of the rear axle, and steers along the circular arc that passes through it:

`δ = atan(2 L sin α / l_d)`

Here `L` is the wheelbase and `α` is the angle between the car's heading and the line to the target point. The look-ahead grows with speed, `l_d = 0.6 |v| + 1.2 m`, limited to between 1.2 m and 4 m. A longer look-ahead gives smoother steering but cuts corners; a shorter one tracks tightly but reacts more to noise.

## Steering: Stanley

The Stanley controller [15], [16] steers by the heading error plus a term that grows with the sideways (cross-track) error `e`:

`δ = ψ_e + atan(k e / (k_s + |v|))`

with gain `k = 1.5` and a softening constant `k_s = 0.5` m/s that keeps the term bounded at low speed. Going forward, the error is measured at the front axle, as in the original controller.

## Reversing

A car reversing behaves like a car driving forward with its heading turned by 180° and its steering angle mirrored. Both controllers use this: when the segment is driven in reverse, M4 applies the forward law to this "virtual car" and flips the sign of the result (`m4_control/lateral.py`).

This exposed a weakness in plain Stanley. When reversing, its reference point is the rear axle, and on a steady arc the heading error there is close to zero, so nothing supplies the steering angle the arc needs. The car drifts outwards until the cross-track error is large enough to correct it. The fix is **curvature feed-forward**: when reversing, add the steering angle that the path's curvature `κ` needs, `atan(L κ)`. Going forward it is not added, because the front-axle reference already carries the curvature through the heading error and adding it would count it twice. The integrated agent uses Stanley with feed-forward.

## Speed

The target speed at each point is the lowest of three limits (`m4_control/follower.py`):

| Limit | Formula | Purpose |
|---|---|---|
| Cruise | 1.0 m/s forward, 0.5 m/s reverse (in the agent) | Speed on the route |
| Curve | `sqrt(a_lat / κ)`, with `a_lat` = 1 m/s² | Slow down for bends |
| Stopping | `sqrt(2 a_dec d)`, with `a_dec` = 1 m/s² | Arrive at the end of a segment at rest |

The target is ramped up and down at a limited rate, and a PID controller drives the measured speed towards it. The PID has three refinements:

- its derivative is low-pass filtered, so it does not amplify noise;
- integration pauses while the output is saturated in the same direction, so the integral does not "wind up" and cause overshoot;
- the planned acceleration is added to its output as a feed-forward term.

The final gains are `k_p = 1.5`, `k_i = 0.8` and `k_d = 0`. The output is limited to 2 m/s² of acceleration and 4 m/s² of braking.

At each change of gear the follower stops, waits 0.8 s while the wheels turn to the next segment's steering angle, and then sets off in the new direction. When the last segment is finished it reports that the route is complete, which is M3's signal to start the parking manoeuvre.

## Handling noise

`PoseFilter` (`m4_control/estimator.py`) is an optional complementary filter. Each step it predicts the pose from the bicycle model and the last steering command, then moves it 10 % of the way towards the GPS and compass measurement. It smooths noisy positions without adding a long delay.

## Offline test vehicle

For experiments without Webots, `m4_control/sim.py` simulates the car with the kinematic bicycle model plus the effects that matter when comparing controllers:

- steering that is limited, rate-limited to 1 rad/s and lags by 0.12 s;
- acceleration that lags by 0.25 s, with drag;
- Gaussian noise on GPS, compass and speed.

## Testing

`tests/test_m4_control.py` holds 27 unit tests. They cover:

- the PID controller, including anti-windup;
- path handling and splitting at gear changes;
- the sign conventions of both steering controllers, forward and in reverse;
- that feed-forward acts only in reverse;
- the pose filter;
- the emergency stop;
- the three modes of the M4 controller.

Two of the tests re-run the main controller comparison and check its result: Pure Pursuit and Stanley with feed-forward park, while plain Stanley fails in reverse. The tests were checked by deliberately breaking the controllers, for example by reversing a sign or removing the feed-forward. Each fault made at least one test fail.

## Limits

- The controllers are geometric and assume the kinematic bicycle model. They ignore tyre slip, which is acceptable at parking speeds.
- The gains were tuned in the offline simulator. In Webots, M3's parking speed and look-ahead were re-tuned on three bays (Results), but the route-following gains were not.
- Pure Pursuit and Stanley were compared offline only; the Webots runs used Stanley with feed-forward.
