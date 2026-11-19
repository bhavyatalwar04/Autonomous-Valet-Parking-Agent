# Video script: Autonomous Valet Parking Agent (P13, G08)

Target length: **about 21.5 minutes** (allowed 18–22). Everyone keeps their camera on for the whole recording.

- **Slides:** https://claude.ai/artifact/DU43H77LGqmJncPuBNjXhC (23 slides). **Bhavya shares them** for the whole talk and moves to the next slide on each `[NEXT SLIDE]` cue.
- **Demo:** **Bhavya runs the Webots demo** and switches the Zoom share from the slides to the Webots window for it.
- **Pace:** the script is written for about 130 words a minute. Learn it well enough to say it in your own words; reading it word for word sounds flat.

## Running order

| Time | Slides | Speaker |
|---|---|---|
| 0:00–2:50 | 1–5 | Bhavya |
| 2:50–5:05 | 6 | Devansh |
| 5:05–8:50 | 7–10 | Bhavya |
| 8:50–10:50 | 11 | Harshil |
| 10:50–12:50 | 12 | Shahvez |
| 12:50–14:20 | 13–14 | Bhavya |
| 14:20–17:20 | Live demo | Devansh, Bhavya, then Harshil |
| 17:20–19:40 | 15–17 | Shahvez |
| 19:40–21:30 | 18–23 | Bhavya, then everyone |

| Speaker | Speaking time |
|---|---|
| Bhavya | about 10.5 min |
| Harshil | about 3.5 min |
| Shahvez | about 4.5 min |
| Devansh | about 3 min |

## Before pressing Record

- [ ] Everyone has camera and microphone on, headphones in, and is in a quiet room.
- [ ] Zoom recording settings: *Record video during screen sharing* and *Place video next to the shared screen* are on.
- [ ] Bhavya: latest `main` pulled, `worlds/parking_lot.wbt` open in Webots, run once and **Reset**, console visible next to the 3D view with a large font.
- [ ] Bhavya: `results/m3_webots_tuning/A2_tuned_demo.mp4` ready to play as a fallback.
- [ ] Bhavya: practise switching the Zoom share from the slides to the Webots window and back.
- [ ] Bhavya: deck open on slide 1, in presenter mode.

---

## Slide 1: Title (Bhavya, 0:00–0:30)

> Hello everyone. We are Group G08, and this is project P13 for Algorithms for Intelligent Systems and Robotics: an **Autonomous Valet Parking Agent**.
>
> I'm Bhavya Talwar, and with me are Devansh Singh Rawat, Mohammad Shahvez and Harshil Mittal.
>
> The idea is simple to say: a car enters a parking lot with no driver, finds a free bay, plans a route it can actually drive, and reverses itself in. Over the next twenty minutes we'll show how we built it, what we measured, and then run it live in Webots.

`[NEXT SLIDE]`

## Slide 2: The task (Bhavya, 0:30–1:15)

> The task has three parts.
>
> First, **find** a free bay. The car has a 360-degree lidar, and it has to tell taken bays from empty ones.
>
> Second, **plan** a route. This is harder than it sounds, because a car can't turn on the spot. Our car has a 2.8-metre wheelbase, and its tightest turn is a circle of about 5.1 metres.
>
> Third, **park**, by reversing into a 2.5-metre bay between two parked cars, and stopping for anything that gets in the way.
>
> The brief asked for a deliberative planner for the route and reactive rules for the close-range manoeuvres. Everything runs in Webots, written in Python, in a lot with 40 bays. The same problem appears in smart car parks and in self-driving cars.

`[NEXT SLIDE]`

## Slide 3: Objectives (Bhavya, 1:15–1:35)

> We set ourselves five objectives: find free bays using only the lidar; plan routes a real car can drive; reverse into a bay between two parked cars without contact; stop and replan when the world changes; and measure all of it, not just show one demo.

`[NEXT SLIDE]`

## Slide 4: Literature review (Bhavya, 1:35–2:05)

