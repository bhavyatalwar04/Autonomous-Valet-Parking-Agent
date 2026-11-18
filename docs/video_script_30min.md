# Video script, 30-minute version: Autonomous Valet Parking Agent (P13, G08)

> **Check the length rule first.** The course brief asks for an 18–22 minute video. Use this 30-minute version only if the limit has changed, or for a longer presentation. The 20-minute script is in `docs/video_script.md`.

Same 17 slides (https://claude.ai/artifact/DU43H77LGqmJncPuBNjXhC). Everyone keeps their camera on throughout.

- **Slides:** Bhavya shares them and moves on at each `[NEXT SLIDE]`.
- **Demo:** Harshil shares Webots, only during the demo.
- **Pace:** written for about 130 words a minute. Learn it well enough to say it in your own words.

## Running order

| Time | Slides | Speaker |
|---|---|---|
| 0:00–3:00 | 1–3 | Bhavya |
| 3:00–6:30 | 4 | Devansh |
| 6:30–12:30 | 5–8 | Bhavya |
| 12:30–16:00 | 9 | Harshil |
| 16:00–19:30 | 10 | Shahvez |
| 19:30–22:00 | 11–12 | Bhavya |
| 22:00–26:00 | Live demo | Devansh, then Harshil |
| 26:00–28:30 | 13–14 | Shahvez |
| 28:30–30:00 | 15–17 | Bhavya, then everyone |

| Speaker | Speaking time |
|---|---|
| Bhavya | about 12 min |
| Harshil | about 6.5 min |
| Shahvez | about 6 min |
| Devansh | about 4.5 min |

## Before pressing Record

- [ ] Everyone has camera and microphone on, headphones in, and is in a quiet room.
- [ ] Zoom recording settings: *Record video during screen sharing* and *Place video next to the shared screen* are on. Free Zoom meetings with three or more people end at 40 minutes, which is enough.
- [ ] Harshil: latest `main` pulled, `worlds/parking_lot.wbt` open, run once and **Reset**, console visible with a large font.
- [ ] Harshil: `results/m3_webots_tuning/A2_tuned_demo.mp4` ready as a fallback.
- [ ] Bhavya: deck open on slide 1, in presenter mode.

---

## Slide 1: Title (Bhavya, 0:00–0:45)

> Hello everyone. We are Group G08, and this is project P13 for Algorithms for Intelligent Systems and Robotics: an **Autonomous Valet Parking Agent**.
>
> I'm Bhavya Talwar, and presenting with me are Devansh Singh Rawat, Mohammad Shahvez and Harshil Mittal. Each of us built one module of the system, and each of us will present our own part.
>
> The goal is easy to say. A car enters a parking lot with no driver. It finds a free bay, plans a route it can actually drive, and reverses itself into the bay without touching anything. It also has to cope when things change: when someone takes the bay it chose, or when a person steps in front of it.
>
> In the next half hour we'll explain how each part works, show what we measured, run it live in Webots, and finish with what we would improve.

`[NEXT SLIDE]`

## Slide 2: The task (Bhavya, 0:45–1:55)

> The task has three parts.
>
> First, **find** a free bay. The car has a 360-degree lidar, a laser scanner, and it has to tell taken bays from empty ones.
>
> Second, **plan** a route. This is harder than it sounds, because a car cannot turn on the spot. Our car has a 2.8-metre wheelbase, and its tightest possible turn is a circle of about 5.1 metres. Any route with a sharper bend is useless.
>
> Third, **park**, by reversing into a 2.5-metre bay between two parked cars, and stopping for anything that gets in the way.
>
> In agent terms, this environment is **partially observable**, because the lidar can't see behind parked cars, and **dynamic**, because bays get taken and people move. That's why the agent can't simply plan once and execute blindly.
>
> The brief asked for a deliberative planner for the route and reactive rules for the close-range manoeuvres. Everything runs in Webots, written in Python, in a lot with 40 bays. The same problem shows up in real smart car parks and in self-driving cars.

`[NEXT SLIDE]`

## Slide 3: Architecture (Bhavya, 1:55–3:00)

> To handle that, we built a **layered** intelligent agent. It follows the declarative, procedural and reflexive hierarchy from our syllabus, and it's the same split as Gat's three-layer architecture from robotics.
>
> At the top is the **deliberative** layer, my module, M2. It knows *what* to do: which bay to go to, and which route to take. It's slow, about a second per plan, so it runs rarely.
>
> Below it is the **procedural** layer, Harshil's state machine. It knows *how*: drive, align, reverse in, done.
>
> Then the **reflexive** layer, also Harshil's: a safety check that runs every step and stops the car the moment anything gets too close. It doesn't think; it reacts.
>
> At the bottom is **control**, Shahvez's module, which turns the route into steering and speed commands, every step.
>
> And Devansh's sensing module, M1, feeds all of them with the lidar, GPS and compass.
>
> The important design choice is that the layers talk to each other. When the reflex layer stops the car, the planner wakes up and plans again from where the car is. Devansh will start with the world and the sensors.

`[NEXT SLIDE]`

## Slide 4: World and sensors (Devansh, 3:00–6:30)

> Thanks, Bhavya. This is our world in Webots, seen from above.
>
> The lot is 40 by 34 metres, with the entrance in the left wall. There are four rows of ten bays, each 2.5 metres wide and 5 metres deep, so 40 bays in total. There are two aisles, and a kerb between the two middle rows, so the car can't cut across the island. Twenty-two bays have parked cars in them. The blue car on the left, at the entrance, is ours.
>
> Our car is a four-wheel Ackermann vehicle, 4.6 by 1.9 metres, with a 2.8-metre wheelbase. All four wheels have motors and the front two steer. In Ackermann steering, the inner front wheel turns more than the outer one, so both roll around the same centre.
>
> For sensing, the car has GPS and a compass for its position and heading, an IMU, four short-range distance sensors, and the main sensor: a 360-degree lidar with 721 rays and a 40-metre range.
>
> The lidar is how we find free bays. For each bay we check every ray against it. If a ray hits something inside the bay, the bay is **occupied**. If a ray passes right through the bay and lands beyond it, the bay is visible and empty, so it's **free**. If no ray reaches a bay, it stays **unknown**, and we never assume unknown means free. Sending the car to a taken bay is much worse than skipping a free one.
>
> We hit one subtle bug here. Rows A and D are against the outer walls. At first, a wall just behind an empty bay counted as a car, so free bays read as occupied. A parked car never extends past its bay's back line, so the detector now ignores returns beyond that line.
>
> Getting the sensors right took care. Webots returns the lidar scan clockwise, but our code expects anticlockwise, so we reverse it. The compass reports north in the car's own frame, so the heading is atan2 of its x and y readings. And the lidar was first mounted 0.28 metres above the axle, where it saw the car's own wheels. The planner thought the car was surrounded and couldn't plan anything. We raised it to 0.35 metres, above the tyres and below the body.
>
> Finally, the world and the planner must describe the same lot. So we wrote tests that read the world file and check every bay, every row and every parked car against the planner's map. If someone moves a bay in one place but not the other, the tests fail. Back to Bhavya for the planner.

`[NEXT SLIDE]`

## Slide 5: Why grid A* is not enough (Bhavya, 6:30–8:00)

> Thanks, Devansh. My module, M2, plans the route.
>
> The standard method is **A***, from Hart, Nilsson and Raphael in 1968. We turn the lot into an occupancy grid of 0.25-metre cells, 160 by 136 cells. Each cell is either free or blocked.
>
> Then we grow every obstacle by the size of the car. After that we can plan for the car as a single point. That's the configuration-space idea from LaValle's textbook.
>
> A* keeps a priority queue of cells ordered by f equals g plus h. g is the distance travelled so far; h is an estimate of the distance left. It always expands the cell with the lowest f. If the estimate never overestimates the true distance, the heuristic is called **admissible**, and A* is guaranteed to find the shortest path.
>
> We move in eight directions, so we use the **octile distance**: the straight part plus root-two times the diagonal part. On an empty grid, that's exactly the true cost, so it's admissible and as informative as possible.
>
> But there's a catch. On a grid, the path turns 45 or 90 degrees in an instant. A car can't. Its tightest turn has radius L over tan of the maximum steering angle: 2.8 over tan of 0.5, which is **5.13 metres**. A* also has no idea which way the car is facing. So A* gives the shortest route, but not one a car can drive.

`[NEXT SLIDE]`

## Slide 6: Hybrid A* (Bhavya, 8:00–10:00)

> So the planner we actually use is **Hybrid A***. It comes from Dolgov and colleagues at Stanford, who used it to drive through parking lots in the DARPA Urban Challenge. That's exactly our setting.
>
> It is still A*, the same f equals g plus h search, but with four changes.
>
> One: the state is the car's real **position and heading**, x, y and heading of the rear axle, as real numbers, not a grid cell.
>
> Two: to get from one state to the next, we actually **drive the car model**. We use the kinematic bicycle model, and drive it one metre with one of five steering angles: full left, half left, straight, half right, full right, forwards or in reverse. That's ten moves from each state. Every route is a chain of these arcs, so every route can be driven, by construction. We check each arc for collisions every 25 centimetres, using three circles that cover the car's body.
>
> Three: real-valued states would make the search infinite. So we sort them into bins of half a metre by half a metre by five degrees, and expand only one state per bin. That's the "hybrid" part: continuous states, grid-style bookkeeping.
>
> Four: the cost isn't just distance. Reversing costs double, steering costs a little, and every switch between forward and reverse costs extra. So the planner prefers calm forward driving and reverses only when it has to.
>
> To guide the search, before it starts we compute the shortest distance from every cell to the goal around the obstacles, with one Dijkstra pass. That steers the search along the aisles instead of into walls.
>
> One honest point: because binning throws states away, Hybrid A* doesn't guarantee the shortest route, only a drivable one.

`[NEXT SLIDE]`

## Slide 7: Planner comparison (Bhavya, 10:00–11:45)

> This is our first comparison. We planned six routes from the entrance, to bays in all four rows, with all three methods. We measured not just length and time, but whether the car could actually drive the result.
>
> Look at the "too tight" column first. That's how many metres of the route bend more sharply than the car can turn.
>
> Grid A* is the shortest and fastest, about 10 milliseconds. But on average 3.3 metres of each route is too tight to drive. The real car body would overlap an obstacle at four points along the route. And it arrives 52 degrees off the heading the parking manoeuvre needs.
>
> A* with **smoothing** rounds the corners, but knows nothing about the turning radius, so the too-tight length actually goes up slightly.
>
> **Hybrid A*** has zero metres too tight, zero collisions, and arrives within 3.4 degrees. The price is 8 per cent more length and about 0.4 seconds of planning time. For the farthest bay, C9, it takes 1.3 seconds.
>
> That's a good trade: the car plans once, at a standstill, then drives for a minute.

`[NEXT SLIDE]`

## Slide 8: Routes to bay C4 (Bhavya, 11:45–12:30)

> Here are the three routes to bay C4. Same start, same goal.
>
> Blue is A*. Look at this right-angle corner next to the parked cars. The red crosses mark where the real car would hit them, because A* treated the car as a small disc.
>
> Orange is smoothed A*: rounder, but still far too tight for a 5-metre turning circle.
>
> Green is Hybrid A*. It swings wide, stays clear of the cars, and reverses once, the dashed part, to line up with the aisle.
>
> Notice that the route doesn't go into the bay. It stops on the aisle beside it, at what we call the pre-park pose. From there, Harshil's module takes over.

`[NEXT SLIDE]`

## Slide 9: Parking manoeuvre (Harshil, 12:30–16:00)

> Thanks, Bhavya. My module, M3, does the final parking manoeuvre. It holds two of the four layers: the procedural layer and the reflexive layer.
>
> The procedural part is a **state machine**. It starts in **Search**, waiting while M1 finds free bays and M2 picks one.
>
> In **Drive**, I hand control to Shahvez's module to follow Bhavya's route, and I wait until it's finished and the car has fully stopped.
>
> In **Align**, the car moves forward to a turning point just past the bay, then stops and confirms its pose.
>
> In **Park**, it reverses along a quarter circle into the bay, then straight back. If it isn't centred, it stops and makes a short correction, at most twice, so it can never loop forever.
>
> **Done** is only declared after strict checks: the car must be stopped, within 15 centimetres of the bay centre, within 3 degrees of straight, and with all four corners of the body inside the bay.
>
> The reverse arc uses 85 per cent of full steering, which gives a radius of 6.19 metres. We deliberately don't use full lock, so there's steering left in reserve for corrections. While reversing, the steering follows the arc with pure-pursuit geometry, using feedback from the measured pose rather than replaying a fixed sequence.
>
> That brings me to the reflexive part, the **safety layer**. Every single step, it looks at the gap between the car body and the nearest obstacle, on all four sides. It stops the car immediately if any gap is under 15 centimetres, or under the distance the car needs to stop at its current speed. We work that out from a 0.2-second reaction time and a braking deceleration of one metre per second squared. At 1 metre per second the car needs 0.7 metres to stop, plus the 15-centimetre margin.
>
> The stop is **latched**: the car won't creep forward again on its own. The planner has to take over and decide what to do.
>
> Then I tuned it in Webots. Over 15 Webots runs I compared parking speeds and lookahead distances. Going from 0.35 to 0.45 metres per second, with a 0.55-metre lookahead, made parking about **19 per cent faster**, from 45 seconds to 37, and **halved** the final heading error, with no loss of clearance. Over to Shahvez for control.

`[NEXT SLIDE]`

## Slide 10: Path tracking (Shahvez, 16:00–19:30)

> Thank you, Harshil. My module, M4, is the control layer. It turns the planned route into steering and speed, every step.
>
> For steering, we compared two classic controllers.
>
> **Pure pursuit** picks a point on the route a fixed distance ahead, the lookahead, and steers along the circle that passes through it. The steering angle is the arctangent of 2L sin alpha over the lookahead distance.
>
> **Stanley**, from Stanford's winning DARPA Grand Challenge car, steers by the heading error plus a term that grows with the sideways error, measured at the front axle.
>
> This table is our second comparison, on an L-shaped route that ends with a reverse park. Pure pursuit tracks well in both directions: about 10 centimetres of RMS error forward, 2.3 in reverse, and it parks.
>
> Plain Stanley works forward but **fails in reverse**: 42 centimetres of error, and it doesn't park. Stanley is built around the front axle, and when the car reverses that reference is on the wrong end. We fixed it with **curvature feed-forward**: we steer in advance for the bend the route is about to take. The reverse error drops from 42 centimetres to 1.8, and it parks. The straight and tight routes show the same pattern. The integrated agent uses Stanley with feed-forward.
>
> We also tuned them. A longer pure-pursuit lookahead steers more smoothly but cuts corners: the final sideways error grows from 0.3 centimetres to 18. And Stanley's gain can't be too high: at 8 it oscillates and never parks.
>
> For speed we use a **PID** controller. P alone leaves a steady error, so we need the integral term, and the derivative term added overshoot without helping. What really mattered was **feed-forward**, steering the throttle from the planned acceleration. Without it, the car stopped 39 centimetres off its target and never parked. With it, the error is under a centimetre.
>
> We also tested with GPS noise: a simple pose filter keeps parking at 100 per cent even with 20 centimetres of noise. Back to Bhavya, to show how all four modules run together.

`[NEXT SLIDE]`

## Slide 11: Integration (Bhavya, 19:30–20:45)

> Thanks, Shahvez. Building each module was half the work. Joining them was the other half.
>
> All four modules run in one loop, in a single Python class. The exact same code runs in Webots and in an offline simulator we wrote, with a ray-cast lidar and the same bicycle model. Only the source of the sensor data changes, so what we measure offline is the code that runs in Webots.
>
> **Every step**, the lidar gives the gaps around the car, Harshil's module decides what to do, and Shahvez's module drives the motors.
>
> **Every second**, the planner checks two things: is my bay still free, and is the rest of my route still clear?
>
> **If not**, the car stops and plans again from where it is: to the same bay if it can still reach it, otherwise to the next best one. A safety stop on the route also triggers a new plan, so the reflex and the planner work together.
>
> If nothing can be planned, for example while a pedestrian blocks the aisle, it waits five seconds and tries again. And if it's stopped three times in a row without moving 10 centimetres, it reports that it's **boxed in** and fails cleanly, instead of looping forever.
>
> Choosing a bay quickly matters too. Hybrid A* for every free bay would take many seconds. So we rank all free bays with fast grid A*, a few milliseconds each, and run Hybrid A* only on the best one.

`[NEXT SLIDE]`

## Slide 12: Where the route ends (Bhavya, 20:45–22:00)

> The biggest lesson from integration: **where the route ends decides whether parking works.**
>
> At first, the route ended on the centre line of the aisle. In our first integrated run, the reverse swing touched the next parked car. Here's why. The car reverses on a circle of radius 6.19 metres. The inner side of the car body sweeps a circle of radius 6.19 minus half the width, 5.24 metres. From the centre line, the neighbour's corner sits exactly 5.24 metres from the centre of that circle: zero gap. Moving the end point 4 metres out from the bay, half a metre further, leaves a gap of 0.2 metres, and the simulation measured 0.19.
>
> Second, Hybrid A* only gets within half a metre of its goal, but parking allows about 0.3. So we stop the search 5 metres early and join the last 5 metres to the exact point with a **cubic curve**, checked for curvature and for collisions. It's a few lines of algebra instead of Reeds–Shepp curves.
>
> Third, Harshil's manoeuvre needs about 6.5 metres to set up past the bay. At the last bay in a row, that runs into the wall, so the planner now approaches end bays from the other side.
>
> All three came from running the whole chain; each module had passed its own tests. Now let's see it live. Over to Devansh and Harshil.

`[STOP SHARING. Harshil shares the Webots window.]`

## Live demo (Devansh, then Harshil, 22:00–26:00)

**Devansh (about 45 seconds, before Run):**

> This is the world from slide 4, live in Webots. Our car is at the entrance on the left. It knows the layout of the lot, the walls and where the bays are, but **not** which bays are free. It has to find that out with its lidar, exactly as I described. Harshil, go ahead.

**Harshil (presses Run, then narrates):**

> I'm pressing Run. The controller is the full agent: all four of our modules in one loop.
>
> *(after about 1 second)* In the console you can see it has scanned the lot, chosen **bay A2**, and planned a route in about a second. That's Bhavya's planner choosing the closest reachable bay.
>
> *(car driving)* Now it's in **Drive**. Shahvez's controller follows the route at one metre per second. The status line says "Driving to slot A2". Every second, the planner checks the bay is still free and the route is still clear.
>
> *(around 16 s, ALIGN)* The route has ended beside the bay, 4 metres out from it. The state machine switches to **Align**, and the car drives forward past the bay to its turning point, at 0.45 metres per second.
>
> *(around 25 s, PARK)* Now **Park**. It's reversing along the quarter circle. The safety layer checks the gap to the neighbouring cars every step.
>
> *(car straightening)* Now it straightens up and backs into the bay...
>
> *(around 53 s)* The console says **DONE, Parking completed**, at about 53 seconds.
>
> Our offline simulator predicted 52.9 seconds for this exact run. Every phase starts within 0.15 seconds of the prediction, which is why we trust the offline tests you'll see next.

`[STOP SHARING. Bhavya shares the slides again.]`

**If the live run fails:**

> Harshil: That didn't go as planned. Here's a recording of the same run from our tests.

Play `A2_tuned_demo.mp4` and narrate it the same way. Don't spend more than 15 seconds troubleshooting live.

## Slide 13: Scenarios (Shahvez, 26:00–27:15)

> Thank you. Now the results. Besides the normal run you just saw, we tested two cases where the world changes during the drive.
>
> In the **normal** run, it parks in A2 in 53 seconds with no replanning. The closest it came to anything was 20 centimetres.
>
> In the second, **another car takes our bay** three seconds into the drive. On its next check, the agent notices, stops, replans once, and parks in B0 instead, in 55 seconds.
>
> In the third, a **pedestrian** steps onto the route 6 metres ahead and leaves ten seconds later. The plot on the right shows it. The dotted lines are routes the agent abandoned; the red dots are where it was braking. It stops, replans twice, waits until the way is clear, and parks in A2 after 78 seconds.
>
> All three end within 5.2 centimetres of the bay centre and a tenth of a degree of straight. In Webots, the full agent parked in A2, B0 and A5 in every run.

`[NEXT SLIDE]`

## Slide 14: Every bay (Shahvez, 27:15–28:30)

> One demo can hide a lot, so we tried to park in **every one of the 40 bays**, each time with cars on both sides, which is the hardest case.
>
> It parked in **34 of 40, 85 per cent**: 9 out of 10 in rows A, B and D, and 7 out of 10 in row C.
>
> Most importantly, there was **no contact in any of the 40 runs**. The closest the car body ever came to an obstacle was 7 centimetres.
>
> The six failures are all at or next to the ends of the aisles. There, reaching the bay needs a multi-point turn in a tight space, or the reverse swing passes the end wall too closely. Every time, the safety layer stopped the car before it touched anything, so it failed safely.
>
> This test also found four bugs that a single demo would have missed, and each was fixed. After Harshil's Webots tuning we ran it again: still 34 out of 40, and 11 per cent faster. Back to Bhavya to wrap up.

`[NEXT SLIDE]`

## Slide 15: Novelty (Bhavya, 28:30–29:10)

> Each method we used is known. What's new is **how the layers fit together**, and how carefully we measured it:
>
> - a planner comparison measured on whether the car can drive the route, not just length and time;
> - a hand-over point worked out from the parking manoeuvre's own geometry;
> - an exact final approach with a simple cubic curve instead of Reeds–Shepp curves;
> - a two-stage bay choice, fast A* to rank and Hybrid A* to plan;
> - safety stops that trigger replanning, with a clean "boxed in" failure;
> - and parking success measured in all 40 bays, then confirmed in Webots.

`[NEXT SLIDE]`

## Slide 16: Who built what (everyone, 29:10–29:40)

Each person says one sentence, in this order:

> **Devansh:** I built the Webots world, the car with its motors and sensors, and free-bay detection from the lidar.
>
> **Bhavya:** I built the route planner, A* and Hybrid A*, the replanning, and the integration that runs all four modules together.
>
> **Harshil:** I built the parking state machine, the reverse manoeuvre and the safety stops, and tuned it in Webots.
>
> **Shahvez:** I built path tracking and speed control, and the Pure Pursuit versus Stanley experiments.
>
> **Bhavya:** Each of us committed our own code from our own GitHub account, through pull requests checked by automated tests.

`[NEXT SLIDE]`

## Slide 17: Conclusion (Bhavya, 29:40–30:00)

> To conclude: we built a layered agent that parks safely, and knows when it can't.
>
> Hybrid A* gives drivable routes where A* does not. The agent parks in 85 per cent of bays with no contact, and replans when a bay is taken or the way is blocked.
>
> Next, we'd like better tracking through changes of direction, a smarter set-up for end-of-aisle bays, and parallel parking.
>
> Thank you for watching.

**Everyone:** Thank you.

`[STOP RECORDING]`

---

## Timing check

Practise once with a timer.

| If you are... | Then |
|---|---|
| Over 31 minutes | Shorten slides 5, 6 and 10 first; keep the demo intact |
| Under 29 minutes | Let the demo run with more narration, and spend longer on the pedestrian plot on slide 13 |
