# Limitations and Future Work

## Limitations

- Six bays at the ends of the aisles cannot be parked in yet.
- Webots runs cover three bays, without the pedestrian. The 40-bay result is from the offline simulator.
- The layout of the lot is given to the agent. Only occupancy and obstacles are sensed.
- Pose comes from GPS and a compass, which an indoor car park would not provide.
- The pedestrian is an obstacle that appears and leaves. The agent does not track or predict a moving person.
- Hybrid A* is neither optimal nor complete, and takes up to about 1.3 s for the farthest bays, so the car plans while standing still.

## Future work

- **End-of-aisle bays.** Better tracking through changes of direction, a tighter set-up move, or a Reeds–Shepp connection to the goal [9] should recover most of the six failing bays.
- **More Webots coverage.** Repeat the 40-bay test and the pedestrian scenario in Webots.
- **Moving obstacles.** Track pedestrians and other cars over time, and avoid them locally, for example with the dynamic window approach [17], before falling back to a full replan.
- **Localisation.** Estimate the pose from the lidar and wheel odometry instead of GPS.
- **Smoother routes.** Add the optimisation step of the original Hybrid A* [10], so that the steering angle changes continuously along the route.
- **Other bay types.** Parallel and angled bays, and driving in forwards where there is room.