> We built on well-known work. For the agent, Gat's three-layer architecture, which matches the hierarchy in our syllabus. For planning, A*, and Hybrid A* from Dolgov and colleagues. For tracking, pure pursuit and the Stanley controller. Each of these studies one layer on its own. What is less often shown, and what we focused on, is how the layers depend on each other.

`[NEXT SLIDE]`

## Slide 5: Architecture (Bhavya, 2:05–2:50)

> To do this we built a layered intelligent agent. It matches the declarative, procedural and reflexive hierarchy from our syllabus.
>
> At the top is the **deliberative** layer, my module: which bay, and which route. It takes about a second, so it runs rarely.
>
> Below it, Harshil's **procedural** state machine: drive, align, reverse in, done. And his **reflexive** safety check, every step, which stops the car if anything gets too close.
>
> At the bottom, Shahvez's **control** turns the route into steering and speed. Devansh's sensing feeds all of them.
>
> The layers talk to each other: when the reflex stops the car, the planner plans again. Devansh will start with the world.

`[NEXT SLIDE]`

## Slide 6: World and sensors (Devansh, 2:50–5:05)

> Thanks, Bhavya. This is our world in Webots, seen from above.
>
> The lot is 40 by 34 metres, with the entrance on the left. There are four rows of ten bays, each 2.5 by 5 metres, so 40 bays in total. There are two aisles, and a kerb between the two middle rows so the car can't cut across. Twenty-two bays have parked cars in them; the blue car on the left is ours.
>
> The car is a four-wheel Ackermann vehicle, 4.6 by 1.9 metres. All four wheels have motors and the front two steer. For its position it has GPS and a compass, and for seeing the world it has a 360-degree lidar with 721 rays.
>
> The lidar is how we find free bays. For each bay we check every ray against it. If a ray hits something inside the bay, it's **occupied**. If a ray passes right through the bay and lands beyond it, the bay is visible and empty, so it's **free**. If no ray reaches a bay, it stays **unknown**, and we never assume an unknown bay is free, because sending the car to a taken bay is worse than skipping a free one.
>
> Getting the sensors right took care. Webots returns the lidar scan clockwise, so we reverse it, and the heading comes from the compass as atan2 of its readings. The lidar was first mounted so low that it saw the car's own wheels, and the planner thought it was surrounded. We raised it from 0.28 to 0.35 metres.
>
> A test also checks every bay and parked car in the world against the planner's map, so the two can't drift apart. Back to Bhavya.

`[NEXT SLIDE]`

## Slide 7: Why grid A* is not enough (Bhavya, 5:05–6:05)

> Thanks, Devansh. My module plans the route.
>
> The standard method is **A***. We turn the lot into a grid of 0.25-metre cells. We grow every obstacle by the size of the car, so we can then plan for the car as a single point; that's the configuration-space idea. A* expands cells in order of the cost so far plus an estimate of the cost to the goal. We use the octile distance as the estimate. It never overestimates, so A* is guaranteed to find the shortest grid path.
>
> But there's a catch. On a grid, the path turns 45 or 90 degrees instantly. A car can't do that. Its tightest turn is L over tan of the maximum steering angle: 2.8 over tan of 0.5, which is **5.13 metres**. So A* gives the shortest route, but not one a car can drive.

`[NEXT SLIDE]`

## Slide 8: Hybrid A* (Bhavya, 6:05–7:20)

> So the planner we actually use is **Hybrid A***, from Dolgov and colleagues, who used it in the DARPA Urban Challenge.
>
> It's still A*, but with four changes.
>
> One: the state is the car's real position and heading, not a grid cell.
>
> Two: to get to the next state, we **drive the car model** one metre, with one of five steering angles, forwards or in reverse. Every route is made of these arcs, so every route can be driven, by construction.
>
> Three: we keep one state per bin of half a metre and five degrees. That's the "hybrid": continuous states, grid-style bookkeeping.
>
> Four: reversing, steering and gear changes cost extra, so it prefers calm forward driving. A distance-to-goal map around the obstacles guides the search.

