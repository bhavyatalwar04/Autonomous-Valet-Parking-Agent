"""Unit tests for M4 (m4_control/): PID, path handling, the two steering
controllers, the pose filter, the path follower and the M4 controller that the
integrated agent calls.

The last group re-runs experiment E1 on two scenarios and checks the result the
report relies on: Pure Pursuit and Stanley with feed-forward park, plain
Stanley does not, because it fails when reversing.
"""
import math
import unittest

import numpy as np

from behaviours.parking_types import ControlMode, ParkingCommand, ParkingState, Pose
from m4_control.estimator import PoseFilter
from m4_control.follower import FollowerConfig, PathFollower
from m4_control.lateral import PurePursuit, Stanley
from m4_control.m4_controller import M4Controller
from m4_control.metrics import summarize
from m4_control.path import Path, fillet_polyline, resample, wrap
from m4_control.pid import PID
from m4_control.scenarios import scenario_L_route, scenario_straight
from m4_control.sim import run_episode

DT = 0.02


def straight_path(length=20.0, direction=1):
    """A straight path along +x, driven forward (1) or in reverse (-1)."""
    xy = np.c_[np.linspace(0.0, length, 41), np.zeros(41)]
    return Path.from_points(xy, np.full(len(xy), direction))


class TestPID(unittest.TestCase):
    def test_proportional_only(self):
        pid = PID(kp=2.0, out_min=-10, out_max=10)
        self.assertAlmostEqual(pid.step(1.5, DT), 3.0)

    def test_integral_accumulates(self):
        pid = PID(kp=0.0, ki=1.0, out_min=-10, out_max=10)
        for _ in range(50):
            out = pid.step(1.0, DT)
        # the integral term is added after the output is formed, so after
        # 50 steps the output holds 49 steps' worth: 49 * 1.0 * 0.02
        self.assertAlmostEqual(out, 0.98, places=6)

    def test_output_is_clipped(self):
        pid = PID(kp=100.0, out_min=-1.0, out_max=2.0)
        self.assertEqual(pid.step(5.0, DT), 2.0)
        self.assertEqual(pid.step(-5.0, DT), -1.0)

    def test_no_windup_while_saturated(self):
        # Held at the limit for a long time, the integral must not keep growing,
        # or the controller overshoots badly when the error changes sign.
        pid = PID(kp=10.0, ki=5.0, out_min=-1.0, out_max=1.0)
        for _ in range(500):
            pid.step(1.0, DT)
        self.assertLess(pid.i, 1.0)

    def test_reset(self):
        pid = PID(kp=1.0, ki=1.0, kd=1.0)
        for _ in range(10):
            pid.step(1.0, DT)
        pid.reset()
        self.assertEqual(pid.i, 0.0)
        self.assertIsNone(pid.prev_err)


class TestPath(unittest.TestCase):
    def test_wrap_range(self):
        for a in np.linspace(-10, 10, 101):
            w = wrap(a)
            self.assertGreaterEqual(w, -math.pi)
            self.assertLess(w, math.pi)
            self.assertAlmostEqual(math.cos(w), math.cos(a), places=9)
            self.assertAlmostEqual(math.sin(w), math.sin(a), places=9)

    def test_resample_spacing(self):
        xy = resample([[0, 0], [10, 0], [10, 5]], ds=0.1)
        steps = np.hypot(*np.diff(xy, axis=0).T)
        self.assertTrue(np.allclose(steps, 0.1, atol=0.01))
        self.assertTrue(np.allclose(xy[0], [0, 0]) and np.allclose(xy[-1], [10, 5]))

    def test_fillet_rounds_a_right_angle(self):
        # An A*-style 90 degree corner becomes an arc no tighter than the radius.
        pts = fillet_polyline([[0, 0], [20, 0], [20, 20]], radius=6.0)
        self.assertTrue(np.allclose(pts[0], [0, 0]) and np.allclose(pts[-1], [20, 20]))
        seg = Path.from_points(resample(pts, 0.05)).segments[0]
        inner = slice(5, seg.n_real - 5)
        self.assertLess(np.max(np.abs(seg.kappa[inner])), 1 / 6.0 * 1.15)

    def test_split_at_gear_changes(self):
        xy = np.c_[np.arange(10.0), np.zeros(10)]
        d = np.array([1, 1, 1, 1, -1, -1, -1, 1, 1, 1])
        path = Path.from_points(xy, d)
        self.assertEqual([s.direction for s in path.segments], [1, -1, 1])

    def test_target_pose_of_a_reverse_segment(self):
        # Reversing along +x means the car's nose points along -x.
        x, y, yaw = straight_path(direction=-1).target_pose
        self.assertAlmostEqual(abs(wrap(yaw)), math.pi, places=6)
        self.assertAlmostEqual(x, 20.0, places=6)

    def test_lateral_error_sign(self):
        seg = straight_path().segments[0]
        left, _ = seg.lateral_error(5.0, 0.4)
        right, _ = seg.lateral_error(5.0, -0.4)
        self.assertAlmostEqual(left, 0.4, places=6)
        self.assertAlmostEqual(right, -0.4, places=6)