`[NEXT SLIDE]`

## Slide 9: Planner comparison (Bhavya, 7:20–8:20)

> This is our first comparison. We planned six routes from the entrance with all three methods and measured not just length and time, but whether the car could actually drive them.
>
> Grid A* is the shortest and fastest, about 10 milliseconds. But on average 3.3 metres of each route is **too tight** for the car to turn, the car's body would hit an obstacle at four points, and it arrives 52 degrees off the heading it needs.
>
> Smoothing makes the corners rounder, but it doesn't know about the turning radius, so the too-tight length actually goes up slightly.
>
> **Hybrid A*** has zero metres too tight, zero hits, and arrives within 3.4 degrees. The price is 8 per cent more length and about 0.4 seconds of planning. That's a good trade for a car that plans once and then drives for a minute.

`[NEXT SLIDE]`

## Slide 10: Routes to bay C4 (Bhavya, 8:20–8:50)

> Here are the three routes to bay C4. Same start, same goal.
>
> Blue is A*: look at this right-angle corner next to the parked cars. The red crosses are where the real car would hit them. Orange is smoothed A*: rounder, still too tight. Green is Hybrid A*: it swings wide, stays clear, and reverses once to line up. The dashed part is reversing.
>
> The route ends beside the bay. From there, Harshil's module takes over.

`[NEXT SLIDE]`

## Slide 11: Parking manoeuvre (Harshil, 8:50–10:50)

> Thanks, Bhavya. My module, M3, does the final parking manoeuvre, and it holds both the procedural and the reflexive layers.
>
> The procedural part is a **state machine**. In **Drive**, the control module follows Bhavya's route, and I wait until it's finished and the car has stopped. In **Align**, the car moves forward to a turning point just past the bay. In **Park**, it reverses on a quarter circle into the bay and then straight back. If it isn't centred, it can make up to two short corrections. **Done** is only declared after checks: the car must be stopped, within 15 centimetres of the bay centre, within 3 degrees of straight, and with all four corners inside the bay.
>
> The reflexive part is the **safety layer**. Every step, it looks at the gap on each side of the car. If any gap is under 15 centimetres, or under the distance the car needs to stop at its current speed, it stops the car immediately, whatever the planner wanted. The stop is latched, so the car doesn't creep forward again on its own; the planner has to take over.
>
> In Webots I tuned the parking speed and lookahead: going from 0.35 to 0.45 metres per second made parking about 19 per cent faster and halved the final heading error. Over to Shahvez for control.

`[NEXT SLIDE]`

## Slide 12: Path tracking (Shahvez, 10:50–12:50)

> Thank you, Harshil. My module, M4, turns the route into steering and speed commands.
>
> We compared two classic steering controllers. **Pure pursuit** picks a point on the route a fixed distance ahead and steers along the circle that passes through it. **Stanley** steers by the heading error plus a term that grows with the sideways error, measured at the front axle.
>
> This is our second comparison, on an L-shaped route that ends with a reverse park. Pure pursuit tracks well in both directions: 9.6 centimetres of RMS error forward and 2.3 centimetres in reverse, and it parks.
>
> Plain Stanley works forward, but it **fails in reverse**: 42 centimetres of error, and it doesn't park. The reason is that Stanley is designed around the front axle, and in reverse the geometry changes. We fixed it by adding **curvature feed-forward**, steering in advance for the bend the route is about to take. With that, the reverse error drops to 1.8 centimetres and it parks. The straight and tight routes gave the same pattern, and the agent uses Stanley with feed-forward.
>
> Speed is held by a **PID** controller, with feed-forward from the planned acceleration. We also swept the lookahead distance and the gains, and tested with noise on the GPS, and the results are in our report. Back to Bhavya to show how it all fits together.

`[NEXT SLIDE]`