class TestSteering(unittest.TestCase):
    def setUp(self):
        self.fwd = straight_path().segments[0]
        self.rev = straight_path(direction=-1).segments[0]

    def steer(self, ctrl, seg, y, yaw, v):
        x = 5.0
        rx, ry = ctrl.ref_point(x, y, yaw, seg.direction)
        i = seg.nearest(rx, ry)
        return ctrl.steer(seg, i, x, y, yaw, v)

    def test_on_the_path_means_straight_wheels(self):
        for ctrl in (PurePursuit(L=2.8), Stanley(L=2.8), Stanley(L=2.8, use_ff=True)):
            self.assertAlmostEqual(self.steer(ctrl, self.fwd, 0.0, 0.0, 1.0), 0.0, places=6, msg=ctrl.name)

    def test_steers_back_towards_the_path(self):
        # Car 0.5 m to the right of the path, driving forward: steer left (+).
        # Car 0.5 m to the left: steer right (-).
        for ctrl in (PurePursuit(L=2.8), Stanley(L=2.8)):
            self.assertGreater(self.steer(ctrl, self.fwd, -0.5, 0.0, 1.0), 0.0, ctrl.name)
            self.assertLess(self.steer(ctrl, self.fwd, 0.5, 0.0, 1.0), 0.0, ctrl.name)

    def test_steers_back_when_reversing(self):
        # Reversing along +x with the nose towards -x. The car is 0.5 m to the
        # left of the path (y = +0.5) in world terms. Turning the wheels to the
        # car's right (-) while reversing swings the rear axle back towards y = 0.
        for ctrl in (PurePursuit(L=2.8), Stanley(L=2.8)):
            s = self.steer(ctrl, self.rev, 0.5, math.pi, -0.5)
            self.assertNotEqual(s, 0.0, ctrl.name)
            # simulate a short reverse move with that steering and check it helps
            x, y, yaw = 5.0, 0.5, math.pi
            for _ in range(25):
                yaw += -0.5 * math.tan(s) / 2.8 * DT
                x += -0.5 * math.cos(yaw) * DT
                y += -0.5 * math.sin(yaw) * DT
            self.assertLess(abs(y), 0.5, ctrl.name)

    def test_feed_forward_only_acts_in_reverse(self):
        # Forward, Stanley's front-axle reference already carries the curvature,
        # so feed-forward must not change the output.
        path = Path.from_points(fillet_polyline([[0, 0], [10, 0], [10, 10]], 5.0))
        seg = path.segments[0]
        i = seg.n_real // 2
        x, y = seg.x[i], seg.y[i]
        yaw = seg.phi[i]
        plain = Stanley(L=2.8).steer(seg, i, x, y, yaw, 1.0)
        ff = Stanley(L=2.8, use_ff=True).steer(seg, i, x, y, yaw, 1.0)
        self.assertAlmostEqual(plain, ff, places=9)


class TestPoseFilter(unittest.TestCase):
    def test_first_update_takes_the_measurement(self):
        f = PoseFilter(L=2.8)
        self.assertEqual(f.update(1.0, 2.0, 0.3, 0.0, 0.0, DT), (1.0, 2.0, 0.3))

    def test_full_gain_follows_the_measurement(self):
        f = PoseFilter(L=2.8, alpha=1.0, beta=1.0)
        f.update(0.0, 0.0, 0.0, 1.0, 0.0, DT)
        x, y, yaw = f.update(3.0, 4.0, 0.5, 1.0, 0.0, DT)
        self.assertAlmostEqual(x, 3.0)
        self.assertAlmostEqual(y, 4.0)
        self.assertAlmostEqual(yaw, 0.5)

    def test_smooths_noise(self):
        rng = np.random.default_rng(0)
        f = PoseFilter(L=2.8)
        err_raw, err_filt = [], []
        for k in range(500):
            true_x = k * DT * 1.0
            zx = true_x + rng.normal(0, 0.2)
            fx, _, _ = f.update(zx, 0.0, 0.0, 1.0, 0.0, DT)
            if k > 50:
                err_raw.append(zx - true_x)
                err_filt.append(fx - true_x)
        self.assertLess(np.std(err_filt), 0.5 * np.std(err_raw))