## Slide 13: Integration (Bhavya, 12:50–13:35)

> Thanks, Shahvez. All four modules run in one loop, in one class, and the exact same code runs offline and in Webots.
>
> **Every step**, the lidar gives the gaps around the car, Harshil's module decides, and Shahvez's module drives the motors.
>
> **Every second**, the planner checks: is my bay still free? Is the rest of the route still clear?
>
> **If not**, the car stops and plans again from where it is: to the same bay if it can, otherwise to the next best one. A safety stop on the route also triggers a new plan, so the reflex and the planner work together.
>
> To choose the bay quickly, we rank all free bays with fast grid A*, milliseconds each, and run Hybrid A* only on the best one.

`[NEXT SLIDE]`

## Slide 14: Where the route ends (Bhavya, 13:35–14:20)

> Joining the modules taught us that **where the route ends decides whether parking works**.
>
> At first the route ended on the centre of the aisle. But the reverse swing has a radius of 6.19 metres, and from the centre line the car's inner side touched the next parked car. The geometry gave exactly zero gap. Moving the end point half a metre further out gave a 0.2-metre gap, and the simulation measured 0.19.
>
> Hybrid A* only gets within half a metre of its goal, but parking allows about 0.3, so we join the last 5 metres to the exact point with a cubic curve that we check for curvature and collisions.
>
> Now let's see it run. Over to Devansh for the live demo.

`[Bhavya switches the share from the slides to the Webots window.]`

## Live demo (Devansh, Bhavya, then Harshil, 14:20–17:20)

**Devansh (30 seconds, before Run):**

> This is the world you saw on slide 6, live in Webots. Our car is at the entrance on the left. It knows the layout of the lot, but not which bays are free: it has to find that out with its lidar as it drives. Bhavya, go ahead.

**Bhavya (presses Run, then narrates):**

> I'm pressing Run. The controller is the full agent, all four modules together.
>
> *(car still, for a few seconds)* First it scans the lot and plans. On this laptop that takes a few seconds, so the car waits.
>
> *(console shows the bay)* In the console, you can see it chose **bay A2**, the closest bay it can reach, and planned a route to it.
>
> *(car driving)* Now it's in **Drive**. Shahvez's controller is following the route at one metre per second. Every second, the planner checks the bay is still free and the route is still clear. Harshil, over to you for the parking.