class TestFollower(unittest.TestCase):
    def test_emergency_stop_brakes_hard(self):
        cfg = FollowerConfig(max_steer=0.5)
        fol = PathFollower(straight_path(), PurePursuit(L=2.8), cfg)
        cmd = fol.step(0.0, 0.0, 0.0, 1.0, DT, estop=True)
        self.assertEqual(cmd.accel, -cfg.a_brk)
        self.assertEqual(cmd.v_ref, 0.0)

    def test_steering_respects_the_limit(self):
        cfg = FollowerConfig(max_steer=0.3)
        fol = PathFollower(straight_path(), PurePursuit(L=2.8), cfg)
        cmd = fol.step(0.0, -3.0, 0.0, 1.0, DT)     # far off the path
        self.assertLessEqual(abs(cmd.steer), 0.3 + 1e-12)

    def test_drives_a_straight_path_to_the_end(self):
        path = straight_path()
        log = run_episode(path, PurePursuit(L=2.7), init_offset=(0.0, 0.0), t_max=60.0)
        self.assertTrue(log["done"])
        self.assertTrue(summarize(log, path)["success"])


class TestM4Controller(unittest.TestCase):
    def setUp(self):
        self.m4 = M4Controller(straight_path(), Stanley(L=2.8, use_ff=True), max_steer=0.5)
        self.pose = Pose(0.0, 0.0, 0.0)

    def test_follow_route_mode_uses_the_follower(self):
        act = self.m4.step(ParkingCommand(ParkingState.DRIVE, ControlMode.FOLLOW_ROUTE), self.pose, 0.0, DT)
        self.assertEqual(act.mode, "follow_route")
        self.assertEqual(act.direction, 1)
        self.assertFalse(self.m4.route_complete)

    def test_emergency_stop_is_a_hard_brake(self):
        cmd = ParkingCommand(ParkingState.EMERGENCY_STOP, ControlMode.STOP)
        act = self.m4.step(cmd, self.pose, 1.0, DT)
        self.assertTrue(act.hard_brake)
        self.assertEqual(act.accel, -self.m4.cfg.a_brk)
        self.assertEqual(act.mode, "emergency_stop")

    def test_parking_mode_applies_m3_steering_within_limits(self):
        cmd = ParkingCommand(ParkingState.PARK, ControlMode.PARKING, -0.4, 0.9)
        act = self.m4.step(cmd, self.pose, 0.0, DT)
        self.assertEqual(act.steer, 0.5)               # clipped to max_steer
        self.assertEqual(act.direction, -1)            # stopped, so reverse is allowed

    def test_no_gear_change_while_moving(self):
        cmd = ParkingCommand(ParkingState.PARK, ControlMode.PARKING, -0.4, 0.0)
        act = self.m4.step(cmd, self.pose, 0.5, DT)    # still rolling forward
        self.assertEqual(act.direction, 1)


class TestExperimentE1(unittest.TestCase):
    """The controller comparison the report quotes (results/m4/tables.md, E1)."""

    def run_all(self, scenario):
        path = scenario()
        out = {}
        for name, ctrl in (("pp", PurePursuit()), ("stanley", Stanley()), ("ff", Stanley(use_ff=True))):
            out[name] = summarize(run_episode(path, ctrl), path)
        return out

    def test_l_route(self):
        r = self.run_all(scenario_L_route)
        self.assertTrue(r["pp"]["success"])
        self.assertTrue(r["ff"]["success"])
        self.assertFalse(r["stanley"]["success"])
        # plain Stanley fails in reverse; feed-forward fixes it
        self.assertGreater(r["stanley"]["rms_cte_rev"], 0.3)
        self.assertLess(r["ff"]["rms_cte_rev"], 0.05)
        self.assertLess(r["pp"]["rms_cte_rev"], 0.05)

    def test_straight(self):
        r = self.run_all(scenario_straight)
        self.assertTrue(r["pp"]["success"] and r["ff"]["success"])
        self.assertFalse(r["stanley"]["success"])


if __name__ == "__main__":
    unittest.main()