**Harshil (narrates while Bhavya's screen shows the run):**

> *(around 16 s on the Webots clock, ALIGN)* The route has ended beside the bay, 4 metres out. My state machine switches to **Align**: it drives forward past the bay to the turning point.
>
> *(around 25 s, PARK)* Now **Park**. It's reversing on the quarter circle. The safety layer is checking the gaps to the neighbouring cars every step.
>
> *(car straightening)* Straightening up into the bay...
>
> *(around 53 s)* And the console says **DONE, Parking completed**, at about 53 seconds. Our offline simulator predicts 52.9 seconds for this same run, so Webots and our simulator agree to within a fraction of a second.

`[Bhavya switches the share back to the slides.]`

**If the live run fails:**

> Bhavya: That didn't go as planned. Here's a recording of the same run from our tests.

Play `A2_tuned_demo.mp4` and narrate it the same way: Bhavya for Drive, Harshil for Align and Park. Don't spend more than 15 seconds troubleshooting live.

## Slide 15: Scenarios (Shahvez, 17:20–18:20)

> Thank you. Now the results. Besides the normal run, we tested two cases where the world changes.
>
> In the **normal** run, it parks in A2 with no replanning, and the closest it came to anything was 20 centimetres.
>
> In the second, **another car takes our bay** three seconds into the drive. The agent notices on its next check, stops, replans once, and parks in B0 instead.
>
> In the third, a **pedestrian** steps onto the route 6 metres ahead. On the right, the dotted lines are the routes the agent abandoned, and the red dots are where it was stopping. It stops, replans twice, waits until the pedestrian leaves, then parks in A2.
>
> All three end parked within 5.2 centimetres of the bay centre and a tenth of a degree of straight. In Webots, the full agent parked in A2, B0 and A5 in every run.

`[NEXT SLIDE]`

## Slide 16: Every bay (Shahvez, 18:20–19:20)

> One demo can hide a lot, so we tried to park in **every one of the 40 bays**, with cars on both sides, which is the hardest case.
>
> It parked in **34 of 40, 85 per cent**: 9 out of 10 in rows A, B and D, and 7 out of 10 in row C.
>
> Most importantly, there was **no contact in any of the 40 runs**. The closest the car body ever came to an obstacle was 7 centimetres.
>
> The six failures are all at or next to the ends of the aisles, where reaching the bay needs a multi-point turn in a tight space. In every one, the safety layer stopped the car before it touched anything, so it failed safely.
>
> This test found four bugs a single demo would have missed, and each was fixed.

`[NEXT SLIDE]`

## Slide 17: Webots (Shahvez, 19:20–19:40)

> And Webots confirms the offline results. In the run to A2 you just saw, every phase started within 0.15 seconds of what our offline simulator predicts, and Harshil's tuning made parking 19 per cent faster, with half the heading error. Back to Bhavya.

`[NEXT SLIDE]`

## Slide 18: Novelty (Bhavya, 19:40–20:15)

> Each method we used is known. What's new is **how the layers fit together**, and how we measured it:
>
> - a planner comparison measured on whether the car can drive the route, not just length and time;
> - a hand-over point worked out from the parking manoeuvre's own geometry;
> - an exact final approach with a simple cubic curve instead of Reeds–Shepp curves;
> - a two-stage bay choice, fast A* to rank and Hybrid A* to plan;
> - safety stops that trigger replanning, with a clean "boxed in" failure instead of looping;
> - and parking success measured in all 40 bays, confirmed in Webots.

`[NEXT SLIDE]`

## Slide 19: Who built what (everyone, 20:15–20:45)

Each person says one sentence, in this order:

> **Devansh:** I built the Webots world, the car with its motors and sensors, and free-bay detection from the lidar.
>
> **Bhavya:** I built the route planner, A* and Hybrid A*, the replanning, and the integration that runs all four modules together.
>
> **Harshil:** I built the parking state machine, the reverse manoeuvre and the safety stops, and tuned it in Webots.
>
> **Shahvez:** I built path tracking and speed control, and the Pure Pursuit versus Stanley experiments.
>
> **Bhavya:** Everyone committed their own code from their own GitHub account, through pull requests checked by automated tests.

`[NEXT SLIDE]`

## Slide 20: Limitations (Bhavya, 20:45–21:05)

> Before we conclude, our limitations. Six bays at the ends of the aisles don't park yet. Webots was tested on three bays, and the pedestrian case only offline. The lot's layout is given, the position comes from GPS, and pedestrians are treated as static obstacles.

`[NEXT SLIDE]`

## Slide 21: Conclusion (Bhavya, 21:05–21:30)

> To conclude: we built a layered agent that parks safely, and knows when it can't.
>
> We showed that Hybrid A* gives drivable routes where A* does not, that the agent parks in 85 per cent of bays with no contact, and that it replans when a bay is taken or the way is blocked.
>
> Next, we'd like better tracking through changes of direction, a smarter set-up for the end-of-aisle bays, and parallel parking.

`[NEXT SLIDE]`

## Slide 22: References (not spoken)

Not read out. Bhavya moves straight on.

`[NEXT SLIDE]`

## Slide 23: Thank you (everyone, 21:30)

> **Bhavya:** Thank you for watching.

**Everyone:** Thank you.

`[STOP RECORDING]`

---

## Timing check

Practise once with a timer.

| If you are... | Then |
|---|---|
| Over 22 minutes | Shorten slides 8 and 14 first; keep the demo intact |
| Under 18 minutes | Let the demo run with more narration, and expand the scenarios on slide 15 |
